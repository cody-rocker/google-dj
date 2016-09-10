# -*- coding: utf-8 -*-
import os

### GNU GENERAL PUBLIC LICENSE
### Author: cody.rocker.83@gmail.com
### 2015
#-----------------------------------
#   Requires:                    """
#    - Python 2.7+               """
#    - dropbox                   """
#    - hurry.filesize            """
#-----------------------------------


config_path = os.path.join(os.path.dirname(__file__), 'config')


def get_config():
    ''' Create a config parser for reading INI files '''
    try:
        import ConfigParser
        return ConfigParser.ConfigParser()
    except:
        import configparser
        return configparser.ConfigParser()


def load_config(config_file):
    config = get_config()
    try:
        config.read(os.path.join(config_path, config_file))
        return config
    except:
        return config


def write_config(config_instance, config_file):
    try:  # try to write to directory, or
        with open(os.path.join(config_path, config_file), 'w') as configFile:
            config_instance.write(configFile)
    except:  # create the directory, if necessary
        os.mkdir(config_path)
        with open(os.path.join(config_path, config_file), 'w') as configFile:
            config_instance.write(configFile)
