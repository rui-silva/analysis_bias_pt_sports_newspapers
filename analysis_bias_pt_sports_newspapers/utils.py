from enum import Enum


class Newspaper(Enum):
    Abola = 0
    Record = 1
    Ojogo = 2

    @staticmethod
    def names():
        return [c.name for c in Newspaper]


class Clubs(Enum):
    BENFICA = (1, 'red')
    PORTO = (2, 'blue')
    SPORTING = (3, 'green')
    OTHER = (5, 'gray')

    def __init__(self, id, color):
        self.id = id
        self.color = color

    @staticmethod
    def ids():
        return [c.id for c in Clubs]

    @staticmethod
    def names():
        return [c.name for c in Clubs]

    @staticmethod
    def colors():
        return [c.color for c in Clubs]


class LabelClass(Enum):
    BACKGROUND = 0
    BENFICA = 1
    PORTO = 2
    SPORTING = 3
    PUB = 4
    OTHER = 5

    def __init__(self, id):
        self.id = id

    @staticmethod
    def names():
        return [c.name for c in LabelClass]
