# communication.py

import threading, time, socket
import comm, config

if hasattr(config, 'DEBUG') and config.DEBUG:
    comm.set_default_logging(debug=config.DEBUG)
LOG = comm.LOG

class CommBase(comm.BaseClient):
    
    def __init__(self, server_addrPort):
        comm.BaseClient.__init__(self, server_addrPort)
        self.set_timeout(5)
        threading.Thread(target=self.connect_and_run).start()

        # information blocks
        self.last_ack = None
        self.last_nack = None
        self.lips_info = None
        self.gaze_info = None
        self.face_info = None

    def handle_connect(self):
        """Callback for sucessful connection.
        Inits communication and set robot on origin"""
        if type(self.target_addr) == type(''):
            LOG.info("Connected to server on {0}".format(self.target_addr))
            return
        LOG.info("Connected to server {0[0]}:{0[1]}".format(self.target_addr))

    def handle_disconnect(self):
        """Callback for sucessful disconnection. Info log level."""
        if type(self.target_addr) == type(''):
            LOG.info("Disconnected from {0}".format(self.target_addr))
            return
        LOG.info("Disconnected from {0[0]}:{0[1]}".format(self.target_addr))

    def send_msg(self, msg):
        if self.connected:
#            import pdb; pdb.set_trace()
#            LOG.debug("sending to %s: '%s'", self.target_addr, msg)
            return comm.BaseClient.send_msg(self, msg)
        LOG.debug("*NOT* sending to %s: '%s'", self.target_addr, msg)

    def cmd_ACK(self, argline):
        self.last_ack = argline
    
    def cmd_NACK(self, argline):
        self.last_nack = argline
        
    def cmd_INT(self, argline):
        print argline
        
    def cmd_lips(self, argline):
        self.lips_info = argline
        
    def cmd_gaze(self, argline):
        self.gaze_info = argline
        
    def cmd_face(self, argline):
        self.face_info = argline  

    # TODO: support absolute orientation with '((' instead of '('
    def set_neck_gaze(self, gaze='  ', neck=''):
        """Formats and sends a gaze and/or neck packet to expression server.
        Relative Values.
         gaze: 3D vector for focal point
         neck: (3axis orientation, 3axis position) each can be None.
        """
        if not neck:
            neck = ''
        else:
            neck = (neck[0] and '(%s)' % str(neck[0])[1:-1] or '') + \
                (neck[1] and '[%s]' % str(neck[1])[1:-1] or '')
        try:
            self.send_msg(";;;'';%s;%s;tag_NECK_GAZE" % (str(gaze)[1:-1],
                                                         neck))
        except socket.error:
            self.handle_disconnect()

    def set_expression(self, activity='*', expression="neutral", intensity=0):
        try:
            self.send_msg("%s;%s;%i;'';;;tag_FEXPRESSION" % (activity,
                                                             expression,
                                                             intensity))
        except socket.error:
            self.handle_disconnect()

    def get_snapshot(self):
        self.send_msg("get_snapshot")
        time.sleep(0.1)
        return (self.lips_info, self.gaze_info, self.face_info)
