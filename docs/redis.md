# cachext.exts.Redis

方便在 `sea`/`flask`中使用 redis

## 快速入门

以 `flask` 为例：

```python
from flask import Flask
from cachext.ext import Redis

SECRET_KEY = 'ssshhhh'
REDIS_HOST = 'localhost'

app = Flask(__name__)
app.config.from_object(__name__)

redis = Redis()
redis.init_app(app)

redis.zadd('my-key', 1.1, 'name1', 2.2, 'name2', name3=3.3, name4=4.4)
```

## 相关配置

`REDIS_*`

> 所有配置去掉 `REDIS_`前缀并且小写化，会作为字典参数传递给 `redis.ConnectionPool`

**注意：`REDIS_` 为默认的配置前缀，可以在初始化 Redis 对象时通过指定 `ns` 参数改变。例如：**

```python
redis = cachext.exts.Redis(ns='XXX_')
```

会读取： `XXX_HOST`, `XXX_PORT` 等配置。


## 接口

同 `redis.StrictRedis`
