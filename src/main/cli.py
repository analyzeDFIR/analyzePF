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

from src.main.directives import DirectiveRegistry

def DBConnectConfig(arg):
    '''
    Args:
        arg: String => database connection string or filepath
    Returns:
        String
        Database connection string
    Preconditions:
        arg is of type String   (assumed True)
    '''
    ext = path.splitext(arg)
    if ext in set(['.db', '.sqlite']) or not path.exists(path.dirname(arg)):
        return arg
    try:
        with open(path.abspath(arg), 'r') as config:
            connect = config.read().strip()
        return connect
    except Exception as e:
        raise ArgumentTypeError(str(e))

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

    ## Base parent
    base_parent = ArgumentParser(add_help=False)
    base_parent.add_argument('--lpath', type=str, default=path.abspath(path.dirname(sys.argv[0])), help='Path to log file directory (i.e. /path/to/logs or C:\\Users\\<user>\\Documents\\)', dest='log_path')
    base_parent.add_argument('--lpref', type=str, default=None, help='Prefix for log file (default: apf_<date>)', dest='log_prefix')

    ## Base parse parent
    base_parse_parent = ArgumentParser(add_help=False)
    base_parse_parent.add_argument('-s', '--source', action='append', help='Path to input file(s)', dest='sources')
    base_parse_parent.add_argument('--threads', type=int, default=1, help='Number of threads to use', dest='threads')

    ## Base output parent
    base_output_parent = ArgumentParser(add_help=False)
    base_output_parent.add_argument('-t', '--target', type=str, required=True, help='Path to output file', dest='target')

    ## CSV output parent parser
    csv_output_parent = ArgumentParser(parents=[base_output_parent], add_help=False)
    csv_output_parent.add_argument('-S', '--sep', default=',', help='Output file separator (default: ",")', dest='sep')

    ## Bodyfile output parent parser
    body_output_parent = ArgumentParser(parents=[base_output_parent], add_help=False)
    body_output_parent.add_argument('-S', '--sep', default='|', choices=['|'], help='Output file separator (default: "|")', dest='sep')

    ## DB connect parent parser
    db_connect_parent = ArgumentParser(add_help=False)
    db_connect_parent.add_argument('-d', '--driver', type=str, default='sqlite', help='Database driver to use (default: sqlite)', dest='db_driver')
    db_connect_parent.add_argument('-n', '--db', type=str, required=True, help='Name of database to connect to (path to database if using sqlite)', dest='db_name')
    db_connect_parent.add_argument('-C', '--connect', type=DBConnectConfig, help='Database connection string, or filepath to file containing connection string', dest='db_conn_string')
    db_connect_parent.add_argument('-u', '--user', type=str, help='Name of database user (alternative to connection string)', dest='db_user')
    db_connect_parent.add_argument('-p', '--passwd', type=str, help='Database user password (alternative to connection string)', dest='db_passwd')
    db_connect_parent.add_argument('-H', '--host', type=str, default='localhost', help='Hostname or IP address of database (alternative to connection string)', dest='db_host')
    db_connect_parent.add_argument('-P', '--port', type=str, help='Port database is listening on (alternative to connection string)', dest='db_port')

    ## Parse directives
    parse_directive = main_directives.add_parser('parse', help='prefetch file parser directives')
    parse_subdirectives = parse_directive.add_subparsers()

    # CSV parse directive
    csv_parse_directive = parse_subdirectives.add_parser('csv', parents=[base_parent, base_parse_parent, csv_output_parent], help='Parse prefetch file to csv')
    csv_parse_directive.add_argument('info_type', \
        type=str, \
        default='summary', \
        choices=['summary'], \
        help='Type of information to output')
    csv_parse_directive.set_defaults(func=DirectiveRegistry.retrieve('ParseCSVDirective'))
    
    # Bodyfile parse directive
    body_parse_directive = parse_subdirectives.add_parser('body', parents=[base_parent, base_parse_parent, body_output_parent], help='Parse prefetch MAC times to bodyfile')
    body_parse_directive.set_defaults(func=DirectiveRegistry.retrieve('ParseBODYDirective'))

    # JSON parse directive
    json_parse_directive = parse_subdirectives.add_parser('json', parents=[base_parent, base_parse_parent, base_output_parent], help='Parse prefetch file to JSON')
    json_parse_directive.add_argument('-p', '--pretty', action='store_true', help='Whether to pretty-print the JSON output', dest='pretty')
    json_parse_directive.set_defaults(func=DirectiveRegistry.retrieve('ParseJSONDirective'))

    # Database parse directive
    db_parse_directive = parse_subdirectives.add_parser('db', parents=[base_parent, base_parse_parent, db_connect_parent], help='Parse prefetch file to database')
    db_parse_directive.set_defaults(func=DirectiveRegistry.retrieve('ParseDBDirective'))

    #TODO: implement conversion directives
    ### Convert directives
    #convert_directives = main_directives.add_parser('convert', help='Parsed prefetch file output conversion directives')
    #convert_subdirectives = convert_directives.add_subparsers()
    #
    ## JSON conversion directive
    #json_convert_directive = convert_subdirectives.add_parser('json', parents=[base_parent], help='Convert from JSON output')

    ## DB conversion directive
    #db_convert_directive = convert_subdirectives.add_parser('db', parents=[base_parent], help='Convert from database output')

    ## Query directive
    query_directive = main_directives.add_parser('query', parents=[base_parent, db_connect_parent], help='Submit queries to $MFT database')
    query_directive.add_argument('-t', '--target', type=str, help='Path to output file', dest='target')
    query_directive.add_argument('-q', '--query', type=str, required=True, help='Query to submit to database', dest='query')
    query_directive.add_argument('-S', '--sep', default=',', help='Output file separator (default: ",")', dest='sep')
    query_directive.add_argument('-T', '--title', type=str, help='Title to use for output table', dest='title')
    query_directive.set_defaults(func=DirectiveRegistry.retrieve('DBQueryDirective'))

    return main_parser
