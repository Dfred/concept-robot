
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys
import cv
import cv2  # should be the same as cv, but includes wrappers for OpenCV 2.x functionality
from layout import Ui_MainWindow
import numpy as np
import pyvision as pv
pv.disableCommercialUseWarnings()
from pyvision.face.CascadeDetector import CascadeDetector,AVE_LEFT_EYE,AVE_RIGHT_EYE
from pyvision.types.Video import Webcam
from pyvision.edge.canny import canny
from PIL import ImageQt
import Image
import time, datetime, Queue
import globals as gl
import cfg, gui


class Vision():
    """ vision class
    """
    def __init__(self, use_gui=False, from_gui_q=None, from_beh_q=None):
        
        self.gui = None
            
        gl.from_gui_q = from_gui_q
        gl.from_beh_q = from_beh_q
        
        self.camera_running = False
        haar_casc = cfg.vis_dir +"/haarcascade_frontalface_alt.xml"     # change path for compatibility
        self.face_detector = CascadeDetector(cascade_name=haar_casc, min_size=(50,50), image_scale=0.5)
        
        #opencv visual processing
        self.old_movement_image = None
        self.prev_frame = None
        self.attention = cv.CreateImage(cfg.cam_resolution[1], 8, 1)    # create attention heatmap
        cv.SetZero(self.attention)
        self.blank = cv.CreateImage(cfg.cam_resolution[1], 8, 1)        # create blank image
        cv.Set(self.blank, 2)
        self.saliency = cv.CreateImage(cfg.cam_resolution[1], 8, 1)     # saliency map
        cv.Set(self.saliency, 255)
        self.hsv_saliency_map = cv.CreateImage( cfg.cam_resolution[1], 8, 3 )
        cv.Set(self.hsv_saliency_map, (0, 255, 255))
        self.motion_history = np.zeros((cfg.cam_resolution[1][1], cfg.cam_resolution[1][0]), np.float32)
        self.hsv = np.zeros((cfg.cam_resolution[1][0], cfg.cam_resolution[1][1], 3), np.uint8)
        self.hsv[:,:,1] = 255
        self.MHI_DURATION = 0.5
        self.DEFAULT_THRESHOLD = 32
        self.MAX_TIME_DELTA = 0.25
        self.MIN_TIME_DELTA = 0.05
        self.hist = None
        self.recorded_histogram = None
        self.robot_target = None    # target that the robot should look at/move to
        self.info = ""
        
        if use_gui:
            app = QApplication(sys.argv)
            self.gui = gui.GUI(parent=self)
            ui = Ui_MainWindow()
            ui.setupUi(self.gui)
            self.gui.layout = ui
            self.gui.set_layout()
            self.gui.show()
            sys.exit(app.exec_())
        

    def start_camera(self):
        """main vision loop
        """
        if not self.camera_running:
            
            self.webcam = Webcam(cfg.cam_resolution[0], cfg.cam_resolution[1])
            
            try:
                self.webcam.query()
                self.camera_running = True
                if self.gui:
                    self.gui.layout.label.show()
                    self.gui.layout.pushButton_2.setText("Stop camera")
            except AttributeError:
                self.publish_message("No camera found, please make sure a camera is connected")

            while self.camera_running:
                im = self.webcam.query()
                
                # handle events
                key = cv.WaitKey(10) &255   # remove higher bits
                if key != -1:
                    key = chr(key)
                    
                if cfg.detect_faces:
                    self.detect_face(im)
                    
                if gl.get_target:
                    cv.Circle(im.asOpenCV(), (gl.attention_point[0], gl.attention_point[1]), 2, (0, 0, 255))
                    if self.gui:
                        self.info += "Target: " + str(gl.attention_point)
                    
                if cfg.detect_edge:
                    im = canny(im, (cfg.canny_threshold1 * 1.0), (cfg.canny_threshold1 * 3.0))
                    self.publish_message("Detecting edges")

