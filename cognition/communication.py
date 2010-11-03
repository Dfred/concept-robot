# communication.py

import threading, logging, time
import comm
    
    
class CommBase(comm.BaseClient):
    
    def __init__(self, params, server='localhost', port= 4242 ):
        self.params = params
        comm.BaseClient.__init__(self, (server, port))
        comm.LOG.setLevel(logging.DEBUG)
        t_client = threading.Thread(target=self.connect_and_run)
        t_client.start()
        self.time_last_gaze = 0
        self.last_ack = None
        self.last_nack = None
        time.sleep(0.1)
        self.set_neck_orientation("(0,0,0)")  # to init communication and set robot on origin
        self.set_gaze(str(params.gaze_pos[0]) + "," + str(params.gaze_pos[1]) + "," + str(params.gaze_pos[2]))


    def cmd_ACK(self, argline):
        self.last_ack = argline
    
    
    def cmd_NACK(self, argline):
        self.last_nack = argline
        
    def cmd_INT(self, argline):
        print argline
        
        
    def handle_notfound(self, cmd, args):
        pass
    
    
    def set_gaze(self, coordinates="0.0, 0.5, 0.0"):
        if (time.time() - self.time_last_gaze) > 0.2:
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
    
