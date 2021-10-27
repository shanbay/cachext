from . import backends
from .cache import cached


CACHE_LABELS = ("prefix_name", "func_name")


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
        monitor_enable = opts.pop('monitor_enable', False)
        # default ttl: 60 * 60 * 48
        self._backend = backend_cls(
            prefix=prefix, default_ttl=opts.pop('default_ttl', 172800),
            **opts)

        class _c(cached):
            client = self._backend

        self.cached = _c
        if monitor_enable:
            self.cached.request_counter = new_request_counter()
            self.cached.hit_counter = new_hit_counter()

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


def new_request_counter():
    from prometheus_client import Counter

    # Create a collector for total cache request counter
    return Counter(
        'cache_request_counter',
        'Number of cache requests',
        CACHE_LABELS,
    )


def new_hit_counter():
    from prometheus_client import Counter

    # Create a collector for cache hit counter
    return Counter(
        'cache_hit_counter',
        'Number of cache hits',
        CACHE_LABELS,
    )
