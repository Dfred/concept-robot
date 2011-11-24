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

from utils.comm import ASCIICommandClient, set_debug_logging
from utils import get_logger

set_debug_logging(True)
LOG = get_logger(__package__)


class ThreadedComm(ASCIICommandClient):
    """A communication class based on the comm protocol with threaded polling.
    """

    CONNECT_TIMEOUT = 3

    def __init__(self, server_addrPort):
        super(ThreadedComm,self).__init__(server_addrPort)
        self.connect_timeout = self.CONNECT_TIMEOUT
        self.working = True
        # let's the threaded object manage the socket independently
        self.thread = threading.Thread(target=self.always_connected)
        self.thread.start()

    def handle_connect_error(self, e):
        """See handle_connect_timeout.
        """
        super(ThreadedComm, self).handle_connect_error(e)
        self.handle_connect_timeout()

    def handle_connect_timeout(self):
        """Sleeps a bit.
        """
        time.sleep(1)

    def always_connected(self):
        """
        """
        while self.working:
            self.connect_and_run()

    def done(self):
        """
        """
        self.working = False
        self.disconnect()
        self.thread.join()

    def send_msg(self, msg):
        if self.connected:
            return super(ThreadedComm, self).send_msg(msg)
        LOG.debug("*NOT* sending to %s: '%s'", self.addr_port, msg)


class LightHeadComm(ThreadedComm):
    """Class dedicated for communication with lightHead server.
    """

    def __init__(self, srv_addrPort):
        """
        """
        super(LightHeadComm, self).__init__(srv_addrPort)
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

    def get_snapshot(self):
        self.send_msg("get_snapshot")

    def end_snapshot(self):
        return (self.lips_info, self.gaze_info, self.face_info)


class ExpressionComm(ThreadedComm):
    """Class dedicated for communication with expression server.
    """

    ST_ACK, ST_NACK, ST_INT, ST_DSC = range(4)

    def __init__(self, srv_addrPort):
        """
        """
        super(ExpressionComm,self).__init__(srv_addrPort)
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

    def set_fExpression(self, name, intensity=1.0):
        """
        name: facial expression identifier, no colon (:) allowed.
        intensity: normalized gain.
        """
        assert type(name) is str and type(intensity) is float, 'wrong types'
        self.datablock[0] = '{0!s}:{1:.3f}'.format(name, intensity)

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

    def set_neck(self, rotation=(), orientation=(), position=()):
        """Set head placement.
        rotation:    (x,y,z) : relative normalized orientation 
        orientation: (x,y,z) : absolute normalized orientation
        position:    (x,y,z) : relative normalized position
        right handedness (ie: with y+ pointing forward)
        """
        assert rotation and \
            (len(rotation)==3 and type(rotation[0]) is float) or \
            True, 'wrong types'
        assert orientation and \
            (len(orientation) == 3 and type(orientation[0]) is float) or\
            True, 'wrong types'
        assert position and \
            (len(position) == 3 and type(position[0]) is float) or \
            True, 'wrong types'
        assert rotation or orientation, 'cannot specify orientation and rotation'
        msg = ""
        if rotation:
          self.datablock[3] += str(rotation)
        if orientation:
          self.datablock[3] += "((%s, %s, %s))" % orientation
        if position:
          self.datablock[3] += str(list(position))
        

    def set_instinct(self, command):
        """
        command: you should know what you are doing when dealing with this.
        """
        assert type(command) is str, 'wrong types'
        self.datablock[4] = command

    def set_datablock(self, f_expr, intens, txt, gaze, neck_rot, neck_pos, cmd):
        """
        All-in-one function, check parameters details from specific functions.
        """
        assert type(f_expr) is str and type(intens) is float, 'wrong types'
        assert type(txt) is str, 'wrong types'
        assert len(gaze) == 3 and type(gaze[0]) is float, 'wrong types'
        assert len(neck_rot) == 3 and type(neck_rot[0]) is float, 'wrong types'
        assert len(neck_pos) == 3 and type(neck_pos[0]) is float, 'wrong types'
        assert type(cmd) is str, 'wrong types'
        self.datablock = [ f_expr, intens, txt, gaze, neck_rot, neck_pos, cmd ]

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

    def send_my_datablock(self, datablock, tag):
        self.status = None
        self.send_msg(datablock+tag)

    def wait_reply(self, tag):
        """Wait for a reply from the server.
        """
        while self.status is None:
            if self.tag == tag:
                break
            time.sleep(0.05)