#                if self.layout.checkBox_6.isChecked():
#                    self.detect_circle(im)
#                    self.statusBar().showMessage("Detecting circles")        
#
#                if self.layout.checkBox_7.isChecked():
#                    movement_image = self.detect_movement2(im)
#                    image_ipl = cv.GetImage(cv.fromarray(movement_image))
#                    im = pv.Image(image_ipl)
#                    self.statusBar().showMessage("Detecting movement")    
#                    
#                if self.layout.checkBox_11.isChecked():
#                    im = pv.Image(self.set_threshold(im))
#                    self.statusBar().showMessage("Applying threshold") 
#                    
#                if self.layout.checkBox_12.isChecked():
#                    im = pv.Image(self.set_adaptive_threshold(im))
#                    self.statusBar().showMessage("Applying adaptive threshold") 
#                    
#                if self.layout.checkBox_22.isChecked():
#                    im = pv.Image(self.set_colour_threshold(im))
#                    self.statusBar().showMessage("Applying colour threshold") 
#                    
#                if self.layout.checkBox_3.isChecked():
#                    self.detect_corners(im)
#                    self.statusBar().showMessage("Detecting corners")
#                    
#                if self.layout.checkBox_4.isChecked():
#                    self.detect_contours(im)
#                    self.statusBar().showMessage("Detecting contours")
#                    
#                if self.get_colour:
#                    sub_image = cv.GetSubRect(im.asOpenCV(), (gl.attention_point[0], gl.attention_point[1], 30, 30))
#                    scalar = cv.Avg(sub_image)
#                    RGB_data = (int(scalar[2]), int(scalar[1]), int(scalar[0]))
#                    self.info += "RGB: " + str(RGB_data) + "\n"
#                    
#                if self.layout.checkBox_8.isChecked():
#                    self.detect_surf(im)
#                    self.statusBar().showMessage("Extracting SURF")
#                    
#                if self.layout.checkBox_9.isChecked():
#                    self.detect_star(im)
#                    self.statusBar().showMessage("Extracting STAR")
#                    
#                if self.layout.checkBox_16.isChecked():
#                    if self.current_agent == None:
#                        self.statusBar().showMessage("Please select an agent first")
#                    else:
#                        self.statusBar().showMessage("Agent detecting objects")
#                        
#                if self.layout.checkBox_21.isChecked():
#                    im = self.do_DFT(im)
#                    self.statusBar().showMessage("DFT")
#                        
#                if self.layout.checkBox_17.isChecked():
#                    self.update_saliency(im)
#                    self.statusBar().showMessage("Saliency map")
            
            
                # pv.Image(image) # to create a pv image from an opencv image

                if self.gui:
                    pil = im.asAnnotated()                          # get image as PIL with annotations (e.g. from face detection)
                    qimage = ImageQt.ImageQt(pil)                   # convert to Qimage
                    qpixmap = QPixmap.fromImage(qimage)
                    self.gui.layout.label.setPixmap(qpixmap)          # update label pixmap

                if self.gui:
                    fps = self.gui.get_fps()
                    if fps:
                        self.gui.layout.label_16.setText("FPS: " + str(fps))
                    
                # general display of information    
                if self.gui:
                    self.gui.layout.textEdit.setPlainText(self.info)
                self.info = "" #clear info
                
                # have a connected robot follow a target (if there is one)
                self.robot_follow_target()
                self.robot_target = None    # reset target
                                  
                
        if self.camera_running:
            self.webcam = None
            self.camera_running = False
            if self.gui:
                self.gui.layout.label.hide()
                self.gui.layout.pushButton_2.setText("Start camera")
            
            
    def publish_message(self, message):
        if self.gui:
            self.gui.statusBar().showMessage(message)
        else:
            print message
        
        
        
    def detect_face(self, img):
        """ detect faces in the given video stream
        """
        
        human_face = True  # check for human face by comparing histogram
        faces = self.findFaces(img)
        
        if faces:
            close_face_rect = None
            close_face_w = 0.0
            face0 = (faces[0][0].x, faces[0][0].y, faces[0][0].w, faces[0][0].h)
            face_box = (int(face0[0]), int(face0[1]), int(face0[2]), int(face0[3]))
            
            if cfg.histogram_filter: #histogram checking
                sub_image = cv.GetSubRect(img.asOpenCV(), face_box)
                human_face = self.check_histogram(sub_image)
                    
            if human_face:
                
                self.robot_target = face0   # update robot target
                cv.Rectangle(img.asOpenCV(), (int(face0[0]), int(face0[1])), (int(face0[0])+1, int(face0[1])+1), 255, 3)
                
#                if self.layout.checkBox_17.isChecked(): # update saliency map
#                    for i in range(int(face0[0]), int(face0[0]+face0[2])):
#                        for j in range(int(face0[1]), int(face0[1]+face0[3])):
#                            self.saliency[j,i] = np.array([0])
                    #cv.SaveImage("face.png", self.saliency)
                
                for rect, leye, reye in faces:
                    img.annotateRect(rect, color='blue')    # draw square around face
                    if rect.w > close_face_w:               # get closest face coordinates
                        close_face_w = rect.w
                        close_face_rect = rect
                    if True:                             # draw point on eyes and mouth
                        img.annotatePoint(leye,color='blue')
                        img.annotatePoint(reye,color='blue')
                        mid_eye = pv.Point(leye.x + (reye.x-leye.x)/2, (leye.y + reye.y)/2 )
                        img.annotatePoint(mid_eye,color='red')
                        mouth = pv.Point(mid_eye.x, (rect.y + rect.h - rect.h/5)) # 1/5 is an estimation, may differ for different faces
                        img.annotatePoint(mouth,color='red')
            
        self.publish_message(str(len(faces)) + " face(s) detected\n")
                    
                    

################### Robot control ###################


    def robot_follow_target(self):
        """ send commands to have a connected robot follow targets
        """
        
        #no target
        if self.robot_target == None:
            pass
        
        # there is a target
        else:
            
            if gl.from_gui_q:   # there is a connection
                print "here"
                if cfg.gaze_follows_target:
                    tuning = (cfg.gaze_tune_x, cfg.gaze_tune_y,  cfg.neck_tune_x, cfg.neck_tune_y)
                    gl.from_gui_q.put(("face_gaze", self.robot_target, tuning), None)    # make first face available
                if cfg.neck_follows_target:
                    tuning = (cfg.gaze_tune_x, cfg.gaze_tune_y,  cfg.neck_tune_x, cfg.neck_tune_y)
                    gl.from_gui_q.put(("face_neck", self.robot_target, tuning), None)    # make first face available


   
   
