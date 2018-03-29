from flask import Flask

SECRET_KEY = 'ssshhhh'
SECRET_KEY = 'ssshhhh'
REDIS_HOST = 'localhost'

app = Flask(__name__)
app.config.from_object(__name__)
