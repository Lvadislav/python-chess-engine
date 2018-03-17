import re
from collections import Counter
from pprint import pprint
from sys import argv


def main():
    if len(argv) >= 2:
        filenames = argv[1:]
    else:
        filenames = ['testX.pgn']

    pgn_data = ''
    for filename in filenames:
        with open(filename) as pgn_file:
            pgn_data += pgn_file.read()

    pgn_comments = re.findall(r'\{([^}]{6,})\}', pgn_data)

    for index, comment in enumerate(pgn_comments):
        if ', ' in comment:
            comment = comment.split(', ')[-1]
            pgn_comments[index] = comment

    pprint(Counter(pgn_comments))
    print(
        sum([
            len(comment) >= 6 for comment in pgn_comments
        ])
    )


if __name__ == '__main__':
    main()
