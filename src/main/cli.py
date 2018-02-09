# -*- coding: UTF-8 -*-
# cli.py
# Noah Rubin
# 01/31/2018

import os
from argparse import ArgumentParser

def initialize_parser():
    ## Main parser
    main_parser = ArgumentParser(prog='apf.py', description='Windows prefetch file parser')
    main_parser.add_argument('-V', '--version', action='version', version='%(prog)s v0.0.1')
    main_directives = main_parser.add_subparsers()

    ## Parse directives
    parse_directive = main_directives.add_parser('parse', help='prefetch file parser directives')
    parse_subdirectives = parse_directive.add_subparsers()

    # CSV parse directive
    csv_parse_directive = parse_subdirectives.add_parser('csv', help='Parse prefetch file to csv')
    
    # Bodyfile parse directive
    body_parse_directive = parse_subdirectives.add_parser('body', help='Parse prefetch MAC times to bodyfile')

    # JSON parse directive
    json_parse_directive = parse_subdirectives.add_parser('json', help='Parse prefetch file to json')

    # Database parse directive
    db_parse_directive = parse_subdirectives.add_parser('db', help='Parse prefetch file to database')

    ## Convert directives
    convert_directives = main_directives.add_parser('convert', help='Parsed prefetch file output conversion directives')
    convert_subdirectives = convert_directives.add_subparsers()

    # CSV conversion directive
    csv_convert_directive = convert_subdirectives.add_parser('csv', help='Convert from CSV output')

    # Body conversion directive
    body_convert_directive = convert_subdirectives.add_parser('body', help='Convert from bodyfile output')
    
    # JSON conversion directive
    json_convert_directive = convert_subdirectives.add_parser('json', help='Convert from JSON output')

    # DB conversion directive
    db_convert_directive = convert_subdirectives.add_parser('db', help='Convert from database output')

    return main_parser
