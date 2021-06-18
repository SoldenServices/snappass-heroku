import os
import re
import sys
import uuid

import redis
import environ

from cryptography.fernet import Fernet
from flask import abort, Flask, render_template, request
from redis.exceptions import ConnectionError
from werkzeug.urls import url_quote_plus
from werkzeug.urls import url_unquote_plus
from flask_s3 import FlaskS3


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env = environ.Env(
    DEBUG=(bool, False),
    USE_S3=(bool, False),
    NO_SSL=(bool, False),
    MOCK_REDIS=(bool, False),
    USE_CDN=(bool, False),
)
env.read_env()

SNEAKY_USER_AGENTS = (
    "Slackbot",
    "facebookexternalhit",
    "Twitterbot",
    "Facebot",
    "WhatsApp",
    "SkypeUriPreview",
    "Iframely",
    "Google",
)
SNEAKY_USER_AGENTS_RE = re.compile("|".join(SNEAKY_USER_AGENTS))
NO_SSL = env("NO_SSL")
URL_PREFIX = env("URL_PREFIX", default=None)
TOKEN_SEPARATOR = "~"


def start_app():
    flask_app = Flask(__name__)
    debug = env("DEBUG")
    use_S3 = env("USE_S3")

    if use_S3:
        s3 = FlaskS3()
        flask_app.config["FLASKS3_BUCKET_NAME"] = env("S3_BUCKET_NAME")
        flask_app.config["FLASKS3_ACTIVE"] = use_S3
        if env("USE_CDN"):
            flask_app.config["FLASKS3_CDN_DOMAIN"] = env("CDN_DOMAIN")
        s3.init_app(flask_app)

    flask_app.debug = debug
    return flask_app


# Initialize Flask Application
app = start_app()

app.secret_key = env("SECRET_KEY")
app.config["STATIC_URL"] = env("STATIC_URL", default="static")

if app.debug is True:
    from flask_debugtoolbar import DebugToolbarExtension

    toolbar = DebugToolbarExtension(app)


# Initialize Redis
if env("MOCK_REDIS"):
    from fakeredis import FakeStrictRedis

    redis_client = FakeStrictRedis()
elif env("REDIS_URL"):
    redis_client = redis.StrictRedis.from_url(env("REDIS_URL"))
else:
    redis_host = env("REDIS_HOST", default="localhost")
    redis_port = env("REDIS_PORT", default=6379)
    redis_db = env("SNAPPASS_REDIS_DB", default=0)
    redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)
REDIS_PREFIX = env("REDIS_PREFIX", default="snappass")

TIME_CONVERSION = {"week": 604800, "day": 86400, "hour": 3600}


def check_redis_alive(fn):
    def inner(*args, **kwargs):
        try:
            if fn.__name__ == "main":
                redis_client.ping()
            return fn(*args, **kwargs)
        except ConnectionError as e:
            print("Failed to connect to redis! %s" % e.message)
            if fn.__name__ == "main":
                sys.exit(0)
            else:
                return abort(500)

    return inner


def encrypt(password):
    """
    Take a password string, encrypt it with Fernet symmetric encryption,
    and return the result (bytes), with the decryption key (bytes)
    """
    encryption_key = Fernet.generate_key()
    fernet = Fernet(encryption_key)
    encrypted_password = fernet.encrypt(password.encode("utf-8"))
    return encrypted_password, encryption_key


def decrypt(password, decryption_key):
    """
    Decrypt a password (bytes) using the provided key (bytes),
    and return the plain-text password (bytes).
    """
    fernet = Fernet(decryption_key)
    return fernet.decrypt(password)


def parse_token(token):
    token_fragments = token.split(TOKEN_SEPARATOR, 1)  # Split once, not more.
    storage_key = token_fragments[0]

    try:
        decryption_key = token_fragments[1].encode("utf-8")
    except IndexError:
        decryption_key = None

    return storage_key, decryption_key


@check_redis_alive
def set_password(password, ttl):
    """
    Encrypt and store the password for the specified lifetime.

    Returns a token comprised of the key where the encrypted password
    is stored, and the decryption key.
    """
    storage_key = REDIS_PREFIX + uuid.uuid4().hex
    encrypted_password, encryption_key = encrypt(password)
    redis_client.setex(storage_key, ttl, encrypted_password)
    encryption_key = encryption_key.decode("utf-8")
    token = TOKEN_SEPARATOR.join([storage_key, encryption_key])
    return token


@check_redis_alive
def get_password(token):
    """
    From a given token, return the initial password.

    If the token is tilde-separated, we decrypt the password fetched from Redis.
    If not, the password is simply returned as is.
    """
    storage_key, decryption_key = parse_token(token)
    password = redis_client.get(storage_key)
    redis_client.delete(storage_key)

    if password is not None:

        if decryption_key is not None:
            password = decrypt(password, decryption_key)

        return password.decode("utf-8")


@check_redis_alive
def password_exists(token):
    storage_key, decryption_key = parse_token(token)
    return redis_client.exists(storage_key)


def empty(value):
    if not value:
        return True


def clean_input():
    """
    Make sure we're not getting bad data from the front end,
    format data to be machine readable
    """
    if empty(request.form.get("password", "")):
        abort(400)

    if empty(request.form.get("ttl", "")):
        abort(400)

    time_period = request.form["ttl"].lower()
    if time_period not in TIME_CONVERSION:
        abort(400)

    return TIME_CONVERSION[time_period], request.form["password"]


def request_is_valid(request):
    """
    Ensure the request validates the following:
        - not made by some specific User-Agents (to avoid chat's preview feature issue)
    """
    return not SNEAKY_USER_AGENTS_RE.search(request.headers.get("User-Agent", ""))


@app.route("/", methods=["GET"])
def index():
    return render_template("set_password.html")


@app.errorhandler(404)
def page_not_found(e):
    """Add in ability to render a clean error page"""
    return render_template("404.html"), 404


@app.route("/", methods=["POST"])
def handle_password():
    ttl, password = clean_input()
    token = set_password(password, ttl)

    if NO_SSL:
        base_url = request.url_root
    else:
        base_url = request.url_root.replace("http://", "https://")
    if URL_PREFIX:
        base_url = base_url + URL_PREFIX.strip("/") + "/"
    link = base_url + url_quote_plus(token)
    return render_template("confirm.html", password_link=link)


@app.route("/<password_key>", methods=["GET"])
def preview_password(password_key):
    password_key = url_unquote_plus(password_key)
    if not request_is_valid(request):
        abort(404)
    if not password_exists(password_key):
        abort(404)

    return render_template("preview.html")


@app.route("/<password_key>", methods=["POST"])
def show_password(password_key):
    password_key = url_unquote_plus(password_key)
    password = get_password(password_key)
    if not password:
        abort(404)

    return render_template("password.html", password=password)


@check_redis_alive
def main():
    app.run(host="0.0.0.0")


if __name__ == "__main__":
    main()
