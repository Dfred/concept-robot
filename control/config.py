import sys
from os import path

def get_RootPath():
    this_path = [ p for p in sys.path if p.endswith("control") \
                      and p.find('control') == p.rfind('control') ][0]
    return path.realpath(this_path+'/../')

ROOT_PATH=get_RootPath()

# TODO: remove class, use as a singleton
class Params():
    def __init__(self):

        self.haar_casc = path.realpath(ROOT_PATH+"/HRI/vision/haarcascade_frontalface_alt.xml")
        self.use_gui = True
        self.use_comm = True           # communicate with expression server
        self.server = '141.163.186.5'   # server address
        self.port = 4242                # server port
        self.command = '0'
        self.show = True
        self.face_d = True
        self.detect_threshold = 35
        self.follow_face_gaze = True
        self.follow_face_neck = False
        self.search_for_face = False
        self.eye_d = False
        self.edge_d = False
        self.edge_d_non_vision = True
        self.circle_d = False
        self.detect_colour = False
        self.colour_to_find = None
        self.colour_s = False
        self.save_video = False
        self.kalm = False
        self.quit = False
        self.check = True
        self.size = False
        self.game_coors = "10.0, 50.0, 0.0"
        self.x_search = -0.5
        self.print_d = False
        self.cam_shift = False
        self.slow_adjust = True
        self.face_x = None
        self.face_y = None
        self.gain = 0.2
        self.neck_pos = [0.0, 0.0, 0.0]
        self.gaze_pos = [0.0, 0.5, 0.0]
        self.idle_go = True
        self.follow_ball_neck = True
        self.follow_ball_gaze = False

        if len(sys.argv) > 1:
            try:
                self.server, self.port = sys.argv[1].split(':')
                self.port = int(self.port)
            except Exception, e:
                print 'Exception parsing arguments:', e
                print 'Usage: %s [interface:port]' % sys.argv[0]
                exit(1)