############ visual processing ##############################                 
                    
                    
    def findFaces(self, im):
        """ run the face detection algorithm
        """
        rects = self.face_detector.detect(im) 
        faces = []
        for rect in rects:
            affine = pv.AffineFromRect(rect,(1,1))
            leye = affine.invertPoint(AVE_LEFT_EYE)
            reye = affine.invertPoint(AVE_RIGHT_EYE)
            faces.append([rect,leye,reye])

        self.current_faces = faces
        return faces
    
    
    def check_histogram(self, sub_image):
        """ checks if the histogram of a given subimage matches with a recorded histogram
        """
        if self.gui:
            self.show_histogram(sub_image)
        if self.recorded_histogram:
            compare = cv.CompareHist(self.hist, self.recorded_histogram, cv.CV_COMP_CORREL)
            self.info += "\n Histogram similarity: \n" + str(round(compare, 2)) + "\n\n"
            if compare > (self.layout.horizontalSlider_10.value()/100.0):
                return True
            else:
                return False
        else:
            self.info += "\n No histogram to match with recorded \n\n"
            return True
    
    
    def show_histogram(self, sub_image):
        self.hist = cv.CreateHist([180], cv.CV_HIST_ARRAY, [(0,180)], 1 )
        # Convert to HSV and keep the hue
        hsv = cv.CreateImage(cv.GetSize(sub_image), 8, 3)
        cv.CvtColor(sub_image, hsv, cv.CV_BGR2HSV)
        hue = cv.CreateImage(cv.GetSize(sub_image), 8, 1)
        cv.Split(hsv, hue, None, None, None)
        cv.CalcArrHist( [hue], self.hist, 0)
        
        hist_image = self.hue_histogram_as_image(self.hist)
        qimage = rgb2qimage(np.asarray(cv.GetMat(hist_image)))  # convert iplimage to qimage via numpy array
        qpixmap = QPixmap.fromImage(qimage)
        self.gui.layout.label_21.setPixmap(qpixmap)          # update label pixmap
        
