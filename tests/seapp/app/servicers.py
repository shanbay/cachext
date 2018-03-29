from sea.servicer import ServicerMeta

from app.extensions import cache


class HelloServicer(metaclass=ServicerMeta):

    def return_normal(self, request, context):
        cache.get()
