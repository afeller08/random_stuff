

class Tokens(list):
    def __mul__(self, other):
        return Tokens(x + y for x in self for y in other)

    def __add__(self, other):
        return Tokens(self + list(other))


COMP = Tokens('!<>=') * '=' + '<>'
COMP2 = Tokens('<>=') * '=' + '<>' + ['<>']
ARITH = Tokens('+-*/%')
BINARY = Tokens('&|^') + ['<<', '>>']
UOP = Tokens('+-~')


class Operators(object):
    def __init__(self, comp=COMP, bop=ARITH+BINARY, uop=UOP):
        self.comp = comp
        self.bop = bop
        self.uop = uop
        self.assign = bop * '=' + '='

