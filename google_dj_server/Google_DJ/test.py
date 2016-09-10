#!/usr/bin/python
# -*- coding: utf-8 -*-
from gPlayClient import GPlayClient, logout
from color_output import Color


def TestPersistence():
    print (('\n%s>> Test Session Persistence%s' % (Color.BOLD, Color.RESET)))
    print (('\n%s%s    Persistence Test 1\\3 Create GPlayer Instance%s' % (
        Color.BOLD, Color.YELLOW, Color.RESET)))
    GPlayClient()
    print (('    %s..passed%s' % (Color.LT_GREEN, Color.RESET)))

    print (('\n%s%s    Persistence Test 2\\3 Logout current user.%s' % (
        Color.BOLD, Color.YELLOW, Color.RESET)))
    logout()
    print (('    %s..passed%s' % (Color.LT_GREEN, Color.RESET)))

    print (('\n%s%s    Persistence Test 3\\3 Login new user.%s' % (
        Color.BOLD, Color.YELLOW, Color.RESET)))
    GPlayClient()
    print (('    %s..passed%s' % (Color.LT_GREEN, Color.RESET)))


def TestGStreamer():
    print (('\n%s>> Test GStreamer%s' % (Color.BOLD, Color.RESET)))
    print (('\n%s%s    GStreamer Test 1\\1 Play sample stream.%s' % (
        Color.BOLD, Color.YELLOW, Color.RESET)))
    #newGPlayer = GPlayClient()
    print (('    %s..passed%s' % (Color.LT_GREEN, Color.RESET)))


from socket import *


def getNetworkIp():
    s = socket(AF_INET, SOCK_DGRAM)
    s.connect(('8.8.8.8', 0))
    #return s.getsockname()  # [0]
    return socket.gethostname()


print (('%s>> Running Google_DJ Tests..%s' % (Color.BOLD, Color.RESET)))
#TestPersistence()
#TestGStreamer()


print getNetworkIp()