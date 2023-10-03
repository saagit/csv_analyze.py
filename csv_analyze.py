#!/usr/bin/env python3
"""
Display interesting information about the fields in a CSV file.
"""

# Copyright 2023 Scott A. Anderson
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import collections
import contextlib
import csv
import os
import sys

VERSION='0.2'

def progname():
    return os.path.basename(__file__)

@contextlib.contextmanager
def open_ro_with_error(filename):
    """
    Adapted from PEP 343 Example 6
    """
    try:
        if filename == '-':
            file_handle = sys.stdin
        else:
            file_handle = open(filename, 'r')
    except IOError as err:
        yield None, err
    else:
        try:
            yield file_handle, None
        finally:
            if filename != '-':
                file_handle.close()

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, prog=progname(),
                                     add_help=False)
    parser.add_argument('-h', '--help',
                        help='display this help and exit',
                        action='help')
    parser.add_argument('-V', '--version',
                        help='output version information and exit',
                        action='version', version='%(prog)s v' + VERSION)
    parser.add_argument('-d', '--dialect', default=None,
                        help='Python csv module dialect to use')
    parser.add_argument('--list-dialects', action='store_true',
                        help='List Python csv module dialects')
    parser.add_argument('-c', '--column', dest='columns', metavar='COLUMN',
                        action='append',
                        help='Instead of analyzing, output specified column')
    parser.add_argument('files', metavar='FILE', nargs="*",
                        help='input files or stdin if none provided')
    args = parser.parse_args()

    return args

BORING_SET = set(['', '0', '0.0'])
def show_set(name, a_set):
    if a_set.issubset(BORING_SET):
        print('boring: {0}'.format(name))
        return

    if len(a_set) == 1:
        print('constant: {0}={1}'.format(name, list(a_set)[0]))
        return

    if len(a_set) <= 5:
        print('limited: {0}={1}'.format(name, sorted(a_set)))
    else:
        try:
            a_set.remove('')
        except KeyError:
            sempty = ''
        else:
            sempty = ' excluding empties'

        try:
            slist = [ int(v) for v in a_set ]
            stype = 'integer '
        except ValueError:
            try:
                slist = [ float(v) for v in a_set ]
                stype = 'float '
            except ValueError:
                slist = list(a_set)
                stype = ''
        smin = min(slist)
        smax = max(slist)
        print('{0} different {1}values for {2} '
              'ranging from {3} to {4}{5}'.format(len(a_set), stype, name,
                                                  smin, smax, sempty))
def main():
    args = parse_args()
    if not args.files:
        args.files = [ '-' ]

    if args.list_dialects:
        for dialect in csv.list_dialects():
            print(dialect)
        sys.exit(1)

    rtn = 0
    field_counter = collections.defaultdict(set)
    for filename in args.files:
        with open_ro_with_error(filename) as (csvfile, err):
            if err:
                print('%s: %s: %s' % (progname(), err.filename, err.strerror),
                      file=sys.stderr)
                rtn += 1
            else:
                dialect =  args.dialect
                if not dialect:
                    dialect = csv.Sniffer().sniff(csvfile.read(1024))
                    csvfile.seek(0)
                reader = csv.DictReader(csvfile, dialect=dialect)
                if args.columns:
                    print('\t'.join([key for key in args.columns]))
                for row in reader:
                    if args.columns:
                        print('\t'.join([row[key] for key in args.columns]))
                    else:
                        for key in row:
                            field_counter[key].add(row[key])

    for key in sorted(field_counter):
        show_set(key, field_counter[key])

    return rtn

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
