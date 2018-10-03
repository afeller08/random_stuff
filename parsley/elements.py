











class Type(object):
    prototype = None
    transition = ''


class Set(Type):
    prototype = Brackets
    transition = ','


class SingleItemDict(Type):
    prototype = Brackets
    transition = ':'


class DictComprehension(Type):
    prototype = SingleItemDict
    transition = 'for'


class Dict(Type):
    prototype = SingleItemDict
    transition = ','


class Variable(object):
    pass





class FuncDef(StructuralElement):
    left, right = 'def', ':'


class ClassDef(StructuralElement):
    left, right = 'def', ':'
