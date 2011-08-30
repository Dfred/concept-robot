#!/usr/bin/python
# -*- coding: utf-8 -*-

# LightHead programm is a HRI PhD project at the University of Plymouth,
#  a Robotic Animation System including face, eyes, head and other
#  supporting algorithms for vision and basic emotions.
# Copyright (C) 2010 Frederic Delaunay, frederic.delaunay@plymouth.ac.uk

#  This program is free software: you can redistribute it and/or
#   modify it under the terms of the GNU General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   General Public License for more details.

#  You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

#
# Most feature detections are provided by the (very nice) pyvision module.
# For a list of all of them, check: http://pyvision.sourceforge.net/api/
#
import math
import threading
import logging

import numpy

import cv
import pyvision as pv
pv.disableCommercialUseWarnings()

from pyvision.face.CascadeDetector import CascadeDetector
from pyvision.face.FilterEyeLocator import FilterEyeLocator
#, AVE_LEFT_EYE, AVE_RIGHT_EYE
from pyvision.types.Video import Webcam
from pyvision.types.Rect import Rect
from pyvision.edge.canny import canny

from RAS import FeaturePool
from utils import conf, get_logger, Frame, fps

conf.load()
LOG = get_logger(__package__, conf.DEBUG_MODE)            # assume valid config
VIS_CONF = conf.ROBOT['mod_vision']


class VisionException(Exception):
    """
    """
    pass


class CamGUI(object):
    """
    """

    def __init__(self, name='Camera'):
        """
        """
        self.name = name
        self.quit_request = None
        cv.NamedWindow(self.name, cv.CV_WINDOW_AUTOSIZE)

    def destroy(self):
        """
        """
        cv.DestroyWindow(self.name)

    def show_frame(self, camFrame, delay = 30):
        """
        camFrame:
        delay: in ms.
        """
        # cv.WaitKey processes GUI events. value in ms.
        if cv.WaitKey(delay) == 1048603:
            self.quit_request = True

        pil = camFrame.asAnnotated()    # get image with annotations (PIL)
        rgb = cv.CreateImageHeader(pil.size, cv.IPL_DEPTH_8U, 3)
        cv.SetData(rgb, pil.tostring())

        frame = cv.CreateImage(cv.GetSize(rgb), cv.IPL_DEPTH_8U,3)
        if frame is None:
            print "error creating openCV frame for gui"
        cv.CvtColor(rgb, frame, cv.CV_RGB2BGR)
        cv.Flip(frame, None, 1)
        cv.ShowImage(self.name, frame)

    def add_slider(self, label, min_v, max_v, callback):
        """Adds a slider.
        label: label for the slider.
        min_v: minimum value for the slider.
        max_v: maximum value for the slider.
        callback: function (bound or not) to be called upon slider change.
        """
        cv.CreateTrackbar(label, self.name, min_v, max_v, callback)


class Camera(Webcam):
    """Additionaly stores camera specifics.
    """

    def __init__(self, name, dev_index, resolution, tolerance=1):
        Webcam.__init__(self, dev_index, resolution)
        self.factors = None, None, None
        self.tolerance = tolerance
        self.name = name

    def set_tolerance(self, value):
        self.tolerance = value

    def set_factors(self, x, y, z):
        """Set the gain to convert relative coordinates to real coordinates.
        """
        self.factors = x, y, z

    def get_resolution(self):
        """
        Returns: (width,height) of camera frames.
        """
        return self.size

    # TODO: see TODO in CamCapture.use_camera()
    def get_3Dfocus(self, rects):
        """Generates gaze vector, using a Frame's origin and estimating depth
         from its width.
        rects: utils.Frame instance (or iterable of).
        Return: list of the same length as rects.
        """
        assert self.factors[0] != None, 'you must provide camera factors 1st'
        w, h = self.size
        fw, fh, fz = self.factors
        if hasattr(rects, '__iter__'):
            return [( (c.x/w-.5) * fw, (c.y/h-.5) * fh, math.log(r.w/w * fz) )
                    for c in rects ]
        return (rects.x/w-.5) * fw, (rects.y/h-.5)* fh, math.log(rects.w/w * fz)

    def is_within_tolerance(self, x, y):
        """Return True if point is in tolerance frame.
        """
        values = 0, 0, self.size[0]*self.tolerance, self.size[1]*self.tolerance
        return Frame(values).is_within(x,y)


