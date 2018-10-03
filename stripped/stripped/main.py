class Clock(object):
    pass


class Stream(object, metaclass=type):
    clock = Clock()
    cdict = set()

    def __init__(self, **kwargs):
        kwds = set(kwargs)
        assert kwds & self.cdict == kwds

    def on(self, stream):
        return type(self)(self, clock=stream.clock)


class DerivedStream(Stream):
    pass


class Op(DerivedStream):
    pass


class BinaryOp(Op):
    pass


class AbelianOp(BinaryOp):
    pass


class _BooleanStream(object):
    side = None
    preside = None
    left = []
    right = []

    def __call__(self, side):
        if self.side is not None or self.preside is not None:
            raise Exception('trying to re-enter condition')
        if self.side is not True and self.side is not False:
            raise Exception('{} is not a boolean'.format(side))
        self.preside = side
        return self

    def __enter__(self):
        if self.preside is None:
            raise Exception('trying to enter uncalled condition')
        self.side = self.preside
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.side = self.preside = None

    def And(self, other):
        return And(op_left=self, op_right=other)

    def Or(self, other):
        return Or(op_left=self, op_right=other)

    def use(self, stream):
        if self.side is None:
            raise Exception('trying to use unentered condition')
        elif self.side is True:
            self.left.append(stream)
        elif self.side is False:
            self.right.append(stream)
        else:
            raise Exception('side should not be {}'.format(self.side))
        return Bound(stream=stream, condition=self, side=self.side)


class Bound(Stream):
    stream = Stream()
    condition = _BooleanStream()
    side = bool


class ExternalCondition(_BooleanStream, Stream):
    condition = _BooleanStream()


class BooleanStream(_BooleanStream, Stream):
    condition = _BooleanStream()


class And(_BooleanStream, BinaryOp):
    op_left = _BooleanStream()
    op_right = _BooleanStream()


class Or(_BooleanStream, BinaryOp):
    op_left = _BooleanStream()
    op_right = _BooleanStream()


def If(condition, left, right):
    with condition(True):
        condition.use(left)
    with condition(False):
        condition.use(right)


x = ExternalCondition('use slow loop')

with ENUMERATE(collection) as i_v:
    i, v = i_v

with FOR(0, INCR < 50, INCR + 1):
    pass


with IF():
    pass
with ELIF():
    pass
with ELSE():
    pass
