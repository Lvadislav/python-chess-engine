import doctest
from decimal import Decimal

try:
    from .primitives import Coordinate, EmptyCell, EmptyMove
except (ImportError, SystemError):
    from primitives import Coordinate, EmptyCell, EmptyMove

STARTING_POSITION_FEN = ('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR', 'w', 'KQkq', '-', '0', '1')


class Move:
    '''

    >>> move = Move('e2e4')

    >>> move
    Move(Coordinate(4, 1), Coordinate(4, 3), False)
    >>> str(move)
    'e2e4'

    >>> move = Move('a7a8q')

    >>> move
    Move(Coordinate(0, 6), Coordinate(0, 7), Queen)
    >>> str(move)
    'a7a8q'

    >>> move = Move(Coordinate(4, 1), Coordinate(4, 3))

    >>> move
    Move(Coordinate(4, 1), Coordinate(4, 3), False)
    >>> str(move)
    'e2e4'

    >>> move = Move(Coordinate(4, 1), Coordinate(4, 3), Knight)

    >>> move
    Move(Coordinate(4, 1), Coordinate(4, 3), Knight)
    >>> str(move)
    'e2e4n'
    >>> move.start
    Coordinate(4, 1)
    >>> move.finish
    Coordinate(4, 3)
    >>> move.promotion.__name__
    'Knight'

    '''
    def __init__(self, *args):
        if len(args) == 1:
            self._start = Coordinate(args[0][: 2])
            self._finish = Coordinate(args[0][2: 4])

            if len(args[0]) > 4:
                self._promotion = FIGURES[args[0][4]]
            else:
                self._promotion = False

        else:
            self._start, self._finish = args[: 2]

            if len(args) > 2:
                self._promotion = args[2]
            else:
                self._promotion = False

    @property
    def start(self):
        return self._start

    @property
    def finish(self):
        return self._finish

    @property
    def promotion(self):
        return self._promotion

    def is_promotion(self):
        '''

        >>> move_a = Move('e7f8q')
        >>> move_b = Move('a6a7')

        >>> move_a.is_promotion()
        True

        >>> move_b.is_promotion()
        False

        '''
        return bool(self._promotion)

    def is_short_castling(self, figure):
        '''

        >>> move_a = Move('e1g1')
        >>> move_b = Move('e1c1')

        >>> move_a.is_short_castling(King('w'))
        True

        >>> move_b.is_short_castling(King('w'))
        False

        '''
        return bool(
            isinstance(figure, King) and
            (self._start.x - self._finish.x == -2)
        )

    def is_long_castling(self, figure):
        '''

        >>> move_a = Move('e8g8')
        >>> move_b = Move('e8c8')

        >>> move_a.is_long_castling(King('b'))
        False

        >>> move_b.is_long_castling(King('b'))
        True

        '''
        return bool(
            isinstance(figure, King) and
            (self._start.x - self._finish.x == 2)
        )

    def is_double_jump(self, figure):
        '''

        >>> move_a = Move('e2e3')
        >>> move_b = Move('e2e4')
        >>> move_c = Move('a7a5')

        >>> move_a.is_double_jump(Pawn('w'))
        False

        >>> move_b.is_double_jump(Pawn('w'))
        True

        >>> move_c.is_double_jump(Pawn('b'))
        True

        '''
        return bool(
            isinstance(figure, Pawn) and
            abs(self._start.y - self._finish.y) == 2
        )

    def is_en_passant(self, figure, en_passant):
        '''

        >>> move_a = Move('a5b6')
        >>> move_b = Move('a5a6')

        >>> move_a.is_en_passant(Pawn('w'), Coordinate('b6'))
        True

        >>> move_a.is_en_passant(Queen('w'), Coordinate('b6'))
        False

        >>> move_b.is_en_passant(Pawn('w'), Coordinate('a6'))
        True

        >>> move_b.is_en_passant(Pawn('w'), Coordinate('c6'))
        False

        '''
        return bool(
            isinstance(figure, Pawn) and
            en_passant and
            en_passant == self._finish
        )

    def __eq__(self, other):
        '''

        >>> move_a = Move('e7e8')
        >>> move_b = Move(Coordinate(4, 6), Coordinate(4, 7))
        >>> move_c = Move(Coordinate(4, 6), Coordinate(4, 7), Queen)

        >>> move_a == move_b
        True

        >>> move_a == move_c
        False

        '''
        return (
            self._start == other.start and
            self._finish == other.finish and
            self._promotion == other.promotion
        )

    def __str__(self):
        promotion = '' if not self._promotion else self._promotion.symbol
        return f'{self._start}{self._finish}{promotion}'

    def __repr__(self):
        if self._promotion:
            promotion = self._promotion.__name__
        else:
            promotion = False

        return f'{type(self).__name__}({self._start!r}, {self._finish!r}, {promotion})'


class Board:
    '''

    >>> board = Board()

    >>> board
    Board('8/8/8/8/8/8/8/8')
    >>> str(board)
    '8/8/8/8/8/8/8/8'
    >>> board.as_fen
    '8/8/8/8/8/8/8/8'

    >>> board = Board('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR')

    >>> board.as_fen
    'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR'

    >>> board = Board('rnb1kb1r/ppp1qppp/3p1n2/3Pp3/4P3/2N2P2/PPP3PP/R1BQKBNR')

    >>> board
    Board('rnb1kb1r/ppp1qppp/3p1n2/3Pp3/4P3/2N2P2/PPP3PP/R1BQKBNR')
    >>> str(board)
    'rnb1kb1r/ppp1qppp/3p1n2/3Pp3/4P3/2N2P2/PPP3PP/R1BQKBNR'
    >>> board.as_fen
    'rnb1kb1r/ppp1qppp/3p1n2/3Pp3/4P3/2N2P2/PPP3PP/R1BQKBNR'

    '''
    def __init__(self, fen_board=None):
        self._cells = [
            [EmptyCell() for y in range(8)] for x in range(8)
        ]

        if fen_board is not None:
            self._load_from_fen(fen_board)

    def _load_from_fen(self, fen_board):
        x, y = 0, 7
        for symbol in fen_board:
            if symbol == '/':
                y -= 1
                x = 0

            elif '1' <= symbol <= '8':
                x += int(symbol)

            else:
                color = 'w' if symbol.isupper() else 'b'
                symbol = symbol.lower()

                self._cells[x][y] = FIGURES[symbol](
                    color=color
                )

                x += 1

    @property
    def as_fen(self):
        fen_board = ''

        empty_chain = 0
        for y in range(7, -1, -1):
            for x in range(8):
                cell = self._cells[x][y]

                if isinstance(cell, EmptyCell):
                    empty_chain += 1

                if not isinstance(cell, EmptyCell) or x == 7:
                    if empty_chain > 0:
                        fen_board += str(empty_chain)
                        empty_chain = 0

                if not isinstance(cell, EmptyCell):
                    fen_board += cell.fen_symbol

            if y != 0:
                fen_board += '/'

        return fen_board

    @property
    def cells(self):
        return self._cells

    def __getitem__(self, index):
        if isinstance(index, Coordinate):
            return self._cells[index.x][index.y]
        else:
            return self._cells[index]

    def __setitem__(self, index, value):
        self._cells[index.x][index.y] = value

    def __str__(self):
        return self.as_fen

    def __repr__(self):
        return f'{type(self).__name__}({self.as_fen!r})'


