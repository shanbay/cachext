from flask import Flask

from cachext import Cachext

SECRET_KEY = 'ssshhhh'

app = Flask(__name__)
app.config.from_object(__name__)

cache = Cachext()
cache.init_app(app)
