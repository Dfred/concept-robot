import sys, threading, math, time
import cv
import numpy, pylab
import voice_command, auks
import robot_control as rc
import pyvision as pv
pv.disableCommercialUseWarnings()
from pyvision.face.CascadeDetector import CascadeDetector,AVE_LEFT_EYE,AVE_RIGHT_EYE
from pyvision.types.Video import Webcam
from pyvision.edge.canny import canny


edge_threshold1 = 50
edge_threshold2 = 90
edge_threshold3 = 11
edge_threshold4 = 0
        
        
class CaptureVideo(threading.Thread):
    """ captures video stream from camera and performs various detections (face, edge, circle)
    """
    
    def __init__(self, params, comm = None):
        """ initiate variables"""
        
        threading.Thread.__init__(self)
        self.comm = comm
        self.p = params
        self.current_colour = None

        self.face_detector = CascadeDetector(cascade_name="haarcascade_frontalface_alt.xml",image_scale=0.5)
        self.webcam = Webcam()
        
        # create windows
        cv.NamedWindow('Camera', cv.CV_WINDOW_AUTOSIZE)
        
        # create the trackbar
        cv.CreateTrackbar ('edge threshold', 'Camera', 50, 100, self.change_value1)
        cv.CreateTrackbar ('circle threshold', 'Camera', 90, 100, self.change_value2)
        cv.CreateTrackbar ('gaussian blur', 'Camera', 11, 50, self.change_value3)
        cv.CreateTrackbar ('hue', 'Camera', 0, 100, self.change_value4)


    def run(self):
        self.main_loop(self.p)
    

    def detect_face(self, img, p):
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
                if p.eye_d:                             # draw point on eyes
                    img.annotatePoint(leye,color='blue')
                    img.annotatePoint(reye,color='blue')
            p.face_detected = True
                    
            if p.follow_face_gaze:
                relative_x = (320 - (close_face_rect.x + (close_face_rect.w/2.0)))
                relative_y = (240 - (close_face_rect.y + (close_face_rect.h/2.0)))
                gaze = self.follow_face_with_gaze(p, relative_x, relative_y, close_face_rect.w)
                if self.comm.last_ack != "wait" and gaze:
                    self.comm.set_neck_gaze(gaze)
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
    
    
    def follow_face_with_gaze(self, p, x, y, width):
        """adjust coordinates of detected faces to mask
        """
        if p.slow_adjust and (p.face_x is not None and p.face_y is not None):
            p.face_x += (x - p.face_x) * p.gain
            p.face_y += (y - p.face_y) * p.gain
        else:
            p.face_x = x
            p.face_y = y
            
        face_distance = ((-88.4832801364568 * math.log(width)) + 538.378262966656)
        x_dist = ((p.face_x/1400.6666)*face_distance)/-100
        y_dist = ((p.face_y/700.6666)*face_distance)/100
        if self.comm:
            return str(x_dist) + "," + str(face_distance/100) + "," + str(y_dist)
            
            
    def follow_face_with_neck(self, p, x, y, width):
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
        if move:
            return [distance_x, distance_y]
        
                
    
    def detect_edge(self, image):
        return canny(image)
        
        
    def detect_circle(self, image, image_org, params):
        grayscale = cv.CreateImage(cv.GetSize(image), 8, 1)
        grayscale_smooth = cv.CreateImage(cv.GetSize(image), 8, 1)
        cv.CvtColor(image, grayscale, cv.CV_BGR2GRAY)
        if params.edge_d_non_vision:
            cv.Canny(grayscale, grayscale, edge_threshold1, edge_threshold1 * 3, 3)
        cv.Smooth(grayscale, grayscale_smooth, cv.CV_GAUSSIAN, edge_threshold3)
        #storage = cv.CreateMemStorage()
        storage = cv.CreateMat(480, 640, cv.CV_8UC1)
        circles = cv.HoughCircles(grayscale_smooth, storage, cv.CV_HOUGH_GRADIENT, 2, 50, 200, (edge_threshold2 + 150) )
        circles_simple = []
        gazing = None
        for i in range(0, circles.total):
            c = circles[i]
            point = cvPoint(int(c[0]), int(c[1]))
            radius = int(c[2])
            cvCircle(image, point, radius, cvScalar(0, 0, 255))
            if params.detect_colour:
                self.get_colour(image, image_org, [int(c[0]), int(c[1])], radius)
                params.detect_colour = False
            colour = self.record_colour(image, image_org, [int(c[0]), int(c[1])], radius)
            circles_simple.append([point, radius, colour])
            
        if params.follow_ball_gaze and circles_simple:
            x_adjust = 320 - circles_simple[0][0].x
            y_adjust = 240 - circles_simple[0][0].y
            gazing = self.follow_ball_with_gaze(params, x_adjust, y_adjust)
        
        if params.follow_ball_neck and circles_simple:
            #self.comm.send_msg("recognizing;*;1;;;;tag_SPEECH")
            x_adjust = 320 - circles_simple[0][0].x
            y_adjust = 240 - circles_simple[0][0].y
            if x_adjust < 315 or x_adjust > 325:
                distance_x = (x_adjust/-640.0) * 0.2 * math.pi
            if y_adjust < 235 or y_adjust > 245:
                distance_y = (y_adjust/-480.0) * 0.2 * math.pi
            if self.comm.last_ack != "wait":
                    if gazing:
                        self.comm.set_neck_gaze(gazing, "(" + str(params.neck_pos[0] + distance_y) + ",0," + str(params.neck_pos[2] + distance_x) + ")", "TRACK_GAZE")
                    else:
                        self.comm.set_neck_orientation( "(" + str(params.neck_pos[0] + distance_y) + ",0," + str(params.neck_pos[2] + distance_x) + ")", "TRACKING")
                    params.neck_pos[2] += distance_x
                    params.neck_pos[0] += distance_y
                    self.comm.last_ack = "wait"
        

            
            
        if params.colour_to_find and circles_simple:
            dist = []
            for i in circles_simple:
                if i[2]:
                    #dist.append(auks.calculate_distance_hsv(params.colour_to_find, i[2]))
                    dist.append(auks.calculate_distance(params.colour_to_find, i[2]))
                else:
                    dist.append(999999)
            index = auks.posMin(dist)
            #print dist
            if dist[index] < params.detect_threshold:
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
#                        print "x_neck:", str(params.neck_pos[2]), "   y_neck:", str(params.neck_pos[0])
#                        print "x:", str(params.neck_pos[2] + distance_x), "   y:", str(params.neck_pos[0] + distance_y)
                        if gazing:
                            self.comm.set_neck_gaze(gazing, "(" + str(params.neck_pos[0] + distance_y) + ",0," + str(params.neck_pos[2] + distance_x) + ")", "TRACK_GAZE")
                        else:
                            self.comm.set_neck_orientation( "(" + str(params.neck_pos[0] + distance_y) + ",0," + str(params.neck_pos[2] + distance_x) + ")", "TRACKING")
                        params.neck_pos[2] += distance_x
                        params.neck_pos[0] += distance_y
                        self.comm.last_ack = "wait"
                              
        return circles_simple
                 
                 
    def follow_ball_with_gaze(self, p, x, y):
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



    def find_colour(self, image, colour, p):
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
    
        
    def main_loop(self, p):
        
        #writer = cvCreateVideoWriter("out.avi",CV_FOURCC('P','I','M','1'), 30,cvSize(640,480),1)
        
        while 1:
            im = self.webcam.query()

            # handle events
            key = cv.WaitKey(10)
            if key != -1:
                key = chr(key)
                
            if key == '1' or p.command == '1':
                if p.face_d == False:
                    p.face_d = True
                    print "looking for faces"
                    
            if key == '2' or p.command == 'edge':
                if p.edge_d == False:
                    p.edge_d = True
                    print "detecting edges"
                    
            if key == '3' or p.command == '3':
                if p.save_video == False:
                    p.save_video = True
                    print "saving video"
                    
            if key  == '4' or p.command == '4':
                if p.circle_d == False:
                    p.circle_d = True
                    print "detecting circles"
                    
            if key  == '5' or p.command == '5':
                if p.edge_d_non_vision == False:
                    p.edge_d_non_vision = True
                    print "detecting circles using edge detection"
                else:
                    p.edge_d_non_vision = False
                    
            if key == 's' or p.command == 's':
                if p.show == False:
                    p.show = True
                    print "showing video"
                    
            if key == 'g' or p.command == 'g':
                if p.follow_face == False:
                    p.follow_face = True
                else:
                    p.follow_face = False

            if key == 'b' or p.command == 'b':
                if p.game_coors == "10.0, 50.0, 0.0":
                    self.commr.set_gaze("10.0, 50.0, 0.0")
                    p.game_coors = "0.0, 50.0, 0.0"
                else:
                    self.commr.set_gaze("0.0, 50.0, 0.0")
                    p.game_coors = "10.0, 50.0, 0.0"
                    
            if key == 'e' or p.command == 'e':
                p.face_d = False
                p.edge_d = False
                p.circle_d = False
                p.save_video = False
                p.colour_s = False
                print "stop tracking"
                    
            if key == 'q' or p.command == 'q':
                p.quit = True
                
            p.command = '0'
              
            if p.face_d:    # face detection
                self.detect_face(im, p)
                
            if p.edge_d:    # edge detection
                im = self.detect_edge(im)
                

    
            if p.colour_s:
                self.find_colour(frame, 10, p)
            
            if p.save_video:    # save
                cv.WriteFrame(writer,frame)
                
            if p.quit:  # quit
                print 'Camera closed'
                break
            
            pil = im.asAnnotated()                      # get image as PIL              
            rgb = cv.CreateImageHeader(pil.size, cv.IPL_DEPTH_8U, 3)        # create IPL image
            cv.SetData(rgb, pil.tostring())                                 
            frame = cv.CreateImage(cv.GetSize(rgb), cv.IPL_DEPTH_8U,3)      # convert to bgr
            cv.CvtColor(rgb, frame, cv.CV_RGB2BGR)                          
            cv.Flip(frame, None, 1)                                         # mirror
            
            if p.circle_d: # circle detection
                frame_org = cv.CreateImage(cv.GetSize(frame), cv.IPL_DEPTH_8U,3)      # convert to bgr
                cv.Copy(frame, frame_org)
                self.detect_circle(frame, frame_org, p)

            if frame is None:
                print "error capturing frame"
                break
     
            if p.show:
                cv.ShowImage('Camera', frame) # display webcam image
                
            else:
                cv.ShowImage('Camera', empty)
    
    
if __name__ == "__main__":
    cap = CaptureVideo(voice_command.Params())
    cap.start()

