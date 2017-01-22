from syntax_sugar import *
from sys import argv
from functools import partial


pipe(argv[1:]) | each(lambda filename: open(filename).read()) | concat | partial(print, end='')
