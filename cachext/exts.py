from . import backends
from .cache import cached


class Cache:

    PROTO_METHODS = ('get', 'get_many', 'set', 'set_many', 'delete',
                     'delete_many', 'expire', 'expireat', 'clear',
                     'ttl', 'exists', 'incr', 'decr')

    def __init__(self, ns='CACHE_'):
        self._backend = None
        self.ns = ns

    def init_app(self, app):
        opts = app.config.get_namespace(self.ns).copy()
        backend_cls = getattr(backends, opts.pop('backend'))
        prefix = opts.pop('prefix', app.name)
        # default ttl: 60 * 60 * 48
        self._backend = backend_cls(
            prefix=prefix, default_ttl=opts.pop('default_ttl', 172800),
            **opts)

        class _c(cached):
            client = self._backend

        self.cached = _c

    def __getattr__(self, name):
        if name in self.PROTO_METHODS:
            return getattr(self._backend, name)
        raise AttributeError


class Redis:

    def __init__(self, ns='REDIS_'):
        self._client = None
        self.ns = ns

    def init_app(self, app):
        import redis
        opts = app.config.get_namespace(self.ns)
        self._pool = redis.ConnectionPool(**opts)
        self._client = redis.StrictRedis(connection_pool=self._pool)

    def __getattr__(self, name):
        return getattr(self._client, name)
