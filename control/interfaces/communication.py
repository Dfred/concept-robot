# communication.py

import threading, time, socket
import comm, config
    
    
class CommBase(comm.BaseClient):
    
    def __init__(self, server, port):
        self.connected_to_server = False
        comm.BaseClient.__init__(self, (server, port))
        t_client = threading.Thread(target=self.connect_and_run)
        t_client.start()
        self.time_last_gaze = 0
        
        # information blocks
        self.last_ack = None
        self.last_nack = None
        self.lips_info = None
        self.gaze_info = None
        self.face_info = None
        
        time.sleep(0.1)
        try:
            self.set_neck_orientation("(0,0,0)")  # to init communication and set robot on origin
            self.set_gaze(str(config.gaze_pos[0]) + "," + str(config.gaze_pos[1]) + "," + str(config.gaze_pos[2]))
            self.connected_to_server = True
        except socket.error:
            print "Connection error, server %s (port %i) not found" % (server, port)
            self.connected_to_server = False

        
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
        
        
    def handle_notfound(self, cmd, args):
        pass
    
    def set_gaze(self, coordinates="0.0, 0.5, 0.0"):
        if (time.time() - self.time_last_gaze) > config.gaze_timer:
            self.send_msg(";;;;" + coordinates + ";;tag_GAZE")
            self.time_last_gaze = time.time()
            
    def set_neck_orientation(self, orientation = "(0,0,0)", tag = "0"):
        self.send_msg(";;;;;" + orientation + ";tag_NECK_OR_" + tag)
        
    def set_neck_gaze(self, gaze = "0.0, 0.5, 0.0", orientation = "(0,0,0)", tag = "0"):
        if (time.time() - self.time_last_gaze) > config.gaze_timer:
            self.send_msg(";;;;" + gaze + ";" + orientation + ";tag_NECK_GAZE_" + tag)
            #print gaze
            self.time_last_gaze = time.time()
                  
    def set_expression(self, expression = "neutral", mode = "*", intensety = 0.5, tag = "0"):
        self.send_msg(expression + ";" + mode + ";" + str(intensety) + ";;;;tag_EXPRESSION_" + tag)
        
    def get_snapshot(self):
        self.send_msg("get_snapshot")
        time.sleep(0.1)
        return (self.lips_info, self.gaze_info, self.face_info)
        
    def close(self):
        self.disconnect()  
    
