#!/usr/bin/python
# -*- coding: utf-8 -*-

# LightHead programm is a HRI PhD project at the University of Plymouth,
#  a Robotic Animation System including face, eyes, head and other
#  supporting algorithms for vision and basic emotions.
# Copyright (C) 2010 Frederic Delaunay, frederic.delaunay@plymouth.ac.uk

#  This program is free software: you can redistribute it and/or
#   modify it under the terms of the GNU General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   General Public License for more details.

#  You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import threading
import logging

# convenient format.
LOGFORMATINFO={'format':"%(asctime)s.%(msecs)d %(name)s.%(filename).21s:"
                        "%(lineno)-4d-%(levelname)s-\t%(message)s",
               'datefmt':"%H:%M:%S"}
VFLAGS2LOGLVL={ 0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG,
                3: logging.DEBUG-1      # USR1
                }


def set_logging_default(verbosity_level=0):
    verbosity_level = min(verbosity_level,len(VFLAGS2LOGLVL))
    logging.basicConfig(level=VFLAGS2LOGLVL[verbosity_level], **LOGFORMATINFO)

# now we patch Python code to add color support to logging.StreamHandler
#Taken from stackoverflow.com, Thanks and Credits to sorin (and Peter Hoffman?)
#
#                       --- start of code copy ---
#

def add_colors_windows(fn):
    import ctypes
    def _out_handle(self):
        return ctypes.windll.kernel32.GetStdHandle(self.STD_OUTPUT_HANDLE)
    out_handle = property(_out_handle)

    def _set_color(self, code):
        # Constants from the Windows API
        self.STD_OUTPUT_HANDLE = -11
        hdl = ctypes.windll.kernel32.GetStdHandle(self.STD_OUTPUT_HANDLE)
        ctypes.windll.kernel32.SetConsoleTextAttribute(hdl, code)

    setattr(logging.StreamHandler, '_set_color', _set_color)

    def new(*args):
        FOREGROUND_BLUE      = 0x0001 # text color contains blue.
        FOREGROUND_GREEN     = 0x0002 # text color contains green.
        FOREGROUND_RED       = 0x0004 # text color contains red.
        FOREGROUND_INTENSITY = 0x0008 # text color is intensified.
        FOREGROUND_WHITE     = FOREGROUND_BLUE|FOREGROUND_GREEN |FOREGROUND_RED
        # winbase.h
        STD_INPUT_HANDLE = -10
        STD_OUTPUT_HANDLE = -11
        STD_ERROR_HANDLE = -12

        # wincon.h
        FOREGROUND_BLACK     = 0x0000
        FOREGROUND_BLUE      = 0x0001
        FOREGROUND_GREEN     = 0x0002
        FOREGROUND_CYAN      = 0x0003
        FOREGROUND_RED       = 0x0004
        FOREGROUND_MAGENTA   = 0x0005
        FOREGROUND_YELLOW    = 0x0006
        FOREGROUND_GREY      = 0x0007
        FOREGROUND_INTENSITY = 0x0008 # foreground color is intensified.

        BACKGROUND_BLACK     = 0x0000
        BACKGROUND_BLUE      = 0x0010
        BACKGROUND_GREEN     = 0x0020
        BACKGROUND_CYAN      = 0x0030
        BACKGROUND_RED       = 0x0040
        BACKGROUND_MAGENTA   = 0x0050
        BACKGROUND_YELLOW    = 0x0060
        BACKGROUND_GREY      = 0x0070
        BACKGROUND_INTENSITY = 0x0080 # background color is intensified.

        levelno = args[1].levelno
        if(levelno>=50):
            color = BACKGROUND_YELLOW | FOREGROUND_RED | FOREGROUND_INTENSITY
            #| BACKGROUND_INTENSITY
        elif(levelno>=40):
            color = FOREGROUND_RED | FOREGROUND_INTENSITY
        elif(levelno>=30):
            color = FOREGROUND_YELLOW | FOREGROUND_INTENSITY
        elif(levelno>=20):
            color = FOREGROUND_GREEN
        elif(levelno>=10):
            color = FOREGROUND_MAGENTA
        elif(levelno==9):
            color = FOREGROUND_CYAN
        else:
            color =  FOREGROUND_WHITE
        args[0]._set_color(color)

        ret = fn(*args)
        args[0]._set_color( FOREGROUND_WHITE )
        #print "after"
        return ret
    return new

def add_colors_ansi(fn):
    # add methods we need to the class
    def new(*args):
        levelno = args[1].levelno
        if(levelno>=50):
            color = COLORS['RED'][0]
        elif(levelno>=40):
            color = COLORS['RED'][0]
        elif(levelno>=30):
            color = COLORS['YELLOW'][0]
        elif(levelno>=20):
            color = COLORS['GREEN'][0]
        elif(levelno>=10):
            color = COLORS['MAGENTA'][0]
        elif(levelno==9):
            color = COLORS['CYAN'][0]
        else:
            color = COLORS['NORMAL']
        args[1].msg = color + args[1].msg + COLORS['NORMAL']
        return fn(*args)
    return new

import platform
if platform.system()=='Windows':
    # Windows does not support ANSI escapes
    logging.StreamHandler.emit = add_colors_windows(logging.StreamHandler.emit)
else:
    #XXX: Non portable.
    COLORS = {
        'NORMAL'     : '\x1b[0m',
        # color_key: (FOREGROUND, BACKGROUND)
        'BLACK'      : ('\x1b[31m', '\x1b[40m'),
        'RED'        : ('\x1b[31m', '\x1b[41m'),
        'GREEN'      : ('\x1b[32m', '\x1b[42m'),
        'YELLOW'     : ('\x1b[33m', '\x1b[43m'),
        'BLUE'       : ('\x1b[34m', '\x1b[44m'),
        'MAGENTA'    : ('\x1b[35m', '\x1b[45m'),
        'CYAN'       : ('\x1b[36m', '\x1b[46m'),
        'WHITE'      : ('\x1b[37m', '\x1b[47m'),
}
    logging.StreamHandler.emit = add_colors_ansi(logging.StreamHandler.emit)
#
#                       --- end of code copy ---
#


def round(iterable):
    """version for iterables, different signature from __builtins__.round"""
    return [ round(v, Spine_Server.PRECISION) for v in iterable ]

def weighted_choice(weights):
    """Returns random index biased by relative value of weights.

    weights: iterable of numbers. Faster if sorted with descending ordering.
             Weights don't need to sum to 1.
    """
    r = random.random() * sum(weights)
    for i, w in enumerate(weights):
        r -= w
        if r < 0:
            return i

def print_remaining_threads(prefix=""):
    """Return: list of remaining threads"""
    threads_str = [ "* alive: %s - daemon: %s <%s>" % (
            th.isAlive(), th.isDaemon(), th.name) for th in
                    threading.enumerate() if th.name != "MainThread" ]
    if not threads_str:
        return
    print prefix+"\n\t".join(threads_str)
