# LeskoChessEngine
LeskoChessEngine is an open source chess engine, written in [Python](https://www.python.org).

### Supported [UCI](http://wbec-ridderkerk.nl/html/UCIProtocol.html) commands
* uci
* isready
* ucinewgame
* position
  * fen
  * startpos
  * moves
* go
  * movetime
  * infinite
* stop
* quit

### Example of use
<pre>
$ pypy3 uci.py

LeskoChessEngine 0.1 by Lesko Vladislav
<b>uci</b>
id name LeskoChessEngine 0.1
id author Lesko Vladislav
uciok
<b>ucinewgame</b>
<b>position startpos moves e2e4</b>
<b>go</b>
<b>stop</b>
bestmove e7e6
<b>isready</b>
readyok
<b>quit</b>
</pre>

For better performance use [PyPy3](http://pypy.org).
