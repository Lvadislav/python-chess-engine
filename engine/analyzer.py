import doctest
import weakref
from decimal import Decimal
from random import choice
from threading import Thread

try:
    from .core.position import *
except (SystemError, ImportError):
    from core.position import *

INFINITY = Decimal('1e18')

NAME = 'LeskoChessEngine 0.1'
AUTHOR = 'Lesko Vladislav'

DEFAULT_DEPTH = 2 # full moves (1 move = 2 plies)


class RootMoveNode:
    '''

    >>> root_move = Move('e2e4')
    >>> root_move_node = RootMoveNode(root_move)

    >>> root_move_node
    RootMoveNode(Move(Coordinate(4, 1), Coordinate(4, 3), False), Decimal('0'))
    >>> str(root_move_node)
    'RootMoveNode for e2e4'
    >>> root_move_node.move
    Move(Coordinate(4, 1), Coordinate(4, 3), False)
    >>> root_move_node.children
    []

    >>> root_move_node.grade
    Decimal('0')
    >>> root_move_node.grade = Decimal('300')
    >>> root_move_node.grade
    Decimal('300')

    >>> list(root_move_node.moves_chain)
    [Move(Coordinate(4, 1), Coordinate(4, 3), False)]
    >>> list(root_move_node.moves_chain) # doctest: +ELLIPSIS
    [Move(...)]

    '''
    def __init__(self, move, grade=Decimal('0')):
        self._move = move
        self._children = []

        self._grade = grade

    @property
    def move(self):
        return self._move

    @property
    def grade(self):
        return self._grade

    @grade.setter
    def grade(self, value):
        self._grade = value

    def _update_grade(self):
        best_grade = max(
            -child.grade for child in self._children
        )
        self._grade = best_grade

    @property
    def children(self):
        '''

        >>> root_move = Move('e2e4')
        >>> root_move_node = RootMoveNode(root_move)

        >>> child_move_a = Move('a7a6')
        >>> child_move_a_node = MoveNode(child_move_a, root_move_node)
        >>> child_move_b = Move('b7b6')
        >>> child_move_b_node = MoveNode(child_move_b, root_move_node)

        >>> root_move_node.children # doctest: +ELLIPSIS
        [MoveNode(...), MoveNode(...)]

        '''
        return self._children

    @property
    def moves_chain(self):
        yield self._move

    def __str__(self):
        return f'{type(self).__name__} for {self._move}'

    def __repr__(self):
        return f'{type(self).__name__}({self._move!r}, {self._grade!r})'


class MoveNode(RootMoveNode):
    '''

    >>> parent_move = Move('e2e4')
    >>> parent_move_node = RootMoveNode(parent_move)

    >>> move = Move('d7d6')
    >>> move_node = MoveNode(move, parent_move_node, Decimal('-100'))

    >>> move_node # doctest: +ELLIPSIS
    MoveNode(Move(Coordinate(3, 6), Coordinate(3, 5), False), RootMoveNode(...), Decimal('-100'))
    >>> str(move_node)
    'MoveNode for d7d6'
    >>> move_node.move
    Move(Coordinate(3, 6), Coordinate(3, 5), False)
    >>> move_node.parent # doctest: +ELLIPSIS
    RootMoveNode(...)
    >>> move_node.children
    []

    >>> move_node.grade
    Decimal('-100')
    >>> move_node.parent.grade
    Decimal('100')
    >>> move_node.grade = Decimal('-200')
    >>> move_node.grade
    Decimal('-200')
    >>> move_node.parent.grade
    Decimal('200')

    >>> list(move_node.moves_chain) # doctest: +NORMALIZE_WHITESPACE
    [Move(Coordinate(4, 1), Coordinate(4, 3), False),
     Move(Coordinate(3, 6), Coordinate(3, 5), False)]

    '''
    def __init__(self, move, parent, grade=Decimal('0')):
        super().__init__(move, grade)
        self._parent = weakref.ref(parent)
        self._parent().children.append(self)

        self._parent()._update_grade()

    @property
    def parent(self):
        return self._parent()

    @property
    def grade(self):
        '''

        >>> root_move = Move('a2a3')
        >>> root_move_node = RootMoveNode(root_move, Decimal('10'))

        >>> parent_move = Move('a7a6')
        >>> parent_move_node = MoveNode(parent_move, root_move_node, Decimal('-15'))

        >>> move = Move('a3a4')
        >>> move_node = MoveNode(move, parent_move_node, Decimal('20'))

        >>> root_move_node.grade
        Decimal('20')
        >>> parent_move_node.grade
        Decimal('-20')
        >>> move_node.grade
        Decimal('20')

        >>> move_node.grade = Decimal('-10')
        >>> root_move_node.grade
        Decimal('-10')
        >>> parent_move_node.grade
        Decimal('10')
        >>> move_node.grade
        Decimal('-10')

        >>> parent_move_node.grade = Decimal('-100')
        >>> root_move_node.grade
        Decimal('100')
        >>> parent_move_node.grade
        Decimal('-100')
        >>> move_node.grade
        Decimal('-10')

        '''
        return self._grade

    @grade.setter
    def grade(self, value):
        self._grade = value
        self._parent()._update_grade()

    def _update_grade(self):
        old_grade = self._grade
        super()._update_grade()

        if self._grade != old_grade:
            self._parent()._update_grade()

    @property
    def moves_chain(self):
        '''

        >>> root_move = Move('a2a3')
        >>> root_move_node = RootMoveNode(root_move)

        >>> parent_move = Move('a7a6')
        >>> parent_move_node = MoveNode(parent_move, root_move_node)

        >>> move = Move('a3a4')
        >>> move_node = MoveNode(move, parent_move_node)

        >>> list(move_node.moves_chain) # doctest: +NORMALIZE_WHITESPACE
        [Move(Coordinate(0, 1), Coordinate(0, 2), False),
         Move(Coordinate(0, 6), Coordinate(0, 5), False),
         Move(Coordinate(0, 2), Coordinate(0, 3), False)]
        >>> list(move_node.moves_chain) # doctest: +ELLIPSIS
        [Move(...), Move(...), Move(...)]

        '''
        yield from self._parent().moves_chain
        yield self._move

    def __str__(self):
        return f'{type(self).__name__} for {self._move}'

    def __repr__(self):
        return f'{type(self).__name__}({self._move!r}, {self._parent()!r}, {self._grade!r})'


