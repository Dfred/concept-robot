#!/usr/bin/python
# -*- coding: utf-8 -*-

# ARAS is an OSS HRI project by Syntheligence available for academic research.
# This copyright covers the Abstract Robotic Animation System, including
# the animation software for the face, eyes, head and other supporting
# algorithms for vision and basic emotions.
# Copyright (C) 2013 Frederic Delaunay and syntheligence.
# For further details, visit http://www.syntheligence.com

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

import cv
try:
    import pyvision as pv
except ImportError, e:
    print("python import error: %s" % e)
    raise ImportError('path to pyvision should be included in PYTHONPATH')
pv.disableCommercialUseWarnings()

from pyvision.face.CascadeDetector import CascadeDetector
from pyvision.face.FilterEyeLocator import FilterEyeLocator
from pyvision.surveillance.VideoStreamProcessor import VideoWriterVSP
#, AVE_LEFT_EYE, AVE_RIGHT_EYE
from pyvision.types.Video import Webcam
from pyvision.types.Point import Point
from pyvision.types.Rect import Rect
from pyvision.edge.canny import canny

from .. import conf, fps

LOG = logging.getLogger(__package__)



class VisionException(Exception):
    """
    """
    pass


class CamGUI(object):
    """
    """
    KEY_ESC = 1048603                           #XXX ESC key (at least on linux)

    def __init__(self, name='Camera'):
        """
        >name: window and application name.
        """
        self.name = name
        self.mirror_image = True
        self.quit_request = None
        cv.NamedWindow(self.name, cv.CV_WINDOW_AUTOSIZE)

    def destroy(self):
        """
        """
        cv.DestroyWindow(self.name)

    def show_frame(self, camFrame, delay = 30):
        """
        >camFrame: pyvision camera frame
        >delay: value in ms.
        Return: None
        """
        ## cv.WaitKey processes GUI events. value in ms.
        if cv.WaitKey(delay) == self.KEY_ESC:
            self.quit_request = True

        pil = camFrame.asAnnotated()                            ## PIL format
        rgb = cv.CreateImageHeader(pil.size, cv.IPL_DEPTH_8U, 3)
        cv.SetData(rgb, pil.tostring())

        frame = cv.CreateImage(cv.GetSize(rgb), cv.IPL_DEPTH_8U,3)
        if frame is None:
            print "error creating openCV frame for gui"
        cv.CvtColor(rgb, frame, cv.CV_RGB2BGR)
        self.mirror_image and cv.Flip(frame, None, 1)
        cv.ShowImage(self.name, frame)

    def add_slider(self, label, min_v, max_v, callback):
        """Adds a slider.
        >label: label for the slider.
        >min_v: minimum value for the slider.
        >max_v: maximum value for the slider.
        >callback: function (bound or not) to be called upon slider change.
        Return: None
        """
        cv.CreateTrackbar(label, self.name, min_v, max_v, callback)


