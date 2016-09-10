#!/usr/bin/python
# -*- coding: utf-8 -*-

import gobject
import threading
import random
import struct
import json
from socket import *
from gPlayClient import GPlayClient
from gStreamer import GStreamer, convert_time
from color_output import Color
from helpers import load_config

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


class GPlayServer(threading.Thread):

    # Socket variables
    server_name = (Color.YELLOW + "GOOGLE_DJ SERVER " + Color.RESET)
    conn = None

    # Server threading variables
    is_running = False

    # Gstreamer variables
    audio_stream = None
    track_id = None
    track_info = None

    # Playlist variables
    playlist = []
    current_index = 0
    default_artRef = 'http://i.imgur.com/zEwXYX7.png'

    def __init__(self):
        # output to server console
        print (("%s..initializing Threads...%s" % (Color.YELLOW, Color.RESET)))
        self._stop = threading.Event()
        threading.Thread.__init__(self)
        # output to server console
        print (("\n>> %sStarting Google DJ...%s" % (Color.BOLD, Color.RESET)))
        self.gPlayClient = GPlayClient()  # login user to fetch library data
        try:
            self.is_running = True  # set server state
            self.listen()  # listen for TCP traffic from Client (while loop)
        except KeyboardInterrupt:
            self.is_running = False  # set server state
            self.stop()  # kill thread containing main server loop & exit

    def listen(self):
        settings = load_config('server_config.ini')
        self.HOST_NAME = gethostname()
        HOST = getNetworkIp()
        PORT = int(settings.get('DEFAULT', 'port'))
        s = socket(AF_INET, SOCK_STREAM)
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(4)  # how many connections can it receive at one time
        # output to server console
        print (("  >> server is listening at %s%s:%s%s" % (
            Color.GREEN, HOST, PORT, Color.RESET)))
        print (("     ..press %s^C%s to quit." % (
            Color.YELLOW, Color.RESET)))

        ################################################
        ###            Main server loop              ###
        ################################################
        while self.is_running:
            self.conn, addr = s.accept()  # accept the connection
            client_ip = (Color.LT_CYAN + str(addr[0]) + ":" + str(addr[1]) + Color.RESET)
            # Read data from Android Client
            try:
                # First two bytes of Java DataOutputStream provide size of string buffer
                data = self.conn.recv(2)
                data_length = struct.unpack('>H', data)[0]
                # get string
                data = self.conn.recv(data_length)
                cmd_string = data.strip()
            except:
                print (("%s >> unexpected package size: %s" % (
                    self.server_name, repr(data))))
                self.conn.close()

            ################################################
            ###         HANDLE CLIENT COMMANDS           ###
            ################################################
            # Debug server command input to Server console
            #if cmd_string != 'get_state':
                #print (("%s#DEBUG server cmd_string: %s%s" % (
                    #Color.YELLOW, repr(cmd_string), Color.RESET)))

            ### GET_CURRENT_STATE ###
            if cmd_string == 'get_state':
                #print client_ip + " >> client synchronizing with server."
                if self.audio_stream is None:  # No active audio_strea
                    server_reply = json.dumps(
                        self.makeReply(cmd_string, 'SERVER_IDLE'))
                    self.conn.sendall(server_reply)
                    self.conn.close()
                elif self.audio_stream.playing:  # audio_stream playing
                    server_reply = json.dumps(
                        self.makeReply(cmd_string, 'PLAY_STATE_PLAYING'))
                    # Reply to Android Client
                    self.conn.sendall(server_reply)
                    self.conn.close()
                else:  # audio_stream paused
                    server_reply = json.dumps(
                        self.makeReply(cmd_string, 'PLAY_STATE_PAUSED'))
                    # Reply to Android Client
                    self.conn.sendall(server_reply)
                    self.conn.close()

            ### TOGGLE_PLAY_STATE ###
            elif cmd_string == 'toggle_play':
                # output to server console
                print client_ip + " >> client toggled play state: ",
                if self.audio_stream.playing:  # audio_stream playing
                    # output to server console
                    print (("%sPAUSED%s" % (Color.BOLD, Color.RESET)))
                    server_reply = json.dumps(
                        self.makeReply(cmd_string, 'PLAY_STATE_PAUSED'))
                    # Reply to Android Client
                    self.conn.sendall(server_reply)
                else:  # audio_stream paused
                    # output to server console
                    print (("%sPLAY%s" % (Color.BOLD, Color.RESET)))
                    server_reply = json.dumps(
                        self.makeReply(cmd_string, 'PLAY_STATE_PLAYING'))
                    # Reply to Android Client
                    self.conn.sendall(server_reply)
                self.conn.close()
                self.audio_stream.toggle_play()

            ### PLAY_NEXT ###
            elif cmd_string == 'play_next':
                # output to server console
                print (("%s >> play next track in playlist." % (client_ip)))
                if (self.current_index + 1) <= len(self.playlist) - 1:
                    self.current_index += 1
                    self.setTrack(self.playlist[self.current_index])
                    server_reply = json.dumps(
                        self.makeReply(cmd_string, 'PLAY_STATE_PLAYING'))
                    # Reply to Android Client
                    self.conn.sendall(server_reply)
                    self.conn.close()
                    # start audio stream
                    self.playMedia(self.track_id)
                else:
                    # output to server console
                    print (("%s >> end of playlist, ignored." % (self.server_name)))
                    server_reply = json.dumps(
                        self.makeReply(cmd_string, 'END_OF_PLAYLIST'))
                    # Reply to Android Client
                    self.conn.sendall(server_reply)
                    self.conn.close()

            ### PLAY_PREV ###
            elif cmd_string == 'play_prev':
                # output to server console
                print (("%s >> play previous track in playlist." % (client_ip)))
                if (self.current_index - 1) >= 0:
                    self.current_index -= 1
                    self.setTrack(self.playlist[self.current_index])
                    server_reply = json.dumps(
                        self.makeReply(cmd_string, 'PLAY_STATE_PLAYING'))
                    # Reply to Android Client
                    self.conn.sendall(server_reply)
                    self.conn.close()
                    # start audio stream
                    self.playMedia(self.track_id)
                else:
                    # output to server console
                    print (("%s >> start of playlist, ignored." % (self.server_name)))
                    server_reply = json.dumps(
                        self.makeReply(cmd_string, 'START_OF_PLAYLIST'))
                    # Reply to Android Client
                    self.conn.sendall(server_reply)
                    self.conn.close()

            ### SHUFFLE_ARTIST ###
            elif cmd_string[:14] == 'shuffle_artist':  # shuffled playlist Artist query
                query = cmd_string.split("::")[1]
                # output to server console
                print (("%s >> shuffle artist: %s" % (client_ip, query)))
                # perform artist query against user library
                track_ids = self.gPlayClient.searchLibrary(query, artist=True)
                if self.makePlaylist(track_ids):  # if playlist was populated
                    shufflePlaylist(self.playlist)
                    self.startPlaylist()  # reset current_index, metadata and track_id
                    self.track_info = self.gPlayClient.getTrackInfo(self.track_id)
                    server_reply = json.dumps(
                        self.makeReply(cmd_string[:14], 'PLAY_STATE_PLAYING'))
                    # Reply to Android Client
                    self.conn.sendall(server_reply)
                    self.conn.close()
                    # start audio stream
                    self.playMedia(self.track_id)
                else:  # if playlist was empty
                    # Reply to Android Client
                    server_reply = json.dumps(
                        self.makeReply(cmd_string[:14], 'SEARCH_EMPTY'))
                    # output to server console
                    print (("%s >> artist '%s' not found." % (
                        self.server_name, query)))
                    self.conn.sendall(server_reply)
                    self.conn.close()

            ### SEEK TO POSITION ###
            elif cmd_string[:4] == 'seek':  # simple seek query
                query = cmd_string.split("::")[1]
                # output to server console
                print (("%s >> seek to position: %s" % (client_ip, convert_time(query))))
                converted = self.audio_stream.seekToPosition(int(query))
                server_reply = json.dumps(
                    self.makeReply(cmd_string[:4], converted))
                # Reply to Android Client
                self.conn.sendall(server_reply)
                self.conn.close()

            ### CATCHALL ###
            else:
                print (("%s >> command not recognized: %s" % (
                    self.server_name, cmd_string)))
                self.conn.close()

    ################################################
    ###              Worker Methods              ###
    ################################################

    # Format a reply to the client
    def makeReply(self, request, expected):
        responseHeaders = {
            'get_state': 'SERVER_STATE',
            'toggle_play': 'PLAY_STATE_TOGGLED',
            'play_next': ['PLAY_STATE_PLAYING', 'END_OF_PLAYLIST'],
            'play_prev': ['PLAY_STATE_PLAYING', 'START_OF_PLAYLIST'],
            'shuffle_artist': ['PLAY_STATE_PLAYING', 'SEARCH_EMPTY'],
            'seek': 'SEEK_TO_POSITION',
            }
        for key in responseHeaders:
            if key == request:
                responseType = responseHeaders[key]
        serverReply = dict()
        if expected == 'PLAY_STATE_PLAYING' or expected == 'PLAY_STATE_PAUSED':
            if request != 'shuffle_artist':
                position, duration = self.audio_stream.getTime()
                serverReply['now_playing_artist'] = self.track_info['artist']
                serverReply['now_playing_title'] = self.track_info['title']
                serverReply['position'] = position
                serverReply['duration'] = duration
                serverReply['time'] = convert_time(position)
                try:
                    serverReply['now_playing_artRef'] = (
                        self.track_info['albumArtRef'][0]['url'])
                except:  # catch exceptions for missing artwork
                    serverReply['now_playing_artRef'] = self.default_artRef
        if request == 'get_state':
            serverReply['current_state'] = expected
            serverReply['host'] = self.HOST_NAME
            if expected == 'SERVER_IDLE':
                return serverReply
            return serverReply
        if request == 'toggle_play':
            serverReply['current_state'] = expected
            serverReply['host'] = self.HOST_NAME
            return serverReply
        if request == 'play_next' or request == 'play_prev':
            if expected in responseType:
                serverReply['current_state'] = expected
                serverReply['host'] = self.HOST_NAME
                return serverReply
        if request == 'shuffle_artist':
            if expected in responseType:
                serverReply['current_state'] = expected
                serverReply['host'] = self.HOST_NAME
                return serverReply
        if request == 'seek':
            serverReply['current_state'] = 'SEEKING'
            serverReply['host'] = self.HOST_NAME
            serverReply['seek_pos'] = expected
            return serverReply

    # Start a new audio stream
    def playMedia(self, track_id):
        if not self.audio_stream:  # No audio_stream is currently in use
            # build a new audio_stream object
            self.track_id = track_id
            self.audio_stream = makeStream(self.gPlayClient, track_id)
        else:  # There's a strem currently in use
            self.audio_stream.stop()  # stop current audio object
            self.audio_stream = None
            self.audio_stream = makeStream(self.gPlayClient, self.track_id)
        # output to server console
        print (('%s >> %sNow Playing:%s %s%s%s by %s%s%s' % (
            self.server_name, Color.BOLD, Color.RESET,
            Color.GREEN, self.track_info['title'][:16], Color.RESET,
            Color.GREEN, self.track_info['artist'][:18], Color.RESET)))
        # start audio_stream
        self.audio_stream.bus.connect('message::eos', self.on_eos)
        self.audio_stream.play()
        self.audio_stream.playing = True

    # End of stream
    def on_eos(self, bus, msg):
        self.audio_stream.stop()
        print (('%s >> the stream has ended.' % (self.server_name)))
        self.playNext()

    # Play next track in playlist
    def playNext(self):
        # output to server console
        print (("%s >> play next track in playlist." % (self.server_name)))
        if (self.current_index + 1) <= len(self.playlist) - 1:
            self.current_index += 1
            self.setTrack(self.playlist[self.current_index])
            # start audio stream
            self.playMedia(self.track_id)
        else:
            # output to server console
            print (("%s >> end of playlist." % (self.server_name)))

    # Check population of track_ids(List)
    def makePlaylist(self, track_ids=[]):
        if len(track_ids) > 0:
            self.playlist = track_ids
            return True
        else:
            return False

    # Reset parameters for a new playlist
    def startPlaylist(self):
        self.current_index = 0
        self.track_id = self.playlist[self.current_index]
        self.track_info = self.gPlayClient.getTrackInfo(self.track_id)

    # Reset parameters for a new track
    def setTrack(self, track_id):
        self.track_id = track_id
        self.track_info = self.gPlayClient.getTrackInfo(self.track_id)

    # Shutdown server
    def stop(self):
        if self.audio_stream:
            self.audio_stream.stop()
        if self.conn:
            self.conn.close()
        print "\n>> stopping server...",
        self._stop.set()
        print (("%sdone.%s" % (
            Color.YELLOW, Color.RESET)))
        print (("%s>> Quitting Google DJ%s...\n" % (
            Color.BOLD, Color.RESET)))
        print (("%s..done.%s" % (
            Color.YELLOW, Color.RESET)))

""" End Main Class """


################################################
###            Utility Functions             ###
################################################

# Return local network IP addr for host machine
def getNetworkIp():
    s = socket(AF_INET, SOCK_DGRAM)
    s.connect(('8.8.8.8', 0))
    return s.getsockname()[0]


# Shuffle a List
def shufflePlaylist(playlist):
    random.shuffle(playlist)


# Return an audio_stream object
def makeStream(gPlayClient, track_id):
    stream_url = gPlayClient.gPlayer.get_stream_url(track_id)
    audio_stream = GStreamer(stream_url)
    return audio_stream


# Necessary to enable pygst bus messages
class GobjectThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.loop = gobject.MainLoop()

    def run(self):
        self.loop.run()

    def quit(self):
        self.loop.quit()


"""***---RunShebang---***"""
if __name__ == '__main__':
    gobject.threads_init()
    t = GobjectThread()
    t.start()
    GPlayServer().start()
    t.quit()