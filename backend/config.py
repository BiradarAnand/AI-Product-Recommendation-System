import os
class Config:
    SECRET_KEY = "supersecretkey"
    JWT_SECRET_KEY = "jwtsecret"
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:Passwordmysql@127.0.0.1:3305/ecommerce"
SQLALCHEMY_TRACK_MODIFICATIONS = False