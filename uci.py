import doctest
import sys
from threading import Thread
from time import sleep, time

from engine import analyzer as engine

INFINITY = 1e18


class UCI:
    '''

    >>> uci = UCI()

    >>> uci.handle('uci')
    id name Engine
    id author author
    uciok
    >>> uci.handle('isready')
    readyok
    >>> uci.handle('position startpos moves e2e4')
    >>> uci.handle('go movetime 1000')
    >>> uci.handle('stop'); sleep(0.005) # doctest: +ELLIPSIS
    bestmove ...
    >>> uci.handle('isready')
    readyok

    '''
    def __init__(self, name='Engine', author='author'):
        self._name, self._author = name, author

        self._position = engine.Position.starting_position()
        self._analyzer = engine.Analyzer(self._position)

        self._debug = False

    def greet(self):
        print(f'{self._name} by {self._author}')

    def _identify(self):
        '''

        >>> uci = UCI()

        >>> uci.handle('uci')
        id name Engine
        id author author
        uciok

        '''
        print(f'id name {self._name}')
        print(f'id author {self._author}')

        print('uciok')

    def _handle_debug(self, arguments):
        '''

        >>> uci = UCI()

        >>> uci.debug
        False
        >>> uci.handle('debug on')
        >>> uci.debug
        True
        >>> uci.handle('debug off')
        >>> uci.debug
        False
        >>> uci.handle('debug off')
        >>> uci.debug
        False

        '''
        if len(arguments) >= 1:
            self._debug = (arguments[0] == 'on')

    def _handle_ready(self):
        '''

        >>> uci = UCI()

        >>> uci.handle('isready')
        readyok

        '''
        print('readyok')

    def _handle_position(self, arguments):
        '''

        >>> uci = UCI()

        >>> uci.handle('position startpos moves e2e4 c7c5 b1c3 d7d6 f1c4 e7e6 c4e6 f7e6 d1h5')
        >>> uci.position
        'rnbqkbnr/pp4pp/3pp3/2p4Q/4P3/2N5/PPPP1PPP/R1B1K1NR b KQkq - 1 5'

        >>> uci.handle(
        ...     'position fen rnbqkbnr/pp4pp/3pp3/2p4Q/4P3/2N5/PPPP1PPP/R1B1K1NR '
        ...     'b KQkq - 1 5 moves e8d7 c3d5 g7g6'
        ... )
        >>> uci.position
        'rnbq1bnr/pp1k3p/3pp1p1/2pN3Q/4P3/8/PPPP1PPP/R1B1K1NR w KQ - 0 7'

        >>> uci.handle('position moves e2e4')
        >>> uci.position
        'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1'

        '''
        try:
            moves_index = arguments.index('moves')

            starting_position = arguments[: moves_index]
            moves = arguments[moves_index + 1: ]

        except ValueError:
            starting_position = arguments
            moves = []

        if len(starting_position) <= 1:
            starting_position = engine.STARTING_POSITION_FEN
        else:
            starting_position = starting_position[1: ]

        self._position = engine.Position.from_fen(starting_position, moves)
        self._analyzer = engine.Analyzer(self._position)

    def _handle_go(self, arguments):
        '''

        >>> uci = UCI()

        >>> uci.handle('go')
        >>> uci.handle('stop'); sleep(0.005) # doctest: +ELLIPSIS
        bestmove ...

        >>> uci.handle('go movetime 0'); sleep(0.005) # doctest: +ELLIPSIS
        bestmove ...

        '''
        def monitoring(analyzer, start_time, duration=INFINITY):
            while(
                (not analyzer.ready) and
                (time() < start_time + duration)
            ):
                sleep(0.001)

            analyzer.stop()
            best_move = analyzer.best_move

            print(f'bestmove {best_move}')
            sys.stdout.flush()

        start_time = time()
        self._analyzer.go()

        if 'movetime' in arguments:
            move_time_index = arguments.index('movetime') + 1
            move_time = int(arguments[move_time_index]) / 1000.0
        else:
            move_time = INFINITY

        monitoring_thread = Thread(
            target=monitoring,
            args=(self._analyzer, start_time, move_time),
            daemon=True
        )
        monitoring_thread.start()

    def _handle_stop(self):
        self._analyzer.stop()

    def handle(self, command):
        command = command.split()

        if command[0] == 'uci':
            self._identify()

        elif command[0] == 'debug':
           self._handle_debug(command[1: ])

        elif command[0] == 'isready':
            self._handle_ready()

        elif command[0] == 'position':
            self._handle_position(command[1: ])

        elif command[0] == 'go':
            self._handle_go(command[1: ])

        elif command[0] == 'stop':
            self._handle_stop()

        elif command[0] == 'quit':
            raise SystemExit

    @property
    def name(self):
        return self._name

    @property
    def author(self):
        return self._author

    @property
    def debug(self):
        return self._debug

    @property
    def position(self):
        return ' '.join(self._position.as_fen)


def main():
    uci = UCI(engine.NAME, engine.AUTHOR)
    uci.greet()

    while True:
        try:
            command = input()
            uci.handle(command)

        except (SystemExit, EOFError, KeyboardInterrupt):
            break

        except BaseException:
            continue


if __name__ == '__main__':
    doctest.testmod()
    main()
