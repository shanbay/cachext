import abc
import pickle
import time
from threading import RLock, Lock


class BaseBackend(metaclass=abc.ABCMeta):

    def trans_key(self, key):
        if self.prefix is None:
            return key
        return '{}.{}'.format(self.prefix, key)

    @abc.abstractmethod
    def get(self, key):
        raise NotImplementedError

    @abc.abstractmethod
    def get_many(self, keys):
        raise NotImplementedError

    @abc.abstractmethod
    def set(self, key, value, ttl=None):
        raise NotImplementedError

    @abc.abstractmethod
    def set_many(self, mapping, ttl=None):
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, key):
        raise NotImplementedError

    @abc.abstractmethod
    def delete_many(self, keys):
        raise NotImplementedError

    @abc.abstractmethod
    def incr(self, key, delta=1):
        raise NotImplementedError

    @abc.abstractmethod
    def decr(self, key, delta=1):
        raise NotImplementedError

    @abc.abstractmethod
    def expire(self, key, seconds):
        raise NotImplementedError

    @abc.abstractmethod
    def expireat(self, key, timestamp):
        raise NotImplementedError

    @abc.abstractmethod
    def ttl(self, key):
        raise NotImplementedError

    @abc.abstractmethod
    def exists(self, key):
        raise NotImplementedError

    @abc.abstractmethod
    def clear(self):
        raise NotImplementedError


class Redis(BaseBackend):

    def __init__(self, prefix=None, default_ttl=600, **kwargs):
        import redis
        self._client = redis.StrictRedis(**kwargs)
        self.prefix = prefix
        self.default_ttl = default_ttl

    def get(self, key):
        key = self.trans_key(key)
        v = self._client.get(key)
        return v if v is None else pickle.loads(v)

    def get_many(self, keys):
        keys = [self.trans_key(k) for k in keys]
        values = self._client.mget(keys)
        return [v if v is None else pickle.loads(v) for v in values]

    def set(self, key, value, ttl=None):
        key = self.trans_key(key)
        if ttl is None:
            ttl = self.default_ttl
        else:
            ttl = int(ttl)
        return self._client.set(
            key, pickle.dumps(value),
            ex=ttl)

    def set_many(self, mapping, ttl=None):
        mapping = {self.trans_key(k): pickle.dumps(v)
                   for k, v in mapping.items()}
        rv = self._client.mset(mapping)
        if ttl is None:
            ttl = self.default_ttl
        else:
            ttl = int(ttl)
        for k in mapping.keys():
            self._client.expire(k, ttl)
        return rv

    def delete(self, key):
        key = self.trans_key(key)
        return self._client.delete(key)

    def delete_many(self, keys):
        keys = [self.trans_key(k) for k in keys]
        return self._client.delete(*keys)

    def incr(self, key, delta=1):
        key = self.trans_key(key)
        return self._client.incr(key, delta)

    def decr(self, key, delta=1):
        key = self.trans_key(key)
        return self._client.decr(key, delta)

    def expire(self, key, seconds):
        key = self.trans_key(key)
        return self._client.expire(key, int(seconds))

    def expireat(self, key, timestamp):
        key = self.trans_key(key)
        return self._client.expireat(key, int(timestamp))

    def ttl(self, key):
        key = self.trans_key(key)
        return self._client.ttl(key)

    def exists(self, key):
        key = self.trans_key(key)
        return self._client.exists(key) > 0

    def clear(self):
        self._client.flushdb()
        return True


