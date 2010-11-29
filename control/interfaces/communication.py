# communication.py

import threading, logging, time, socket
import comm, config
    
    
class CommBase(comm.BaseClient):
    
    def __init__(self):
        self.connected_to_server = False
        #comm.LOG.setLevel(logging.DEBUG)
        comm.BaseClient.__init__(self, (config.server, config.port))
        t_client = threading.Thread(target=self.connect_and_run)
        t_client.start()
        self.time_last_gaze = 0
        self.last_ack = None
        self.last_nack = None
        time.sleep(0.1)
        try:
            self.set_neck_orientation("(0,0,0)")  # to init communication and set robot on origin
            self.set_gaze(str(config.gaze_pos[0]) + "," + str(config.gaze_pos[1]) + "," + str(config.gaze_pos[2]))
            self.connected_to_server = True
        except socket.error:
            print "Connection error, server %s (port %i) not found" % (config.server, config.port)
            self.connected_to_server = False

        
    def cmd_ACK(self, argline):
        self.last_ack = argline
    
    def cmd_NACK(self, argline):
        self.last_nack = argline
        
    def cmd_INT(self, argline):
        print argline
        
        
    def handle_notfound(self, cmd, args):
        pass
    
    
    def set_gaze(self, coordinates="0.0, 0.5, 0.0"):
        if (time.time() - self.time_last_gaze) > 0.03:
            self.send_msg(";;;;" + coordinates + ";;tag_GAZE")
            self.time_last_gaze = time.time()
            

    def set_neck_orientation(self, orientation = "(0,0,0)", tag = "0"):
        self.send_msg(";;;;;" + orientation + ";tag_NECK_OR_" + tag)
        
        
    def set_neck_gaze(self, gaze = "0.0, 0.5, 0.0", orientation = "(0,0,0)", tag = "0"):
        self.send_msg(";;;;" + gaze + ";" + orientation + ";tag_NECK_GAZE_" + tag)
            
            
    def set_expression(self, expression = "neutral", mode = "*", intensety = 0.5, tag = "0"):
        self.send_msg(expression + ";" + mode + ";" + str(intensety) + ";;;;tag_EXPRESSION_" + tag)
          
            
    def close(self):
        self.disconnect()  
    
