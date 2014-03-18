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
import logging
import time

from comm.threaded_comm import ThreadedComm
from comm import ASCIICommandClient, set_debug_logging

set_debug_logging(True)
LOG = logging.getLogger(__package__)

##
## ARAS
##


class ArasProtocol(object):
    """
    """
    def __init__(self):
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

    def get_snapshot(self, origins):
        """Returns a snapshot from remote server.
        origins: iterable of strings, name of origins to retreive; None for all.
        """
        assert hasattr(origins,'__iter__'), "origins isn't an iterable"
        self.send_msg("get_snapshot " + (origins and ' '.join(origins) or '') )


class ArasComm(ASCIICommandClient, ArasProtocol):
    """Class dedicated for communication with ARAS server.
    """
    def get_snapshot(self, origins):
        ArasProtocol.get_snapshot(self, origins)
        self.read_socket_and_process()
        return self.snapshot


class ArasCommTh(ThreadedComm, ArasProtocol):
    """Class dedicated for threaded communication with ARAS server.
    """

    def __init__(self, *args, **kwds):
        """
        """
        ## init all subclasses
        super(ArasCommTh, self).__init__(*args, **kwds)
        self._thread_name = 'ARAS'

    def get_snapshot(self, origins):
        ArasProtocol.get_snapshot(self, origins)
        self.wait()                             ## wait for unwait() by thread
        return self.snapshot

    def cmd_snapshot(self,argline):
        ArasProtocol.cmd_snapshot(self,argline)
        if self.snapshot:                       #TDL XXX incomplete snapshot ?
            self.unwait()

##
## CHLAS
##


class ChlasProtocol(object):
    """
    It's possible to set handlers for any kind of answer from expr2.
    """

    ROTP_PRE_SUFF = { 'o':('((','))'), 'r':('(',')'),
                      'p':('[[',']]'), 't':('[',']'),
                    }
    
    def __init__(self):
        """
        """
        self.tag = None
        self._tag_count = 0
        self._tags_callbacks = {}
        self._datablock = []
        self.reset_datablock()

    def cmd_ACK(self, argline):
        arg = argline.strip()
        self.tag = arg
        fct = self._tags_callbacks.pop(arg, None)
        if fct:
            LOG.debug('calling callback %s for tag %s', fct, arg)
            fct(arg, "ACK")
        LOG.debug("no ACK callback for tag %s", arg)
    def cmd_NACK(self, argline):
        arg = argline.strip()
        LOG.error('bad message (%s)', arg)
        self.tag = arg
        fct = self._tags_callbacks.pop(arg, None)
        fct and fct(arg, "NACK")
    def cmd_INT(self, argline):
        LOG.warning('animation interruption')
        self.tag = None
        fct = self._tags_callbacks.pop(arg, None)
        fct and fct(arg, "INT")
    def cmd_DSC(self, argline):
        LOG.warning('the RAS is disconnected!')
        fct = self._tags_callbacks.pop(arg, None)
        fct and fct(arg, "DSC")

    def get_transform(self, vector, trnsf_type):
        """Translates a vector of floats into a CHLAS transform string.
        >vector: (float,)*3, transform vector
        >trnsf_type: char, transform type identifier. see format_element().
        Return: string, a transform formatted according to CHLAS protocol.
        """
        assert trnsf_type in ('r','o','t','p',None), "unknown transform"
        return ( ("%s%%s%s" % self.ROTP_PRE_SUFF[trnsf_type]) %
                 str([round(v,3) for v in vector])[1:-1] )

    def format_element(self, i, value, trnsf=None, intns=None, durtn=None,
                       keywd=None, args=None):
        """Sets (and returns) an element of our CHLAS datablock.

        Transforms use right handedness (ie: with y+ pointing forward).
        
        value:  representable object supported by the CHLAS. Your check. 
        trnsf:  char, one of o,r,t,p (Orientation, Rotatn, Transltn, Positn)
        intns:  float, intensity of action whenever relevant.
        durtn:  float, duration of action in seconds.
        keywd:  string, see CHLAS' documentation.
        """
        FIELDS = ['Animation', 'Utterance', 'Gaze', 'Spine', 'Reflexes']
        assert durtn is None or type(durtn) is float, "duration isn't a float"
        if self._datablock[i]:
            if i in (1,4):
                LOG.warning("appending to %s field!", FIELDS[i])
            self._datablock[i] += '|'
        if keywd:
            self._datablock[i] += keywd+':'
        if trnsf:
            self._datablock[i] += self.get_transform(value, trnsf)
        else:
            self._datablock[i] += "%s" % value
        if intns:
            self._datablock[i] += "*%.3f" % intns
        if durtn:
            self._datablock[i] += "/%.2f" % durtn
        return self._datablock[i]

    def set_animation(self, name, intensity=None, duration=None):
        """Sets (and returns) the animation part of our CHLAS datablock.
        name: animation identifier, no colon (:) allowed.
        intensity: float, normalized gain.
        duration: float, duration of facial expression in seconds.
        """
        assert hasattr(name, 'lower'), 'name should be a string'
        if not name:
            return
        return self.format_element(0, name, None, intensity, duration)

    def set_speech(self, text, language=None):
        """Sets (and returns) the speech (text) part of our CHLAS datablock.
        >text: string, text to utter, no double-quotes (") allowed.
        >language: string, default to None (no language change)
        """
        assert hasattr(text, 'lower'), "text should be a string"
        assert '"' not in text, "no \" allowed"
        if not text:
            return
        text = '"%s"' % text
        if language:
            text = "%s:%s" % (language, text)
        return self.format_element(1, text)

    def set_gaze(self, vector3, transform='o', duration=None):
        """Sets (and returns) the eye-gaze part of our CHLAS datablock.
        vector3: (x,y,z) : right handedness (ie: with y+ pointing forward)
        """
        assert len(vector3)==3, "vector3: wrong type"
        if not vector3:
            return
        return self.format_element(2, vector3, transform, None, duration)

    def set_neck(self, vector3, transform='o', duration=None):
        """Places head. Arguments: see format_element()."""
        assert len(vector3)==3, "vector3: wrong type"
        if not vector3:
            return
        return self.format_element(3, vector3, transform, None, duration,
                              keywd='Cervicals')

    def set_thorax(self, vector3, tranform='o', duration=None):
        """Places thorax. Arguments: see format_element()."""
        assert len(vector3)==3, "vector3: wrong type"
        if not vector3:
            return
        return self.format_element(3, vector3, transform, None, duration,
                              keywd='Thorax')

    def set_spine(self, spine_section, vector3, transform, duration):
        """Generic Spine placement."""
        if not spine_section:
            return
        return self.format_element(3, vector3, transform, None, duration,
                              spine_section)

    def set_reflexes(self, command):
        """Sets (and returns) the reflex part of our CHLAS datablock.
        command: you should know what you are doing when dealing with this.
        """
        assert hasattr(command, 'lower'), 'wrong types'
        if not command:
            return
        self._datablock[4] = command
        return self._datablock[4]

    def reset_datablock(self):
        """Forgets values previously stored with set_ functions.
        """
        self._datablock = ['']*5

    def send_datablock(self, tag='', callback=None, return_datablock=False):
        """Sends self._datablock to server and resets self._datablock.
        Use wait_reply to block until server replies for your tag.

        >tag: string identifying your datablock.
        >callback: fct(tag, CHLAS_reply) -> None, called upon CHLAS reply.
        Returns: tag, part of it is generated, need for wait_reply().
        """
        if not tag:
            LOG.debug("using tag %i", self._tag_count)
            self._tag_count += 1
            tag = str(self._tag_count)
        datablock = ';'.join(self._datablock)+';'
        self.reset_datablock()
        if callback:
            self._tags_callbacks[tag] = callback
        self.send_msg(datablock+tag)
        return (tag, datablock) if return_datablock else tag

    def send_my_datablock(self, datablock):
        """Sends a raw datablock, so you have to know datablock formatting.
        """
        self.send_msg(datablock)


