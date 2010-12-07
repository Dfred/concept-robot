import sys
from os import path

def get_RootPath():
    this_path = [ p for p in sys.path if p.endswith("control") \
                      and p.find('control') == p.rfind('control') ][0]
    return path.realpath(this_path+'/../')

ROOT_PATH=get_RootPath()
print 'ROOT_PATH is', ROOT_PATH

# system config
haar_casc = path.realpath(ROOT_PATH+"/HRI/vision/haarcascade_frontalface_alt.xml")
control_options = ["keyboard", "voice_command", "network"]
use_comm_expression = True           # communicate with expression server
use_comm_features = True             # communicate with lightHead server (feature pool)
expression_server = 'localhost'   # server address
expression_port = 4242                # server port
features_server = 'localhost'   # server address
features_port = 4244                # server port
command = '0'

# visual processing
face_d = True
detect_threshold = 35
follow_face_gaze = True
follow_face_neck = False
search_for_face = False
neck_pos = [0.0, 0.0, 0.0]
gaze_pos = [0.0, 0.5, 0.0]
face_x = None
face_y = None
gaze_timer = 0.03
eye_d = False
edge_d = False
edge_d_non_vision = True
circle_d = False
detect_colour = False
colour_to_find = None
colour_s = False
follow_ball_neck = True
follow_ball_gaze = False
check = True
size = False
game_coors = "10.0, 50.0, 0.0"
x_search = -0.5
print_d = False
cam_shift = False
slow_adjust = True
gain = 0.2
idle_go = True

# gui config
use_gui = True
show = True
save_video = False
kalm = False
quit = False


#        if len(sys.argv) > 1:
#            try:
#                self.server, self.port = sys.argv[1].split(':')
#                self.port = int(self.port)
#            except Exception, e:
#                print 'Exception parsing arguments:', e
#                print 'Usage: %s [interface:port]' % sys.argv[0]
#                exit(1)

