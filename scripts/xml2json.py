#!/usr/bin/env python
"""convert XML to JSON via stdin"""
import sys
from xmltodict import parse
import json

def main():
    try:
        inf = open(sys.argv[1], 'r') 
    except IndexError:
        inf = sys.stdin
    data = parse(inf.read())
    print(json.dumps(data, indent=2))


if __name__ == '__main__':
    main()
