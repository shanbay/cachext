# 与 Flask 的集成

## 创建一个 flask app

```python
from flask import Flask
from cachext.ext import Cache

SECRET_KEY = 'ssshhhh'
CACHE_BACKEND = 'Redis'
CACHE_HOST = 'localhost'

app = Flask(__name__)
app.config.from_object(__name__)

cache = Cache()
cache.init_app(app)
```

## 使用 cache

```python
from app.extensions import cache

count = 1

@cache.cached
def query():
    count += 1
    return count

cache.set('key', 'value')
cache.get('key')   # 'value'
testcode.query()   # 2
testcode.query()   # 2
testcode.query.uncached()  # 3
```
