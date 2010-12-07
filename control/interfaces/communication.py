# communication.py

import threading, time, socket
import comm, config

comm.set_default_logging(debug=config.DEBUG)
LOG = comm.LOG

class CommBase(comm.BaseClient):
    
    def __init__(self, server_addrPort):
        self.time_last_gaze = 0
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
        """Callback for sucessful connection"""
        LOG.info("Connected to server %s:%i", 
                 self.target_addr[0], self.target_addr[1])
        try:
            # to init communication and set robot on origin
            self.set_neck_orientation((0,0,0))
            self.set_gaze(config.gaze_pos)
        except socket.error:
            self.handle_disconnect()

    def handle_disconnect(self):
        """Callback for sucessful disconnection"""
        LOG.error("Disconnected from server %s:%i",
                  self.target_addr[0], self.target_addr[1])

    def send_msg(self, msg):
        if self.connected:
            LOG.debug("sending to %s: '%s'", self.target_addr, msg)
            return comm.BaseClient.send_msg(self, msg)
        LOG.debug("*NOT* sending to %s: '%s'", self.target_addr, msg)

    def cmd_ACK(self, argline):
        print argline
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

    def set_neck_gaze(self, gaze='  ', neck=''):
        """Formats and sends a gaze and/or neck packet to expression server."""
        # TODO: remove time check, replace with logic based on reply from expr.
        if (time.time() - self.time_last_gaze) > config.gaze_timer:
            self.send_msg(";;;;%s;%s;tag_NECK_GAZE" % (str(gaze)[1:-1], neck))
            self.time_last_gaze = time.time()

    def set_expression(self, expression="neutral", mode="*", intensity=0):
        self.send_msg("%s;%s;%s;;;;tag_FEXPRESSION" % (expression, mode,
                                                       intensity))

    def get_snapshot(self):
        self.send_msg("get_snapshot")
        time.sleep(0.1)
        return (self.lips_info, self.gaze_info, self.face_info)
