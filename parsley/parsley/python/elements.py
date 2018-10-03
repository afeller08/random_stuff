from ..core.elements.base import (LrElement, CompoundElement)
from ..core.elements.common_lr import (Quotes)


class SQuotes3(Quotes):
    left = "'''"


class DQuotes3(Quotes):
    left = '"""'



class StructuralElement(CompoundElement):
    pass
