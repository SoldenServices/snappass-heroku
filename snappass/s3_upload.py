from flask_s3 import FlaskS3, create_all
from flask import Flask
import environ

env = environ.Env(
)
env.read_env()

app = Flask(__name__)
app.config["STATIC_URL"] = env("STATIC_URL", default="static")
app.config["FLASKS3_BUCKET_NAME"] = env("S3_BUCKET_NAME")
s3 = FlaskS3(app)

create_all(app)

