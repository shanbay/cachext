import functools


DEFAULT_KEY_TYPES = (str, int, float, bool)


def norm_cache_key(v):
    if isinstance(v, type):
        return v.__name__
    if isinstance(v, bytes):
        return v.decode()
    if v is None or isinstance(v, DEFAULT_KEY_TYPES):
        return str(v)
    else:
        raise ValueError('only str, int, float, bool can be key')


def default_key(f, *args, **kwargs):
    keys = [norm_cache_key(v) for v in args]
    keys += sorted(
        ['{}={}'.format(k, norm_cache_key(v)) for k, v in kwargs.items()])
    return 'default.{}.{}.{}'.format(f.__module__, f.__name__, '.'.join(keys))


class CacheNone:
    pass


class cached:

    client = None

    def __init__(self, func=None, ttl=None, cache_key=default_key,
                 cache_version=None, unless=None, fallbacked=None,
                 cache_none=False):
        self.ttl = ttl
        self.cache_key = cache_key
        self.unless = unless
        self.fallbacked = fallbacked
        self.cache_none = cache_none
        self.cache_version = cache_version
        if func is not None:
            func = self.decorator(func)
        self.func = func

    def __call__(self, *args, **kwargs):
        if self.func is not None:
            return self.func(*args, **kwargs)
        f = args[0]
        return self.decorator(f)

    def decorator(self, f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if callable(self.unless) and self.unless(*args, **kwargs):
                return f(*args, **kwargs)
            key = wrapper.make_cache_key(*args, **kwargs)
            rv = self.client.get(key)
            labels = (self.client.prefix, f.__name__)
            if self.request_counter:
                # Increment request counter.
                self.request_counter.labels(*labels).inc()
            if rv is None:
                rv = f(*args, **kwargs)
                if self.cache_none and rv is None:
                    rv = CacheNone
                if rv is not None:
                    self.client.set(key, rv, ttl=wrapper.ttl)
                if callable(self.fallbacked):
                    self.fallbacked(wrapper, rv, *args, **kwargs)
            elif self.hit_counter:
                # Increment hit counter.
                self.hit_counter.labels(*labels).inc()
            if self.cache_none and rv is CacheNone:
                return None
            return rv

        def make_cache_key(*args, **kwargs):
            if callable(self.cache_key):
                key = self.cache_key(f, *args, **kwargs)
            else:
                key = self.cache_key

            return key if not self.cache_version else\
                '{key}.{version}'.format(key=key, version=self.cache_version)

        wrapper.uncached = f
        wrapper.ttl = self.ttl
        wrapper.make_cache_key = make_cache_key

        return wrapper

    def __getattr__(self, name):
        return getattr(self.func, name, None)
