"""
Program entry point.
"""
import argparse

from client import client
from server import teacher

import demos


_DATABASE_PATH = r"D:\Data\AudioDetective"
_DEFAULT_RECORD_TIME = 5


def main():
    """
    Main Function.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', help='record time (default: {})'.format(_DEFAULT_RECORD_TIME),
                        dest='record_time', type=int, metavar='TIME', default=_DEFAULT_RECORD_TIME)
    parser.add_argument('-v', help='increase output verbosity', dest='verbose', action='store_true')
    parser.add_argument('-x', help='visualize the algorithm', dest='visualize', action='store_true')
    parser.add_argument('-e', help='echo the recorded sound', dest='echo', action='store_true')
    parser.add_argument('-l', help='learn the sounds in a directory', dest='path', metavar='PATH')
    parser.add_argument('-d', help='run a demo of the core digital signal processing part of the application',
                        dest='demo', action='store_true')
    args = parser.parse_args()

    if args.demo:
        demos.demo_all()
    elif args.path:
        teacher.teach(args.path, _DATABASE_PATH, visualize=args.visualize)
    else:
        client.audio_detective(args.record_time, _DATABASE_PATH,
                               verbose=args.verbose, visualize=args.visualize, echo=args.echo)


if __name__ == "__main__":
    main()
