#!/usr/bin/python

import sys

from HRI import vision


class MyCameraCalib(object):

    target_size = 146

    def __init__(self, capture):
        self.factors = None
        self.cap = capture
        self.min, self.max = 0,0
        self.cap.gui.add_slider('edge_min', 0, 255, self.set_edge_min_th)
        self.cap.gui.add_slider('edge_max', 0, 255, self.set_edge_max_th)
        self.target = None

    def set_target(self, cam_res):
        if cam_res[0] < self.target_size or cam_res[1] < self.target_size:
            raise Exception('resolution too low, change arguments')
        self.target = vision.Rect((cam_res[0] - self.target_size)/2,
                                  (cam_res[1] - self.target_size)/2,
                                  self.target_size, self.target_size)

    def set_edge_min_th(self, val):
        self.min = val

    def set_edge_max_th(self, val):
        self.max = val

    def run(self):
        
        while not self.cap.gui.quit_request:
            self.cap.update()
            if self.check_pattern():
                break
            self.cap.mark_rects([self.target])
            cap.gui_show()
        if self.factors:
            print self.factors

    def check_pattern(self):
        #self.cap.frame = 
        vision.canny(self.cap.frame, self.min, self.max)
        return False


if __name__ == '__main__':

    if len(sys.argv) > 3:
        print sys.argv[0], ': [camera_device_index] [x_res y_res]'
        exit(1)
    dev_index = 0
    if len(sys.argv) > 1:
        dev_index = int(sys.argv[1])
    res = 640,480
    if len(sys.argv) == 3:
        res = int(sys.argv[2]), int(sys.argv[3])

    cap = vision.CamCapture()
    cap.set_device(dev_index, res)
    cap.gui_create()

    app = MyCameraCalib(cap)
    app.set_target(res)
    app.run()

    print "done"
