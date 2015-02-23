'''
Tests for the Decorator module.

@author: chrcoe
'''
import time
import unittest

from standardlibs.Decorators import retry, memoize_expire, deprecated
class DecoratorsTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_retry_negative(self):
        ''' Test ValueErrors from the retry decorator '''
        with self.assertRaises(ValueError):
            @retry(tries=-1)
            def passFunct():
                pass
        with self.assertRaises(ValueError):
            @retry(tries=1, delay=0)
            def passFunct1():
                pass
        with self.assertRaises(ValueError):
            @retry(tries=1, backoff=1)
            def passFunct2():
                pass


        with self.assertRaises(Exception):
            @retry(1)
            def failFunct(input_):
                ''' Returns the opposite of the input bool '''
                return not input_
            # call the function and let it test failing
            failFunct(True)

    def test_retry_positive(self):
        @retry(1)
        def passFunct(input_):
            ''' Returns the input bool '''
            return input_

        self.assertTrue(passFunct(True))

    def test_memoize_expire(self):

        def norm_fib(n):
            if n in (0, 1):
                return n
            return norm_fib(n - 1) + norm_fib(n - 2)

        t0 = time.time()
        norm_fib(25)
        t1 = time.time()
        total_time = t1 - t0

        self.assertGreater(total_time, 0.02)

        @memoize_expire
        def memo_fib(n):
            if n in (0, 1):
                return n
            return memo_fib(n - 1) + memo_fib(n - 2)

        t0 = time.time()
        memo_fib(25)
        t1 = time.time()
        total_time = t1 - t0

        self.assertLess(total_time, 0.02)

    def test_deprecated(self):
        ''' Tests that a deprecated function returns the DeprecationWarning. '''

        @deprecated
        def dep_func():
            return True

        self.assertWarns(DeprecationWarning, dep_func)

if __name__ == "__main__":
    unittest.main()
