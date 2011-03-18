import sys

from HRI import vision

def overlay_pattern(capture):


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print sys.argv[0], ': camera_device_index x_resolution y_resolution'
        exit(1)
    cap = vision.CamCapture()
    cap.set_device(sys.argv[1], (int(sys.argv[2]),int(sys.argv[3])))
    cap.gui_create()
    while True:
        cap.update()
        overlay_pattern(cap)
        cap.gui_show()
        
    print "done"
