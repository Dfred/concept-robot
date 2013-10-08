#!/usr/bin/python
# -*- coding: utf-8 -*-

# ARAS is the open source software (OSS) version of the basic component of
# Syntheligence's software suite. This software is provided for academic
# research only. Any other use is not permitted.
# Syntheligence SAS is a robotics and software company established in France.
# For more information, visit http://www.syntheligence.com .

# ARAS stands for Abstract Robotic Animation System, and features actuator,
# sensor, animation and remote management high-level interfaces.
# Copyright 2013 Syntheligence, fdelaunay@syntheligence.com

# This software was originally named LightHead, the Human-Robot-Interaction part
# of the CONCEPT project, taking place at the University of Plymouth (UK).
# The project originated as the PhD pursued by Frédéric Delaunay, who was under
# the supervision of Prof. Tony Belpaeme.
# This PhD project started in late 2008 and ended in late 2011.
# Visit http://www.tech.plym.ac.uk/SoCCE/CONCEPT/ for more information.

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

from comm.threaded_comm import MTComm
from comm import ASCIICommandClient, set_debug_logging
from . import get_logger

set_debug_logging(True)
LOG = get_logger(__package__)


class MT_ArasComm(MTComm):
    """Class dedicated for communication with ARAS server.
    """

    def __init__(self, srv_addrPort, connection_lost_fct = None,
                 connection_succeded_fct = None):
        """
        """
        super(MT_ArasComm, self).__init__(srv_addrPort,
                                              connection_succeded_fct,
                                              connection_lost_fct)
        self.thread.name += '_ARAS'
        # information blocks
        self.face_info = None
        self.snapshot = None

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


class MT_ChlasComm(MTComm):
    """Class dedicated for communication with expression server.

    It's possible to set handlers for any kind of answer from expr2.
    """

    ROTP_PRE_SUFF = { 'o':('((','))'), 'r':('(',')'),
                      'p':('[[',']]'), 't':('[',']'),
                    }

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
        setattr(MT_ChlasComm, 'cmd_'+status, cmd_)

    def __init__(self, srv_addrPort, connection_lost_fct = None,
                 connection_succeded_fct = None):
        """
        srv_addrPort: (server_address, port)
        connection_succeded_fct: function called on successful connection.
        """
        super(MT_ChlasComm,self).__init__(srv_addrPort,
                                              connection_succeded_fct,
                                              connection_lost_fct)
        self.thread.name += '_CHLAS'
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
            MT_ChlasComm.add_handler(status,fct,msg)

    def reset_datablock(self):
        """Forgets values previously stored with set_ functions.
        """
        self.datablock = ['']*5

    def on_reply_fct(self, tag, fct):
        """Installs a callback on reply from the CHLAS.
        Use the same function with argument None to unset.
        """
        if not fct:
            del self.on_reply[tag]
            return
        assert fct.func_code.co_argcount == 2, fct.func_name+" shall get 2 args"
        self.on_reply[tag] = fct

    def set_fExpression(self, name, intensity=1.0, duration=None):
        """Sets (and returns) the facial expression part of our CHLAS datablock.
        name: facial expression identifier, no colon (:) allowed.
        intensity: float, normalized gain.
        duration: float, duration of facial expression in seconds.
        """
        assert type(name) is str , 'name should be a string'
        return self.format_DB(0, name, None, intensity, duration)

    def set_text(self, text):
        """Sets (and returns) the text part of our CHLAS datablock.
        text: text to utter, no double-quotes (") allowed.
        """
        assert type(text) is str, 'text should be a string'
        return self.format_DB(1, '"%s"'%text)

    def set_gaze(self, vector3, transform='p', duration=None):
        """Sets (and returns) the eye-gaze part of our CHLAS datablock.
        vector3: (x,y,z) : right handedness (ie: with y+ pointing forward)
        """
        assert len(vector3)==3, "vector3: wrong type"
        return self.format_DB(2, vector3, transform, None, duration)

    def set_neck(self, vector3, transform='o', duration=None):
        """Places head. Arguments: see format_DB()."""
        assert len(vector3)==3, "vector3: wrong type"
        return self.format_DB(3, vector3, transform, None, duration,
                              keywd='Cervicals')

    def set_thorax(self, vector3, tranform='o', duration=None):
        """Places thorax. Arguments: see format_DB()."""
        assert len(vector3)==3, "vector3: wrong type"
        return self.format_DB(3, vector3, transform, None, duration,
                              keywd='Thorax')

    def set_spine(self, spine_section, vector3, transform, duration):
        """Generic Spine placement."""
        return self.format_DB(3, vector3, transform, None, duration,
                              spine_section)

    def set_instinct(self, command):
        """Sets (and returns) the instinct part of our CHLAS datablock.
        command: you should know what you are doing when dealing with this.
        """
        assert type(command) is str, 'wrong types'
        self.datablock[4] = command
        return self.datablock[4]

    def format_DB(self, i, value, trnsf=None, intns=None, durtn=None,
                  keywd=None, args=None):
        """Sets (and returns) an element of our CHLAS datablock.

        Transforms use right handedness (ie: with y+ pointing forward).
        
        value:  representable object supported by the CHLAS. Your check. 
        trnsf:  char, one of o,r,t,p (Orientation, Rotatn, Transltn, Positn)
        intns:  float, intensity of action whenever relevant.
        durtn:  float, duration of action in seconds.
        keywd:  string, see CHLAS' documentation.
        """
        assert durtn is None or type(durtn) is float, 'duration not float'
        if self.datablock[i]:
            self.datablock[i] += '|'
        if keywd:
            self.datablock[i] += keywd+':'
        if trnsf:
            self.datablock[i] += self.get_transform(value, trnsf)
        else:
            self.datablock[i] += "%s" % value
        if intns:
            self.datablock[i] += "*%.3f" % intns
        if durtn:
            self.datablock[i] += "/%.2f" % durtn
        return self.datablock[i]

    def get_transform(self, vector, trnsf_type):
        """
        """
        assert trnsf_type in ('r','o','t','p',None), "unknown transform"
        return ( ("%s%%s%s" % self.ROTP_PRE_SUFF[trnsf_type]) %
                 str([round(v,3) for v in vector])[1:-1] )

    def send_datablock(self, tag=''):
        """Sends self.datablock to server and resets self.datablock.
        Use wait_reply to block until server replies for your tag.
        tag: string identifying your datablock.
        Returns: tag, part of it is generated. You may need it for wait_reply().
        """
        if not tag:
            self.tag_count += 1
            tag = str(self.tag_count)
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
            self.wait_reply(self.send_datablock(tag))


if __name__ == "__main__":
    raise NotImplementedError("untested, potentially unreliable. Behind you!!!")
