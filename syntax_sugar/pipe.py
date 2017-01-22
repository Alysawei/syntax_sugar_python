from functools import partial
from .composable import compose
from multiprocess.pool import ThreadPool, Pool

__all__ = [
    'dump',
    'pipe',
    'each',
    'where',
    'concat',
    'puts',
    'read',
    'readlines',
    'p',
    't',
]

def puts(data):
    print(data)
    return data

def each(fn):
    return partial(compose(list, map), fn)

def where(fn):
    return partial(compose(list, filter), fn)

def concat(lst):
    return ''.join(lst)

def read(fd):
    return fd.read()

def readlines(fd):
    return fd.readlines()

class dump:
    "mark end of pipe"
    pass

class MultiTask:
    def __init__(self, func):
        self.poolsize = 1
        self.func = func
    def __mul__(self, other):
        self.poolsize = other
        return self

class MultiProcess(MultiTask):
    pass

class MultiThread(MultiTask):
    pass

class ProcessSyntax:
    def __getitem__(self, func):
        return MultiProcess(func)

class ThreadSyntax:
    def __getitem__(self, func):
        return MultiThread(func)

p = ProcessSyntax()
t = ThreadSyntax()

class pipe:
    def __init__(self, data = None):
        if data is None:
            self.pipein = False
        else:
            self.pipein = True
        self.data = data

    def start(self, left):
        # pipe start
        self.data = left
        self.pipein = True

    def partial(self, left):
        # partial function
        self.data = partial(*left)(self.data)

    def multiprocess(self, func, poolsize):
        p = Pool(poolsize)
        if poolsize == 1:
            self.data = p.map(func, [self.data])
        else:
            self.data = p.map(func, self.data)

    def multithread(self, func, poolsize):
        p = ThreadPool(poolsize)
        if poolsize == 1:
            self.data = p.map(func, [self.data])
        else:
            self.data = p.map(func, self.data)

    def function(self, left):
        self.data = left(self.data)

    def __or__(self, left):
        if isinstance(left, dump):
            # pipe end, return/dump data
            return self.data
        elif not self.pipein:
            self.start(left)
        elif isinstance(left, tuple):
            self.partial(left)
        elif isinstance(left, list):
            if len(set(left)) != 1:
                raise SyntaxError('Bad pipe multiprocessing syntax.')
            poolsize = len(left)
            func = left[0]
            self.multithread(func, poolsize)
        elif isinstance(left, MultiProcess):
            self.multiprocess(left.func, left.poolsize)
        elif isinstance(left, MultiThread):
            self.multithread(left.func, left.poolsize)
        else:
            self.function(left)
        return self

    def __gt__(self, right):
        "pipe > 'filename'"
        with open(right, 'w') as f:
            f.write(str(self.data))
    
    def __rshift__(self, right):
        "pipe >> 'filename'"
        with open(right, 'a') as f:
            f.write(str(self.data))

#####
# TODO: experiment
# lazy_pipe
#####

class until:
    def __init__(self, cond):
        self.cond = cond

class lazy_pipe:
    def __init__(self, source):
        self.source = source
        self.func = composable(lambda x: x)

    def __or__(self, left):
        if isinstance(left, dump):
            # dump termination
            return self.dump()
        elif isinstance(left, until):
            return self.until(left.cond)
        else:
            # read actions
            self.func = composable(left) * self.func
        return self

    def dump(self):
        return self.func(self.source)

    def until(self, cond):
        if hasattr(self.source, '__call__'):
            data = self.source()
            while not cond(data):
                self.func(data)
                data = self.source()
            return self
        elif hasattr(self.source, '__iter__'):
            for data in self.source:
                if cond(data):
                    break
                else:
                    self.func(data)
            return self
        else:
            raise TypeError('pipeline source need be callable or iterable with until condition')
