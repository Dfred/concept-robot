import sys, threading, math, time
import cv
import numpy
import config

import pyvision as pv
pv.disableCommercialUseWarnings()
from pyvision.face.CascadeDetector import CascadeDetector,AVE_LEFT_EYE,AVE_RIGHT_EYE
from pyvision.types.Video import Webcam
from pyvision.edge.canny import canny

import config

edge_threshold1 = 50
edge_threshold2 = 90
edge_threshold3 = 11
edge_threshold4 = 0
        
        
class CaptureVideo(threading.Thread):
    """ captures video stream from camera and performs various detections (face, edge, circle)
    """
    
    def __init__(self, comm = None):
        """ initiate variables"""
        
        threading.Thread.__init__(self)
        self.comm = comm
        self.current_colour = None

        self.face_detector = CascadeDetector(cascade_name=config.haar_casc,min_size=(50,50), image_scale=0.5)
        self.webcam = Webcam()
        
        if config.use_gui: # create windows            
            cv.NamedWindow('Camera', cv.CV_WINDOW_AUTOSIZE)
            cv.CreateTrackbar ('edge threshold', 'Camera', 50, 100, self.change_value1)
            cv.CreateTrackbar ('circle threshold', 'Camera', 90, 100, self.change_value2)
            cv.CreateTrackbar ('gaussian blur', 'Camera', 11, 50, self.change_value3)
            cv.CreateTrackbar ('hue', 'Camera', 0, 100, self.change_value4)


    def run(self):
        self.main_loop()
    

    def detect_face(self, img):
        """ detect faces in the given video stream
        """
        
        faces = self.findFaces(img)
        
        if faces:
            close_face_rect = None
            close_face_w = 0.0
            for rect, leye, reye in faces:
                img.annotateRect(rect, color='blue')    # draw square around face
                if rect.w > close_face_w:               # get closest face coordinates
                    close_face_w = rect.w
                    close_face_rect = rect
                if config.eye_d:                             # draw point on eyes
                    img.annotatePoint(leye,color='blue')
                    img.annotatePoint(reye,color='blue')
                    
            if config.follow_face_gaze:
                relative_x = (320 - (close_face_rect.x + (close_face_rect.w/2.0)))
                relative_y = (240 - (close_face_rect.y + (close_face_rect.h/2.0)))
                gaze = self.follow_face_with_gaze(relative_x, relative_y, close_face_rect.w)
                neck = self.follow_face_with_neck(relative_x, relative_y, gaze[1])
                if self.comm:
                    if self.comm.last_ack != "wait" and gaze:
                        self.comm.set_neck_gaze(gaze, neck)
                        self.comm.last_ack = "wait"
                    
                    
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
    
    
    def follow_face_with_gaze(self, x, y, width):
        """adjust coordinates of detected faces to mask
        """
        #TODO: change coordinates that are kept in config into something local
        if config.slow_adjust and (config.face_x is not None and config.face_y is not None):
            config.face_x += (x - config.face_x) * config.gain
            config.face_y += (y - config.face_y) * config.gain
        else:
            config.face_x = x
            config.face_y = y
            
        face_distance = ((-88.4832801364568 * math.log(width)) + 538.378262966656)
        x_dist = ((config.face_x/1400.6666)*face_distance)/100
        y_dist = ((config.face_y/700.6666)*face_distance)/100
        if config.camera_on_projector:
		  return (x_dist, (face_distance/100.0), y_dist)  # x is inverted for compatibility
		else:
		  return (-x_dist, (face_distance/100.0), y_dist)
            
            
    def follow_face_with_neck(self, x, y, face_distance):
        """adjust coordinates of detected faces to neck movement
        """
        move = False
        if x > 95 or x < -95: # threshold
            distance_x = (x/-640.0) * 0.2 * math.pi
            move = True
        else:
            distance_x = 0.0
            
        if y > 60 or y < -60: # threshold
            distance_y = (y/-480.0) * 0.1 * math.pi
            move = True
        else:
            distance_y = 0.0

        if face_distance > 1.0:    # threshold for moving forward when perceived face is far
            config.getting_closer_to_face = 1.0
        if config.getting_closer_to_face > 0.05:
            distance_z = 0.1
            config.getting_closer_to_face += -0.1
            move = True
        if face_distance < 0.2:    # threshold for moving back when face is too close
            distance_z = -0.3 + face_distance
            move = True
        else:
            distance_z = 0
        if move:
            return ((distance_y, .0, -distance_x), (.0,distance_z,.0))
                
    
    def detect_edge(self, image):
        grayscale = cv.CreateImage(cv.GetSize(image), 8, 1)
        cv.CvtColor(image, grayscale, cv.CV_BGR2GRAY)
        cv.Canny(grayscale, grayscale, edge_threshold1, edge_threshold1 * 3, 3)
        return grayscale
        
        
    def detect_circle(self, image, image_org):
        grayscale = cv.CreateImage(cv.GetSize(image), 8, 1)
        grayscale_smooth = cv.CreateImage(cv.GetSize(image), 8, 1)
        cv.CvtColor(image, grayscale, cv.CV_BGR2GRAY)
        if config.edge_d_non_vision:
            cv.Canny(grayscale, grayscale, edge_threshold1, edge_threshold1 * 3, 3)
        cv.Smooth(grayscale, grayscale_smooth, cv.CV_GAUSSIAN, edge_threshold3)
        mat = cv.CreateMat(100, 1, cv.CV_32FC3 )
        cv.SetZero(mat)
        cv.HoughCircles(grayscale_smooth, mat, cv.CV_HOUGH_GRADIENT, 2, 50, 200, (edge_threshold2 + 150) )
        circles_simple = []
        gazing = None
        if mat.rows != 0:
            for i in xrange(0, mat.rows):
                c = mat[i,0]
                point = (int(c[0]), int(c[1]))
                radius = int(c[2])
                cv.Circle(image, point, radius, (0, 0, 255))
                if config.detect_colour:
                    self.get_colour(image, image_org, [int(c[0]), int(c[1])], radius)
                    config.detect_colour = False
                    colour = self.record_colour(image, image_org, [int(c[0]), int(c[1])], radius)
                    circles_simple.append([point, radius, colour])
            
        if config.follow_ball_gaze and circles_simple:
            x_adjust = 320 - circles_simple[0][0].x
            y_adjust = 240 - circles_simple[0][0].y
            gazing = self.follow_ball_with_gaze(x_adjust, y_adjust)
        
        if config.follow_ball_neck and circles_simple:
            #self.comm.send_msg("recognizing;*;1;;;;tag_SPEECH")
            x_adjust = 320 - circles_simple[0][0].x
            y_adjust = 240 - circles_simple[0][0].y
            if x_adjust < 315 or x_adjust > 325:
                distance_x = (x_adjust/-640.0) * 0.2 * math.pi
            if y_adjust < 235 or y_adjust > 245:
                distance_y = (y_adjust/-480.0) * 0.2 * math.pi
            if self.comm.last_ack != "wait":
                    if gazing:
