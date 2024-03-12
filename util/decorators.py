import time


def timer(func):
    """
    计算执行时间
    :param func: 装饰的方法
    :return:
    """

    def decorated(*args, **kwargs):
        st = time.perf_counter()
        ret = func(*args, **kwargs)
        et = time.perf_counter()
        print(f'Cost time:{et - st:0.4f} seconds')
        return ret

    return decorated


def print_log(checker_name):
    """
    日志打印装饰器
    :param checker_name: 执行检查的插件名称
    :return:
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            print(f'begin to execute {checker_name} checker')
            ret = func(*args, **kwargs)
            print(f'{checker_name} check finished:{ret}')
            return ret

        return wrapper

    return decorator
