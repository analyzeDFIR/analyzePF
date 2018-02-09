# -*- coding: UTF-8 -*-
# app.py
# Noah Rubin
# 01/31/2018

from src.utils.config import initialize_paths
initialize_paths()
from src.main.cli import initialize_parser

def apf_main():
    parser = initialize_parser()
    args = parser.parse_args()
    #args.func(args)
    return 0
