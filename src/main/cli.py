## -*- coding: UTF-8 -*-
## cli.py
##
## Copyright (c) 2018 Noah Rubin
## 
## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:
## 
## The above copyright notice and this permission notice shall be included in all
## copies or substantial portions of the Software.
## 
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
## SOFTWARE.

import sys
from os import path
from argparse import ArgumentParser, ArgumentTypeError

import adfir.cli as cli
from adfir.directives import DirectiveRegistry
from src.database.models import BaseTable

def initialize_parser():
    '''
    Args:
        N/A
    Returns:
        ArgumentParser
        Command line argument parser
    Preconditions:
        N/A
    '''
    ## Main parser
    main_parser = ArgumentParser(prog='apf.py', description='Windows prefetch file parser')
    main_parser.add_argument('-V', '--version', action='version', version='%(prog)s v0.0.1')
    main_directives = main_parser.add_subparsers()

    ## Parse directives
    parse_directive = main_directives.add_parser('parse', help='prefetch file parser directives')
    parse_subdirectives = parse_directive.add_subparsers()

    # JSON parse directive
    json_parse_directive = parse_subdirectives.add_parser(
        'json', 
        parents=[
            cli.base_parent, 
            cli.base_parse_parent, 
            cli.base_output_parent
        ], 
        help='Parse prefetch file to JSON'
    )
    json_parse_directive.add_argument('-p', '--pretty', action='store_true', help='Whether to pretty-print the JSON output', dest='pretty')
    json_parse_directive.set_defaults(directive=DirectiveRegistry.retrieve('ParseJSONDirective'))

    # Database parse directive
    db_parse_directive = parse_subdirectives.add_parser(
        'db', 
        parents=[
            cli.base_parent, 
            cli.base_parse_parent, 
            cli.db_connect_parent
        ], 
        help='Parse prefetch file to database'
    )
    db_parse_directive.set_defaults(
        directive=DirectiveRegistry.retrieve('ParseDBDirective'),
        metadata=BaseTable.metadata
    )

    ## Query directive
    query_directive = main_directives.add_parser(
        'query', 
        parents=[
            base_parent, 
            db_connect_parent
        ], 
        help='Query database for parsed data'
    )
    query_directive.add_argument('-t', '--target', type=str, help='Path to output file', dest='target')
    query_directive.add_argument('-q', '--query', type=str, required=True, help='Query to submit to database', dest='query')
    query_directive.add_argument('-S', '--sep', default=',', help='Output file separator (default: ",")', dest='sep')
    query_directive.add_argument('-T', '--title', type=str, help='Title to use for output table', dest='title')
    query_directive.set_defaults(
        directive=DirectiveRegistry.retrieve('DBQueryDirective'),
        metadata=BaseTable.metadata
    )

    return main_parser