class CamCapture(object):
    """Captures video stream from camera.
    A visualisation of the video stream is also available through the gui.
    """

    def __init__(self):
        """
        """
        self.camera = None
        self.gui = None

    def set_device(self, dev_index=0,resolution=(800,600)):
        """
        dev_index: specify camera number for multiple camera configurations.
        resolution: (width,height) of the frames to grab.
        """
        self.camera = Camera('eye', dev_index, resolution)
        if not self.camera.grab():
            raise VisionException("Can't get camera at device index: %i" %
                                  dev_index)

    def use_camera(self, name):
        """
        name: identifier of camera as found in conf.
        """
        # Required attributes
        try:
            cam_props = conf.lib_vision[name]
            cam_props_req = (cam_props['dev_index'], cam_props['resolution'])
        except AttributeError:
            raise VisionException("Camera '%s' has no definition in your"
                                   " configuration file." % name)
        except KeyError, e:
            raise VisionException("Definition of camera '%s' has no %s property"
                                  " in your configuration file." % (name, e))
        self.set_device(*cam_props_req)
        if cam_props.has_key('tolerance'):
            self.camera.set_tolerance(cam_props['tolerance'])
        else:
            LOG.info("no tolerance configured for camera %s", name)

        # TODO: create a calibration tool so factors is mandatory (for 3d info)
        if cam_props.has_key('factors'):
            self.camera.set_factors(*cam_props['factors'])
        else:
            LOG.info("no factors configured for camera %s", name)

    def set_featurePool(self, feature_pool):
        """Attach the feature_pool for further registration of self.AUs .
        Setting None for our origin puts us in polling mode.
        feature_pool: a dict of { origin : numpy.array }
        """
        self.FP = feature_pool
        self.FP['vision'] = None

    def get_feature(self, origin):
        """Polling mode for the feature Pool.
        Return: numpy.ndarray
        """
        return self.frame.asMatrix3D()

    def update(self):
        """
        """
        self.frame = self.camera.query()        # grab ?

    def mark_rects(self, rects, thickness=1, color='blue'):
        """Outlines the rects given in our video stream.
        rects: absolute Rects.
        thickness: in pixels.
        color: string, #rrggbb (in hexa) or color name.
        Return: None
        """
        args = [color]
        if thickness > 1:
            fct = self.frame.annotateThickRect
            args.append(thickness)
        else:
            fct = self.frame.annotateRect

        for rect in rects:
            fct(rect, *args)

    def gui_create(self):
        """
        """
        self.gui = CamGUI()

    def gui_show(self):
        """
        """
        if self.gui:
            self.gui.show_frame(self.frame)

    def gui_destroy(self):
        """
        """
        if self.gui:
            self.gui.destroy()