#        if self.recorded_histogram:
#            compare = cv.CompareHist(self.hist, self.recorded_histogram, cv.CV_COMP_CORREL)
#            self.info += "\n Histogram similarity: \n" + str(compare) + "\n\n"
        
        
    def rec_histogram(self):
        if self.layout.checkBox_25.isChecked() or self.layout.checkBox_26.isChecked():
            self.recorded_histogram = self.hist
            hist_image = self.hue_histogram_as_image(self.recorded_histogram)
            self.layout.checkBox_24.setChecked(2) 
        else:
            self.statusBar().showMessage("Please select histogram first")
            
            
    def save_histogram(self):
        if self.recorded_histogram is not None:
            #cv.Save("target_histogram.his", self.recorded_histogram)
            filehandler = open("target_histogram.his", 'w')
            numpy_array = np.asarray(self.recorded_histogram.bins)
            #pickle.dump(self.recorded_histogram.bins.tostring(), filehandler)
            np.save('target_histogram.npy', numpy_array)

            
            
    def load_histogram(self):
        #filehandler = open("target_histogram.his", 'r')
        filehandler = QFileDialog.getOpenFileName(self, 'Open file', "Image Files (*.npy)")
        data2 = np.load(str(filehandler))
        if data2.any():
            #temp_array = pickle.load(filehandler)
            new_hist = cv.CreateHist([180], cv.CV_HIST_ARRAY, [(0,180)], 1 )
            #new_hist.bins = cv.fromarray(data2, True)
            cv.CalcHist(cv.fromarray(data2, True), new_hist)
            self.recorded_histogram = new_hist
            qimage = rgb2qimage(np.asarray(cv.GetMat(hist_image)))  # convert iplimage to qimage via numpy array
            qpixmap = QPixmap.fromImage(qimage)
            self.layout.label_21.setPixmap(qpixmap)          # update label pixmap
            
            
    def clear_hist(self):
        self.recorded_histogram = None
        self.layout.checkBox_24.setChecked(0)
        
         
    def hue_histogram_as_image(self, hist):
        """ Returns a nice representation of a hue histogram """

        histimg_hsv = cv.CreateImage( (180,140), 8, 3)
        
        mybins = cv.CloneMatND(hist.bins)
        cv.Log(mybins, mybins)
        (_, hi, _, _) = cv.MinMaxLoc(mybins)
        cv.ConvertScale(mybins, mybins, 255. / hi)

        w,h = cv.GetSize(histimg_hsv)
        hdims = cv.GetDims(mybins)[0]
        for x in range(w):
            xh = (180 * x) / (w - 1)  # hue sweeps from 0-180 across the image
            val = int(mybins[int(hdims * x / w)] * h / 255)
            cv.Rectangle( histimg_hsv, (x, 0), (x, h-val), (xh,255,64), -1)
            cv.Rectangle( histimg_hsv, (x, h-val), (x, h), (xh,255,255), -1)

        histimg = cv.CreateImage( (180,140), 8, 3)
        cv.CvtColor(histimg_hsv, histimg, cv.CV_HSV2BGR)
        return histimg
    
    
    def set_threshold(self, im):
        im_threshold = cv.CreateImage( cfg.cam_resolution[1], 8, 1 )
        cv.Threshold(im.asOpenCVBW(), im_threshold, ( self.layout.horizontalSlider_4.value()/100.0)*255, 255, cv.CV_THRESH_BINARY_INV)
        if self.layout.checkBox_13.isChecked():
            
            box, pca = self.get_bounding_rect(im_threshold)
            #box = cv.BoundingRect(mat)    #opencv function BoundingRect seems to cause a memory leak
            if box:
                (x, y, w, h) = box
                cv.Rectangle(im.asOpenCV(), (int(x), int(y)), (int(x+w), int(y+h)), 255)
                self.info += "BoundingBox\n x: " + str(x) + "\n y: " + str(y) + "\n w: " + str(w) + "\n h: " + str(h) + "\n"
                if self.current_object_name:
                    cv.PutText(im.asOpenCV(), self.current_object_name, (int(x+w), int(y+h)), cv.InitFont(cv.CV_FONT_HERSHEY_PLAIN, 1.0, 1.0) , 255)
            
                if self.layout.checkBox_14.isChecked():
                    if box[2]>0:    # bit of a hack
                        sub_image = cv.GetSubRect(im.asOpenCV(), box)
                        scalar, sd_rgb = cv.AvgSdv(sub_image)
                        RGB_data = (int(scalar[2]), int(scalar[1]), int(scalar[0]))
                        self.info += "\n RGB: \n" + str(RGB_data) + " -- SD:" + str( round(sum(sd_rgb)/len(sd_rgb))) + "\n"
                        
                        hsv_copy = cv.CreateImage( cv.GetSize(sub_image), cv.IPL_DEPTH_8U, 3 )
                        cv.Copy(sub_image, hsv_copy)    # copy otherwise sub_image is modified on conversion
                        cv.CvtColor(hsv_copy, hsv_copy, cv.CV_BGR2HSV)  # create hsv version
                        scalar, sd_hsv = cv.AvgSdv(sub_image)
                        self.info += "\n HSV: \n" + "("+ str(int((scalar[0]*2))) + "," + str(int(scalar[1]/255.0*100)) + "," + str(int(scalar[2]/255.0*100)) + ") -- Hue SD: " + str(round(sd_hsv[0])) + "\n\n"
                        
                        self.current_sensory_input = [RGB_data[0]/255.0, RGB_data[1]/255.0, RGB_data[2]/255.0, round(sum(sd_rgb)/len(sd_rgb))/255.0, (scalar[0]*2)/360.0, round(sd_hsv[0])/360.0, pca/550.0 ]
                        self.layout.textEdit_3.setPlainText(str([round(x, 2) for x in self.current_sensory_input]))
                
                    if self.layout.checkBox_20.isChecked():
                        sub_image = cv.GetSubRect(im.asOpenCVBW(), box)
                        #im = cv.LoadImage( "test.jpg", cv.CV_LOAD_IMAGE_GRAYSCALE)
                        realInput = cv.CreateImage( cv.GetSize(sub_image), cv.IPL_DEPTH_64F, 1)
                        imaginaryInput = cv.CreateImage( cv.GetSize(sub_image), cv.IPL_DEPTH_64F, 1)
                        complexInput = cv.CreateImage( cv.GetSize(sub_image), cv.IPL_DEPTH_64F, 2)
                    
                        cv.Scale(sub_image, realInput, 1.0, 0.0)
                        cv.Zero(imaginaryInput)
                        cv.Merge(realInput, imaginaryInput, None, None, complexInput)
                    
                        dft_M = cv.GetOptimalDFTSize( sub_image.height - 1 )
                        dft_N = cv.GetOptimalDFTSize( sub_image.width - 1 )
                    
                        dft_A = cv.CreateMat( dft_M, dft_N, cv.CV_64FC2 )
                        image_Re = cv.CreateImage( (dft_N, dft_M), cv.IPL_DEPTH_64F, 1)
                        image_Im = cv.CreateImage( (dft_N, dft_M), cv.IPL_DEPTH_64F, 1)
                    
                        # copy A to dft_A and pad dft_A with zeros
                        tmp = cv.GetSubRect( dft_A, (0,0, sub_image.width, sub_image.height))
                        cv.Copy( complexInput, tmp, None )
                        if(dft_A.width > sub_image.width):
                            tmp = cv.GetSubRect( dft_A, (sub_image.width,0, dft_N - sub_image.width, sub_image.height))
                            cv.Zero( tmp )
                    
                        # no need to pad bottom part of dft_A with zeros because of
                        # use nonzero_rows parameter in cv.FT() call below
                    
                        cv.DFT( dft_A, dft_A, cv.CV_DXT_FORWARD, complexInput.height )
                    
                        # Split Fourier in real and imaginary parts
                        cv.Split( dft_A, image_Re, image_Im, None, None )
                    
                        # Compute the magnitude of the spectrum Mag = sqrt(Re^2 + Im^2)
                        cv.Pow( image_Re, image_Re, 2.0)
                        cv.Pow( image_Im, image_Im, 2.0)
                        cv.Add( image_Re, image_Im, image_Re, None)
                        cv.Pow( image_Re, image_Re, 0.5 )
                    
                        # Compute log(1 + Mag)
                        cv.AddS( image_Re, cv.ScalarAll(1.0), image_Re, None ) # 1 + Mag
                        cv.Log( image_Re, image_Re ) # log(1 + Mag)
                    
                    
                        # Rearrange the quadrants of Fourier image so that the origin is at
                        # the image center
                        cvShiftDFT( image_Re, image_Re )
                    
                        min, max, pt1, pt2 = cv.MinMaxLoc(image_Re)
                        cv.Scale(image_Re, image_Re, 1.0/(max-min), 1.0*(-min)/(max-min))
                        test = cv.CreateImage( cv.GetSize(image_Re), cv.IPL_DEPTH_8U, 1)
                        cv.ConvertScale(image_Re, test, 255./1.)
                        #cv.SaveImage("mag_test.png", test)
                        

                    
                    else:
                        self.info += "\n no box\n"
                
            if pca:
                self.info += "\n PCA1: \n" + str(round(pca)) + "\n\n"
                
        return im.asOpenCV()
    
    
    def get_bounding_rect(self, im):
        a = np.asarray(cv.GetMat(im))
        values = np.argwhere(a==255)
        if len(values):
            pca1_diff = None
            if  self.layout.checkBox_15.isChecked():
                #pca = mdp.pca(values.astype(float) )
                #pca1 = pca[:,0]
                #pca1_diff = abs(np.max(pca1) -np.min(pca1))
                pca1_diff = 0
            y_array = values[:,0]
            x_array = values[:,1]
        
            min_x = np.min(x_array)
            max_x = np.max(x_array)
            min_y = np.min(y_array)
            max_y = np.max(y_array)
            return (min_x, min_y, abs(max_x-min_x), abs(max_y-min_y)), pca1_diff
        else:
            return None, None

    
    
    def set_adaptive_threshold(self, im):
        thresh_image = cv.CreateImage( cfg.cam_resolution[1], 8, 1 )
        cv.AdaptiveThreshold(im.asOpenCVBW(), thresh_image, (self.layout.horizontalSlider_5.value()/100.0)*255)
        return thresh_image
    
    
    def set_colour_threshold(self, im):
        hsv_copy = cv.CreateImage( cv.GetSize(im.asOpenCV()), cv.IPL_DEPTH_8U, 3 )
        dest = cv.CreateImage( cv.GetSize(im.asOpenCV()), cv.IPL_DEPTH_8U, 1 )
        cv.Copy(im.asOpenCV(), hsv_copy)                # copy otherwise sub_image is modified on conversion
        cv.CvtColor(hsv_copy, hsv_copy, cv.CV_BGR2HSV)  # create hsv version
        hue = 180*(self.layout.horizontalSlider_6.value()/99.0)
        self.info += "\n Hue: + " + str(hue) + "\n\n"
        expansion = self.layout.horizontalSlider_9.value()

        cv.InRangeS(hsv_copy, (hue-expansion, 50, 50), (hue+expansion, 255, 255), dest)
        cv.CvtColor(dest, hsv_copy, cv.CV_GRAY2RGB)  # create hsv version
        cv.AddWeighted(hsv_copy, .5, im.asOpenCV(), .5, 1.0, im.asOpenCV())    # show saliency map as overlay
        return im.asOpenCV()
    
    
    def detect_circle(self, image):
        im_opencv = image.asOpenCV()
        grayscale = cv.CreateImage(cfg.cam_resolution[1], 8, 1)
        grayscale_smooth = cv.CreateImage(cfg.cam_resolution[1], 8, 1)
        cv.CvtColor(im_opencv, grayscale, cv.CV_BGR2GRAY)
        cv.Smooth(grayscale, grayscale_smooth, cv.CV_GAUSSIAN, 11)
        mat = cv.CreateMat(100, 1, cv.CV_32FC3 )
        cv.SetZero(mat)
        cv.HoughCircles(grayscale_smooth, mat, cv.CV_HOUGH_GRADIENT, 2, 50, 200, (self.layout.horizontalSlider_2.value() + 150) )
        if mat.rows != 0:
            for i in xrange(0, mat.rows):
                c = mat[i,0]
                point = (int(c[0]), int(c[1]))
                radius = int(c[2])
                cv.Circle(im_opencv, point, radius, (0, 0, 255))
        self.info += str(mat.rows) + " circle(s) detected\n"
                
                
    def detect_movement(self, im):
        im_opencv = im.asOpenCVBW()         # open image as opencv BW
        dst = cv.CreateImage(cfg.cam_resolution[1], 8, 1)
        if self.old_movement_image:
            cv.Sub(im_opencv, self.old_movement_image, dst) # subtract image from previous image
        self.old_movement_image = im_opencv
        
        im_threshold = cv.CreateImage(cfg.cam_resolution[1], 8, 1)
        cv.Threshold(dst, im_threshold, (self.layout.horizontalSlider_3.value() + 150), 255, cv.CV_THRESH_BINARY)
        #cv.SaveImage("test.png", im_threshold)
        #box = cv.BoundingRect(cv.GetMat(im_threshold))
        #(x, y, w, h) = box
        #cv.Rectangle(dst, (int(x), int(y)), (int(x+w), int(y+h)), 255, cv.CV_FILLED)

        
        if self.counter > 20: # onlys start adding after 50 cycles -> magic number
            cv.ScaleAdd(im_threshold, .5, self.attention, self.attention)          # add movement to attention
            cv.Sub(self.attention, self.blank, self.attention)                     # substract fixed value to have attention fade
            
            
        (minVal, maxVal, minLoc, maxLoc) = cv.MinMaxLoc(self.attention)
        if (maxVal > 50 and (maxLoc != (0,0))):   # bit of a hack to counter weird behaviour of cv.MinMaxLoc
            #cv.Circle(self.attention, maxLoc, 2, 255) 
            if gl.from_gui_q:
                gl.from_gui_q.put(("motion", maxLoc), False)    # make first face available
            
        self.counter += 1
        
