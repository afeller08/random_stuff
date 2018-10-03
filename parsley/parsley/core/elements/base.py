class Element(object):
    sub_parsers = []


class LrElement(Element):
    left = None
    right = None

    def __init__(self):
        self.start_buffer = []
        self.stop_buffer = []
        self.contents = []

    def activated(self):
        return self.left == self.start_buffer

    def deactivated(self):
        return self.right == self.stop_buffer


class CompoundElement(Element):
    opening = Element
    closing = Element