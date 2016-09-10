# -*- coding: utf-8 -*-

### GNU GENERAL PUBLIC LICENSE
### Author: cody.rocker.83@gmail.com
### 2015
#-----------------------------------
#   Requires:                    """
#    - Python 2.7+               """
#    - dropbox                   """
#    - hurry.filesize            """
#-----------------------------------


# Define colors for coding terminal output
class Color:
    BLACK = '\033[30m'
    GREY = '\033[90m'
    LT_GREY = '\033[37m'
    PURPLE = '\033[35m'
    MAGENTA = '\033[95m'
    PINK = '\033[95m'
    CYAN = '\033[36m'
    LT_CYAN = '\033[96m'
    BLUE = '\033[34m'
    LT_BLUE = '\033[94m'
    GREEN = '\033[92m'
    LT_GREEN = '\033[92m'
    RED = '\033[91m'
    LT_RED = '\033[91m'
    YELLOW = '\033[93m'
    ORANGE = '\033[33m'

    class bg:
        BLACK = '\033[40m'
        RED = '\033[41m'
        GREEN = '\033[42m'
        ORANGE = '\033[43m'
        BLUE = '\033[44m'
        PURPLE = '\033[45m'
        CYAN = '\033[46m'
        LT_GREY = '\033[47m'

    # Formatting options
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    # Reset text format
    RESET = '\033[0m'