#                        self.comm.set_neck_gaze(gazing, "(" + str(config.neck_pos[0] + distance_y) + ",0," + str(config.neck_pos[2] + distance_x) + ")", "TRACK_GAZE")
                        pass
                    else:
                        self.comm.set_neck_orientation( "(" + str(config.neck_pos[0] + distance_y) + ",0," + str(config.neck_pos[2] + distance_x) + ")", "TRACKING")
                    config.neck_pos[2] += distance_x
                    config.neck_pos[0] += distance_y
                    self.comm.last_ack = "wait"
        

        if config.colour_to_find and circles_simple:
            dist = []
            for i in circles_simple:
                if i[2]:
                    #dist.append(auks.calculate_distance_hsv(params.colour_to_find, i[2]))
                    dist.append(auks.calculate_distance(config.colour_to_find, i[2]))
                else:
                    dist.append(999999)
            index = auks.posMin(dist)
            #print dist
            if dist[index] < config.detect_threshold:
                #self.comm.send_msg("recognizing;*;1;;;;tag_SPEECH")
                cv.Circle(image, circles_simple[index][0], 2, cvScalar(0, 100, 255), 2)
                x_adjust = 320 - circles_simple[index][0].x
                y_adjust = 240 - circles_simple[index][0].y
                if x_adjust < 315 or x_adjust > 325:
                    distance_x = (x_adjust/-640.0) * 0.2 * math.pi
                if y_adjust < 235 or y_adjust > 245:
                    distance_y = (y_adjust/-480.0) * 0.2 * math.pi
                if self.comm.last_ack != "wait":
