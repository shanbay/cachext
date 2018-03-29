import redis
from cachext.exts import Redis

from tests.flaskapp import app


def test_redis():
    r = Redis()
    assert r._client is None
    r.init_app(app)
    assert isinstance(r._client, redis.StrictRedis)
    assert r.ping()