class CamFaceFinder(CamCapture):
    """This class detects faces and return them as rects (width, height and pos)
    """

    def __init__(self, haar_cascade_path=None):
        """
        haar_cascade_path: path to .xml, if None then use default
        index: camera device index
        resolution: defaults to (320,240)
        """
        super(CamFaceFinder,self).__init__()
        if not haar_cascade_path:
            haar_cascade_path = VIS_CONF['haar_cascade']
        self.face_detector = CascadeDetector(cascade_name=haar_cascade_path,
                                             min_size=(50,50), image_scale=0.5)
        self.eyes_detector = FilterEyeLocator()

    def find_faces(self):
        """Run the face detection algorithm
        Return: list of rects or None
        """
        return self.face_detector.detect(self.frame)

    def find_eyes(self, faces):
        """Extract the eyes from the list of faces.
         Warning: calling self.update() after find_faces() is not supported!!!

        faces: absolute rects as returned by find_faces().
        Return: list (of list) of the same length as faces. Each sublist
         contains the rect produced by the face detector and the right and left
         eye coordinates produced by the filters.
        """
        return self.eyes_detector(self.frame, faces)
        # eyes = []
        # if hasattr(faces, '__iter__'):
        #     for r in faces:
        #         affine = pv.AffineFromRect(r,(1,1))
        #         eyes.append( (affine.invertPoint(AVE_LEFT_EYE),
        #                       affine.invertPoint(AVE_RIGHT_EYE)) )
        #         return eyes
        # aff = pv.AffineFromRect(faces,(1,1))
        # return aff.invertPoint(AVE_LEFT_EYE), aff.invertPoint(AVE_RIGHT_EYE)



    # def follow_face_with_gaze(self, x, y, width):
    #     """adjust coordinates of detected faces to mask
    #     """
    #     #TODO: change coordinates that are kept in config into something local
    #     if config.slow_adjust and (config.face_x is not None and config.face_y is not None):
    #         config.face_x += (x - config.face_x) * config.gain
    #         config.face_y += (y - config.face_y) * config.gain
    #     else:
    #         config.face_x = x
    #         config.face_y = y

    #     face_distance = ((-88.4832801364568 * math.log(width)) + 538.378262966656)
    #     x_dist = ((config.face_x/1400.6666)*face_distance)/100
    #     y_dist = ((config.face_y/700.6666)*face_distance)/100
    #     if config.camera_on_projector:
    #         return (x_dist, (face_distance/100.0), y_dist)  # x is inverted for compatibility
    #     else:
    #         return (-x_dist, (face_distance/100.0), y_dist)


    # def follow_face_with_neck(self, x, y, face_distance):
    #     """adjust coordinates of detected faces to neck movement
    #     """
    #     move = False
    #     if x > 95 or x < -95: # threshold
    #         distance_x = (x/-640.0) * 0.2 * math.pi
    #         move = True
    #     else:
    #         distance_x = 0.0

    #     if y > 60 or y < -60: # threshold
    #         distance_y = (y/-480.0) * 0.1 * math.pi
    #         move = True
    #     else:
    #         distance_y = 0.0

    #     if face_distance > 1.0:    # threshold for moving forward when perceived face is far
    #         config.getting_closer_to_face = 1.0
    #     if config.getting_closer_to_face > 0.05:
    #         distance_z = 0.1
    #         config.getting_closer_to_face += -0.1
    #         move = True
    #     if face_distance < 0.2:    # threshold for moving back when face is too close
    #         distance_z = -0.3 + face_distance
    #         move = True
    #     else:
    #         distance_z = 0
    #     if move:
    #         return ((distance_y, .0, -distance_x), (.0,distance_z,.0))

#     def follow_ball_with_gaze(self, x, y):
#         """adjust coordinates of detected faces to mask
#         """