class Position:
    '''

    >>> position = Position(
    ...     Board('rnbqkb1r/pp3ppp/2p5/3pP2n/2BQ4/5N2/PPP2PPP/RNB1K2R'),
    ...     'w',
    ...     {'w': {'k': True, 'q': True}, 'b': {'k': True, 'q': True}},
    ...     Coordinate('d6'),
    ...     0,
    ...     6
    ... )

    >>> position.as_fen
    ('rnbqkb1r/pp3ppp/2p5/3pP2n/2BQ4/5N2/PPP2PPP/RNB1K2R', 'w', 'KQkq', 'd6', '0', '7')
    >>> position.as_short_fen
    ('rnbqkb1r/pp3ppp/2p5/3pP2n/2BQ4/5N2/PPP2PPP/RNB1K2R', 'w', 'KQkq', 'd6')
    >>> position # doctest: +ELLIPSIS
    Position.from_fen(('...', 'w', 'KQkq', 'd6', '0', '7'))
    >>> str(position)
    'rnbqkb1r/pp3ppp/2p5/3pP2n/2BQ4/5N2/PPP2PPP/RNB1K2R w KQkq d6 0 7'
    >>> position.board
    Board('rnbqkb1r/pp3ppp/2p5/3pP2n/2BQ4/5N2/PPP2PPP/RNB1K2R')
    >>> position.turn
    'w'
    >>> position.castling == {'w': {'k': True, 'q': True}, 'b': {'k': True, 'q': True}}
    True
    >>> position.en_passant
    Coordinate(3, 5)
    >>> position.number_of_reversible_moves
    0
    >>> position.move_number
    6

    >>> position.move(Move('e5d6'))

    >>> position.as_fen
    ('rnbqkb1r/pp3ppp/2pP4/7n/2BQ4/5N2/PPP2PPP/RNB1K2R', 'b', 'KQkq', '-', '0', '7')
    >>> position.as_short_fen
    ('rnbqkb1r/pp3ppp/2pP4/7n/2BQ4/5N2/PPP2PPP/RNB1K2R', 'b', 'KQkq', '-')
    >>> position.board
    Board('rnbqkb1r/pp3ppp/2pP4/7n/2BQ4/5N2/PPP2PPP/RNB1K2R')
    >>> position.turn
    'b'
    >>> position.castling == {'w': {'k': True, 'q': True}, 'b': {'k': True, 'q': True}}
    True
    >>> position.en_passant
    False
    >>> position.number_of_reversible_moves
    0
    >>> position.move_number
    6

    '''
    def __init__(self, board, turn, castling, en_passant,
                 number_of_reversible_moves, move_number, moves=None):
        if moves is None:
            moves = []

        self._board = board

        self._turn = turn

        self._castling = castling
        self._en_passant = en_passant
        self._next_en_passant = False

        self._number_of_reversible_moves = number_of_reversible_moves
        self._move_number = move_number
        for move in moves:
            self.move(move)

    @classmethod
    def starting_position(cls):
        '''

        >>> position = Position.starting_position()

        >>> position.board
        Board('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR')
        >>> position.turn
        'w'
        >>> position.castling == {'w': {'k': True, 'q': True}, 'b': {'k': True, 'q': True}}
        True
        >>> position.en_passant
        False
        >>> position.number_of_reversible_moves
        0
        >>> position.move_number
        0
        >>> position.as_fen
        ('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR', 'w', 'KQkq', '-', '0', '1')
        >>> position.as_short_fen
        ('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR', 'w', 'KQkq', '-')

        '''
        return cls.from_fen(STARTING_POSITION_FEN)

    @classmethod
    def from_fen(cls, fen_position, moves=None):
        if moves is None:
            moves = []

        board = Board(fen_position[0])

        turn = fen_position[1]
        castling = {
            'w': {'k': 'K' in fen_position[2], 'q': 'Q' in fen_position[2]},
            'b': {'k': 'k' in fen_position[2], 'q': 'q' in fen_position[2]}
        }

        en_passant = fen_position[3]
        if en_passant == '-':
            en_passant = False
        else:
            en_passant = Coordinate(en_passant)

        number_of_reversible_moves = int(fen_position[4])
        move_number = int(fen_position[5]) - 1

        for index, move in enumerate(moves):
            moves[index] = Move(move)

        return cls(
            board, turn, castling, en_passant,
            number_of_reversible_moves, move_number, moves
        )

    @property
    def as_fen(self):
        fen_position = []

        fen_position.append(self._board.as_fen)
        fen_position.append(self._turn)

        castling = ''
        if self._castling['w']['k']:
            castling += 'K'
        if self._castling['w']['q']:
            castling += 'Q'
        if self._castling['b']['k']:
            castling += 'k'
        if self._castling['b']['q']:
            castling += 'q'
        if not castling:
            castling = '-'
        fen_position.append(castling)

        if not self._en_passant:
            fen_position.append('-')
        else:
            fen_position.append(str(self._en_passant))

        fen_position.append(str(self._number_of_reversible_moves))
        fen_position.append(str(self._move_number + 1))

        return tuple(fen_position)

    @property
    def as_short_fen(self):
        short_fen_position = self.as_fen[:-2]

        return short_fen_position

    def deepcopy(self):
        '''

        >>> position = Position.starting_position()
        >>> position_copy = position.deepcopy()
        >>> str(position_copy)
        'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

        >>> position.board is position_copy.board
        False
        >>> position.castling is position_copy.castling
        False

        '''
        cls = type(self)

        position_copy = cls.from_fen(self.as_fen)

        return position_copy

    def _update_castling(self, start, finish):
        '''

        >>> position_a = Position.from_fen((
        ...     'r1bq1bnr/pppk1ppp/2np4/4Q3/4P3/8/PPP2PPP/RNB1KBNR',
        ...     'w', 'KQ', '-',
        ...     '2', '6'
        ... ))
        >>> position_b = Position.from_fen((
        ...     'r1bqkbnr/ppp2ppp/2np4/4Q3/4P3/8/PPP2PPP/RNB1KBNR',
        ...     'b', 'KQkq', '-',
        ...     '1', '5'
        ... ))

        >>> position_a.move(Move('e1d1'))
        >>> position_a.as_fen
        ('r1bq1bnr/pppk1ppp/2np4/4Q3/4P3/8/PPP2PPP/RNBK1BNR', 'b', '-', '-', '3', '6')
        >>> position_b.move(Move('e8d7'))
        >>> position_b.as_fen
        ('r1bq1bnr/pppk1ppp/2np4/4Q3/4P3/8/PPP2PPP/RNB1KBNR', 'w', 'KQ', '-', '2', '6')

        >>> position_c = Position.from_fen((
        ...     'rnbqk2r/pppp3p/5n2/2b1ppp1/2B1PPP1/5N2/PPPP3P/RNBQK2R',
        ...     'w', 'KQkq', '-',
        ...     '4', '6'
        ... ))
        >>> position_d = Position.from_fen((
        ...     'rnbqk2r/pppp3p/5n2/2b1ppp1/2B1PPP1/5N2/PPPP3P/RNBQK1R1',
        ...     'b', 'Qkq', '-',
        ...     '5', '6'
        ... ))

        >>> position_c.move(Move('h1g1'))
        >>> position_c.as_fen
        ('rnbqk2r/pppp3p/5n2/2b1ppp1/2B1PPP1/5N2/PPPP3P/RNBQK1R1', 'b', 'Qkq', '-', '5', '6')
        >>> position_d.move(Move('h8g8'))
        >>> position_d.as_fen
        ('rnbqk1r1/pppp3p/5n2/2b1ppp1/2B1PPP1/5N2/PPPP3P/RNBQK1R1', 'w', 'Qq', '-', '6', '7')

        >>> position_e = Position.from_fen((
        ...     'r3k1r1/p1ppq2p/b1n2n2/1pb1ppp1/1PB1PPP1/B1N2N2/P1PPQ2P/R3K1R1',
        ...     'w', 'Qq', '-',
        ...     '2', '11'
        ... ))
        >>> position_f = Position.from_fen((
        ...     'r3k1r1/p1ppq2p/b1n2n2/1pb1ppp1/1PB1PPP1/B1N2N2/P1PPQ2P/3RK1R1',
        ...     'b', 'q', '-',
        ...     '3', '11'
        ... ))

        >>> position_e.move(Move('a1d1'))
        >>> position_e.as_fen
        ('r3k1r1/p1ppq2p/b1n2n2/1pb1ppp1/1PB1PPP1/B1N2N2/P1PPQ2P/3RK1R1', 'b', 'q', '-', '3', '11')
        >>> position_f.move(Move('a8d8'))
        >>> position_f.as_fen
        ('3rk1r1/p1ppq2p/b1n2n2/1pb1ppp1/1PB1PPP1/B1N2N2/P1PPQ2P/3RK1R1', 'w', '-', '-', '4', '12')

        >>> position_g = Position.from_fen((
        ...     'Rnb1kbnr/1pp1pp1p/8/3q2p1/3Q2P1/8/1PP1PP1P/1NB1KBNR',
        ...     'w', 'Kk', '-',
        ...     '0', '9'
        ... ))
        >>> position_h = Position.from_fen((
        ...     'Rnb1kbnQ/1pp1pp1p/8/3q2p1/6P1/8/1PP1PP1P/1NB1KBNR',
        ...     'b', 'K', '-',
        ...     '0', '9'
        ... ))

        >>> position_g.move(Move('d4h8'))
        >>> position_g.as_fen
        ('Rnb1kbnQ/1pp1pp1p/8/3q2p1/6P1/8/1PP1PP1P/1NB1KBNR', 'b', 'K', '-', '0', '9')
        >>> position_h.move(Move('d5h1'))
        >>> position_h.as_fen
        ('Rnb1kbnQ/1pp1pp1p/8/6p1/6P1/8/1PP1PP1P/1NB1KBNq', 'w', '-', '-', '0', '10')

        >>> position_i = Position.from_fen((
        ...     'r1bqkbnr/1ppppppp/1N6/p7/P7/1n6/1PPPPPPP/R1BQKBNR',
        ...     'w', 'KQkq', '-',
        ...     '10', '7'
        ... ))
        >>> position_j = Position.from_fen((
        ...     'N1bqkbnr/1ppppppp/8/p7/P7/1n6/1PPPPPPP/R1BQKBNR',
        ...     'b', 'KQk', '-',
        ...     '0', '7'
        ... ))

        >>> position_i.move(Move('b6a8'))
        >>> position_i.as_fen
        ('N1bqkbnr/1ppppppp/8/p7/P7/1n6/1PPPPPPP/R1BQKBNR', 'b', 'KQk', '-', '0', '7')
        >>> position_j.move(Move('b3a1'))
        >>> position_j.as_fen
        ('N1bqkbnr/1ppppppp/8/p7/P7/8/1PPPPPPP/n1BQKBNR', 'w', 'Kk', '-', '0', '8')

        >>> position_k = Position.from_fen((
        ...     'rnb1kbnr/1pp1pppp/8/3Q4/3q4/8/1PP1PPPP/RNB1KBNR',
        ...     'w', 'KQkq', '-',
        ...     '0', '6'
        ... ))

        >>> position_k.move(Move('a1a8'))
        >>> position_k.as_fen
        ('Rnb1kbnr/1pp1pppp/8/3Q4/3q4/8/1PP1PPPP/1NB1KBNR', 'b', 'Kk', '-', '0', '6')

        '''
        figure = self._board[start]
        destination = self._board[finish]

        if isinstance(figure, King):
            self._castling[figure.color]['k'] = False
            self._castling[figure.color]['q'] = False
        if isinstance(figure, Rook):
            if (figure.color == 'w' and start.y == 0) or (figure.color == 'b' and start.y == 7):
                if start.x == 0:
                    self._castling[figure.color]['q'] = False
                elif start.x == 7:
                    self._castling[figure.color]['k'] = False
        if isinstance(destination, Rook):
            if(
                (destination.color == 'w' and finish.y == 0) or
                (destination.color == 'b' and finish.y == 7)
            ):
                if finish.x == 0:
                    self._castling[destination.color]['q'] = False
                elif finish.x == 7:
                    self._castling[destination.color]['k'] = False

    def _move_simple(self, start, finish):
        self._update_castling(start, finish)

        self._board[finish] = self._board[start]
        self._board[start] = EmptyCell()

    def _move_promotion(self, start, finish, promotion):
        '''

        >>> position_a = Position.from_fen((
        ...     '3k2nr/1P6/5pp1/7p/3NpB2/p7/P2K1bPP/R7',
        ...     'w', '-', '-',
        ...     '0', '25'
        ... ))
        >>> position_b = Position.from_fen((
        ...     '1R4nr/3k4/6p1/1N2p2p/4K3/p7/P3pbPP/R7',
        ...     'b', '-', '-',
        ...     '1', '29'
        ... ))

        >>> position_a.move(Move('b7b8r'))
        >>> position_a.as_fen
        ('1R1k2nr/8/5pp1/7p/3NpB2/p7/P2K1bPP/R7', 'b', '-', '-', '0', '25')
        >>> position_b.move(Move('e2e1q'))
        >>> position_b.as_fen
        ('1R4nr/3k4/6p1/1N2p2p/4K3/p7/P4bPP/R3q3', 'w', '-', '-', '0', '30')

        >>> position_c = Position.from_fen((
        ...     'rnb1k1nr/2P3pp/p2b1p2/1p2p3/2Pq4/3P1N2/P4PPP/RNBQKB1R',
        ...     'w', 'KQkq', '-',
        ...     '1', '10'
        ... ))
        >>> position_d = Position.from_fen((
        ...     'rbb1k1nr/6pp/p4p2/2P1p3/3q4/1Q1P1N2/p3KPPP/RNB2B1R',
        ...     'b', 'kq', '-',
        ...     '0', '14'
        ... ))

        >>> position_c.move(Move('c7b8b'))
        >>> position_c.as_fen
        ('rBb1k1nr/6pp/p2b1p2/1p2p3/2Pq4/3P1N2/P4PPP/RNBQKB1R', 'b', 'KQkq', '-', '0', '10')
        >>> position_d.move(Move('a2b1n'))
        >>> position_d.as_fen
        ('rbb1k1nr/6pp/p4p2/2P1p3/3q4/1Q1P1N2/4KPPP/RnB2B1R', 'w', 'kq', '-', '0', '15')

        '''
        color = self._board[start].color

        self._update_castling(start, finish)

        self._board[start] = EmptyCell()
        self._board[finish] = promotion(color)

    def _move_short_castling(self, start, finish):
        '''

        >>> position_a = Position.from_fen((
        ...     'rn3rk1/pp2bppp/3p1q1n/5P2/2B2P2/5N2/PPP3PP/RNBQK2R',
        ...     'w', 'KQ', '-',
        ...     '5', '9'
        ... ))
        >>> position_b = Position.from_fen((
        ...     'rn2k2r/pp2bppp/3p1q1n/5P2/2B2P2/5N2/PPP3PP/RNBQK2R',
        ...     'b', 'KQkq', '-',
        ...     '4', '8'
        ... ))

        >>> position_a.move(Move('e1g1'))
        >>> position_a.as_fen
        ('rn3rk1/pp2bppp/3p1q1n/5P2/2B2P2/5N2/PPP3PP/RNBQ1RK1', 'b', '-', '-', '6', '9')

        >>> position_b.move(Move('e8g8'))
        >>> position_b.as_fen
        ('rn3rk1/pp2bppp/3p1q1n/5P2/2B2P2/5N2/PPP3PP/RNBQK2R', 'w', 'KQ', '-', '5', '9')

        '''
        self._move_simple(start, finish)
        self._move_simple(finish.delta(1, 0), start.delta(1, 0))

    def _move_long_castling(self, start, finish):
        '''

        >>> position_a = Position.from_fen((
        ...     'r2qkb1r/ppp1p1pp/n1b2n2/3p1p2/3P4/2N1PN2/PPPBQPPP/R3KB1R',
        ...     'w', 'KQkq', '-',
        ...     '8', '7'
        ... ))
        >>> position_b = Position.from_fen((
        ...     'r3kb1r/ppp1p1pp/n1bq1n2/1Q1p1p2/3P4/2N1PN2/PPPB1PPP/2KR1B1R',
        ...     'b', 'kq', '-',
        ...     '2', '8'
        ... ))

        >>> position_a.move(Move('e1c1'))
        >>> position_a.as_fen
        ('r2qkb1r/ppp1p1pp/n1b2n2/3p1p2/3P4/2N1PN2/PPPBQPPP/2KR1B1R', 'b', 'kq', '-', '9', '7')

        >>> position_b.move(Move('e8c8'))
        >>> position_b.as_fen
        ('2kr1b1r/ppp1p1pp/n1bq1n2/1Q1p1p2/3P4/2N1PN2/PPPB1PPP/2KR1B1R', 'w', '-', '-', '3', '9')

        '''
        self._move_simple(start, finish)
        self._move_simple(finish.delta(-2, 0), start.delta(-1, 0))

    def _move_double_jump(self, start, finish):
        '''

        >>> position_a = Position.from_fen((
        ...     'rnb1kbnr/pppp1pp1/8/4p1qp/P7/R3P3/1PPP1PPP/1NBQKBNR',
        ...     'w', 'Kkq', 'h6',
        ...     '0', '4'
        ... ))
        >>> position_b = Position.from_fen((
        ...     'rnb1kbnr/pppp1ppp/8/4p1q1/P7/R3P3/1PPP1PPP/1NBQKBNR',
        ...     'b', 'Kkq', '-',
        ...     '0', '3'
        ... ))

        >>> position_a.move(Move('b2b4'))
        >>> position_a.as_fen
        ('rnb1kbnr/pppp1pp1/8/4p1qp/PP6/R3P3/2PP1PPP/1NBQKBNR', 'b', 'Kkq', 'b3', '0', '4')

        >>> position_b.move(Move('h7h5'))
        >>> position_b.as_fen
        ('rnb1kbnr/pppp1pp1/8/4p1qp/P7/R3P3/1PPP1PPP/1NBQKBNR', 'w', 'Kkq', 'h6', '0', '4')

        '''
        self._move_simple(start, finish)
        self._next_en_passant = Coordinate(
            start.x,
            (start.y + finish.y) // 2
        )

    def _move_en_passant(self, start, finish):
        '''

        >>> position_a = Position.from_fen((
        ...     'rnbqkbnr/p1p2ppp/3p4/1pP1p3/4P3/8/PP1P1PPP/RNBQKBNR',
        ...     'w', 'KQkq', 'b6',
        ...     '0', '4'
        ... ))
        >>> position_b = Position.from_fen((
        ...     'rnbqkbnr/p1p3p1/1P1p4/4pP2/6Pp/7P/PP1P1P2/RNBQKBNR',
        ...     'b', 'KQkq', 'g3',
        ...     '0', '7'
        ... ))

        >>> position_a.move(Move('c5b6'))
        >>> position_a.as_fen
        ('rnbqkbnr/p1p2ppp/1P1p4/4p3/4P3/8/PP1P1PPP/RNBQKBNR', 'b', 'KQkq', '-', '0', '4')

        >>> position_b.move(Move('h4g3'))
        >>> position_b.as_fen
        ('rnbqkbnr/p1p3p1/1P1p4/4pP2/8/6pP/PP1P1P2/RNBQKBNR', 'w', 'KQkq', '-', '0', '8')

        '''
        color = self._board[start].color

        self._move_simple(start, finish)

        if color == 'w':
            self._board[finish.x][finish.y - 1] = EmptyCell()
        else:
            self._board[finish.x][finish.y + 1] = EmptyCell()

    def move(self, move):
        '''

        >>> position = Position.starting_position()
        >>> moves = [
        ...     Move('e2e4'), Move('d7d5'), Move('e4d5'), Move('e7e5'),
        ...     Move('d5e6'), Move('f7f6'), Move('g1f3'), Move('d8d6'),
        ...     Move('c2c4'), Move('f8e7'), Move('g2g4'), Move('g7g5'),
        ...     Move('f1h3'), Move('g8h6'), Move('d1e2'), Move('e8g8'),
        ...     Move('b2b3'), Move('d6d2'), Move('c1d2'), Move('c8d7'),
        ...     Move('e6d7'), Move('c7c6'), Move('b1c3'), Move('e7d6'),
        ...     Move('e1c1'), Move('d6e5'), Move('d7d8q'), Move('b7b5'),
        ...     Move('c4c5'), Move('b5b4'), Move('a2a4'), Move('b4a3')
        ... ]

        >>> for move in moves:
        ...     position.move(move)
        ...     print(' '.join(position.as_fen))
        ...
        rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1
        rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2
        rnbqkbnr/ppp1pppp/8/3P4/8/8/PPPP1PPP/RNBQKBNR b KQkq - 0 2
        rnbqkbnr/ppp2ppp/8/3Pp3/8/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 3
        rnbqkbnr/ppp2ppp/4P3/8/8/8/PPPP1PPP/RNBQKBNR b KQkq - 0 3
        rnbqkbnr/ppp3pp/4Pp2/8/8/8/PPPP1PPP/RNBQKBNR w KQkq - 0 4
        rnbqkbnr/ppp3pp/4Pp2/8/8/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 4
        rnb1kbnr/ppp3pp/3qPp2/8/8/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 5
        rnb1kbnr/ppp3pp/3qPp2/8/2P5/5N2/PP1P1PPP/RNBQKB1R b KQkq c3 0 5
        rnb1k1nr/ppp1b1pp/3qPp2/8/2P5/5N2/PP1P1PPP/RNBQKB1R w KQkq - 1 6
        rnb1k1nr/ppp1b1pp/3qPp2/8/2P3P1/5N2/PP1P1P1P/RNBQKB1R b KQkq g3 0 6
        rnb1k1nr/ppp1b2p/3qPp2/6p1/2P3P1/5N2/PP1P1P1P/RNBQKB1R w KQkq g6 0 7
        rnb1k1nr/ppp1b2p/3qPp2/6p1/2P3P1/5N1B/PP1P1P1P/RNBQK2R b KQkq - 1 7
        rnb1k2r/ppp1b2p/3qPp1n/6p1/2P3P1/5N1B/PP1P1P1P/RNBQK2R w KQkq - 2 8
        rnb1k2r/ppp1b2p/3qPp1n/6p1/2P3P1/5N1B/PP1PQP1P/RNB1K2R b KQkq - 3 8
        rnb2rk1/ppp1b2p/3qPp1n/6p1/2P3P1/5N1B/PP1PQP1P/RNB1K2R w KQ - 4 9
        rnb2rk1/ppp1b2p/3qPp1n/6p1/2P3P1/1P3N1B/P2PQP1P/RNB1K2R b KQ - 0 9
        rnb2rk1/ppp1b2p/4Pp1n/6p1/2P3P1/1P3N1B/P2qQP1P/RNB1K2R w KQ - 0 10
        rnb2rk1/ppp1b2p/4Pp1n/6p1/2P3P1/1P3N1B/P2BQP1P/RN2K2R b KQ - 0 10
        rn3rk1/pppbb2p/4Pp1n/6p1/2P3P1/1P3N1B/P2BQP1P/RN2K2R w KQ - 1 11
        rn3rk1/pppPb2p/5p1n/6p1/2P3P1/1P3N1B/P2BQP1P/RN2K2R b KQ - 0 11
        rn3rk1/pp1Pb2p/2p2p1n/6p1/2P3P1/1P3N1B/P2BQP1P/RN2K2R w KQ - 0 12
        rn3rk1/pp1Pb2p/2p2p1n/6p1/2P3P1/1PN2N1B/P2BQP1P/R3K2R b KQ - 1 12
        rn3rk1/pp1P3p/2pb1p1n/6p1/2P3P1/1PN2N1B/P2BQP1P/R3K2R w KQ - 2 13
        rn3rk1/pp1P3p/2pb1p1n/6p1/2P3P1/1PN2N1B/P2BQP1P/2KR3R b - - 3 13
        rn3rk1/pp1P3p/2p2p1n/4b1p1/2P3P1/1PN2N1B/P2BQP1P/2KR3R w - - 4 14
        rn1Q1rk1/pp5p/2p2p1n/4b1p1/2P3P1/1PN2N1B/P2BQP1P/2KR3R b - - 0 14
        rn1Q1rk1/p6p/2p2p1n/1p2b1p1/2P3P1/1PN2N1B/P2BQP1P/2KR3R w - b6 0 15
        rn1Q1rk1/p6p/2p2p1n/1pP1b1p1/6P1/1PN2N1B/P2BQP1P/2KR3R b - - 0 15
        rn1Q1rk1/p6p/2p2p1n/2P1b1p1/1p4P1/1PN2N1B/P2BQP1P/2KR3R w - - 0 16
        rn1Q1rk1/p6p/2p2p1n/2P1b1p1/Pp4P1/1PN2N1B/3BQP1P/2KR3R b - a3 0 16
        rn1Q1rk1/p6p/2p2p1n/2P1b1p1/6P1/pPN2N1B/3BQP1P/2KR3R w - - 0 17

        >>> position = Position.starting_position()
        >>> moves = [
        ...     Move('e2e4'), Move('c7c5'), Move('g1f3')
        ... ]

        >>> for move in moves:
        ...     position.move(move)
        ...     print(' '.join(position.as_fen))
        ...
        rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1
        rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2
        rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2

        >>> position = Position.starting_position()
        >>> moves = [
        ...     Move('e2e4'), Move('e7e5'), Move('g1f3'), Move('g8f6'),
        ...     Move('d2d4'), Move('d7d6'), Move('d4d5'), Move('f6e4'),
        ...     Move('d1e2'), Move('c8f5'), Move('h2h3'), Move('c7c6'),
        ...     Move('g2g4'), Move('f5g6'), Move('b1c3'), Move('c6d5'),
        ...     Move('c3d5'), Move('d8a5'), Move('c2c3'), Move('a5d5'),
        ...     Move('c1e3'), Move('h7h5'), Move('e2b5'), Move('d5b5'),
        ...     Move('f1b5'), Move('b8c6'), Move('g4g5'), Move('a7a6'),
        ...     Move('b5c4'), Move('f7f5'), Move('h1g1'), Move('f5f4'),
        ...     Move('e3d2'), Move('e8c8'), Move('e1c1'), Move('e4f2'),
        ...     Move('d1f1'), Move('f2h3'), Move('f1h1')
        ... ]

        for move in moves:
        ...     position.move(move)
        ...     print(' '.join(position.as_fen))
        ...
        rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1
        rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2
        rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2
        rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3
        rnbqkb1r/pppp1ppp/5n2/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq d3 0 3
        rnbqkb1r/ppp2ppp/3p1n2/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R w KQkq - 0 4
        rnbqkb1r/ppp2ppp/3p1n2/3Pp3/4P3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 4
        rnbqkb1r/ppp2ppp/3p4/3Pp3/4n3/5N2/PPP2PPP/RNBQKB1R w KQkq - 0 5
        rnbqkb1r/ppp2ppp/3p4/3Pp3/4n3/5N2/PPP1QPPP/RNB1KB1R b KQkq - 1 5
        rn1qkb1r/ppp2ppp/3p4/3Ppb2/4n3/5N2/PPP1QPPP/RNB1KB1R w KQkq - 2 6
        rn1qkb1r/ppp2ppp/3p4/3Ppb2/4n3/5N1P/PPP1QPP1/RNB1KB1R b KQkq - 0 6
        rn1qkb1r/pp3ppp/2pp4/3Ppb2/4n3/5N1P/PPP1QPP1/RNB1KB1R w KQkq - 0 7
        rn1qkb1r/pp3ppp/2pp4/3Ppb2/4n1P1/5N1P/PPP1QP2/RNB1KB1R b KQkq g3 0 7
        rn1qkb1r/pp3ppp/2pp2b1/3Pp3/4n1P1/5N1P/PPP1QP2/RNB1KB1R w KQkq - 1 8
        rn1qkb1r/pp3ppp/2pp2b1/3Pp3/4n1P1/2N2N1P/PPP1QP2/R1B1KB1R b KQkq - 2 8
        rn1qkb1r/pp3ppp/3p2b1/3pp3/4n1P1/2N2N1P/PPP1QP2/R1B1KB1R w KQkq - 0 9
        rn1qkb1r/pp3ppp/3p2b1/3Np3/4n1P1/5N1P/PPP1QP2/R1B1KB1R b KQkq - 0 9
        rn2kb1r/pp3ppp/3p2b1/q2Np3/4n1P1/5N1P/PPP1QP2/R1B1KB1R w KQkq - 1 10
        rn2kb1r/pp3ppp/3p2b1/q2Np3/4n1P1/2P2N1P/PP2QP2/R1B1KB1R b KQkq - 0 10
        rn2kb1r/pp3ppp/3p2b1/3qp3/4n1P1/2P2N1P/PP2QP2/R1B1KB1R w KQkq - 0 11
        rn2kb1r/pp3ppp/3p2b1/3qp3/4n1P1/2P1BN1P/PP2QP2/R3KB1R b KQkq - 1 11
        rn2kb1r/pp3pp1/3p2b1/3qp2p/4n1P1/2P1BN1P/PP2QP2/R3KB1R w KQkq h6 0 12
        rn2kb1r/pp3pp1/3p2b1/1Q1qp2p/4n1P1/2P1BN1P/PP3P2/R3KB1R b KQkq - 1 12
        rn2kb1r/pp3pp1/3p2b1/1q2p2p/4n1P1/2P1BN1P/PP3P2/R3KB1R w KQkq - 0 13
        rn2kb1r/pp3pp1/3p2b1/1B2p2p/4n1P1/2P1BN1P/PP3P2/R3K2R b KQkq - 0 13
        r3kb1r/pp3pp1/2np2b1/1B2p2p/4n1P1/2P1BN1P/PP3P2/R3K2R w KQkq - 1 14
        r3kb1r/pp3pp1/2np2b1/1B2p1Pp/4n3/2P1BN1P/PP3P2/R3K2R b KQkq - 0 14
        r3kb1r/1p3pp1/p1np2b1/1B2p1Pp/4n3/2P1BN1P/PP3P2/R3K2R w KQkq - 0 15
        r3kb1r/1p3pp1/p1np2b1/4p1Pp/2B1n3/2P1BN1P/PP3P2/R3K2R b KQkq - 1 15
        r3kb1r/1p4p1/p1np2b1/4ppPp/2B1n3/2P1BN1P/PP3P2/R3K2R w KQkq f6 0 16
        r3kb1r/1p4p1/p1np2b1/4ppPp/2B1n3/2P1BN1P/PP3P2/R3K1R1 b Qkq - 1 16
        r3kb1r/1p4p1/p1np2b1/4p1Pp/2B1np2/2P1BN1P/PP3P2/R3K1R1 w Qkq - 0 17
        r3kb1r/1p4p1/p1np2b1/4p1Pp/2B1np2/2P2N1P/PP1B1P2/R3K1R1 b Qkq - 1 17
        2kr1b1r/1p4p1/p1np2b1/4p1Pp/2B1np2/2P2N1P/PP1B1P2/R3K1R1 w Q - 2 18
        2kr1b1r/1p4p1/p1np2b1/4p1Pp/2B1np2/2P2N1P/PP1B1P2/2KR2R1 b - - 3 18
        2kr1b1r/1p4p1/p1np2b1/4p1Pp/2B2p2/2P2N1P/PP1B1n2/2KR2R1 w - - 0 19
        2kr1b1r/1p4p1/p1np2b1/4p1Pp/2B2p2/2P2N1P/PP1B1n2/2K2RR1 b - - 1 19
        2kr1b1r/1p4p1/p1np2b1/4p1Pp/2B2p2/2P2N1n/PP1B4/2K2RR1 w - - 0 20
        2kr1b1r/1p4p1/p1np2b1/4p1Pp/2B2p2/2P2N1n/PP1B4/2K2R1R b - - 1 20

        '''
        self._next_en_passant = False

        if not isinstance(move, EmptyMove):
            start, finish = move.start, move.finish
            figure = self._board[start]
            destination = self._board[finish]

            if not isinstance(destination, EmptyCell) or isinstance(figure, Pawn):
                self._number_of_reversible_moves = 0
            else:
                self._number_of_reversible_moves += 1

            if move.is_promotion():
                self._move_promotion(start, finish, move.promotion)

            elif move.is_short_castling(figure):
                self._move_short_castling(start, finish)

            elif move.is_long_castling(figure):
                self._move_long_castling(start, finish)

            elif move.is_double_jump(figure):
                self._move_double_jump(start, finish)

            elif move.is_en_passant(figure, self._en_passant):
                self._move_en_passant(start, finish)

            else:
                self._move_simple(start, finish)

        self._en_passant = self._next_en_passant
        if self._turn == 'b':
            self._move_number += 1
        self._switch_turn()

    def _switch_turn(self):
        if self._turn == 'w':
            self._turn = 'b'
        else:
            self._turn = 'w'

    @property
    def board(self):
        return self._board

    @property
    def turn(self):
        return self._turn

    @property
    def castling(self):
        return self._castling

    @property
    def en_passant(self):
        return self._en_passant

    @property
    def number_of_reversible_moves(self):
        return self._number_of_reversible_moves

    @property
    def move_number(self):
        return self._move_number

    def __str__(self):
        return  ' '.join(self.as_fen)

    def __repr__(self):
        return f'{type(self).__name__}.from_fen({self.as_fen})'


