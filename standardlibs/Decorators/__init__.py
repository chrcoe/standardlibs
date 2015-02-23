'''
This module provides function decorator methods.
'''
import functools
import math
import time
import warnings
import cProfile


def memoize_expire(obj):
    '''
    Memoizes a function.  This will add results to a cache to be used later.
    This makes it possible to avoid calculating the same result twice and can
    help speed up operations.  This function will utilize a function's *args
    and **kwargs.  This decorator has a built in two hour expiration time.

    Each item cached will have its OWN expiration time.
    '''
    cache = obj.cache = {}
    expire_time = 7200  # expire every two hours (2*60*60)

    @functools.wraps(obj)
    def memoizer(*args, **kwargs):
        '''
        The actual function which manages the cache.
        '''
#         key = str(args) + str(kwargs)
        key = str(args) + str(hash(frozenset(kwargs.items())))

        if key in cache:
            result, timestamp = cache[key]
            # check the age
            age = time.time() - timestamp
            if not expire_time or age < expire_time:
                return result
            # if it IS expired, the code below is executed to re-cache results

        # else cache it with timestamp and then return just the result
        result = obj(*args, **kwargs)
        cache[key] = (result, time.time())
        return result

    return memoizer


def retry(tries, delay=3, backoff=2):
    '''
    Retries a function or method until it returns True.

    delay sets the initial delay in seconds, and backoff sets the factor by
    which the delay should lengthen after each failure. backoff must be greater
    than 1, or else it isn't really a backoff. tries must be at least 0, and
    delay greater than 0.

    @raise Exception: upon reaching the final retry, if the underlying method
        still fails, Exception is raised
    '''

    if backoff <= 1:
        raise ValueError("backoff must be greater than 1")

    tries = math.floor(tries)
    if tries < 0:
        raise ValueError("tries must be 0 or greater")

    if delay <= 0:
        raise ValueError("delay must be greater than 0")

    def deco_retry(func):
        '''
        Decorated internal function which calls the actual retry function.
        '''
        def f_retry(*args, **kwargs):
            '''
            The actual retry function.
            '''
            mtries, mdelay = tries, delay  # make mutable

            retry_value = func(*args, **kwargs)  # first attempt
            while mtries > 0:
                if retry_value is True:  # Done on success
                    return True
                mtries -= 1      # consume an attempt
                print('Waiting {} seconds'.format(mdelay))
                time.sleep(mdelay)  # wait...
                mdelay *= backoff  # make future wait longer
                retry_value = func(*args, **kwargs)  # Try again
            raise Exception
        return f_retry  # true decorator -> decorated function
    return deco_retry  # @retry(arg[, ...]) -> true decorator


def deprecated(func):
    '''This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used.'''
    warnings.simplefilter('always', DeprecationWarning)

    def deprecator(*args, **kwargs):
        ''' Function which manages DeprecationWarning. '''
        warnings.warn("Call to deprecated function {}.".format(func.__name__),
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    deprecator.__name__ = func.__name__
    deprecator.__doc__ = func.__doc__
    deprecator.__dict__.update(func.__dict__)
    return deprecator


# if __name__ == '__main__':
# @deprecated
# @memoize_expire
#     def memo_fib(n):
#         if n in (0, 1):
#             return n
#         return memo_fib(n - 1) + memo_fib(n - 2)
#
# import sys
# sys.setrecursionlimit(100000)
#
#     import gc
#     gc.collect()
#
#     t0 = time.time()
#     memo = memo_fib(25)
#     t1 = time.time()
#     total_time = t1 - t0
#     print('{}\t:\t{}'.format(memo, total_time))
#
#     assert total_time > 1
#
#     cProfile.run('memo_fib(25)')
