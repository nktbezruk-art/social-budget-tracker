import time
from functools import wraps

GLOBAL_CACHE = {}


def make_cache_key(func, *args, **kwargs):
    func_name = func.__name__
    kwargs_tuple = tuple(sorted(kwargs.items()))
    key = (func_name, args, kwargs_tuple)
    return key


def cache_for(seconds=300, cache_none=False):
    """Декоратор дя кеширования данных.
    Имеет два аргумента: время хранения кэша seconds и параметр cache_none.
    Cache_none отвечает за то, будут ли кэшироваться None значения или нет.
    По умолчанию False"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = make_cache_key(func, *args, **kwargs)
            if key in GLOBAL_CACHE:
                cached_data, timestamp = GLOBAL_CACHE[key]
                if time.time() - timestamp < seconds:
                    return cached_data
                else:
                    del GLOBAL_CACHE[key]

            result = func(*args, **kwargs)
            if cache_none or result is not None:
                GLOBAL_CACHE[key] = (result, time.time())

            return result
        return wrapper
    return decorator
