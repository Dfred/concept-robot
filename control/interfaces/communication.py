# communication.py

import threading, time
import comm

comm.set_default_logging(True)
LOG = comm.LOG

class Comm(comm.BaseClient):
    """
    """

    CONNECT_TIMEOUT = 3

    def __init__(self, server_addrPort):
        comm.BaseClient.__init__(self, server_addrPort)
        self.set_connect_timeout(self.CONNECT_TIMEOUT)
        self.working = True
        # let's the threaded object manage the socket independently
        self.thread = threading.Thread(target=self.always_connected)
        self.thread.start()

    def handle_connect_error(self, e):
        """See handle_connect_timeout.
        """
        comm.BaseClient.handle_connect_error(self, e)
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
            return comm.BaseClient.send_msg(self, msg)
        LOG.debug("*NOT* sending to %s: '%s'", self.addr_port, msg)


class LightHeadComm(Comm):
    """Class dedicated for communication with lightHead server.
    """
    
    def __init__(self, srv_addrPort):
        """
        """
        Comm.__init__(self, srv_addrPort)
        # information blocks
        self.lips_info = None
        self.gaze_info = None
        self.face_info = None

    def cmd_lips(self, argline):
        self.lips_info = argline
        
    def cmd_gaze(self, argline):
        self.gaze_info = argline
        
    def cmd_face(self, argline):
        self.face_info = argline  

    def get_snapshot(self):
        self.send_msg("get_snapshot")

    def end_snapshot(self):
        return (self.lips_info, self.gaze_info, self.face_info)

class ExpressionComm(Comm):
    """Class dedicated for communication with expression server.
    """

    ST_ACK, ST_NACK, ST_INT, ST_DSC = range(4)

    def __init__(self, srv_addrPort):
        """
        """
        Comm.__init__(self, srv_addrPort)
        self.tag = None
        self.status = None
        self.reset_datablock()

    def cmd_ACK(self, argline):
        self.status = self.ST_ACK
        self.tag = argline.strip()
    
    def cmd_NACK(self, argline):
        self.status = self.ST_NACK
        self.tag = argline.strip()
        
    def cmd_INT(self, argline):
        self.status = self.ST_INT
        self.tag = argline.strip()

    def cmd_DSC(self, argline):
        self.status = self.ST_DSC
        self.tag = None

    def reset_datablock(self):
        """Forgets values previously stored with set_ functions.
        """
        self.datablock = []*4

    def set_fExpression(self, name, intensity=1.0):
        """
        name: facial expression identifier, no colon (:) allowed.
        intensity: normalized gain.
        """
        self.datablock[0] = (name, intensity)

    def set_text(self, text):
        """
        text: text to utter, no double-quotes (") allowed.
        """
        self.datablock[1] = text

    def set_gaze(self, vector3):
        """
        vector3: (x,y,z) : right handedness (ie: with y+ pointing forward)
        """
        self.datablock[2] = str(vector3)[1:-1]

    def set_neck(self, orientation=(), position=()):
        """
        orientation: (x,y,z) : in radians
        position: (x,y,z) : right handedness (ie: with y+ pointing forward)
        """
        self.datablock[2] = (orientation, position)

    def set_instinct(self, command):
        """
        command: you should know what you are doing when dealing with this.
        """
        self.datablock[3] = command

    def set_datablock(self, f_expr, intens, gaze, neck_rot, neck_pos, inst_cmd):
        """
        All-in-one function, check parameters details from specific functions.
        """
        self.datablock = [(f_expr,intens), gaze, (neck_rot,neck_pos), inst_cmd]

    def send_datablock(self, tag='UNUSED'):
        """Sends datablock to server and resets self.datablock.
        You can wait for a reply by checking the value of self.status (None
         until reply is received).
        tag: string identifying your datablock.
        """
        db = '%s:%.3f;"%s";%s;%s;%s;' % datablock
        self.send_msg(db+tag)
        self.reset_datablock()
        self.status = None

    # TODO: support absolute orientation with '((' instead of '('
    def send_neck_gaze(self, gaze='  ', neck=''):
        """Formats and sends a gaze and/or neck packet to expression server.
        Relative Values.
         gaze: 3D vector for focal point
         neck: (3axis orientation, 3axis position) each can be ommitted.
        """
        if neck:
            rot, pos = neck
            neck = (rot and '(%s)' % str(rot)[1:-1] or '') + \
                (pos and '[%s]' % str(pos)[1:-1] or '')
        self.send_msg(";'';%s;%s;;tag_NECK_GAZE" % (str(gaze)[1:-1], neck))

    def send_fExpression(self, expression="neutral", intensity=1):
        self.send_msg("%s:%i;'';;;;tag_FEXPRESSION" % (expression, intensity))
