from executables.Runnable import Runnable
from executables.Saveable import Saveable
from resources.Exceptions import AbstractClassException, SuitableExtractMethodNotFound

class ExtractStrategy(Runnable, Saveable):
    buffer = {}

    def __init__(self, outer):
        self.outer = outer

    def preExtract(self, i = {}):
        self.buffer['args'] = i

    def extractWheel(self, i = {}):
        raise AbstractClassException("This is abstract representation")

    async def extract(self, i = {}):
        __wheel = self.extractWheel(i)
        if __wheel == None:
            __wheel = ""

        __wheel_method = getattr(self, __wheel, None)
        if __wheel_method == None:
            raise SuitableExtractMethodNotFound('Not found suitable extractor for current args')

        __res = await __wheel_method(i)

        return __res

    def self_insert(self, json_data: dict):
        json_data['representation'] = self.outer.full_name()
        json_data['representation_class'] = self

        return json_data
