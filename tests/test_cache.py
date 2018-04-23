import pytest
import os.path
from unittest import mock
from cachext.exts import Cache
from cachext import backends, cache
from sea import create_app

os.environ.setdefault('SEA_ENV', 'testing')
root = os.path.join(os.path.dirname(__file__), 'seapp')
_app = create_app(root)


@pytest.fixture
def app():
    return _app


def test_default_key():
    def tmp(a, b=2, c=None):
        return a, b, c

    with pytest.raises(ValueError):
        cache.default_key(tmp, [], b=b'hello')

    key = cache.default_key(tmp, b'hello', b=True, c=None)
    assert key == 'default.{}.{}.{}'.format(tmp.__module__, tmp.__name__, 'a=hello.b=True.c=None')

    key = cache.default_key(tmp, 1)
    assert key == cache.default_key(tmp, 1, 2)
    assert key == cache.default_key(tmp, 1, b=2)
    assert key == cache.default_key(tmp, a=1, b=2)
    assert key == cache.default_key(tmp, b=2, c=None, a=1)


def test_cache_ext(app):

    c = Cache()
    assert c._backend is None
    c.init_app(app)
    assert isinstance(c._backend, backends.Redis)


def test_cached(app):
    total = 0
    fallbacked_count = 0
    c = app.extensions.cache

    def true_if_gte_10(num):
        return num >= 10

    def fallbacked(f, rv, *args, **kwargs):
        nonlocal fallbacked_count
        fallbacked_count += 1
        return fallbacked_count

    @c.cached(unless=true_if_gte_10, fallbacked=fallbacked)
    def incr1(num):
        nonlocal total
        total += num
        return total

    rt = incr1(1)
    assert rt == 1
    assert fallbacked_count == 1
    rt = incr1(1)
    assert rt == 1
    rt = incr1(10)
    assert rt == 11
    assert fallbacked_count == 1

    @c.cached(cache_key='testkey')
    def incr2(num):
        global total
        total += num
        return total

    with mock.patch.object(c._backend, 'get', return_value=100) as mocked:
        incr2(10)
        mocked.assert_called_once_with('testkey')

    with pytest.raises(AttributeError):
        c.nosuchmethod()

    with mock.patch.object(c._backend, 'set', return_value=True) as mocked:
        c.set('key', 'value')
        mocked.assert_called_once_with('key', 'value')
