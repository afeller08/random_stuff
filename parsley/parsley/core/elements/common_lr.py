from .base import LrElement


class Parens(LrElement):
    left, right = '()'


class Braces(LrElement):
    left, right = '[]'


class Brackets(LrElement):
    left, right = '{}'


class Angles(LrElement):
    left, right = '<>'


class LineContinuation(LrElement):
    left, right = '\\\n'


class StrEscape(LrElement):
    left = '\\'
    right = None


class Quotes(LrElement):
    @property
    def right(self):
        return self.left


class SQuotes(Quotes):
    left = "'"


class DQuotes(Quotes):
    left = '"'


class InlineComment(LrElement):
    left, right = '#\n'


class CComment(LrElement):
    left, right = '/*', '*/'