class Memcached(BaseBackend):

    def __init__(self, prefix=None, default_ttl=600, **kwargs):
        import pylibmc
        self._client = pylibmc.Client(**kwargs)
        self.prefix = prefix
        self.default_ttl = default_ttl

    def get(self, key):
        key = self.trans_key(key)
        return self._client.get(key)

    def get_many(self, keys):
        keys = [self.trans_key(k) for k in keys]
        maps = self._client.get_multi(keys)
        return [maps.get(k, None) for k in keys]

    def set(self, key, value, ttl=None):
        key = self.trans_key(key)
        if ttl is None:
            ttl = self.default_ttl
        else:
            ttl = int(ttl)
        return self._client.set(key, value, time=ttl)

    def set_many(self, mapping, ttl=None):
        mapping = {self.trans_key(k): v
                   for k, v in mapping.items()}
        if ttl is None:
            ttl = self.default_ttl
        else:
            ttl = int(ttl)
        return self._client.set_multi(mapping, time=ttl)

    def delete(self, key):
        key = self.trans_key(key)
        return self._client.delete(key)

    def delete_many(self, keys):
        keys = [self.trans_key(k) for k in keys]
        return self._client.delete_multi(keys)

    def incr(self, key, delta=1):
        key = self.trans_key(key)
        return self._client.incr(key, delta)

    def decr(self, key, delta=1):
        key = self.trans_key(key)
        return self._client.decr(key, delta)

    def expire(self, key, seconds):
        key = self.trans_key(key)
        return self._client.touch(key, int(seconds))

    def expireat(self, key, timestamp):
        key = self.trans_key(key)
        value = self._client.get(key)
        now = time.time()
        delta = int(timestamp - now)
        return self._client.replace(key, value, delta)

    def ttl(self, key):
        raise NotImplementedError

    def exists(self, key):
        key = self.trans_key(key)
        return self._client.get(key) is not None

    def clear(self):
        self._client.flush_all()
        return True


class Simple(BaseBackend):

    def __init__(self, prefix=None, threshold=500, default_ttl=600):
        self._cache = {}
        self.threshold = threshold
        self.default_ttl = default_ttl
        self.prefix = prefix
        self.rlock = RLock()
        self.lock = Lock()

    def _ttl2expire(self, ttl):
        if ttl is None:
            ttl = self.default_ttl
        now = time.time()
        return int(now + ttl)

    def _expired(self, ts):
        now = time.time()
        return now > ts

    def _prune(self):
        toremove = []
        for k, (exp, v) in self._cache.items():
            if self._expired(exp):
                toremove.append(k)
        for k in toremove:
            self._cache.pop(k, None)
        return len(self._cache)

    def get(self, key):
        key = self.trans_key(key)
        exp, v = self._cache.get(key, (None, None))
        if exp is None:
            return None
        if self._expired(exp):
            self._cache.pop(key)
            return None
        return v

    def get_many(self, keys):
        return [self.get(k) for k in keys]

    def set(self, key, value, ttl=None):
        key = self.trans_key(key)
        with self.rlock:
            if len(self._cache) >= self.threshold \
                    and self._prune() >= self.threshold:
                return False
            self._cache[key] = (
                self._ttl2expire(ttl), value)
        return True

    def set_many(self, mapping, ttl=None):
        count = len(mapping.keys())
        with self.rlock:
            if len(self._cache) + count >= self.threshold \
                    and self._prune() + count >= self.threshold:
                return False
            for k, v in mapping.items():
                self._cache[self.trans_key(k)] = (
                    self._ttl2expire(ttl), v)
        return True

    def delete(self, key):
        key = self.trans_key(key)
        try:
            self._cache.pop(key)
            return 1
        except KeyError:
            pass
        return 0

    def delete_many(self, keys):
        with self.rlock:
            return sum([self.delete(k) for k in keys])

    def incr(self, key, delta=1):
        key = self.trans_key(key)
        with self.lock:
            exp, v = self._cache.get(key)
            v += delta
            self._cache[key] = (
                exp, v)
        return v

    def decr(self, key, delta=1):
        key = self.trans_key(key)
        with self.lock:
            exp, v = self._cache.get(key)
            v -= delta
            self._cache[key] = (
                exp, v)
        return v

    def expire(self, key, seconds):
        key = self.trans_key(key)
        try:
            exp, v = self._cache[key]
        except KeyError:
            return 0
        self._cache[key] = (self._ttl2expire(seconds), v)
        return 1

    def expireat(self, key, timestamp):
        key = self.trans_key(key)
        try:
            exp, v = self._cache[key]
        except KeyError:
            return 0
        self._cache[key] = (timestamp, v)
        return 1

    def ttl(self, key):
        key = self.trans_key(key)
        try:
            exp, v = self._cache[key]
        except KeyError:
            return -2
        ttl = exp - time.time()
        if ttl < 0:
            self._cache.pop(key)
            return -2
        return int(ttl)

    def exists(self, key):
        key = self.trans_key(key)
        return key in self._cache

    def clear(self):
        self._cache.clear()
        return True
