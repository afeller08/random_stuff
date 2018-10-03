import functools
import inspect
import abc


class OptionallyParamatizableDecorator(object, metaclass=abc.ABCMeta):
    def __new__(cls, _fn=None, **kwargs):
        if not kwargs and _fn is not None:
            return cls()(_fn)
        else:
            return super(OptionallyParamatizableDecorator, cls).__new__(cls)

    @abc.abstractmethod
    def __call__(self, fn):
        pass


class FunctionMixin(OptionallyParamatizableDecorator):
    def __call__(self, fn):
        def expanded(_, *args, **kwargs):
            return fn(*args, **kwargs)

        f = functools.wraps(fn)(functools.partial(super(FunctionMixin, self).__call__(expanded), expanded))
        f._wrapped = fn
        return f


class memoize_instance_method(OptionallyParamatizableDecorator):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, fn):
        _params = inspect.signature(fn).parameters.values()
        po = inspect.Parameter.POSITIONAL_ONLY
        pk = inspect.Parameter.POSITIONAL_OR_KEYWORD
        params = [p.name if p.kind == pk else i for i, p in enumerate(_params) if p.kind in (pk, po)][1:]

        @functools.wraps(fn)
        def f(s, *args, **kwargs):
            if not hasattr(s, '_memoized'):
                s._memoized = {}
            _args = []
            _args.extend(zip(params, args))
            _args.extend(kwargs.items())
            _args = sorted([(k, self.kwargs[k](v)) if k in self.kwargs else (k, v) for k, v in _args])
            _args.extend(args[len(params):])
            key = (fn.__name__, tuple(_args))
            if key in s._memoized:
                val = s._memoized[key]
            else:
                val = fn(s, *args, **kwargs)
                s._memoized[key] = val
            return val

        f._wrapped = fn
        return f


class memoize(FunctionMixin, memoize_instance_method):
    pass
