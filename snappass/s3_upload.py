from flask_s3 import FlaskS3, create_all
from flask import Flask
import environ

env = environ.Env()
env.read_env()

filepath_headers = {
    r".css$": {
        "Content-Type": "text/css; charset=utf-8",
    },
    r".js$": {"Content-Type": "application/javascript; charset=utf-8"},
}

general_headers = {
    "Cache-Control": "max-age=86400",
}

app = Flask(__name__)
app.config["STATIC_URL"] = env("STATIC_URL", default="static")
app.config["FLASKS3_BUCKET_NAME"] = env("S3_BUCKET_NAME")
app.config["FLASKS3_FILEPATH_HEADERS"] = filepath_headers
app.config["FLASKS3_HEADERS"] = general_headers
s3 = FlaskS3(app)

create_all(app)
