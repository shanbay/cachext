# 与 Sea 的集成

`configs/default/cache.py`

```python
CACHE_BACKEND = 'Redis'
CACHE_HOST = 'localhost'
```

`app/extensions`

```python
from cachext.ext import Cache
cache = Cache()
```

`testcode.py`

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