#         #face_distance = ((-88.4832801364568 * math.log(width)) + 538.378262966656)
#         face_distance = 50.0
#         x_dist = ((x/1400.6666)*face_distance)/-100
#         y_dist = ((y/1400.6666)*face_distance)/100
# #        if self.comm:
# #            if self.comm.last_ack != "wait":
# #                self.comm.set_gaze(str(x_dist) + "," + str(face_distance/100) + "," + str(y_dist))
# #                self.comm.last_ack = "wait"
#         return str(x_dist) + "," + str(face_distance/100) + "," + str(y_dist)


    # def detect_circle(self, image, image_org):
    #     grayscale = cv.CreateImage(cv.GetSize(image), 8, 1)
    #     grayscale_smooth = cv.CreateImage(cv.GetSize(image), 8, 1)
    #     cv.CvtColor(image, grayscale, cv.CV_BGR2GRAY)
    #     if config.edge_d_non_vision:
    #         cv.Canny(grayscale, grayscale, edge_threshold1, edge_threshold1 * 3, 3)
    #     cv.Smooth(grayscale, grayscale_smooth, cv.CV_GAUSSIAN, edge_threshold3)
    #     mat = cv.CreateMat(100, 1, cv.CV_32FC3 )
    #     cv.SetZero(mat)
    #     cv.HoughCircles(grayscale_smooth, mat, cv.CV_HOUGH_GRADIENT, 2, 50, 200, (edge_threshold2 + 150) )

    #     circles_simple = []
    #     gazing = None
    #     if mat.rows != 0:
    #         for i in xrange(0, mat.rows):
    #             c = mat[i,0]
    #             point = (int(c[0]), int(c[1]))
    #             radius = int(c[2])
    #             cv.Circle(image, point, radius, (0, 0, 255))
    #             if config.detect_colour:
    #                 self.get_colour(image, image_org, [int(c[0]), int(c[1])], radius)
    #                 config.detect_colour = False
    #                 colour = self.record_colour(image, image_org, [int(c[0]), int(c[1])], radius)
    #                 circles_simple.append([point, radius, colour])

    #     if config.follow_ball_gaze and circles_simple:
    #         x_adjust = 320 - circles_simple[0][0].x
    #         y_adjust = 240 - circles_simple[0][0].y
    #         gazing = self.follow_ball_with_gaze(x_adjust, y_adjust)

    #     if config.follow_ball_neck and circles_simple:
    #         #self.comm.send_msg("recognizing;*;1;;;;tag_SPEECH")
    #         x_adjust = 320 - circles_simple[0][0].x
    #         y_adjust = 240 - circles_simple[0][0].y
    #         if x_adjust < 315 or x_adjust > 325:
    #             distance_x = (x_adjust/-640.0) * 0.2 * math.pi
    #         if y_adjust < 235 or y_adjust > 245:
    #             distance_y = (y_adjust/-480.0) * 0.2 * math.pi
    #         if self.comm.last_ack != "wait":
    #             if gazing:
    #                 #                        self.comm.set_neck_gaze(gazing, "(" + str(config.neck_pos[0] + distance_y) + ",0," + str(config.neck_pos[2] + distance_x) + ")", "TRACK_GAZE")
    #                 pass
    #             else:
    #                 self.comm.set_neck_orientation( "(" + str(config.neck_pos[0] + distance_y) + ",0," + str(config.neck_pos[2] + distance_x) + ")", "TRACKING")
    #                 config.neck_pos[2] += distance_x
    #                 config.neck_pos[0] += distance_y
    #                 self.comm.last_ack = "wait"


    #     if config.colour_to_find and circles_simple:
    #         dist = []
    #         for i in circles_simple:
    #             if i[2]:
    #                 #dist.append(auks.calculate_distance_hsv(params.colour_to_find, i[2]))
    #                 dist.append(auks.calculate_distance(config.colour_to_find, i[2]))
    #             else:
    #                 dist.append(999999)
    #         index = auks.posMin(dist)
    #         #print dist
    #         if dist[index] < config.detect_threshold:
    #             #self.comm.send_msg("recognizing;*;1;;;;tag_SPEECH")
    #             cv.Circle(image, circles_simple[index][0], 2, cvScalar(0, 100, 255), 2)
    #             x_adjust = 320 - circles_simple[index][0].x
    #             y_adjust = 240 - circles_simple[index][0].y
    #             if x_adjust < 315 or x_adjust > 325:
    #                 distance_x = (x_adjust/-640.0) * 0.2 * math.pi
    #             if y_adjust < 235 or y_adjust > 245:
    #                 distance_y = (y_adjust/-480.0) * 0.2 * math.pi
    #             if self.comm.last_ack != "wait":
    #                 #                        print "x_dist:", distance_x, " y_dist:", distance_y
    #                 #                        print "x_neck:", str(config.neck_pos[2]), "   y_neck:", str(config.neck_pos[0])
    #                 #                        print "x:", str(config.neck_pos[2] + distance_x), "   y:", str(config.neck_pos[0] + distance_y)
    #                 if gazing:
    #                     #                            self.comm.set_neck_gaze(gazing, "(" + str(config.neck_pos[0] + distance_y) + ",0," + str(config.neck_pos[2] + distance_x) + ")", "TRACK_GAZE")
    #                     pass
    #                 else:
    #                     self.comm.set_neck_orientation( "(" + str(config.neck_pos[0] + distance_y) + ",0," + str(config.neck_pos[2] + distance_x) + ")", "TRACKING")
    #                     config.neck_pos[2] += distance_x
    #                     config.neck_pos[0] += distance_y
    #                     self.comm.last_ack = "wait"

    #     return circles_simple


    # def get_colour(self, image, image_org, pos, radius):
    #     radius = int(radius*0.7)
    #     rect = cv.Rect(pos[0]-radius,pos[1]-radius, radius*2, radius*2)
    #     try:
    #         subimage = cv.GetSubRect(image_org, rect)
    #         cv.SaveImage("subimage.png", subimage)
    #         #cvCvtColor(subimage, subimage, CV_BGR2HSV)  # create hsv version
    #         scalar = cv.Avg(subimage)
    #         #self.current_colour = [int((scalar[0]*2)), int(scalar[1]/255.0*100), int(scalar[2]/255.0*100)]
    #         #print "Average colour value: H:"+ str(int((scalar[0]*2))) + " S:"+ str(int(scalar[1]/255.0*100)) + " V:"+ str(int(scalar[2]/255.0*100))
    #         self.current_colour = [int((scalar[2])), int(scalar[1]), int(scalar[0])]
    #         print "Average colour value: R:"+ str(int((scalar[2]))) + " G:"+ str(int(scalar[1])) + " B:"+ str(int(scalar[0]))

    #     except RuntimeError:
    #         print "error"

    #     cv.Rectangle(image, cv.Point( pos[0]-radius, pos[1]-radius), cv.Point(pos[0]+ radius, pos[1]+radius),cv.CV_RGB(0, 255, 0), 2, 8, 0)


    # def record_colour(self, image, image_org, pos, radius):
    #     radius = int(radius*0.7)
    #     if pos[1] > radius: # only record a square when it is in full camera view
    #         try:
    #             rect = cv.Rect(pos[0]-radius, pos[1]-radius, radius*2, radius*2)
    #             subimage = cv.GetSubRect(image_org, rect)
    #             #cvCvtColor(subimage, subimage, CV_BGR2HSV)  # create hsv version
    #             scalar = cv.Avg(subimage)
    #             #return scalar1, [['c', [['h', int((scalar[0]*2))], ['s', int(scalar[1]/255.0*100)], ['v', int(scalar[2]/255.0*100)]]]]
    #             return [['c', [['r', int((scalar[2]))], ['g', int(scalar[1])], ['b', int(scalar[0])]]]]
    #         except RuntimeError:
    #             print "error", "radius:", radius, "position:", pos
    #             return None
    #     else:
    #         return None



    # def find_colour(self, image, colour):
    #     """ searches for the given colour in the image
    #     colour is in hsv
    #     """
    #     # Create a 8-bit 1-channel image with same size as the frame
    #     color_mask = cv.CreateImage(cv.GetSize(image), 8, 1)
    #     image_h = cv.CreateImage(cv.GetSize(image), 8, 1)

    #     cv.CvtColor(image, image, cv.CV_BGR2HSV)  # convert to hsv

    #     cv.Split(image, image_h, None, None, None)

    #     # Find the pixels within the color-range, and put the output in the color_mask
    #     cv.InRangeS(image_h, cv.Scalar((edge_threshold4*2)-5), cv.Scalar((edge_threshold4*2)+5), color_mask)
    #     cv.CvtColor(image, image, cv.CV_HSV2BGR)  # convert to bgr
    #     cv.Set(image, cv.CV_RGB(0, 255, 0), color_mask)

