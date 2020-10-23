import time
import logging

def log_slow_call(wrapped=None, seconds=10):
    """
    基本的思路就是 返回一个新的装饰器用来装饰待装饰的函数
    """
    if wrapped is None:
        def another_decorator(wrapped):
            return log_slow_call(wrapped, seconds)
        return another_decorator
    
    def proxy(*args, **kwargs):
        start_time = time.time()
        result = wrapped(*args, **kwargs)
        expired = time.time() - start_time
        if expired > seconds:
            logging.warning('call {} expires {} seconds'.format(wrapped.__name__, expired))
        return result
    
    return proxy

# 支持下面3中形式的log

@log_slow_call(threshold=1)
def add(a, b):
    time.sleep(1)
    return a + b


@log_slow_call()
def add(b, b):
    time.sleep(1)
    return a + b

@log_slow_call
def add(a, b):
    time.sleep(1)
    return a + b
