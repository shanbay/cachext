import pytest
import pickle
import time
from unittest import mock
from cachext import backends


def test_base_backend():
    c = backends.BaseBackend
    for m in ('get', 'get_many', 'set_many', 'delete', 'delete_many', 'ttl', 'exists'):
        with pytest.raises(NotImplementedError):
            m = getattr(c, m)
            m(mock.Mock(), 'key')

    for m in ('set', 'expire', 'expireat'):
        with pytest.raises(NotImplementedError):
            m = getattr(c, m)
            m(mock.Mock(), 'key', 'value')

    with pytest.raises(NotImplementedError):
        c.clear(mock.Mock())


def test_redis_backend():
    c = backends.Redis(prefix='testapp')
    c.clear()

    assert c.get('key') is None
    assert not c.exists('key')
    assert c.set_many({'ka': 'va', 'kb': 'vb'}, ttl=2)
    ttl = c.ttl('kb')
    assert ttl <= 2 and ttl > 0
    assert c.get_many(['ka', 'kb', 'nokey']) == ['va', 'vb', None]
    assert c.set('key', 'value', ttl=1)
    assert c.exists('key')
    assert c.get('key') == 'value'
    assert c._client.get('testapp.key') == pickle.dumps('value', pickle.HIGHEST_PROTOCOL)
    assert c.expireat('key', time.time() - 1) == 1
    assert c.expireat('nokey', time.time() - 1) == 0
    assert c.get('key') is None
    assert c.delete('nokey') == 0
    c.set('key', 'value')
    assert c.delete('key') == 1
    assert c.delete_many(['nokey', 'ka']) == 1
    c.set('key', 'value')
    assert c.expire('key', 2) == 1
    ttl = c.ttl('key')
    assert ttl <= 2 and ttl > 0
    assert c.incr('number', 1) == 1
    assert c.decr('number', 1) == 0
    assert c.clear()

    c.clear()


def test_memcached_backend():
    c = backends.Memcached(prefix='testapp', servers=['localhost'])
    c.clear()

    assert c.get('key') is None
    assert not c.exists('key')
    assert c.set_many({'ka': 'va', 'kb': 'vb'}, ttl=2) == []
    with pytest.raises(NotImplementedError):
        c.ttl('ka')
    assert c.get_many(['ka', 'kb', 'nokey']) == ['va', 'vb', None]
    assert c.set('key', 'value', ttl=1)
    assert c.exists('key')
    assert c.get('key') == 'value'
    assert c._client.get('testapp.key') == 'value'
    assert c.expireat('key', time.time() + 1) is True
    assert c.expireat('key', time.time() - 1) is True
    assert c.expireat('nokey', time.time() + 1) is False
    time.sleep(0.5)
    assert c.get('key') is None
    assert c.delete('nokey') is False
    c.set('key', 'value')
    assert c.delete('key') is True
    assert c.delete_many(['nokey', 'ka']) is False
    c.set('key', 'value')
    assert c.expire('key', 2) is True
    assert c.delete_many(['key']) is True
    c.set('number', 0)
    assert c.incr('number', 1) == 1
    assert c.decr('number', 1) == 0
    assert c.clear()

    c.clear()


def test_simple_backend():
    c = backends.Simple(threshold=3)
    assert c.get('key') is None
    assert not c.exists('key')
    assert c.set_many({'ka': 'va', 'kb': 'vb'})
    assert c.get_many(['ka', 'kb', 'nokey']) == ['va', 'vb', None]
    assert c.set('key', 'value', ttl=1)
    assert c.exists('key')
    assert c.get('key') == 'value'
    assert not c.set('extra', 'value')
    aminlater = time.time() + 60
    with mock.patch('time.time', new=lambda: aminlater):
        assert c.set('extra', 'value')
    assert c.delete('nokey') == 0
    assert c.delete('extra') == 1
    c.set('key', 'value')
    assert c.delete_many(['extra', 'key']) == 1

    assert c.expire('key', 1) == 0
    c.set('key', 'value')
    assert c.expire('key', 2) == 1
    ttl = c.ttl('key')
    assert ttl <= 2 and ttl > 0
    assert c.ttl('nokey') == -2
    assert c.get('key') == 'value'
    with mock.patch('time.time', new=lambda: aminlater):
        assert c.ttl('key') == -2
        assert c.get('key') is None
    assert c.expireat('nokey', int(time.time())) == 0
    c.set('key', 'value')
    assert c.expireat('key', int(time.time() - 1)) == 1
    assert c.get('key') is None
    c.set('number', 0)
    assert c.incr('number', 1) == 1
    assert c.decr('number', 1) == 0
    c.clear()
    assert len(c._cache) == 0
