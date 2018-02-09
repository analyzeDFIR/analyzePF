# -*- coding: UTF-8 -*-
# config.py
# Noah Rubin
# 02/01/2018

import sys
from os import path
from datetime import datetime
import logging

from src.main.exceptions import PathInitializationError

LOGGING_DEFAULTS = dict(\
    prefix='amft_' + datetime.utcnow().strftime('%Y%m%d'),
    format='%(asctime)s\t%(levelname)s\t%(name)s\t%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO)

def initialize_paths():
    '''
    Args:
        N/A
    Procedure:
        Initialize sys.path to include the lib directory of dependencies.  Raises
        exception if unable to successfully append to sys.path, for example if sys.arv[0]
        is not a valid path.
    Preconditions:
        N/A
    '''
    try:
        runpath = path.abspath(path.dirname(sys.argv[0]))
        assert path.exists(runpath), 'Run path %s does not exist'%runpath
    except Exception as e:
        raise PathInitializationException(e)
    else:
        try:
            sys.path.append(path.join(runpath))          # add runpath so 'from src.<module> import <object>' doesn't fail
            sys.path.append(path.join(runpath, 'lib'))   # add lib so 'import {sqlalchemy, construct}' doesn't fail
        except Exception as e:
            raise PathInitializationException(e)

def initialize_logger(log_path, log_prefix=LOGGING_DEFAULTS.get('prefix'), format=LOGGING_DEFAULTS.get('format'), datefmt=LOGGING_DEFAULTS.get('datefmt'), level=LOGGING_DEFAULTS.get('level')):
    '''
    Args:
        log_path: String    => valid path to output log to
        log_prefix: String  => prefix of log file (default: pmft_<datetime>)
    Procedure:
        Initialize root logger with formatter, level, and handler set to 
        FileHandler at path (log_path + log_prefix.log)
    Preconditions:
        log_path is of type String
        log_prefix is of type String
    '''
    assert isinstance(log_path, str) and path.exists(log_path), 'Log_path is not a valid path'
    assert isinstance(log_prefix, str), 'Log_prefix is not of type String'
    full_log_path = path.join(path.abspath(log_path), log_prefix + '.log')
    logging.basicConfig(filename=full_log_path, format=format, datefmt=datefmt, level=level)
