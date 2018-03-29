TESTING = False
DEBUG = True

MIDDLEWARES = [
    'sea.middleware.ServiceLogMiddleware',
    'sea.middleware.RpcErrorMiddleware'
]

CACHE_BACKEND = 'Redis'
CACHE_PREFIX = 'seapp'
CACHE_HOST = 'localhost'
CACHE_DB = 0
CACHE_PORT = 6379
