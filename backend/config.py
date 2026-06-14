import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-dev-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(basedir, '..', 'database', 'shared_expenses.db')}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    USD_TO_INR_RATE = float(os.environ.get("USD_TO_INR_RATE", "83.0"))
    UPLOAD_FOLDER = os.path.join(basedir, "..", "uploads")
