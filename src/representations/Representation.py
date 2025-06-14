from app.App import logger
from resources.Exceptions import AbstractClassException
from executables.RecursiveDeclarable import RecursiveDeclarable
from executables.Runnable import Runnable
from representations.ExtractStrategy import ExtractStrategy
import asyncio

class Representation(RecursiveDeclarable, Runnable):
    category = "base"

    class Extractor(ExtractStrategy):
        pass

    @classmethod
    async def extract(cls, i: dict = {})->dict:
        if getattr(cls, 'Extractor', None) == None:
            raise AbstractClassException('ExecutableStrategy is not implemented at this class')

        strategy = cls.Extractor(cls)
        args = cls.validate(i)

        strategy.preExtract(args)

        return await strategy.extract(i = args)

    @classmethod
    def rawListMethods(cls):
        fourbidden = ["canBeExecuted", "common_category", "extract", "isAbstract", "rawListMethods"]
        __methods = dir(cls)
        __out = []

        for __method in __methods:
            if __method.startswith("__") == False and __method not in fourbidden:
                __out.append(__method)

        return __out