class Figure:
    '''

    >>> white_figure = Figure('w')

    >>> white_figure
    Figure(color='w')
    >>> str(white_figure)
    'White Figure'
    >>> white_figure.fen_symbol
    'F'

    >>> black_figure = Figure('b')

    >>> black_figure
    Figure(color='b')
    >>> str(black_figure)
    'Black Figure'
    >>> black_figure.fen_symbol
    'f'

    '''
    symbol = 'f'
    worth = Decimal('1')

    def __init__(self, color):
        self._color = color

    @property
    def color(self):
        return self._color

    @property
    def fen_symbol(self):
        if self.color == 'w':
            return self.symbol.upper()
        else:
            return self.symbol.lower()

    def __str__(self):
        full_color = 'White' if self._color == 'w' else 'Black'
        return f'{full_color} {type(self).__name__}'

    def __repr__(self):
        return f'{type(self).__name__}(color={self._color!r})'


class King(Figure):
    symbol = 'k'
    worth = Decimal('300')

    def _simple_moves(self, coordinate, position):
        '''

        >>> position = Position.from_fen((
        ...     'rnb1k1nr/pp2q2p/2p1p1p1/3pPp2/3P4/2NQ1N2/PPP2PPP/R3KB1R',
        ...     'b', 'KQkq', '-',
        ...     '1', '8'
        ... ))
        >>> coordinate = Coordinate('e8')
        >>> king = position.board[coordinate]

        >>> [str(move) for move in king.available_moves(coordinate, position)]
        ['e8d7', 'e8d8', 'e8f7', 'e8f8']

        >>> position = Position.from_fen((
        ...     'rnb1k1nr/pp5p/4pqp1/2ppPp2/3P4/2NQ1N2/PPP1KPPP/R4B1R',
        ...     'w', 'kq', '-',
        ...     '0', '10'
        ... ))
        >>> coordinate = Coordinate('e2')
        >>> king = position.board[coordinate]

        >>> [str(move) for move in king.available_moves(coordinate, position)]
        ['e2d1', 'e2d2', 'e2e1', 'e2e3']

        >>> position = Position.from_fen((
        ...     'rn2k2r/pp1b4/4pnpp/2p1P1N1/2pP1p1K/2N5/PPP2PPP/R4B1R',
        ...     'w', 'kq', '-',
        ...     '0', '16'
        ... ))
        >>> coordinate = Coordinate('h4')
        >>> king = position.board[coordinate]

        >>> [str(move) for move in king.available_moves(coordinate, position)]
        ['h4g3', 'h4g4', 'h4h3', 'h4h5']

        '''
        moves = []

        for delta_x in range(-1, 2):
            for delta_y in range(-1, 2):
                if(
                    not(delta_x == 0 and delta_y == 0) and
                    (0 <= coordinate.x + delta_x < 8) and
                    (0 <= coordinate.y + delta_y < 8)
                ):
                    current = coordinate.delta(delta_x, delta_y)
                    destination = position.board[current]

                    if(
                        isinstance(destination, EmptyCell) or
                        destination.color != self._color
                    ):
                        moves.append(Move(coordinate, current))

        return moves

    def _castling_moves(self, coordinate, position):
        '''

        >>> position = Position.starting_position()
        >>> coordinate = Coordinate('e1')
        >>> king = position.board[coordinate]

        >>> king.available_moves(coordinate, position)
        []

        >>> position = Position.from_fen((
        ...     'r3kb1r/8/2nqbn2/pppppppp/PPPPPPPP/2NQBN2/8/R3KB1R',
        ...     'w', 'KQkq', '-',
        ...     '8', '13'
        ... ))
        >>> coordinate = Coordinate('e1')
        >>> king = position.board[coordinate]

        >>> [str(move) for move in king.available_moves(coordinate, position)]
        ['e1d1', 'e1d2', 'e1e2', 'e1f2', 'e1c1']

        >>> position = Position.from_fen((
        ...     '1r2k2r/8/2nqbn1b/pppppppp/PPPPPPPP/2N1BN1B/3Q4/1R2K2R',
        ...     'b', 'Kk', '-',
        ...     '3', '15'
        ... ))
        >>> coordinate = Coordinate('e8')
        >>> king = position.board[coordinate]

        >>> [str(move) for move in king.available_moves(coordinate, position)]
        ['e8d7', 'e8d8', 'e8e7', 'e8f7', 'e8f8', 'e8g8']

        '''
        moves = []

        if position.castling[self._color]['k']:
            for delta_x in range(1, 3):
                current = coordinate.delta(delta_x)
                cell = position.board[current]

                if not isinstance(cell, EmptyCell):
                    break
            else:
                moves.append(Move(coordinate, coordinate.delta(2, 0)))

        if position.castling[self._color]['q']:
            for delta_x in range(-3, 0):
                current = coordinate.delta(delta_x)
                cell = position.board[current]

                if not isinstance(cell, EmptyCell):
                    break
            else:
                moves.append(Move(coordinate, coordinate.delta(-2, 0)))

        return moves

    def available_moves(self, coordinate, position):
        '''

        >>> position = Position.from_fen((
        ...     'rnb1k1nr/pp5p/2p1pqp1/3pPp2/3P4/2NQ1N2/PPP2PPP/R3KB1R',
        ...     'w', 'KQkq', '-',
        ...     '2', '9'
        ... ))
        >>> coordinate = Coordinate('e1')
        >>> king = position.board[coordinate]

        >>> [str(move) for move in king.available_moves(coordinate, position)]
        ['e1d1', 'e1d2', 'e1e2', 'e1c1']

        >>> position = Position.from_fen((
        ...     'r3k2r/pp1b4/n3pnpp/2p1P1N1/2pP1p2/1PN4K/P1P2PPP/R4B1R',
        ...     'b', 'kq', '-',
        ...     '0', '17'
        ... ))
        >>> coordinate = Coordinate('e8')
        >>> king = position.board[coordinate]

        >>> [str(move) for move in king.available_moves(coordinate, position)]
        ['e8d8', 'e8e7', 'e8f7', 'e8f8', 'e8g8', 'e8c8']

        '''
        moves = []

        moves += self._simple_moves(coordinate, position)
        moves += self._castling_moves(coordinate, position)

        return moves


