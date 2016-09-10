# -*- coding: utf-8 -*-
import sys
from color_output import Color


def profile_error(error, action=None, opt=False):
    print (('>> %sProfile Error: %s' % (Color.LT_RED, Color.RESET)))
    print_error(error)
    print (('\n>> %sQuitting Google_DJ...%s\n' % (Color.LT_RED, Color.RESET)))
    sys.exit()


def print_error(error):
    std_errors = error.args
    metadata = error.__dict__
    print metadata
    if len(metadata) > 0:
        error_status = metadata['status']
        error_body = metadata['body']['error']
        print (('>> %sGoogle_DJ module:%s\n\treason--[%s%s%s]\n\tstatus--[%s%s%s]\n' % (
            Color.LT_RED, Color.RESET,
            Color.LT_RED, error_body, Color.RESET,
            Color.LT_RED, error_status, Color.RESET)))
    elif len(std_errors) > 0:
        print (('>> Standard module:    %s%s%s\n' % (
            Color.LT_RED, str(std_errors), Color.RESET)))
        print std_errors
        #print (('>> Raw string:    %s%s%s\n' % (
            #Color.LT_RED, str(error), Color.RESET)))

    else:
        print (('>> Unknown module:    %s%s%s\n' % (
            Color.LT_RED, str(error), Color.RESET)))