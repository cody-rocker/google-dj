# -*- coding: utf-8 -*-

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from error_handler import profile_error
from helpers import load_config, write_config
from color_output import Color
from gmusicapi import Mobileclient

### GNU GENERAL PUBLIC LICENSE
### Author: cody.rocker.83@gmail.com
### 2015
#-----------------------------------
#   Requires:                    """
#    - Python 2.7+               """
#    - gmusicapi                 """
#    - requests                  """
#    - ubuntu-unrestricted-extras"""
#-----------------------------------

# https://github.com/simon-weber/gmusicapi
# docs: https://unofficial-google-music-api.readthedocs.org/en/latest/


class GPlayClient():

    logged_in = False

    def __init__(self):
        self. supressWarnings()
        self.set_user()
        self.start_client()

    # Suppress unsigned certificate warning
    def supressWarnings(self, opt=True):
        if opt:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        else:
            pass

    def set_user(self):
        # load session config data
        self.saved_accounts = load_config('user_tokens.ini')
        users = self.saved_accounts.sections()
        self.session = load_config('session.ini')

        if self.session.getboolean('DEFAULT', 'logged_in'):
            active_user = self.session.get('DEFAULT', 'active_user')
            print (('  >>%s logged in%s as: %s%s%s' % (
                Color.GREEN, Color.RESET, Color.LT_BLUE, active_user, Color.RESET)))
        else:
            invalid_input = True
            print (('\n%sSelect Account%s' % (Color.BOLD, Color.RESET)))

            for n, userName in enumerate(users):
                print (('%s.  %s' % (str(n + 1), userName)))
            print (('%s.  add new' % (str(len(users) + 1))))
            while invalid_input:
                userInput = raw_input(
                    '\n%sEnter selection number: %s' % (
                    Color.BOLD, Color.RESET)).strip()
                print ('\n')
                try:
                    if int(userInput) == (len(users) + 1):  # add new account
                        new_account()
                    else:  # login & retrieve account authentication token
                        index = int(userInput) - 1
                        self.session = login(users[index])
                        active_user = self.session.get('DEFAULT', 'active_user')
                        print (('\n  >>%s logged in%s as: %s%s%s' % (
                            Color.GREEN, Color.RESET,
                            Color.LT_BLUE, active_user, Color.RESET)))
                    invalid_input = False
                except Exception as error:
                    if str(error) == 'list index out of range':
                        print (('%sInvalid selection (must be a number in list)%s' % (
                            Color.LT_RED, Color.RESET)))
                    else:
                        profile_error(error)

    def start_client(self):
        active_user = self.session.get('DEFAULT', 'active_user')
        saved_accounts = load_config('user_tokens.ini')

        if active_user is not '':
            user_passwd = saved_accounts.get(active_user, 'password')
            self.gPlayer = Mobileclient()
            # login client instance
            self.logged_in = self.gPlayer.login(active_user, user_passwd,
                                                Mobileclient.FROM_MAC_ADDRESS)
            # logged_in is True if login was successful
            if self.logged_in:
                print (('  >> %sconnected%s to Google Play Music library.' % (
                    Color.GREEN, Color.RESET)))
            else:
                print (('  >> %sfailed to connect%s to Google Play Music library.' % (
                    Color.Red, Color.RESET)))
        else:
            self.set_user()
            active_user = self.session.get('DEFAULT', 'active_user')
            user_passwd = saved_accounts.get(active_user, 'password')
            self.gPlayer = Mobileclient()
            # login client instance
            self.logged_in = self.gPlayer.login(active_user, user_passwd,
                                                Mobileclient.FROM_MAC_ADDRESS)
            # logged_in is True if login was successful
            if self.logged_in:
                print (('  >> %sconnected%s to Google Play Music library.' % (
                    Color.GREEN, Color.RESET)))
            else:
                print (('  >> %sfailed to connect%s to Google Play Music library.' % (
                    Color.Red, Color.RESET)))

        self.library = self.gPlayer.get_all_songs()  # retrieve song library
        print (("  >> %s%s%s songs in library." % (
            Color.BOLD, len(self.library), Color.RESET)))

        #playlists = self.gPlayer.get_all_user_playlist_contents()  # retrieve playlists
        #print (("\t>> %s playists" % (len(playlists))))
        #for item in playlists:
            #print (("\t   - %s" % (item['name'])))

    # Fill list of track_ids with results of Client query (List of strings)-
    def searchLibrary(self, query, artist=False, title=False, genre=False):
        if artist:
            track_ids = ([track['id'] for track in self.library
            if track['artist'].lower() == query.lower()])
        elif title:
            track_ids = ([track['id'] for track in self.library
            if query.lower() in track['title'].lower()])
        elif genre:
            track_ids = ([track['id'] for track in self.library
            if track['genre'].lower() == query.lower()])
        else:
            track_ids = []
        return track_ids

    # Return a dict of metadata from a track_id(string) search query
    def getTrackInfo(self, track_id):
        for song in self.library:
            if song['id'] == track_id:
                return song


def new_account():
    try:
        userName = raw_input(
            'Enter Google account email: ')
        user_passwd = raw_input(
            'Enter Google account password: ')

        # write new account info to config_file
        saved_accounts = load_config('user_tokens.ini')
        saved_accounts.add_section(userName)
        saved_accounts.set(userName, 'password', user_passwd)
        write_config(saved_accounts, 'user_tokens.ini')
        print('\n\nAccount authorization saved.\n')
        login(userName)
    except Exception as error:
        profile_error(error)


def login(user_email):
    try:
        saved_accounts = load_config('user_tokens.ini')
        users = saved_accounts.sections()
        session = load_config('session.ini')

        if user_email in users:
            session.set('DEFAULT', 'active_user', user_email)
            session.set('DEFAULT', 'logged_in', 'True')
            write_config(session, 'session.ini')
        else:
            session.set('DEFAULT', 'active_user', '')
            session.set('DEFAULT', 'logged_in', 'False')
            write_config(session, 'session.ini')
            print (('\n%sGoogle DJ does not recognize that email.  Verify command or\n'
                    'execute py_drop without arguments to add new accounts.%s' % (
                        Color.YELLOW, Color.RESET)))
        return session
    except Exception as error:
        profile_error(error)


def logout():
    try:
        session = load_config('session.ini')
        current_user = session.get('DEFAULT', 'active_user')
        session.set('DEFAULT', 'active_user', '')
        session.set('DEFAULT', 'logged_in', 'False')
        write_config(session, 'session.ini')
        if current_user is not '':
            print (('\n  >> %s%s%s has been logged out.\n' % (
                Color.LT_BLUE, current_user, Color.RESET)))
        else:
            print (('\n  >> No active session found.\n'))
    except Exception as error:
        profile_error(error)