def _delta_moves(self, coordinate, position, deltas):
    moves = []

    for delta in deltas:
        current = coordinate

        while True:
            previous = current
            current = current.delta(*delta)
            if(
                (current.x - previous.x != delta[0]) or
                (current.y - previous.y != delta[1])
            ):
                break

            destination = position.board[current]

            if isinstance(destination, EmptyCell):
                moves.append(Move(coordinate, current))

            if isinstance(destination, Figure):
                if destination.color != self._color:
                    moves.append(Move(coordinate, current))

                break

    return moves


class Rook(Figure):
    symbol = 'r'
    worth = Decimal('5')

    def _parallel_moves(self, coordinate, position):
        '''

        >>> position = Position.starting_position()
        >>> coordinate = Coordinate('a1')
        >>> rook = position.board[coordinate]

        >>> rook.available_moves(coordinate, position)
        []

        >>> position = Position.from_fen((
        ...     'rnbqkbnr/p1p3pp/3p4/4pp2/p3P3/2NPB3/1PP2PPP/R2QKBNR',
        ...     'w', 'KQkq', '-',
        ...     '0', '6'
        ... ))
        >>> coordinate = Coordinate('a1')
        >>> rook = position.board[coordinate]

        >>> [str(move) for move in rook.available_moves(coordinate, position)]
        ['a1b1', 'a1c1', 'a1a2', 'a1a3', 'a1a4']

        >>> position = Position.from_fen((
        ...     'rnbqkbnr/p1p3p1/7p/3p1R2/p3P3/2NP1N2/1PP1p2P/R2QKB2',
        ...     'b', 'Qkq', '-',
        ...     '1', '12'
        ... ))
        >>> coordinate = Coordinate('f5')
        >>> rook = position.board[coordinate]

        >>> [str(move) for move in rook.available_moves(coordinate, position)]
        ['f5e5', 'f5d5', 'f5g5', 'f5h5', 'f5f4', 'f5f6', 'f5f7', 'f5f8']

        >>> position = Position.from_fen((
        ...     'rnb1k3/p1p1r1p1/3b1n1p/6N1/p2P4/8/1PPQN2P/R3KB2',
        ...     'b', 'Qq', '-',
        ...     '2', '19'
        ... ))
        >>> coordinate = Coordinate('e7')
        >>> rook = position.board[coordinate]

        >>> [str(move) for move in rook.available_moves(coordinate, position)]
        ['e7d7', 'e7f7', 'e7e6', 'e7e5', 'e7e4', 'e7e3', 'e7e2']

        >>> position = Position.from_fen((
        ...     'rnb1k3/p1p3p1/3b1n1p/6N1/p1QP4/7r/1PP1N2P/R3KB2',
        ...     'b', 'Qq', '-',
        ...     '6', '21'
        ... ))
        >>> coordinate = Coordinate('h3')
        >>> rook = position.board[coordinate]

        >>> [str(move) for move in rook.available_moves(coordinate, position)]
        ['h3g3', 'h3f3', 'h3e3', 'h3d3', 'h3c3', 'h3b3', 'h3a3', 'h3h2', 'h3h4', 'h3h5']

        '''
        return _delta_moves(
            self, coordinate, position,
            [(-1, 0), (1, 0), (0, -1), (0, 1)]
        )

    def available_moves(self, coordinate, position):
        return self._parallel_moves(coordinate, position)