def run(cap):
    import sys
    my_fps = fps.SimpleFPS()
    while True:
        cap.update()

        # # handle events

            # if key != -1 and key < 256:
            #     key = chr(key)

            # if key == '1' or config.command == '1':
            #     if config.face_d == False:
            #         config.face_d = True

            # if key == '2' or config.command == 'edge':
            #     if config.edge_d == False:
            #         config.edge_d = True
            #         print "detecting edges"

            # if key == '3' or config.command == '3':
            #     if config.save_video == False:
            #         config.save_video = True
            #         print "saving video"

            # if key  == '4' or config.command == '4':
            #     if config.circle_d == False:
            #         config.circle_d = True
            #         print "detecting circles"

            # if key  == '5' or config.command == '5':
            #     if config.edge_d_non_vision == False:
            #         config.edge_d_non_vision = True
            #         print "detecting circles using edge detection"
            #     else:
            #         config.edge_d_non_vision = False

            # if key == 's' or config.command == 's':
            #     if config.show == False:
            #         config.show = True
            #         print "showing video"

            # if key == 'b' or config.command == 'b':
            #     if config.game_coors == "10.0, 50.0, 0.0":
            #         cap.commr.set_gaze("10.0, 50.0, 0.0")
            #         config.game_coors = "0.0, 50.0, 0.0"
            #     else:
            #         cap.commr.set_gaze("0.0, 50.0, 0.0")
            #         config.game_coors = "10.0, 50.0, 0.0"

            # if key == 'e' or config.command == 'e':
            #     config.face_d = False
            #     config.edge_d = False
            #     config.circle_d = False
            #     config.save_video = False
            #     config.colour_s = False
            #     print "stop tracking"

            # if key == 'q' or config.command == 'q':
            #     config.quit = True

            # config.command = '0'

            # if config.face_d:    # face detection
        faces = cap.find_faces()
        cap.mark_rects(faces)

            # if config.colour_s:
            #     cap.find_colour(frame, 10)

            # if config.save_video:    # save
            #     cv.WriteFrame(writer,frame)

            # if config.quit:  # quit
            #     print 'Camera closed'
            #     break

            # if config.circle_d: # circle detection
            #     frame_org = cv.CreateImage(cv.GetSize(frame), cv.IPL_DEPTH_8U,3)      # convert to bgr
            #     cv.Copy(frame, frame_org)
            #     cap.detect_circle(frame, frame_org)

            # if config.edge_d:    # edge detection
            #     frame_org = cv.CreateImage(cv.GetSize(frame), cv.IPL_DEPTH_8U,3)      # convert to bgr
            #     cv.Copy(frame, frame_org)
            #     frame = cap.detect_edge(frame)
        cap.gui_show()
        my_fps.update()
        my_fps.show()


# set default haar cascade file
if VIS_CONF is None:
    VIS_CONF = {}
if not VIS_CONF.has_key('haar_cascade'):
    from os.path import dirname, join
    VIS_CONF['haar_cascade'] = join(dirname(__file__),
                                    'haarcascade_frontalface_alt.xml')


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        try:
            r = int(sys.argv[1]), int(sys.argv[2])
        except Exception, e:
            print sys.argv[0], ': [horiz_resolution] [vert_resolution]'
            print e
            exit(1)
    else:
        r = (640,480)
    cap = CamFaceFinder(resolution=r)
    cap.gui_create()
    run(cap)
    print "done"