class CamCapture(object):
    """Captures video stream from camera.
    A visualisation of the video stream is also available through the gui.
    """

    def __init__(self, sensor_name=None):
        """
        >sensor_name: if set, calls self.set_camera with that name.
        """
        self.cam_info = None
        self.camera = None
        self.frame = None
        self.gui = None
        self.gui_message = None
        self.fps_counter = None
        self.vid_writer = None
        sensor_name and self.set_camera(sensor_name)

    def set_device(self, dev_index=0, resolution=(800,600)):
        """
        >dev_index: specify camera number for multiple camera configurations.
        >resolution: (width,height) of the frames to grab.
        Return: None
        """
        self.cam_info = {'dev_index':dev_index, 'resolution':resolution}

    def set_camera(self, name):
        """
        >name: identifier of camera as found in conf.
        Raise: conf.ConfigError
        Return: None
        """
        LOG.debug("vision using camera '%s'", name)
        ## Required attributes
        try:
            cam_props = conf.lib_vision[name]
            self.set_device(cam_props['dev_index'], cam_props['resolution'])
        except AttributeError:
            raise conf.ConfigError("Camera '%s' has no definition in your"
                                   " configuration file." % name)
        except KeyError, e:
            raise conf.ConfigError("Camera '%s' has no '%s' property in your"
                                   " configuration file." % (name, e))

    def set_featurePool(self, feature_pool):
        """Attach the feature_pool for further registration of self.AUs .
        Setting None for our origin puts us in polling mode.
        >feature_pool: a dict of { origin : numpy.array }
        Return: None
        """
        self.FP = feature_pool
        self.FP['vision'] = None

    def get_feature(self, origin):
        """Polling mode for the feature Pool.
        Return: numpy.ndarray
        """
        return self.frame.asMatrix3D()

    def acquire_camera(self):
        """Grab the camera for work.
        Raise: VisionException if camera can't be grabbed.
        Return: None
        """
        self.camera = Webcam(self.cam_info['dev_index'], 
                             self.cam_info['resolution'])
        if not self.camera.grab():
            raise VisionException("Can't get camera at device index: %i" %
                                  self.cam_info['dev_index'])

    def update(self):
        """
        """
        assert self.camera, "acquire_camera() required."
        if self.vid_writer and self.frame:
            self.vid_writer.addFrame(self.frame)
        self.frame = self.camera.query()                        # grab ?
        if self.fps_counter:
            self.fps_counter.update()

    def toggle_record(self, enable, filename, fourCodec=None):
        """
        >enable: boolean
        >filename: "full path of record"
        >fourCodec: supported codec, default: 'XVID'
        Return: None
        """
        self.vid_writer = VideoWriterVSP(filename, size=self.camera.size,
                                         fourCC_str=(fourCodec or 'XVID'))

    def toggle_fps(self, enable, every_frames=30*2):
        """
        >enable: boolean
        >every_frames: refresh period in frames
        Return: None
        """
        self.fps_counter = fps.SimpleFPS(every_frames)

    def gui_create(self):
        """
        """
        self.gui = CamGUI()

    def gui_write(self, message):
        """Allow a user message to be displayed
        >message: text string to display
        Return: None
        """
        self.gui_message = message

    def gui_show(self):
        """
        """
        if self.fps_counter:
            self.frame.annotateLabel(Point(), "FPS: %.2f"% self.fps_counter.fps)
        if self.gui_message:
            self.frame.annotateLabel(Point(), self.gui_message)
        self.gui.show_frame(self.frame)

    def gui_loop(self, callback=None, args=None):
        """Loops until self.quit_request is True (triggered with 'ESC' key).
        """
        while not self.gui.quit_request:
            self.update()
            callback and callback(*args)
            self.gui_show()

    def gui_destroy(self):
        """
        """
        self.gui and self.gui.destroy()


