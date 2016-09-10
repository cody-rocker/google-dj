# -*- coding: utf-8 -*-
# required  ubuntu-restricted-extras
# sudo apt-get install ubuntu-restricted-extras

import pygst
pygst.require("0.10")
import gst

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

# example http://lzone.de/Media%20Player%20with%20GStreamer%20and%20PyGI


class GStreamer():

    def __init__(self, stream_url):
        self.playing = False
        self.player = gst.element_factory_make('playbin2', 'player')
        self.sink = gst.element_factory_make('alsasink', 'gconfaudiosink')
        self.player.set_property('audio-sink', self.sink)
        self.player.set_property('uri', stream_url)
        self.bus = self.player.get_bus()
        self.bus.enable_sync_message_emission()
        self.bus.add_signal_watch()

    def toggle_play(self):
        if self.playing is False:
            self.play()
        else:
            self.pause()
        self.playing = not(self.playing)

    def play(self):
        self.player.set_state(gst.STATE_PLAYING)

    def pause(self):
        self.player.set_state(gst.STATE_PAUSED)

    def stop(self):
        self.playing = False
        self.player.set_state(gst.STATE_NULL)

    # Return current_time and total_time for active stream
    def getTime(self):
        if self.playing:
            try:
                position_nanosecs = self.player.query_position(gst.FORMAT_TIME)[0]
                duration_nanosecs = self.player.query_duration(gst.FORMAT_TIME)[0]
                duration = float(duration_nanosecs) / gst.SECOND
                position = float(position_nanosecs) / gst.SECOND
                return str(int(position)), str(int(duration))
            except Exception:
                # pipeline must not be ready and does not know position
                return str(0), str(100)
        return str(0), str(100)

    def seekToPosition(self, seconds):
        if self.playing:
            try:
                self.player.seek_simple(gst.FORMAT_TIME,
                                        gst.SEEK_FLAG_FLUSH,
                                        seconds * gst.SECOND)
                reply = convert_time(seconds)
                return reply
            except Exception:
                # pipeline must not be ready and does not know position
                return "pipeline is busy."
        return "no audio stream."


def convert_time(seconds):
    t = int(seconds) * gst.SECOND
    s, ns = divmod(t, 1000000000)
    m, s = divmod(s, 60)

    if m < 60:
        return "%02i:%02i" % (m, s)
    else:
        h, m = divmod(m, 60)
        return "%i:%02i:%02i" % (h, m, s)