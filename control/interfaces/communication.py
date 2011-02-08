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
    """
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
        time.sleep(0.1)
        return (self.lips_info, self.gaze_info, self.face_info)


class ExpressionComm(Comm):
    """
    """

    def __init__(self, srv_addrPort):
        """
        """
        Comm.__init__(self, srv_addrPort)
        self.last_ack = None
        self.last_nack = None

    def cmd_ACK(self, argline):
        self.last_ack = argline
    
    def cmd_NACK(self, argline):
        self.last_nack = argline
        
    def cmd_INT(self, argline):
        print argline
        
    # TODO: support absolute orientation with '((' instead of '('
    def set_neck_gaze(self, gaze='  ', neck=''):
        """Formats and sends a gaze and/or neck packet to expression server.
        Relative Values.
         gaze: 3D vector for focal point
         neck: (3axis orientation, 3axis position) each can be None.
        """
        if neck:
            rot, pos = neck
            neck = (rot and '(%s)' % str(rot)[1:-1] or '') + \
                (pos and '[%s]' % str(pos)[1:-1] or '')
        self.send_msg(";;;'';%s;%s;tag_NECK_GAZE" % (str(gaze)[1:-1], neck))

    def set_expression(self, activity='*', expression="neutral", intensity=0):
        self.send_msg("%s;%s;%i;'';;;tag_FEXPRESSION" % (activity,
                                                         expression,
                                                         intensity))