#        size = cv.GetSize(im_opencv)
#        width = size[0]/5.0
#        height = size[1]/5.0
#        activation = 0
#        act_coors = [0,0]
#        movement = False
#        for i in range(0, 5):
#            for j in range(0, 5):
#                sub_image = cv.GetSubRect(dst, (int(i * width), int(j * height), int(width), int(height)))
#                scalar = cv.Avg(sub_image)
#                total = sum(scalar)
#                if total > activation and total > (self.layout.horizontalSlider_3.value()/2.0):
#                    activation = total
#                    act_coors = [i, j]
#                    movement = True
#        if movement:
#            cv.Circle(dst, (int(act_coors[0]*width + 0.5*width), int(act_coors[1]*height + 0.5*height)), 50, (255, 255, 255))   # draw in the original image
        return self.attention
        #return dst
                
                
    def detect_movement2(self, im):
        """ 2nd function to detect movement, based on OpenCV motempl.py example
        """
        if self.layout.checkBox_18.isChecked():
            pass
        
        if self.prev_frame == None:
            self.prev_frame = np.asarray(cv.GetMat(im.asOpenCV()))
        frame_diff = cv2.absdiff(np.asarray(cv.GetMat(im.asOpenCV())), self.prev_frame)
        gray_diff = cv2.cvtColor(frame_diff, cv2.COLOR_BGR2GRAY)
        ret, motion_mask = cv2.threshold(gray_diff, (self.layout.horizontalSlider_3.value()), 1, cv2.THRESH_BINARY)
        timestamp = cv2.getTickCount() / cv2.getTickFrequency()
        cv2.updateMotionHistory(motion_mask, self.motion_history, timestamp, self.MHI_DURATION)
        mg_mask, mg_orient = cv2.calcMotionGradient( self.motion_history, self.MAX_TIME_DELTA, self.MIN_TIME_DELTA, apertureSize=5 )
        seg_mask, seg_bounds = cv2.segmentMotion(self.motion_history, timestamp, self.MAX_TIME_DELTA)
        
        visual_name = 'frame_diff'
        if visual_name == 'input':
            vis = im.asMatrix3D().copy()
        elif visual_name == 'frame_diff':
            vis = frame_diff.copy()
        elif visual_name == 'motion_hist':
            vis = np.uint8(np.clip((self.motion_history-(timestamp-self.MHI_DURATION)) / self.MHI_DURATION, 0, 1)*255)
            vis = cv2.cvtColor(vis, cv2.COLOR_GRAY2BGR)
        elif visual_name == 'grad_orient':
            self.hsv[:,:,0] = mg_orient/2
            self.hsv[:,:,2] = mg_mask*255
            vis = cv2.cvtColor(self.hsv, cv2.COLOR_HSV2BGR)

        for i, rect in enumerate([(0, 0, cfg.cam_resolution[1][0], cfg.cam_resolution[1][1])] + list(seg_bounds)):
            x, y, rw, rh = rect
            area = rw*rh
            if area < 64**2:
                continue
            silh_roi   = motion_mask   [y:y+rh,x:x+rw]
            orient_roi = mg_orient     [y:y+rh,x:x+rw]
            mask_roi   = mg_mask       [y:y+rh,x:x+rw]
            mhi_roi    = self.motion_history[y:y+rh,x:x+rw]
            if cv2.norm(silh_roi, cv2.NORM_L1) < area*0.05:
                continue
            
            histogram_match = True
            if self.layout.checkBox_26.isChecked(): #histogram checking
                sub_image = cv.GetSubRect(im.asOpenCV(), (x, y, rw, rh))
                histogram_match = self.check_histogram(sub_image)
              
            if histogram_match:  
                angle = cv2.calcGlobalOrientation(orient_roi, mask_roi, mhi_roi, timestamp, self.MHI_DURATION)
                color = ((255, 0, 0), (0, 0, 255))[i == 0]
                self.draw_motion_comp(vis, rect, angle, color)
                
                self.robot_target = (rect)   # update robot target
        
        self.prev_frame = np.asarray(cv.GetMat(im.asOpenCV()))
        return vis
        
        
    def draw_motion_comp(self, vis, (x, y, w, h), angle, color):
        """ helper function for detect_movement2
        """
        cv2.rectangle(vis, (x, y), (x+w, y+h), (0, 255, 0))
        # code below is to draw direction and angle of the movement
        if self.layout.checkBox_19.isChecked():
            r = min(w/2, h/2)
            cx, cy = x+w/2, y+h/2
            angle = angle*np.pi/180
            cv2.circle(vis, (cx, cy), r, color, 3)
            cv2.line(vis, (cx, cy), (int(cx+np.cos(angle)*r), int(cy+np.sin(angle)*r)), color, 3)
    
    
    
    def detect_corners(self, im):
        im_opencv = im.asOpenCVBW()         # open image as opencv BW
        im_mat = cv.GetMat(im_opencv)       # open as opencv mat
        eig_image = cv.CreateMat(im_mat.rows, im_mat.cols, cv.CV_32FC1)
        temp_image = cv.CreateMat(im_mat.rows, im_mat.cols, cv.CV_32FC1)
        good_features = cv.GoodFeaturesToTrack(im_mat, eig_image, temp_image, 10, 0.04, 1.0, useHarris = False)
        for i in good_features:
            cv.Circle(im.asOpenCV(), (int(i[0]), int(i[1])), 20, (0, 0, 255))   # draw in the original image
            if self.layout.checkBox_17.isChecked(): # update saliency map
                self.saliency[int(i[1]), int(i[0])] = np.array([0])   # x,y seems to be inverted
            
            
    def detect_contours(self, image):
        #im_opencv = image.asOpenCVBW()         # open image as opencv BW
        if not self.layout.checkBox_10.isChecked():
            thresh_image = canny(image, (self.layout.horizontalSlider.value() * 1.0), (self.layout.horizontalSlider.value() * 3.0))
            thresh_image = thresh_image.asOpenCVBW()
        else:
            thresh_image = cv.CreateImage(cfg.cam_resolution[1], 8, 1)
            cv.Threshold(image.asOpenCVBW(), thresh_image, ( self.layout.horizontalSlider_4.value()/100.0)*255, 255, cv.CV_THRESH_BINARY_INV)
        storage = cv.CreateMemStorage(0)
        #cv.SaveImage("test.png", im_threshold)
    
        # find the contours
        contours = cv.FindContours(thresh_image, storage, cv.CV_RETR_LIST, cv.CV_CHAIN_APPROX_NONE, (0,0))
        cv.DrawContours(image.asOpenCV(), contours, (0, 0, 255, 0), (0, 255, 0, 0), 3, 0, cv.CV_AA, (0, 0))
    
        for i in contours:
            self.info += "contour: " + str(i) + "\n"
        return contours
    

    def detect_surf(self, im):
        (keypoints, descriptors) = cv.ExtractSURF(im.asOpenCVBW(), None, cv.CreateMemStorage(), (0, 30000, 3, 1))
        for ((x, y), laplacian, size, dir, hessian) in keypoints:
            cv.Circle(im.asOpenCV(), (int(x), int(y)), 20, (0, 0, 255))
            if self.layout.checkBox_17.isChecked(): # update saliency map
                self.saliency[x, y] = np.array([255])
            
            
    def detect_star(self, im):
        keypoints = cv.GetStarKeypoints(im.asOpenCVBW(), cv.CreateMemStorage(), (128,100,100,10,4))
        for ((x, y), size, response) in keypoints:
            cv.Circle(im.asOpenCV(), (int(x), int(y)), size, (0, 0, 255))
            
            
            
    def do_DFT(self, im):
        sub_image = im.asOpenCVBW()
        realInput = cv.CreateImage( cv.GetSize(sub_image), cv.IPL_DEPTH_64F, 1)
        imaginaryInput = cv.CreateImage( cv.GetSize(sub_image), cv.IPL_DEPTH_64F, 1)
        complexInput = cv.CreateImage( cv.GetSize(sub_image), cv.IPL_DEPTH_64F, 2)
    
        cv.Scale(sub_image, realInput, 1.0, 0.0)
        cv.Zero(imaginaryInput)
        cv.Merge(realInput, imaginaryInput, None, None, complexInput)
    
        dft_M = cv.GetOptimalDFTSize( sub_image.height - 1 )
        dft_N = cv.GetOptimalDFTSize( sub_image.width - 1 )
    
        dft_A = cv.CreateMat( dft_M, dft_N, cv.CV_64FC2 )
        image_Re = cv.CreateImage( (dft_N, dft_M), cv.IPL_DEPTH_64F, 1)
        image_Im = cv.CreateImage( (dft_N, dft_M), cv.IPL_DEPTH_64F, 1)
    
        # copy A to dft_A and pad dft_A with zeros
        tmp = cv.GetSubRect( dft_A, (0,0, sub_image.width, sub_image.height))
        cv.Copy( complexInput, tmp, None )
        if(dft_A.width > sub_image.width):
            tmp = cv.GetSubRect( dft_A, (sub_image.width,0, dft_N - sub_image.width, sub_image.height))
            cv.Zero( tmp )
    
        # no need to pad bottom part of dft_A with zeros because of
        # use nonzero_rows parameter in cv.FT() call below
    
        cv.DFT( dft_A, dft_A, cv.CV_DXT_FORWARD, complexInput.height )
    
        # Split Fourier in real and imaginary parts
        cv.Split( dft_A, image_Re, image_Im, None, None )
    
        # Compute the magnitude of the spectrum Mag = sqrt(Re^2 + Im^2)
        cv.Pow( image_Re, image_Re, 2.0)
        cv.Pow( image_Im, image_Im, 2.0)
        cv.Add( image_Re, image_Im, image_Re, None)
        cv.Pow( image_Re, image_Re, 0.5 )
    
        # Compute log(1 + Mag)
        cv.AddS( image_Re, cv.ScalarAll(1.0), image_Re, None ) # 1 + Mag
        cv.Log( image_Re, image_Re ) # log(1 + Mag)
    
    
        # Rearrange the quadrants of Fourier image so that the origin is at
        # the image center
        cvShiftDFT( image_Re, image_Re )
    
        min, max, pt1, pt2 = cv.MinMaxLoc(image_Re)
        cv.Scale(image_Re, image_Re, 1.0/(max-min), 1.0*(-min)/(max-min))
        test = cv.CreateImage( cv.GetSize(image_Re), cv.IPL_DEPTH_8U, 1)
        cv.ConvertScale(image_Re, test, 255./1.)
        return pv.Image(test)
            
            
    def update_saliency(self, im):
        
        cv.Add(self.saliency, self.blank, self.saliency)                          # add fixed value to have saliency fade
        #cv.SaveImage("saliency1.png", self.saliency)
        saliency_copy = cv.CreateImage( cfg.cam_resolution[1], 8, 1 )
        cv.Copy(self.saliency, saliency_copy)    
        cv.Div(saliency_copy, self.blank, saliency_copy, 1.0)   # devide saliency by 2 to account for hsv compatibility
        cv.MixChannels([saliency_copy], [self.hsv_saliency_map], [(0,0)])

        bgr_copy = cv.CreateImage( cfg.cam_resolution[1], 8, 3 )  
        cv.Copy(self.hsv_saliency_map, bgr_copy)               
        cv.CvtColor(bgr_copy, bgr_copy, cv.CV_HSV2BGR)  # create hsv version
        #cv.SaveImage("saliency2.png", bgr_copy)
        
        cv.AddWeighted(bgr_copy, .5, im.asOpenCV(), .5, 1.0, im.asOpenCV())    # show saliency map as overlay
            


