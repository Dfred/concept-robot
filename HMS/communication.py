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

"""
"""

__author__ = "Frédéric Delaunay"
__copyright__ = "Copyright 2011, University of Plymouth, lightHead system"
__credits__ = ["Joachim de Greeff"]
__license__ = "GPL"

import threading, time

from utils.comm.threaded_comm import ThreadedComm
from utils.comm import ASCIICommandClient, set_debug_logging
from utils import get_logger

set_debug_logging(True)
LOG = get_logger(__package__)


class ThreadedLightheadComm(ThreadedComm):
    """Class dedicated for communication with lightHead server.
    """

    def __init__(self, srv_addrPort, connection_succeded_fct):
        """
        """
        super(ThreadedLightheadComm, self).__init__(srv_addrPort,
                                                    connection_succeded_fct)
        # information blocks
        self.lips_info = None
        self.gaze_info = None
        self.face_info = None
        self.snapshot = None

    def cmd_lips(self, argline):
        self.lips_info = argline

    def cmd_gaze(self, argline):
        self.gaze_info = argline

    def cmd_face(self, argline):
        self.face_info = argline
        
    def cmd_snapshot(self, argline):
        self.snapshot = argline

    def get_snapshot(self, origin, binary=False):
        """
        origin: string, target subset of LightHead's AU pool; None for all.
        binary: bool, binary (faster) protocol or ASCII (clear text) protocol.
        """
        self.send_msg("get_snapshot")
        self.wait()

    def end_snapshot(self):
        return (self.lips_info, self.gaze_info, self.face_info)


class ThreadedExpressionComm(ThreadedComm):
    """Class dedicated for communication with expression server.
    """

    ST_ACK, ST_NACK, ST_INT, ST_DSC = range(4)

    def __init__(self, srv_addrPort, connection_succeded_fct):
        """
        srv_addrPort: (server_address, port)
        connection_succeded_fct: function called on successful connection.
        """
        super(ThreadedExpressionComm,self).__init__(srv_addrPort,
                                                    connection_succeded_fct)
        self.tag = None
        self.tag_count = 0
        self.status = None
        self.reset_datablock()
        self.on_reply = {}

    def on_reply_fct(self, tag, fct):
        """Installs a callback on reply from Expression.
        Use the same function with argument None to unset.
        """
        if not fct:
            del self.on_reply[tag]
            return
        assert fct.func_code.co_argcount == 2, fct.func_name+" shall get 2 args"
        self.on_reply[tag] = fct

    def cmd_ACK(self, argline):
        self.status = self.ST_ACK
        self.tag = argline.strip()
        try: self.on_reply[self.tag]('ACK', self.tag)
        except KeyError: pass

    def cmd_NACK(self, argline):
        self.status = self.ST_NACK
        self.tag = argline.strip()
        try: self.on_reply[self.tag]('NACK', self.tag)
        except KeyError: pass
        LOG.warning('expression reports bad message (%s).', self.tag)

    def cmd_INT(self, argline):
        self.status = self.ST_INT
        self.tag = argline.strip()
        try: self.on_reply[self.tag]('INT', self.tag)
        except KeyError: pass
        LOG.warning('expression reports animation interruption! (%s)', self.tag)

    def cmd_DSC(self, argline):
        self.status = self.ST_DSC
        self.tag = None
        try: self.on_reply[self.tag]('DSC', self.tag)
        except KeyError: pass
        LOG.warning('expression reports disconnection from lightHead!')

    def reset_datablock(self):
        """Forgets values previously stored with set_ functions.
        """
        self.datablock = ['']*5

    def set_fExpression(self, name, intensity=1.0, duration=None):
        """
        name: facial expression identifier, no colon (:) allowed.
        intensity: float, normalized gain.
        duration: float, duration of facial expression in seconds.
        """
        assert type(name) is str and type(intensity) is float, 'wrong types'
        assert duration is None or type(duration) is float, 'duration not float'
        d_str = duration and '/%.2f' % duration or ''
        self.datablock[0] = '{0!s}:{1:.3f}{2:s}'.format(name, intensity, d_str)

    def set_text(self, text):
        """
        text: text to utter, no double-quotes (") allowed.
        """
        assert type(text) is str, 'wrong types'
        self.datablock[1] = text

    def set_gaze(self, vector3):
        """
        vector3: (x,y,z) : right handedness (ie: with y+ pointing forward)
        """
        assert len(vector3) == 3 and type(vector3[0]) is float, 'wrong types'
        self.datablock[2] = str(vector3)[1:-1]

    def set_neck(self, rotation=(), orientation=(), translation=(),
                 duration=None):
        """Places head (absolute position is not available). See set_spine().
        """
        self.set_spine(rotation, orientation, translation, duration,part='neck')

    def set_thorax(self, rotation=(), orientation=(), duration=None):
        """Places thorax (position is not available). Arguments: see set_spine()
        """
        self.set_spine(rotation, orientation, duration=duration, part='thorax')

    def set_spine(self, rotation=(), orientation=(), translation=(),
                 duration=None, part='neck'):
        """Uses right handedness (ie: with y+ pointing forward) 
        rotation:    (x,y,z) : relative normalized orientation 
        orientation: (x,y,z) : absolute normalized orientation
        translation: (x,y,z) : relative normalized translation
        duration: float, duration of movement in seconds.
        """
        assert rotation and \
            (len(rotation)==3 and type(rotation[0]) is float) or \
            True, 'rotation: wrong types'
        assert orientation and \
            (len(orientation) == 3 and type(orientation[0]) is float) or\
            True, 'orientation: wrong types'
        if part == 'neck':
            assert translation and \
              (len(translation) == 3 and type(translation[0]) is float) or \
              True, 'translation: wrong types'
        assert rotation or orientation, "it's either orientation *OR* rotation"
        assert duration is None or type(duration) is float, 'duration not float'
        if self.datablock[3]:
            self.datablock[3] += '|'
        self.datablock[3] += part+'='
        if rotation:
          self.datablock[3] += "(%s, %s, %s)" % tuple(rotation)
        elif orientation:
          self.datablock[3] += "((%s, %s, %s))" % tuple(orientation)
        elif translation:
          self.datablock[3] += "[%s, %s, %s]" % tuple(translation)
        else:
          raise ValueError("no vector given")
        if duration:
          self.datablock[3] += "/%.2f" % duration

    def set_instinct(self, command):
        """
        command: you should know what you are doing when dealing with this.
        """
        assert type(command) is str, 'wrong types'
        self.datablock[4] = command

    def send_datablock(self, tag=''):
        """Sends self.datablock to server and resets self.datablock.

        Use wait_reply to block until server replies for your tag.
        tag: string identifying your datablock.
        Returns: tag, part of it is generated. You may need it for wait_reply().
        """
        datablock = '{0};"{1}";{2};{3};{4};'.format(*self.datablock)
        self.tag_count += 1
        tag += str(self.tag_count)
        self.status = None
        self.reset_datablock()
        self.send_msg(datablock+tag)
        return tag

    def send_my_datablock(self, datablock):
        """Sends a raw datablock, so you have to know datablock formatting.
        """
        self.status = None
        self.send_msg(datablock)

    def wait_reply(self, tag):
        """Wait for a reply from the server.
        """
        while self.status is None:
            if self.tag == tag:
                break
            time.sleep(0.05)
