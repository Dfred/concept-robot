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

import cPickle as pickle
import time

from utils.comm.threaded_comm import MTComm
from utils.comm import ASCIICommandClient, set_debug_logging
from utils import get_logger

set_debug_logging(True)
LOG = get_logger(__package__)


class MTLightheadComm(MTComm):
    """Class dedicated for communication with lightHead server.
    """

    def __init__(self, srv_addrPort, connection_lost_fct = None,
                 connection_succeded_fct = None):
        """
        """
        super(MTLightheadComm, self).__init__(srv_addrPort,
                                              connection_lost_fct,
                                              connection_succeded_fct)
        self.thread.name += '_LightHead'
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
        """Only supports binary mode of the protocol (using pickle).
        """ 
        args = argline.split()
        if len(args) != 1:
            LOG.error("Binary transfer protocol error.")
            self.snapshot = None
        else:
            try:
                self.snapshot = pickle.loads(self.read(int(args[0])+1))
            except StandardError, e:
                LOG.error("receiving snapshot: %s", e)
                self.snapshot = None
            for k,v in self.snapshot.iteritems():
                self.snapshot[k] = dict(zip(v[0][1], v[1]))
        self.unblock_wait()

    def get_snapshot(self, origins):
        """Returns a snapshot from remote server.
        origins: iterable of strings, name of origins to retreive; None for all.
        """
        assert hasattr(origins,'__iter__'), "origins isn't an iterable"
        self.send_msg("get_snapshot " + (origins and ' '.join(origins) or '') )
        self.wait()
        return self.snapshot


class MTExpressionComm(MTComm):
    """Class dedicated for communication with expression server.

    It's possible to set handlers for any kind of answer from expr2.
    """

    ST_ACK, ST_NACK, ST_INT, ST_DSC = range(4)

    @staticmethod                               #XXX: we're adding to the class
    def add_handler(status, log_fct, msg):
        """cmd_ handlers can only be called by self.thread so threading is easy.
        """
        PRE_MSG = 'expression reports '
        def cmd_(self, argline):
            tag = argline.strip()
            try:
                self.on_reply[tag](status, tag)
            except KeyError:
                pass
            log_fct(PRE_MSG+msg, tag or '')
            if tag in self.tags_pending:
                self.tags_pending.remove(tag)
                self.tag = tag
                self.unblock_wait()
                while self.tag:                     #XXX: waiters reset self.tag
                    time.sleep(.1)
        setattr(MTExpressionComm, 'cmd_'+status, cmd_)

    def __init__(self, srv_addrPort, connection_lost_fct = None,
                 connection_succeded_fct = None):
        """
        srv_addrPort: (server_address, port)
        connection_succeded_fct: function called on successful connection.
        """
        super(MTExpressionComm,self).__init__(srv_addrPort,
                                              connection_lost_fct,
                                              connection_succeded_fct)
        self.thread.name += '_Expr2'
        self.tag = None
        self.tag_count = 0
        self.tags_pending = set()
        self.reset_datablock()
        self.on_reply = {}

        for status,fct,msg in (
            ('ACK', LOG.debug, 'processing of tag %s'),
            ('NACK',LOG.info, 'bad message (%s)'),
            ('INT', LOG.warning,'animation interruption (%s)'),
            ('DSC', LOG.warning,'the RAS is disconnected!%s')):
            MTExpressionComm.add_handler(status,fct,msg)

    def reset_datablock(self):
        """Forgets values previously stored with set_ functions.
        """
        self.datablock = ['']*5

    def on_reply_fct(self, tag, fct):
        """Installs a callback on reply from Expression.
        Use the same function with argument None to unset.
        """
        if not fct:
            del self.on_reply[tag]
            return
        assert fct.func_code.co_argcount == 2, fct.func_name+" shall get 2 args"
        self.on_reply[tag] = fct

    def set_fExpression(self, name, intensity=1.0, duration=None):
        """Sets (and returns) the facial expression part of Expr2's datablock.
        name: facial expression identifier, no colon (:) allowed.
        intensity: float, normalized gain.
        duration: float, duration of facial expression in seconds.
        """
        assert type(name) is str and type(intensity) is float, 'wrong types'
        assert duration is None or type(duration) is float, 'duration not float'
        d_str = duration and '/%.2f' % duration or ''
        self.datablock[0] = '{0!s}:{1:.3f}{2:s}'.format(name, intensity, d_str)
        return self.datablock[0]

    def set_text(self, text):
        """Sets (and returns) the text part of Expr2's datablock.
        text: text to utter, no double-quotes (") allowed.
        """
        assert type(text) is str, 'wrong types'
        self.datablock[1] = '"%s"' % text
        return self.datablock[1]

    def set_gaze(self, vector3):
        """Sets (and returns) the eye-gaze part of Expr2's datablock.
        vector3: (x,y,z) : right handedness (ie: with y+ pointing forward)
        """
        assert len(vector3) == 3 and type(vector3[0]) is float, 'wrong types'
        self.datablock[2] = str(vector3)[1:-1]
        return self.datablock[2]

    def set_neck(self, rotation=(), orientation=(), translation=(),
                 duration=None):
        """Places head (absolute position is not available). See set_spine().
        """
        self.set_spine(rotation, orientation, translation, duration,
                       part='CERVICALS')

    def set_thorax(self, rotation=(), orientation=(), duration=None):
        """Places thorax (position is not available). Arguments: see set_spine()
        """
        self.set_spine(rotation, orientation, duration=duration, part='thorax')

    def set_spine(self, rotation=(), orientation=(), translation=(),
                 duration=None, part='neck'):
        """Sets (and returns) the spine part of Expr2's datablock. Uses right
         handedness (ie: with y+ pointing forward) 
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
        return self.datablock[3]

    def set_instinct(self, command):
        """Sets (and returns) the instinct part of Expr2's datablock.
        command: you should know what you are doing when dealing with this.
        """
        assert type(command) is str, 'wrong types'
        self.datablock[4] = command
        return self.datablock[4]

    def send_datablock(self, tag=''):
        """Sends self.datablock to server and resets self.datablock.
        Use wait_reply to block until server replies for your tag.
        tag: string identifying your datablock.
        Returns: tag, part of it is generated. You may need it for wait_reply().
        """
        self.tag_count += 1
        tag += str(self.tag_count)
        datablock = ';'.join(self.datablock)+';'
        self.reset_datablock()
        self.send_msg(datablock+tag)
        return tag

    def send_my_datablock(self, datablock):
        """Sends a raw datablock, so you have to know datablock formatting.
        """
        self.send_msg(datablock)

    def wait_reply(self, tag):
        """Waits for a reply from the server.
        """
        self.tags_pending.add(tag)
        while self.working:
            self.wait(.5)
            if self.tag == tag:
                break
        self.tag = None

    def sendDB_waitReply(self, datablock=None, tag=None):
        """Sends (given or internal) datablock and returns upon reply about it.
        datablock: string without tag
        tag: string
        """
        if datablock and tag:
            self.send_my_datablock(datablock+tag)
            self.wait_reply(tag)
        else:
            self.wait_reply(self.send_datablock())


if __name__ == "__main__":
    raise NotImplementedError("untested, potentially unreliable. Behind you!!!")