class TreeOfMoves:
    '''

    >>> root_moves = [Move('a2a3'), Move('a2a4')]
    >>> tree_of_moves = TreeOfMoves(root_moves)

    >>> tree_of_moves # doctest: +ELLIPSIS
    TreeOfMoves([Move(...), Move(...)])
    >>> str(tree_of_moves)
    'TreeOfMoves'

    '''
    def __init__(self, root_moves):
        self._levels = []

        self._root_moves = root_moves
        self._levels.append(
            [RootMoveNode(move) for move in root_moves]
        )

    def __getitem__(self, level_index):
        return self._levels[level_index]

    def __len__(self):
        return len(self._levels)

    def add_level(self):
        self._levels.append([])

    def add_node(self, node):
        self._levels[-1].append(node)

    @property
    def root_moves(self):
        return self._levels[0]

    @property
    def best_move(self):
        max_grade = max(
            -move_node.grade for move_node in self._levels[0]
        )
        best_moves = [
            move_node.move for move_node in self._levels[0] if -move_node.grade == max_grade
        ]

        return choice(best_moves)

    def __str__(self):
        return f'{type(self).__name__}'

    def __repr__(self):
        return f'{type(self).__name__}({self._root_moves!r})'


class Analyzer:
    '''

    >>> position = Position.starting_position()
    >>> analyzer = Analyzer(position)

    >>> analyzer.position
    Position.from_fen(('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR', 'w', 'KQkq', '-', '0', '1'))
    >>> analyzer # doctest: +ELLIPSIS
    Analyzer(Position.from_fen(...))
    >>> str(analyzer)
    'Analyzer for rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    >>> analyzer.ready
    True
    >>> analyzer.best_move
    EmptyMove()

    '''
    def __init__(self, position):
        self._position = position

        self._ready = True
        self._best_move = EmptyMove()

    def _candidate_moves(self, position):
        moves = []

        for x in range(8):
            for y in range(8):
                coordinate = Coordinate(x, y)
                cell = position.board[coordinate]

                if isinstance(cell, Figure) and cell.color == position.turn:
                    moves += cell.available_moves(coordinate, position)

        return moves

    def _check_check(self, opponents_position, opponents_candidate_moves):
        for move in opponents_candidate_moves:
            finish = move.finish
            destination = opponents_position.board[finish]

            if isinstance(destination, King) and destination.color != opponents_position.turn:
                return True

        else:
            return False

    def _check_attack(self, position, coordinate):
        opponents_position = position.deepcopy()
        opponents_position.move(EmptyMove())
        opponents_candidate_moves = self._candidate_moves(opponents_position)

        for move in opponents_candidate_moves:
            if move.finish == coordinate:
                return True

        else:
            return False

    def _filter_checks(self, position, moves):
        legal_moves = []

        for move in moves:
            opponents_position = position.deepcopy()
            opponents_position.move(move)
            opponents_candidate_moves = self._candidate_moves(opponents_position)

            if not self._check_check(opponents_position, opponents_candidate_moves):
                legal_moves.append(move)

        return legal_moves

    def _filter_castlings(self, position, moves):
        legal_moves = []

        for move in moves:
            start = move.start
            figure = position.board[start]

            if move.is_short_castling(figure) or move.is_long_castling(figure):
                delta_y = 1 if position.turn == 'w' else -1
                delta_x = 1 if move.is_short_castling(figure) else -1

                for factor_x in range(0, 4):
                    cell = position.board[start.delta(x=delta_x * factor_x, y=delta_y)]

                    if isinstance(cell, Pawn) and cell.color != position.turn:
                        break

                else:
                    if not(
                        self._check_attack(position, start) or
                        self._check_attack(position, start.delta(x=delta_x))
                    ):
                        legal_moves.append(move)

            else:
                legal_moves.append(move)

        return legal_moves

    def _filter_illegal_moves(self, position, moves):
        legal_moves = moves

        legal_moves = self._filter_checks(position, legal_moves)
        legal_moves = self._filter_castlings(position, legal_moves)

        return legal_moves

    def _count_figures(self, position):
        grades = {'current_player': Decimal('0'), 'opponent': Decimal('0')}

        for line in position.board:
            for cell in line:
                if isinstance(cell, Figure):
                    figure = cell

                    if cell.color == position.turn:
                        grades['current_player'] += figure.worth

                    else:
                        grades['opponent'] += figure.worth

        return grades

    def _estimate(self, position, available_moves):
        grade = Decimal('0')

        opponents_position = position.deepcopy()
        opponents_position.move(EmptyMove())
        opponents_candidate_moves = self._candidate_moves(opponents_position)

        if not available_moves:
            if self._check_check(opponents_position, opponents_candidate_moves):
                grade = Decimal('-300')
            else:
                grade = Decimal('0')

        else:
            opponents_available_moves = self._filter_illegal_moves(
                opponents_position, opponents_candidate_moves
            )
            figures = self._count_figures(position)

            grade = (
                (figures['current_player'] - figures['opponent']) +
                Decimal(len(available_moves) - len(opponents_available_moves)) / Decimal('100')
            )

        return grade

    def _estimation_thread_target(self, tree_of_moves, root_position, max_depth):
        index = 0

        for depth in range(max_depth):
            if self._ready or not tree_of_moves[depth]:
                break

            if depth != max_depth - 1:
                tree_of_moves.add_level()

            for move_node in tree_of_moves[depth]:
                opponents_position = root_position.deepcopy()
                for chain_move in move_node.moves_chain:
                    opponents_position.move(chain_move)

                if self._ready:
                    break

                opponents_candidate_moves = self._candidate_moves(opponents_position)
                opponents_available_moves = self._filter_illegal_moves(
                    opponents_position, opponents_candidate_moves
                )

                if depth != max_depth - 1:
                    for available_move in opponents_available_moves:
                        new_node = MoveNode(available_move, move_node, INFINITY)
                        tree_of_moves.add_node(new_node)

                move_node.grade = self._estimate(opponents_position, opponents_available_moves)

                if index % 10 == 0:
                    self._best_move = tree_of_moves.best_move
                index += 1
                if self._ready:
                    break

        self._best_move = tree_of_moves.best_move
        self._ready = True

    def _chosee_best_move(self, position, moves, depth):
        tree_of_moves = TreeOfMoves(moves)

        estimation_thread = Thread(
            target=self._estimation_thread_target,
            args=(tree_of_moves, position, depth),

            daemon=True
        )
        estimation_thread.start()

    def go(self, depth=DEFAULT_DEPTH):
        self._ready = False

        position = self._position

        available_moves = self._candidate_moves(position)
        available_moves = self._filter_illegal_moves(position, available_moves)

        if not available_moves:
            self._best_move = EmptyMove()
            self._ready = True

        elif depth == 0:
            self._best_move = choice(available_moves)
            self._ready = True

        else:
            self._best_move = choice(available_moves)
            self._chosee_best_move(position, available_moves, depth * 2)

    def stop(self):
        self._ready = True

    @property
    def best_move(self):
        return self._best_move

    @property
    def ready(self):
        return self._ready

    @property
    def position(self):
        return self._position

    def __str__(self):
        return f'{type(self).__name__} for {self._position}'

    def __repr__(self):
        return f'{type(self).__name__}({self._position!r})'


if __name__ == '__main__':
    doctest.testmod()
