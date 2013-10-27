import os
from urlparse import urlparse

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from redis import StrictRedis

from BlockingConnectionPool import BlockingConnectionPool

app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(os.path.realpath(__file__)), '../public'),
    static_url_path='/public')

db = SQLAlchemy(app)

def make_redis():
    if os.environ.get('DEBUG'):
        app.config["DEBUG"] = True
    app.config["REDIS_URL"] = os.environ.get("REDIS_URL")
    app.config["REDIS_MAX_CONNECTIONS"] = int(os.environ.get("REDIS_MAX_CONNECTIONS"))


    redis_connection = {}
    redis_connection['url'] = urlparse(app.config["REDIS_URL"])
    redis_connection['connection_pool'] = BlockingConnectionPool(
            max_connections=app.config["REDIS_MAX_CONNECTIONS"],
            host=redis_connection['url'].hostname,
            port=redis_connection['url'].port,
            password=redis_connection['url'].password
    )
    redis_connection['client'] = StrictRedis(connection_pool=redis_connection['connection_pool'])
    return redis_connection['client']
r = make_redis()

if app.config["DEBUG"]:
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
    db.engine.echo = True

from . import views, models