class ChlasComm(ASCIICommandClient, ChlasProtocol):
    """Class dedicated for client communication with expression server.
    """

    ## possible race: reply received before reading from here.
    def wait_reply(self, tag):
        """Waits for a reply from the server.
        """
        LOG.debug("waiting for completion of tag '%s' (curr. %s)", tag,self.tag)
        ## set blocking
        old_to = self.read_timeout
        self.read_timeout = None
        while self.tag != tag:
            if not self.is_threaded():
                self.read_once()
        LOG.debug("tag '%s' complete (curr. %s)", tag,self.tag)
        self.tag = None
        self.read_timeout = old_to

    def sendDB_waitReply(self, my_datablock='', my_tag='', wait=True):
        """Sends (given or internal) datablock and returns upon reply about it.
        >my_datablock: string without tag, if None use internal datablock
        >my_tag: string
        """
        if my_datablock:
            assert my_tag, "when sending your own datablock, provide a tag"
            self.send_my_datablock(my_datablock+my_tag)
        else:
            my_tag = self.send_datablock(tag=my_tag)
        wait and self.wait_reply(my_tag)


class ChlasCommTh(ThreadedComm, ChlasComm):
    """Class dedicated for threaded client communication with expression server.
    """
    pass
    # def __init__(self, srv_addrPort,
    #              fct_disconnected = None,
    #              fct_connected = None):
    #     """
    #     srv_addrPort: (server_address, port)
    #     connection_succeded_fct: function called on successful connection.
    #     """
    #     super(ChlasCommTh,self).__init__(srv_addrPort,
    #                                      fct_connected,
    #                                      fct_disconnected)
    #     self.on_reply = {}                              ## { tag : callback }

    # def cmd_ACK(self, argline):
    #     super(ChlasCommTh,self).cmd_(argline)
    #     ## unblock 
    #     if tag in self.tags_pending:
    #             self.tags_pending.remove(tag)
    #             self.tag = tag
    #             self.unwait()
    #             while self.tag:                     #XXX: waiters reset self.tag
    #                 time.sleep(.1)
    #     setattr(ChlasCommTh, 'cmd_'+status, cmd_)

    # def handle_connect(self):
    #     """Append thread name and connects."""
    #     super(ChlasCommTh,self).handle_connect()
    #     self.thread.setName(self.thread.getName()+'_CHLAS')

    # ## Mask thread management with user's callbacks and ease encapsulation. See
    # ## also add_handler
    # def on_reply_fct(self, tag, fct):
    #     """Installs a callback on reply from the CHLAS, unsets if fct == None.
    #     """
    #     if not fct:
    #         del self.on_reply[tag]
    #         return
    #     assert fct.func_code.co_argcount == 2, fct.func_name+" shall get 2 args"
    #     self.on_reply[tag] = fct

    # def wait_reply(self, tag):
    #     """Waits for a reply from the server.
    #     """
    #     while self.working:
    #         self.wait(.5)
    #         if self.tag == tag:
    #             break
    #     self.tag = None
    

if __name__ == "__main__":
    raise NotImplementedError("untested, potentially unreliable. Behind you!!!")
