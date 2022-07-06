''' a module for utilities '''


def split_args(position, delimiter=','):
    '''this method split string of arguments by delimiter'''
    def wrapper(func):
        def inner(*args):
            args = list(args)
            args[position] = args[position].split(delimiter)
            return func(*args)
        return inner
    return wrapper