#    def mousePressEvent(self, event):
#        button = event.button()
#        self.mouse_x = event.x()
#        self.mouse_y = event.y()
#        gl.attention_point[0] = self.mouse_x #-330
#        gl.attention_point[1] = self.mouse_y #- 120
#        self.repaint()
    
        
#    def paintEvent(self, event):
#        self.painter.begin(self)
#        self.painter.setBrush(QColor(255,0,0,100))
#        self.painter.drawRect(self.attention_point[0]-15, self.attention_point[1]-15, 30, 30)
#        self.painter.end()
                
                

            
################## helper functions ###################################
# Rearrange the quadrants of Fourier image so that the origin is at
# the image center
# src & dst arrays of equal size & type
def cvShiftDFT(src_arr, dst_arr ):

    size = cv.GetSize(src_arr)
    dst_size = cv.GetSize(dst_arr)

    if dst_size != size:
        cv.Error( cv.CV_StsUnmatchedSizes, "cv.ShiftDFT", "Source and Destination arrays must have equal sizes", __FILE__, __LINE__ )    

    if(src_arr is dst_arr):
        tmp = cv.CreateMat(size[1]/2, size[0]/2, cv.GetElemType(src_arr))
    
    cx = size[0] / 2
    cy = size[1] / 2 # image center

    q1 = cv.GetSubRect( src_arr, (0,0,cx, cy) )
    q2 = cv.GetSubRect( src_arr, (cx,0,cx,cy) )
    q3 = cv.GetSubRect( src_arr, (cx,cy,cx,cy) )
    q4 = cv.GetSubRect( src_arr, (0,cy,cx,cy) )
    d1 = cv.GetSubRect( src_arr, (0,0,cx,cy) )
    d2 = cv.GetSubRect( src_arr, (cx,0,cx,cy) )
    d3 = cv.GetSubRect( src_arr, (cx,cy,cx,cy) )
    d4 = cv.GetSubRect( src_arr, (0,cy,cx,cy) )

    if(src_arr is not dst_arr):
        if( not cv.CV_ARE_TYPES_EQ( q1, d1 )):
            cv.Error( cv.CV_StsUnmatchedFormats, "cv.ShiftDFT", "Source and Destination arrays must have the same format", __FILE__, __LINE__ )    
        
        cv.Copy(q3, d1)
        cv.Copy(q4, d2)
        cv.Copy(q1, d3)
        cv.Copy(q2, d4)
    
    else:
        cv.Copy(q3, tmp)
        cv.Copy(q1, q3)
        cv.Copy(tmp, q1)
        cv.Copy(q4, tmp)
        cv.Copy(q2, q4)
        cv.Copy(tmp, q2)
        
        
        
def rgb2qimage(rgb):
    """Convert the 3D numpy array `rgb` into a 32-bit QImage.  `rgb` must
    have three dimensions with the vertical, horizontal and RGB image axes."""
    if len(rgb.shape) != 3:
        raise ValueError("rgb2QImage can expects the first (or last) dimension to contain exactly three (R,G,B) channels")
    if rgb.shape[2] != 3:
        raise ValueError("rgb2QImage can only convert 3D arrays")

    h, w, channels = rgb.shape

    # Qt expects 32bit BGRA data for color images:
    bgra = np.empty((h, w, 4), np.uint8, 'C')
    bgra[...,0] = rgb[...,0]
    bgra[...,1] = rgb[...,1]
    bgra[...,2] = rgb[...,2]
    bgra[...,3].fill(255)

    result = QImage(bgra.data, w, h, QImage.Format_RGB32)
    result.ndarray = bgra
    return result
    
    
if __name__ == "__main__":
    vis = Vision(cfg.use_gui)
    vis.start_camera()
    
    
    
