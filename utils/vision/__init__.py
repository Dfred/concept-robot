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
try:
    import pyvision as pv
except ImportError:
    raise ImportError('path to pyvision should be included in PYTHONPATH')
pv.disableCommercialUseWarnings()

from pyvision.face.CascadeDetector import CascadeDetector
from pyvision.face.FilterEyeLocator import FilterEyeLocator
#, AVE_LEFT_EYE, AVE_RIGHT_EYE
from pyvision.types.Video import Webcam
from pyvision.types.Rect import Rect
from pyvision.edge.canny import canny

from utils import conf, get_logger, Frame, fps

LOG = get_logger(__package__)



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


class CamCapture(object):
    """Captures video stream from camera.
    A visualisation of the video stream is also available through the gui.
    """

    def __init__(self, sensor_name=None):
        """sensor_name: if set, calls self.use_camera with that name.
        """
        self.camera = None
        self.gui = None
        sensor_name and self.use_camera(sensor_name)

    def set_device(self, dev_index=0, resolution=(800,600)):
        """
        dev_index: specify camera number for multiple camera configurations.
        resolution: (width,height) of the frames to grab.
        """
        self.camera = Webcam(dev_index, resolution)
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
        self.cam_props = cam_props

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

    def record(self, filename):
        """
        """
        raise NotImplementedError()
        VideoWriterVSP(filename, size=self.camera.size)

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


class CamUtils(CamCapture):
    """High-level class compiling various image processing algorithms.
    """

    def __init__(self, sensor_name=None):
        super(CamUtils,self).__init__(sensor_name)
        self.XY_factors = None, None

    def use_camera(self, name):
        """Overriding to add our properties.
        """
        super(CamUtils,self).use_camera(name)

        # TODO: create a calibration tool so factors is mandatory (for 3d info)
        for prop in ('XY_factors', 'depth_fct'):
            if self.cam_props.has_key(prop):
                if hasattr(self.camera,prop):
                    LOG.warning("[conf] camera %s: overwriting property '%s'",
                                name, prop)
                setattr(self.camera, prop, self.cam_props[prop])
                LOG.debug("camera %s: setting property %s: %s", name, prop,
                          self.cam_props[prop])
            else:
                LOG.info("[conf] camera %s has no property '%s'", name, prop)

    def mark_rects(self, rects, thickness=1, color='blue'):
        """Outlines the given rects in our video stream.
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

    def mark_points(self, points, color='green'):
        """Outlines the given points in our video stream.
        points: list of Point instances.
        color: string, #rrggbb or color name.
        Return: None
        """
        for p in points:
            self.frame.annotatePoint(p, color)

    def enable_face_detection(self, haar_cascade_path=None,
                              msize=(50,50), scale=.5):
        """Enables face detection algorithms.

        haar_cascade_path: path to .xml, if None then use default
        msize: (width,height), minimum size
        scale: float, image scale
        Returns: None
        """
        if not haar_cascade_path:
            try:
                haar_cascade_path = conf.ROBOT['mod_vision']['haar_cascade']
            except KeyError:
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
        assert self.face_detector, "call to enable_face_detection() required"
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
    
    def get_face_3Dfocus(self, rects):
        """Returns an iterable of gaze vectors (right handeness) from detected
        faces, estimating depth from its width.

        rects: utils.Frame instance (or iterable of).

        Poor's man calibration procedure for 'depth_fct' (valid for a specific
        aspect ratio):
        1/ this script gives normalized face's Width, measure distance (meters).
        2/ perform a regression on these values. You can use this website:
http://people.hofstra.edu/stefan_waner/realworld/newgraph/regressionframes.html
        3/ in conf's lib_vision, set 'depth_fct' with your function as a string.
        """
        assert hasattr(self.camera,'XY_factors'), 'Provide XY_factors in conf.'
        assert hasattr(self.camera,'depth_fct'), 'Provide depth_fct in conf'
        if type(self.camera.depth_fct) == type(''):
            fct = eval('lambda x:'+self.camera.depth_fct)
            try:
                fct(10)
            except StandardError, e:
                LOG.critical("[conf] error with depth_fct expression: %s",e)
                return None
            else:
                self.camera.depth_fct = fct
        w, h = ( float(v) for v in self.camera.size )
        fw, fh = self.camera.XY_factors
        if not hasattr(rects, '__iter__'):
            rects = [rects]
        return [( -(r.x/w-.5)*fw, self.camera.depth_fct(r.w/w), -(r.y/h-.5)*fh )
                for r in rects ]

    def get_motions(self):
        """Returns a list of detected motions.
        """
        raise NotImplementedError()
        #MotionDetector().detect()



if __name__ == "__main__":
    def run(cap):
      import sys
      my_fps = fps.SimpleFPS( 30 * 2 )          # refresh period in frames
      while True:
        cap.update()
        faces = cap.find_faces()
        if faces:
            cap.mark_rects(faces)
            print "W: {0:.6f} note camera-face distance (in meters).".format(
                faces[0].w/float(cap.camera.size[0]))
            try:
                print cap.get_face_3Dfocus(faces)[0][2]
            except AssertionError:
                pass
        cap.gui_show()                          # slashes fps by half...
        my_fps.update()
#        my_fps.show()

    conf.set_name('lightHead')
    conf.load()

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

    import logging
    from utils import comm, conf, LOGFORMATINFO
    logging.basicConfig(level=logging.DEBUG, **LOGFORMATINFO)

    cap = CamUtils('laptop_camera')
#    cap.set_device(resolution=r)
    cap.enable_face_detection()
    cap.gui_create()
    run(cap)
    print "done"