class Bishop(Figure):
    symbol = 'b'
    worth = Decimal('3')

    def _diagonal_moves(self, coordinate, position):
        '''

        >>> position = Position.starting_position()
        >>> coordinate = Coordinate('f1')
        >>> bishop = position.board[coordinate]

        >>> bishop.available_moves(coordinate, position)
        []

        >>> position = Position.from_fen((
        ...     'rnbqkbnr/ppp4p/6pB/3p1p2/3QP3/8/PPP2PPP/RN2KBNR',
        ...     'w', 'KQkq', '-',
        ...     '0', '6'
        ... ))
        >>> coordinate = Coordinate('h6')
        >>> bishop = position.board[coordinate]

        >>> [str(move) for move in bishop.available_moves(coordinate, position)]
        ['h6g5', 'h6f4', 'h6e3', 'h6d2', 'h6c1', 'h6g7', 'h6f8']

        >>> position = Position.from_fen((
        ...     'rnb1kbnr/ppp1q1Bp/6p1/3Q1p2/4P3/8/PPP2PPP/RN2KBNR',
        ...     'b', 'KQkq', '-',
        ...     '2', '7'
        ... ))
        >>> coordinate = Coordinate('f8')
        >>> bishop = position.board[coordinate]

        >>> [str(move) for move in bishop.available_moves(coordinate, position)]
        ['f8g7']

        >>> position = Position.from_fen((
        ...     'rn2kb1r/ppp1q1Bp/4bnp1/2Q2P2/8/8/PPP2PPP/RN2KBNR',
        ...     'b', 'KQkq', '-',
        ...     '0', '9'
        ... ))
        >>> coordinate = Coordinate('e6')
        >>> bishop = position.board[coordinate]

        >>> [str(move) for move in bishop.available_moves(coordinate, position)]
        ['e6d5', 'e6c4', 'e6b3', 'e6a2', 'e6d7', 'e6c8', 'e6f5', 'e6f7', 'e6g8']

        '''
        return _delta_moves(
            self, coordinate, position,
            [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        )

    def available_moves(self, coordinate, position):
        return self._diagonal_moves(coordinate, position)


class Queen(Rook, Bishop):
    symbol = 'q'
    worth = Decimal('9')

    def available_moves(self, coordinate, position):
        '''

        >>> position = Position.starting_position()
        >>> coordinate = Coordinate('d1')
        >>> queen = position.board[coordinate]

        >>> queen.available_moves(coordinate, position)
        []

        >>> position = Position.from_fen((
        ...     'rnb1kbnr/ppp1q1pp/3p4/4Qp2/3pP3/8/PPP2PPP/RNB1KBNR',
        ...     'w', 'KQkq', '-',
        ...     '2', '6'
        ... ))
        >>> coordinate = Coordinate('e5')
        >>> queen = position.board[coordinate]

        >>> [str(move) for move in queen.available_moves(coordinate, position)]
        ... # doctest: +NORMALIZE_WHITESPACE
        ['e5d5', 'e5c5', 'e5b5', 'e5a5', 'e5f5', 'e5e6', 'e5e7',
         'e5d4', 'e5d6', 'e5f4', 'e5g3', 'e5f6', 'e5g7']

        >>> position = Position.from_fen((
        ...     'rnb1kbnr/ppp3pp/3pq3/5p2/3pPQ2/7N/PPP2PPP/RNB1KB1R',
        ...     'b', 'KQkq', '-',
        ...     '5', '7'
        ... ))
        >>> coordinate = Coordinate('e6')
        >>> queen = position.board[coordinate]

        >>> [str(move) for move in queen.available_moves(coordinate, position)]
        ... # doctest: +NORMALIZE_WHITESPACE
        ['e6f6', 'e6g6', 'e6h6', 'e6e5', 'e6e4', 'e6e7',
         'e6d5', 'e6c4', 'e6b3', 'e6a2', 'e6d7', 'e6f7']

        '''
        moves = []

        moves += self._parallel_moves(coordinate, position)
        moves += self._diagonal_moves(coordinate, position)

        return moves


class Knight(Figure):
    symbol = 'n'
    worth = Decimal('3')

    def available_moves(self, coordinate, position):
        '''

        >>> position = Position.starting_position()
        >>> coordinate = Coordinate('b8')
        >>> knight = position.board[coordinate]

        >>> [str(move) for move in knight.available_moves(coordinate, position)]
        ['b8a6', 'b8c6']

        >>> position = Position.from_fen((
        ...     '1r2k2r/3n4/2nqb2b/pppppppp/PPPPPPPP/2N1BN1B/3Q4/1R2K2R',
        ...     'w', 'Kk', '-',
        ...     '4', '16'
        ... ))
        >>> coordinate = Coordinate('f3')
        >>> knight = position.board[coordinate]

        >>> [str(move) for move in knight.available_moves(coordinate, position)]
        ['f3e5', 'f3g1', 'f3g5', 'f3h2']

        >>> position = Position.from_fen((
        ...     'rnb1kb1r/pp1q4/3p1p1n/2p1p1pp/4PP1P/4Q1P1/PPPP2N1/RNB1KB1R',
        ...     'w', 'KQkq', '-',
        ...     '2', '10'
        ... ))
        >>> coordinate = Coordinate('g2')
        >>> knight = position.board[coordinate]

        >>> [str(move) for move in knight.available_moves(coordinate, position)]
        []

        >>> position = Position.from_fen((
        ...     'r1b1kb1r/pp1q4/2np1p1n/2p1p1pp/3PPP1P/4Q1P1/PPP3N1/RNB1KB1R',
        ...     'b', 'KQkq', '-',
        ...     '0', '11'
        ... ))
        >>> coordinate = Coordinate('c6')
        >>> knight = position.board[coordinate]

        >>> [str(move) for move in knight.available_moves(coordinate, position)]
        ['c6a5', 'c6b4', 'c6b8', 'c6d4', 'c6d8', 'c6e7']

        '''
        moves = []

        for delta_x in [-2, -1, 1, 2]:
            for delta_y in [-2, -1, 1, 2]:
                if(
                    abs(delta_x) != abs(delta_y) and
                    (0 <= coordinate.x + delta_x < 8) and
                    (0 <= coordinate.y + delta_y < 8)
                ):
                    current = coordinate.delta(delta_x, delta_y)
                    destination = position.board[current]

                    if(
                        isinstance(destination, EmptyCell) or
                        destination.color != self._color
                    ):
                        moves.append(Move(coordinate, current))

        return moves


class Pawn(Figure):
    symbol = 'p'
    worth = Decimal('1')

    promotion_figures = [Queen, Rook, Bishop, Knight]

    def _simple_moves(self, coordinate, position):
        '''

        >>> position = Position.starting_position()
        >>> coordinate = Coordinate('e2')
        >>> pawn = position.board[coordinate]

        >>> [str(move) for move in pawn.available_moves(coordinate, position)]
        ['e2e4', 'e2e3']

        >>> position = Position.from_fen((
        ...     'rnbqkbnr/pppppp1p/8/6p1/6P1/8/PPPPPP1P/RNBQKBNR',
        ...     'w', 'KQkq', '-',
        ...     '0', '2'
        ... ))
        >>> coordinate = Coordinate('g4')
        >>> pawn = position.board[coordinate]

        >>> [str(move) for move in pawn.available_moves(coordinate, position)]
        []

        >>> position = Position.from_fen((
        ...     'rnbqkb1r/pppppppp/5n2/8/6P1/8/PPPPPP1P/RNBQKBNR',
        ...     'w', 'KQkq', '-',
        ...     '1', '2'
        ... ))
        >>> coordinate = Coordinate('g4')
        >>> pawn = position.board[coordinate]

        >>> [str(move) for move in pawn.available_moves(coordinate, position)]
        ['g4g5']

        >>> position = Position.from_fen((
        ...     'rnbqkbnr/pppppppp/8/8/6P1/8/PPPPPP1P/RNBQKBNR',
        ...     'b', 'KQkq', '-',
        ...     '0', '1'
        ... ))
        >>> coordinate = Coordinate('a7')
        >>> pawn = position.board[coordinate]

        >>> [str(move) for move in pawn.available_moves(coordinate, position)]
        ['a7a5', 'a7a6']

        >>> position = Position.from_fen((
        ...     'rnb1kb1r/pppq1pPp/3p4/8/5pP1/8/PPPP3P/RNBQKBNR',
        ...     'b', 'KQkq', '-',
        ...     '0', '6'
        ... ))
        >>> coordinate = Coordinate('g7')
        >>> pawn = position.board[coordinate]

        >>> [str(move) for move in pawn.available_moves(coordinate, position)]
        ... # doctest: +NORMALIZE_WHITESPACE
        ['g7g8q', 'g7g8r', 'g7g8b', 'g7g8n', 'g7f8q', 'g7f8r',
         'g7f8b', 'g7f8n', 'g7h8q', 'g7h8r', 'g7h8b', 'g7h8n']

        '''
        moves = []

        factor_y = 1 if self._color == 'w' else -1
        promotion_y = 6 if self._color == 'w' else 1

        if(
            (self._color == 'w' and coordinate.y == 1) or
            (self._color == 'b' and coordinate.y == 6)
        ):
            if(
                isinstance(position.board[coordinate.delta(y=1 * factor_y)], EmptyCell) and
                isinstance(position.board[coordinate.delta(y=2 * factor_y)], EmptyCell)
            ):
                moves.append(Move(coordinate, coordinate.delta(y=2 * factor_y)))

        if isinstance(position.board[coordinate.delta(y=1 * factor_y)], EmptyCell):
            if coordinate.y == promotion_y:
                for figure in self.promotion_figures:
                    moves.append(Move(coordinate, coordinate.delta(y=1 * factor_y), figure))
            else:
                moves.append(Move(coordinate, coordinate.delta(y=1 * factor_y)))

        return moves

    def _take_moves(self, coordinate, position):
        '''

        >>> position = Position.from_fen((
        ...     'r1bqkbnr/p1p3p1/2n2p2/1P1P3p/4p1PP/2NP1N2/p1P2P2/1RBQKB1R',
        ...     'b', 'Kkq', '-',
        ...     '0', '11'
        ... ))

        >>> coordinate = Coordinate('a2')
        >>> pawn = position.board[coordinate]
        >>> [str(move) for move in pawn.available_moves(coordinate, position)]
        ['a2a1q', 'a2a1r', 'a2a1b', 'a2a1n', 'a2b1q', 'a2b1r', 'a2b1b', 'a2b1n']

        >>> coordinate = Coordinate('e4')
        >>> pawn = position.board[coordinate]
        >>> [str(move) for move in pawn.available_moves(coordinate, position)]
        ['e4e3', 'e4d3', 'e4f3']

        >>> coordinate = Coordinate('h5')
        >>> pawn = position.board[coordinate]
        >>> [str(move) for move in pawn.available_moves(coordinate, position)]
        ['h5g4']

        >>> position = Position.from_fen((
        ...     'r1b1kbnr/p1p1q1p1/2n2p2/1P1P3p/4p1PP/2NP1N2/p1P2P2/1RBQKB1R',
        ...     'w', 'Kkq', '-',
        ...     '1', '12'
        ... ))

        >>> coordinate = Coordinate('b5')
        >>> pawn = position.board[coordinate]
        >>> [str(move) for move in pawn.available_moves(coordinate, position)]
        ['b5b6', 'b5c6']

        >>> coordinate = Coordinate('d5')
        >>> pawn = position.board[coordinate]
        >>> [str(move) for move in pawn.available_moves(coordinate, position)]
        ['d5d6', 'd5c6']

        >>> position = Position.from_fen((
        ...     '1nb3r1/r2p2p1/5pn1/p1pP1k1p/p1PBPp1P/b2N3P/NP6/R2Q1KRB',
        ...     'b', '-', 'e3',
        ...     '0', '26'
        ... ))

        >>> coordinate = Coordinate('f4')
        >>> pawn = position.board[coordinate]
        >>> [str(move) for move in pawn.available_moves(coordinate, position)]
        ['f4f3', 'f4e3']

        >>> position = Position.from_fen((
        ...     'rb4N1/p3n3/b4Qp1/P1kp2p1/P1pPP3/2P2K1R/5P2/2B3N1',
        ...     'b', '-', 'd3',
        ...     '0', '39'
        ... ))

        >>> coordinate = Coordinate('c4')
        >>> pawn = position.board[coordinate]
        >>> [str(move) for move in pawn.available_moves(coordinate, position)]
        ['c4d3']

        '''
        moves = []

        factor_y = 1 if self._color == 'w' else -1
        promotion_y = 6 if self._color == 'w' else 1

        for delta_x in [-1, 1]:
            if 0 <= coordinate.x + delta_x < 8:
                current = coordinate.delta(delta_x, 1 * factor_y)
                destination = position.board[current]

                if(
                    (
                        position.en_passant and
                        position.en_passant == current
                    ) or
                    (
                        isinstance(destination, Figure) and
                        destination.color != self._color
                    )
                ):
                    if coordinate.y == promotion_y:
                        for figure in self.promotion_figures:
                            moves.append(Move(coordinate, current, figure))
                    else:
                        moves.append(Move(coordinate, current))

        return moves

    def available_moves(self, coordinate, position):
        moves = []

        moves += self._simple_moves(coordinate, position)
        moves += self._take_moves(coordinate, position)

        return moves


FIGURES = {
    King.symbol: King,
    Queen.symbol: Queen,

    Rook.symbol: Rook,
    Bishop.symbol: Bishop,
    Knight.symbol: Knight,

    Pawn.symbol: Pawn
}


if __name__ == '__main__':
    doctest.testmod()
