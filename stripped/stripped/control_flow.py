
class SemiMutableStack(object):
    def __init__(self):
        self.values = []
        self.history = []
        self.previous = None

    def push(self, value):
        self.values.append(value)
        self.history.append(tuple(self.values))

    def pop(self):
        self.previous = self.history.pop()
        return self.values.pop()

    def reference(self):
        return self.history[-1]


class ActiveContext(object):
    current = None

    def __new__(cls):
        if ActiveContext.current is None:
            ActiveContext.current = super(ActiveContext, cls).__new__(cls)
        return ActiveContext.current

    def __init__(self):
        self.control_flow = SemiMutableStack()


class InternalVariable(object):
    pass


class BaseLoopedValue(InternalVariable):
    def __init__(self):
        self.source = ActiveContext.current.control_flow.reference()


class _KEY(BaseLoopedValue):
    pass


class _INDEX(BaseLoopedValue):
    pass


class _VALUE(BaseLoopedValue):
    pass


class BaseControlFlow(object):
    def get_entry_information(self):
        return None

    def __enter__(self):
        ActiveContext().control_flow.push(self)
        return self.get_entry_information()

    def __exit__(self, exc_type, exc_val, exc_tb):
        ActiveContext().control_flow.pop()


class Iteration(BaseControlFlow):
    def __init__(self, collection):
        self.collection = collection


class ENUMERATE(Iteration):
    def get_entry_information(self):
        return _INDEX(), _VALUE()


class ITEMS_IN(Iteration):
    def get_entry_information(self):
        return _KEY(), _VALUE()


class KEYS_IN(Iteration):
    def get_entry_information(self):
        return _KEY()


class VALUES_IN(Iteration):
    def get_entry_information(self):
        return _VALUE()


def renderSheetMusic(measure, notes):
    with VALUES_IN(notes) as note:
