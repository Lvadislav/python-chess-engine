import doctest
from string import ascii_lowercase


class Coordinate:
    '''

    >>> coordinate = Coordinate('a2')

    >>> coordinate
    Coordinate(0, 1)
    >>> str(coordinate)
    'a2'
    >>> coordinate.x
    0
    >>> coordinate.y
    1

    >>> coordinate = Coordinate(7, 7)

    >>> coordinate
    Coordinate(7, 7)
    >>> str(coordinate)
    'h8'
    >>> coordinate.x
    7
    >>> coordinate.y
    7

    '''
    def __init__(self, *args):
        if len(args) == 1:
            self._x = ascii_lowercase.index(args[0][0])
            self._y = int(args[0][1]) - 1

        else:
            self._x, self._y = args

        self._normalize()

    def _normalize(self):
        '''

        >>> Coordinate(-1, 4)
        Coordinate(0, 4)

        >>> Coordinate(2, 10)
        Coordinate(2, 7)

        '''
        self._x = min(7, self._x)
        self._x = max(0, self._x)

        self._y = min(7, self._y)
        self._y = max(0, self._y)

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    def delta(self, x=0, y=0):
        '''

        >>> coordinate = Coordinate(3, 4)

        >>> coordinate.delta(-3, 1)
        Coordinate(0, 5)
        >>> coordinate.delta(-4, -4)
        Coordinate(0, 0)
        >>> coordinate.delta(1, 3)
        Coordinate(4, 7)
        >>> coordinate.delta(1, 8)
        Coordinate(4, 7)

        '''
        return Coordinate(
            self._x + x,
            self._y + y
        )

    def __eq__(self, other):
        '''

        >>> coordinate_a = Coordinate('f1')
        >>> coordinate_b = Coordinate('f2')
        >>> coordinate_c = Coordinate('f1')

        >>> coordinate_a == coordinate_b
        False

        >>> coordinate_a == coordinate_c
        True

        '''
        return self._x == other.x and self._y == other.y

    def __str__(self):
        return f'{ascii_lowercase[self._x]}{self._y + 1}'

    def __repr__(self):
        return f'{type(self).__name__}({self._x}, {self._y})'


class EmptyCell:
    '''

    >>> empty_cell = EmptyCell()

    >>> empty_cell
    EmptyCell()
    >>> str(empty_cell)
    'Empty Cell'

    '''
    def __str__(self):
        return 'Empty Cell'

    def __repr__(self):
        return f'{type(self).__name__}()'


class EmptyMove:
    '''

    >>> empty_move = EmptyMove()

    >>> empty_move
    EmptyMove()
    >>> str(empty_move)
    '0000'

    '''
    def __str__(self):
        return '0000'

    def __repr__(self):
        return f'{type(self).__name__}()'


if __name__ == '__main__':
    doctest.testmod()
