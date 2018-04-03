# Backends

## Backend API

#### Backend.get(key)

#### Backend.get_many(keys)

> `keys` 为 key 的 list

#### Backend.set(key, value, ttl=None)

#### Backend.set_many(keys, mapping, ttl=None)

> `mapping` 为 dict, 格式为 {key: value}

#### Backend.delete(key)

#### Backend.delete_many(keys)

#### Backend.incr(key, delta)

#### Backend.decr(key, delta)

#### Backend.expire(key, seconds)

#### Backend.expireat(key, timestamp)

#### Backend.ttl(key)

> key 的当前 ttl 值

#### Backend.exists(key)

#### Backend.clear()

> 清空所有缓存

## 内置 Backend

内置 Redis, Memcached, Simple 三个 cache backend

不同的Backend需要不同的额外参数来初始化，这些额外参数来自配置，例如 `CACHE_HOST="localhost"`, `CACHE_PORT=6379`, `CACHE_DB=0` 最终会以 `**{'host': 'localhost', 'port': 6379, 'db': 0}` 的形式作为额外参数传给 Backend。

不同的backend接受的额外参数如下：

#### Redis

```python
(host='localhost', port=6379,
db=0, password=None, socket_timeout=None,
socket_connect_timeout=None,
socket_keepalive=None, socket_keepalive_options=None,
connection_pool=None, unix_socket_path=None,
encoding='utf-8', encoding_errors='strict',
charset=None, errors=None,
decode_responses=False, retry_on_timeout=False,
ssl=False, ssl_keyfile=None, ssl_certfile=None,
ssl_cert_reqs=None, ssl_ca_certs=None,
max_connections=None)
```

- Redis [redis.StrictRedis](https://github.com/andymccurdy/redis-py/blob/5109cb4f6b610e8d5949716a16435afbbf35075a/redis/client.py#L490)
- Memcached [pylibmc.Client](http://sendapatch.se/projects/pylibmc/reference.html)
- Simple 无额外参数