#                        print "x_dist:", distance_x, " y_dist:", distance_y
#                        print "x_neck:", str(config.neck_pos[2]), "   y_neck:", str(config.neck_pos[0])
#                        print "x:", str(config.neck_pos[2] + distance_x), "   y:", str(config.neck_pos[0] + distance_y)
                        if gazing:
#                            self.comm.set_neck_gaze(gazing, "(" + str(config.neck_pos[0] + distance_y) + ",0," + str(config.neck_pos[2] + distance_x) + ")", "TRACK_GAZE")
                            pass
                        else:
                            self.comm.set_neck_orientation( "(" + str(config.neck_pos[0] + distance_y) + ",0," + str(config.neck_pos[2] + distance_x) + ")", "TRACKING")
                        config.neck_pos[2] += distance_x
                        config.neck_pos[0] += distance_y
                        self.comm.last_ack = "wait"
                              
        return circles_simple
                 
                 
    def follow_ball_with_gaze(self, x, y):
        """adjust coordinates of detected faces to mask
        """
            
        #face_distance = ((-88.4832801364568 * math.log(width)) + 538.378262966656)
        face_distance = 50.0
        x_dist = ((x/1400.6666)*face_distance)/-100
        y_dist = ((y/1400.6666)*face_distance)/100
#        if self.comm:
#            if self.comm.last_ack != "wait":
#                self.comm.set_gaze(str(x_dist) + "," + str(face_distance/100) + "," + str(y_dist))
#                self.comm.last_ack = "wait"
        return str(x_dist) + "," + str(face_distance/100) + "," + str(y_dist)
                 
            
    def get_colour(self, image, image_org, pos, radius):
        radius = int(radius*0.7)
        rect = cv.Rect(pos[0]-radius,pos[1]-radius, radius*2, radius*2)
        try:
            subimage = cv.GetSubRect(image_org, rect)
            cv.SaveImage("subimage.png", subimage)
            #cvCvtColor(subimage, subimage, CV_BGR2HSV)  # create hsv version
            scalar = cv.Avg(subimage)
            #self.current_colour = [int((scalar[0]*2)), int(scalar[1]/255.0*100), int(scalar[2]/255.0*100)]
            #print "Average colour value: H:"+ str(int((scalar[0]*2))) + " S:"+ str(int(scalar[1]/255.0*100)) + " V:"+ str(int(scalar[2]/255.0*100))
            self.current_colour = [int((scalar[2])), int(scalar[1]), int(scalar[0])]
            print "Average colour value: R:"+ str(int((scalar[2]))) + " G:"+ str(int(scalar[1])) + " B:"+ str(int(scalar[0]))
        
        except RuntimeError:
            print "error"
        
        cv.Rectangle(image, cv.Point( pos[0]-radius, pos[1]-radius), cv.Point(pos[0]+ radius, pos[1]+radius),cv.CV_RGB(0, 255, 0), 2, 8, 0)
        
        
    def record_colour(self, image, image_org, pos, radius):
        radius = int(radius*0.7)
        if pos[1] > radius: # only record a square when it is in full camera view
            try:
                rect = cv.Rect(pos[0]-radius, pos[1]-radius, radius*2, radius*2)
                subimage = cv.GetSubRect(image_org, rect)
                #cvCvtColor(subimage, subimage, CV_BGR2HSV)  # create hsv version
                scalar = cv.Avg(subimage)
                #return scalar1, [['c', [['h', int((scalar[0]*2))], ['s', int(scalar[1]/255.0*100)], ['v', int(scalar[2]/255.0*100)]]]]
                return [['c', [['r', int((scalar[2]))], ['g', int(scalar[1])], ['b', int(scalar[0])]]]]
            except RuntimeError:
                print "error", "radius:", radius, "position:", pos
                return None
        else:
            return None



    def find_colour(self, image, colour):
        """ searches for the given colour in the image
            colour is in hsv
        """
        # Create a 8-bit 1-channel image with same size as the frame
        color_mask = cv.CreateImage(cv.GetSize(image), 8, 1)
        image_h = cv.CreateImage(cv.GetSize(image), 8, 1)
        
        cv.CvtColor(image, image, cv.CV_BGR2HSV)  # convert to hsv
        
        cv.Split(image, image_h, None, None, None)
        
        # Find the pixels within the color-range, and put the output in the color_mask
        cv.InRangeS(image_h, cv.Scalar((edge_threshold4*2)-5), cv.Scalar((edge_threshold4*2)+5), color_mask)
        cv.CvtColor(image, image, cv.CV_HSV2BGR)  # convert to bgr
        cv.Set(image, cv.CV_RGB(0, 255, 0), color_mask)
        
        
    def return_colour(self):
        """ returns current colour
        """
        return self.current_colour
 
    
    def change_value1(self, new_value):
        global edge_threshold1
        edge_threshold1 = new_value
        
    def change_value2(self, new_value):
        global edge_threshold2
        edge_threshold2 = new_value
        
    def change_value3(self, new_value):
        global edge_threshold3
        if new_value % 2:
            edge_threshold3 = new_value
        else:
            edge_threshold3 = new_value+1
            
    def change_value4(self, new_value):
        global edge_threshold4
        edge_threshold4 = new_value
    
        
    def main_loop(self):
        
        #writer = cv.CreateVideoWriter("out.avi", cv.CV_FOURCC('P','I','M','1'), 30, (640,480),1)
        
        while 1:

            im = self.webcam.query()
            
            # handle events
            key = cv.WaitKey(10)
            if key != -1 and key < 256:
                key = chr(key)
                
            if key == '1' or config.command == '1':
                if config.face_d == False:
                    config.face_d = True                   
                    
            if key == '2' or config.command == 'edge':
                if config.edge_d == False:
                    config.edge_d = True
                    print "detecting edges"
                    
            if key == '3' or config.command == '3':
                if config.save_video == False:
                    config.save_video = True
                    print "saving video"
                    
            if key  == '4' or config.command == '4':
                if config.circle_d == False:
                    config.circle_d = True
                    print "detecting circles"
                    
            if key  == '5' or config.command == '5':
                if config.edge_d_non_vision == False:
                    config.edge_d_non_vision = True
                    print "detecting circles using edge detection"
                else:
                    config.edge_d_non_vision = False
                    
            if key == 's' or config.command == 's':
                if config.show == False:
                    config.show = True
                    print "showing video"

            if key == 'b' or config.command == 'b':
                if config.game_coors == "10.0, 50.0, 0.0":
                    self.commr.set_gaze("10.0, 50.0, 0.0")
                    config.game_coors = "0.0, 50.0, 0.0"
                else:
                    self.commr.set_gaze("0.0, 50.0, 0.0")
                    config.game_coors = "10.0, 50.0, 0.0"
                    
            if key == 'e' or config.command == 'e':
                config.face_d = False
                config.edge_d = False
                config.circle_d = False
                config.save_video = False
                config.colour_s = False
                print "stop tracking"
                    
            if key == 'q' or config.command == 'q':
                config.quit = True
                
            config.command = '0'
          
            if config.face_d:    # face detection
                if config.face_d_optimised:
                    if self.comm.last_ack != "wait":
                        self.detect_face(im)
                else:
                    self.detect_face(im)
                
            if config.colour_s:
                self.find_colour(frame, 10)
            
            if config.save_video:    # save
                cv.WriteFrame(writer,frame)
                
            if config.quit:  # quit
                print 'Camera closed'
                break
            
            pil = im.asAnnotated()                                          # get image as PIL              
            rgb = cv.CreateImageHeader(pil.size, cv.IPL_DEPTH_8U, 3)        # create IPL image
            cv.SetData(rgb, pil.tostring())                                 
            frame = cv.CreateImage(cv.GetSize(rgb), cv.IPL_DEPTH_8U,3)      # convert to bgr
            cv.CvtColor(rgb, frame, cv.CV_RGB2BGR)    
            cv.Flip(frame, None, 1)                                         # mirror                    

            if config.circle_d: # circle detection
                frame_org = cv.CreateImage(cv.GetSize(frame), cv.IPL_DEPTH_8U,3)      # convert to bgr
                cv.Copy(frame, frame_org)
                self.detect_circle(frame, frame_org)
                
            if config.edge_d:    # edge detection
                frame_org = cv.CreateImage(cv.GetSize(frame), cv.IPL_DEPTH_8U,3)      # convert to bgr
                cv.Copy(frame, frame_org)
                frame = self.detect_edge(frame)
                
            if frame is None:
                print "error capturing frame"
                break
     
            if config.use_gui:
                if config.show:
                    cv.ShowImage('Camera', frame) # display webcam image
                else:
                    cv.ShowImage('Camera', empty)
    
    
if __name__ == "__main__":
    config.haar_casc = "haarcascade_frontalface_alt.xml"        # change path for compatibility
    cap = CaptureVideo()
    cap.start()

