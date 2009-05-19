#!/usr/bin/python

import sys

import asyncore
import logging

logging.basicConfig(level=logging.DEBUG)

# import the necessary things for OpenCV
from opencv import cv
from opencv import highgui

import comm

#############################################################################
# definition of some constants

USAGE=sys.argv[0]+" --cascade=\"<cascade_path>\" [filename|camera_index]\n" 

CASCADE_NAME="haarcascade_frontalface_alt.xml"
SERVER_ADDR=("localhost", "/tmp/face")

STORAGE=cv.cvCreateMemStorage(0)
SERVER=None
FACE=None
# Parameters for haar detection
# From the API:
# The default parameters (scale_factor=1.1, min_neighbors=3, flags=0) are tuned 
# for accurate yet slow object detection. For a faster operation on real video 
# images the settings are: 
# scale_factor=1.2, min_neighbors=2, flags=CV_HAAR_DO_CANNY_PRUNING, 
# min_size=<minimum possible face size
min_size = cv.cvSize(20,20)
image_scale = 1# 1.3
haar_scale = 1.2
min_neighbors = 4 # 2
haar_flags = 0#cv.CV_HAAR_DO_CANNY_PRUNING # 0

###############################################################################
# server stuff
class FaceClient(comm.BasicHandler):
    """Remote Connection Handler"""
    # nothing specific to do for the moment, server itself sends the stuff..
    pass

class FDetect(comm.BasicServer):
    """Face detection module - server"""

    def __init__(self, addr_port):
        comm.BasicServer.__init__(self, FaceClient)
        try:
            self.listen_to(addr_port)
        except UserWarning, err:
            print err
            exit(-1)

    def send_values(self, face):
        if face:
            n_x = (face.x+float(face.width)/2)/self.img_w
            n_y = (face.y+float(face.height)/2)/self.img_h
            for cl in self.get_clients():
                cl.send_msg("face %f,%f %i"%(n_x, n_y, face.width+face.height))

#############################################################################
# so, here is the main part of the program

def detect_and_draw(img):
    # new img buffer
    gray = cv.cvCreateImage(cv.cvSize(img.width, img.height), 8, 1)
    # reduce size of data
    small_img = cv.cvCreateImage(cv.cvSize(cv.cvRound(img.width/image_scale),
                                           cv.cvRound(img.height/image_scale)),
                                 8, 1)
    cv.cvCvtColor(img, gray, cv.CV_BGR2GRAY)
    cv.cvResize(gray, small_img, cv.CV_INTER_LINEAR)
    cv.cvEqualizeHist(small_img, small_img)

    cv.cvClearMemStorage(STORAGE)

#    t = cv.cvGetTickCount()
    faces = cv.cvHaarDetectObjects(small_img, cascade, STORAGE, haar_scale,
                                       min_neighbors, haar_flags, min_size)
#    t = cv.cvGetTickCount() - t
#    print "detection time = %gms" % (t/(cv.cvGetTickFrequency()*1000.))
    if faces:
        for r in faces:
            pt1 = cv.cvPoint(int(r.x*image_scale), int(r.y*image_scale))
            pt2 = cv.cvPoint(int((r.x+r.width)*image_scale),
                             int((r.y+r.height)*image_scale))
            cv.cvRectangle(img, pt1, pt2, cv.CV_RGB(255,0,0), 3, 8, 0)
        SERVER.send_values(faces[0])
    highgui.cvShowImage("Camera", img)



if __name__ == '__main__':
    # a small welcome
    print "OpenCV Python wrapper test"
    print "OpenCV version: %s (%d, %d, %d)" % (cv.CV_VERSION,
                                               cv.CV_MAJOR_VERSION,
                                               cv.CV_MINOR_VERSION,
                                               cv.CV_SUBMINOR_VERSION)
    input_name = "0"
    if len(sys.argv) > 1:
        if sys.argv[1].startswith("--cascade="):
            CASCADE_NAME = sys.argv[1][len("--cascade="):]
            if len(sys.argv) > 2:
                input_name = sys.argv[2]
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print USAGE
            sys.exit(-1)
        else:
            input_name = sys.argv[1]

    # create a server object
    SERVER = FDetect(SERVER_ADDR)
    
    # the OpenCV API says this function is obsolete, but we can't
    # cast the output of cvLoad to a HaarClassifierCascade, so use this anyways
    # the size parameter is ignored
    cascade = cv.cvLoadHaarClassifierCascade(CASCADE_NAME, cv.cvSize(1,1))
    if not cascade:
        print "ERROR: Could not load classifier cascade"
        sys.exit(-1)

    capture = input_name.isdigit() and \
        highgui.cvCreateCameraCapture(int(input_name)) or \
        highgui.cvCreateFileCapture(input_name)
    if not capture:
        print "Error opening capture device", device
        sys.exit(-1)
        
    # create window
    highgui.cvNamedWindow('Camera', highgui.CV_WINDOW_AUTOSIZE)
    # move the new window to a better place
    highgui.cvMoveWindow('Camera', 10, 40)

    frame_copy = None
    while True:
        # 1. capture the current image
        frame = highgui.cvQueryFrame(capture)
        if frame is None:       # no image captured... end the processing
            break
        SERVER.img_w, SERVER.img_h = frame.width, frame.height

        if not frame_copy:
            frame_copy = cv.cvCreateImage(cv.cvSize(frame.width,frame.height),
                                          cv.IPL_DEPTH_8U, frame.nChannels)
        if frame.origin == cv.IPL_ORIGIN_TL:
            cv.cvCopy(frame, frame_copy)
        else:
            cv.cvFlip(frame, frame_copy, 0)
        
        detect_and_draw(frame_copy)
        asyncore.loop(0.5, count=1)
        
        key = highgui.cvWaitKey(10)
        if key > 0 and ord(key) == 27: # escape
            break

    SERVER.shutdown()
    highgui.cvDestroyWindow('Camera')