class CamUtils(CamCapture):
    """High-level class compiling various image processing algorithms.
    """

    def __init__(self, sensor_name=None):
        ## as CamCapture might call set_camera, init our stuff 1st
        self.XY_factors = None, None
        self.depth_fct = None
        self.face_detector = None
        self.eyes_detector = None
        super(CamUtils,self).__init__(sensor_name)

    def set_depth_fct(self, fct_string):
        """/!\ THIS IS HIGHLY INSECURE: ARBITRARY CODE CAN BE EXECUTED!
        >fct_str: string describing the function
        """
        assert isinstance(fct_string, str)
        ## compile depth_fct
        fct = eval('lambda x:'+fct_string)                  #SEC rework ASAP!
        try:
            fct(10)
        except Exception, e:
            LOG.critical("[conf] error with depth_fct expression: %s",e)
            return
        else:
            self.depth_fct = fct

    def set_XY_factors(self, X, Y):
        """
        """
        self.XY_factors = (X, Y)

    def set_camera(self, name):
        """Overriding to add our properties.
        >name: camera identifier as found in configuration file.
        Raise: conf.ConfigError
        Return: None
        """
        super(CamUtils,self).set_camera(name)

        #TDL create a nice calibration tool to get factors (for 3d info)

        ## Required attributes
        for prop in ('XY_factors', 'depth_fct'):
            try:
                setattr(self,prop,conf.lib_vision[name][prop])
            except KeyError, e:
                raise conf.ConfigErrror("Camera '%s' has no '%s' property in "
                                        "your configuration file." % (name, e))
        assert isinstance(self.XY_factors, tuple) and all(self.XY_factors)
        self.set_depth_fct(self.depth_fct)

    def mark_rects(self, rects, thickness=1, color='blue'):
        """Outlines the given rects in our video stream.
        >rects: absolute Rects.
        >thickness: in pixels.
        >color: string, #rrggbb (in hexa) or color name.
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

    def mark_points(self, points, color='green'):
        """Outlines the given points in our video stream.
        >points: list of Point instances.
        >color: string, #rrggbb or color name.
        Return: None
        """
        for p in points:
            self.frame.annotatePoint(p, color)

    def toggle_face_detection(self, enable, haar_cascade_path=None,
                              msize=(50,50), scale=.5):
        """Toggles face detection algorithms.
        >enable: True or False
        >haar_cascade_path: path to .xml, if None then use default
        >msize: (width,height), minimum size
        >scale: float, image scale
        Return: None
        """
        LOG.debug("%sabling Face Detection", enable and "En" or "Dis")
        if not enable:
            self.face_detector = None
            self.eyes_detector = None
            return
        if not haar_cascade_path:
            try:
                haar_cascade_path = conf.CONFIG['mod_vision']['haar_cascade']
            except (KeyError,TypeError):
                pass
        if not haar_cascade_path:
            from os.path import dirname, join
            haar_cascade_path = join(dirname(__file__),
                                     'haarcascade_frontalface_alt.xml')
        self.face_detector = CascadeDetector(cascade_name=haar_cascade_path,
                                             min_size=msize, image_scale=scale)
        self.eyes_detector = FilterEyeLocator()

    def find_faces(self):
        """Run the face detection algorithm

        Return: list of rects or None
        """
        assert self.face_detector, "toggle_face_detection(True) required"
        return self.face_detector.detect(self.frame)

    def find_eyes(self, faces):
        """Extract the eyes from the list of faces.
         Warning: calling self.update() after find_faces() is not supported!!!

        >faces: absolute rects as returned by find_faces().
        Return: list (of list) of the same length as faces. Each sublist
         contains the rect produced by the face detector and the right and left
         eye coordinates produced by the filters.
        """
        return self.eyes_detector(self.frame, faces)
    
    def get_face_3Dfocus(self, rects):
        """Returns an iterable of gaze vectors (right handeness) from detected
        faces, estimating depth from its width.

        >rects: instances | iterable of pyvision Rects as returned by find_faces

        Poor's man calibration procedure for 'depth_fct' (valid for a specific
        aspect ratio):
        1/ this script gives normalized face's Width, measure distance (meters).
        2/ measure the face Width at different depth levels, i.e. 30cm, 60cm, 1m
        3/ perform a regression on these values, with x=Width and y=Depth.
           You can use this website:
http://people.hofstra.edu/stefan_waner/realworld/newgraph/regressionframes.html
        this will provide a function, e.g. y = 0.249136x^-0.443607
        4/ in conf's lib_vision, set 'depth_fct' with your function as a string,
        e.g. 'depth_fct': '0.249136*x**-0.443607' for the function above
        Return: (gaze_vector, ...)
        """
        assert self.depth_fct, "depth function required, use set_depth_fct"
        assert self.XY_factors, "XY factors required, use set_XY_factors"
        w, h = float(self.camera.size[0]), float(self.camera.size[1])
        fw, fh = self.XY_factors
        if not hasattr(rects, '__iter__'):
            rects = [rects]
        return [( -(r.x/w-.5)*fw, self.depth_fct(r.w/w), -(r.y/h-.5)*fh)
                for r in rects ]

    def get_motions(self):
        """Returns a list of detected motions.
        """
        raise NotImplementedError()
        #MotionDetector().detect()
