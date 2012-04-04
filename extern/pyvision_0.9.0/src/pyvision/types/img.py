# PyVision License
#
# Copyright (c) 2006-2009 David S. Bolme
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
# 
# 3. Neither name of copyright holders nor the names of its contributors
# may be used to endorse or promote products derived from this software
# without specific prior written permission.
# 
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

'''

'''
__author__ = "$Author$"
__version__ = "$Revision$"

import PIL.ImageDraw
import PIL.Image
    
import numpy
import numpy as np
import cv

import unittest
import os.path


import pyvision

TYPE_MATRIX_2D  = "TYPE_MATRIX2D" 
'''Image was created using a 2D "gray-scale" numpy array'''

TYPE_MATRIX_RGB = "TYPE_MATRIX_RGB" 
'''Image was created using a 3D "color" numpy array'''

TYPE_PIL        = "TYPE_PIL" 
'''Image was created using a PIL image instance'''

TYPE_OPENCV     = "TYPE_OPENCV"
'''Image was created using a OpenCV image instance'''

LUMA = [0.299, 0.587, 0.114, 1.0]
'''Values used when converting color to gray-scale.'''


class Image:
    '''
    The primary purpose of the image class is to provide a structure that can
    transform an image back and fourth for different python libraires such as
    U{PIL<http://www.pythonware.com/products/pil>}, 
    U{OpenCV <http://sourceforge.net/projects/opencvlibrary>}, and 
    U{Scipy<http://www.scipy.org">} Images also This also
    allows some simple operations on the image such as annotation.
    
    B{Note:} When working with images in matrix format, they are transposed such
    that x = col and y = row.  You can therefore still work with coords
    such that im[x,y] = mat[x,y].
    
    Images have the following attributes:
      - width = width of the image
      - height = height of the image
      - size = (width,height)
      - channels = number of channels: 1(gray), 3(RGB)
      - depth = bitdepth: 8(uchar), 32(float), 64(double)
    '''
 
 
    #------------------------------------------------------------------------
    def __init__(self,data,bw_annotate=False):
        '''
        Create an image from a file or a PIL Image, OpenCV Image, or numpy array.
         
        @param data: this can be a numpy array, PIL image, or opencv image.
        @param bw_annotate: generate a black and white image to make color annotations show up better
        @return: an Image object instance
        '''

        self.filename = None
        self.pil = None
        self.matrix2d = None
        self.matrix3d = None
        self.opencv = None
        self.annotated = None
        self.bw_annotate = bw_annotate
        
        if isinstance(data,numpy.ndarray) and len(data.shape) == 2:
            self.type=TYPE_MATRIX_2D
            self.matrix2d = data
            
            self.width,self.height = self.matrix2d.shape
            self.channels = 1
            
            if self.matrix2d.dtype == numpy.float32:
                self.depth=32
            elif self.matrix2d.dtype == numpy.float64:
                self.depth=64
            else:
                raise TypeError("Unsuppoted format for ndarray images: %s"%self.matrix2d.dtype)
            
        elif isinstance(data,numpy.ndarray) and len(data.shape) == 3 and data.shape[0]==3:
            self.type=TYPE_MATRIX_RGB
            self.matrix3d = data
            self.channels=3
            self.width = self.matrix3d.shape[1]
            self.height = self.matrix3d.shape[2]
            if self.matrix3d.dtype == numpy.float32:
                self.depth=32
            elif self.matrix3d.dtype == numpy.float64:
                self.depth=64
            else:
                raise TypeError("Unsuppoted format for ndarray images: %s"%self.matrix2d.dtype)
            
        elif isinstance(data,PIL.Image.Image) or type(data) == str:
            if type(data) == str:
                # Assume this is a filename
                # TODO: Removing the filename causes errors in other unittest.
                #       Those errors should be corrected.
                self.filename = data
                data = PIL.Image.open(data)
            self.type=TYPE_PIL
            self.pil = data
            self.width,self.height = self.pil.size
                        
            if self.pil.mode == 'L':
                self.channels = 1
            elif self.pil.mode == 'RGB':
                self.channels = 3
            else:
                raise TypeError("Unsuppoted format for PIL images: %s"%self.pil.mode)
            
            self.depth = 8
                        
        elif isinstance(data,cv.iplimage):
            self.type=TYPE_OPENCV
            self.opencv=data 
            
            self.width = data.width
            self.height = data.height
            
            assert data.nChannels in (1,3)
            self.channels = data.nChannels 
            
            assert data.depth in (8,)
            self.depth = data.depth   

        else:
            raise TypeError("Could not create from type: %s %s"%(data,type(data)))
        
        self.size = (self.width,self.height)
        self.data = data
        
        
    def asMatrix2D(self):
        '''
        @return: the gray-scale image data as a two dimensional numpy array
        '''
        if self.matrix2d == None:
            self._generateMatrix2D()
        return self.matrix2d

    def asMatrix3D(self):
        '''
        @return: color image data as a 3D array with shape (3(rgb),w,h)
        '''
        if self.matrix3d == None:
            self._generateMatrix3D()
        return self.matrix3d

    def asPIL(self):
        '''
        @return: image data as a pil image
        '''
        if self.pil == None:
            self._generatePIL()
        return self.pil

    def asOpenCV(self):
        '''
        @return: the image data in an OpenCV format
        '''
        if self.opencv == None:
            self._generateOpenCV()
        return self.opencv
        
    def asOpenCVBW(self):
        '''
        @return: the image data in an OpenCV one channel format
        '''
        cvim = self.asOpenCV()
        
        if cvim.nChannels == 1:
            return cvim
        
        elif cvim.nChannels == 3:
            cvimbw = cv.CreateImage(cv.GetSize(cvim), cv.IPL_DEPTH_8U, 1);
            cv.CvtColor(cvim, cvimbw, cv.CV_BGR2GRAY);
            return cvimbw
        
        else:
            raise ValueError("Unsupported opencv image format: nChannels=%d"%cvim.nChannels)
        

    def asAnnotated(self):
        '''
        @return: the PIL image used for annotation.
        '''
        if self.annotated == None:
            if self.bw_annotate:
                # Make a black and white image that can be annotated with color.
                self.annotated = self.asPIL().convert("L").copy().convert("RGB")
            else:
                # Annotate over color if avalible.
                self.annotated = self.asPIL().copy().convert("RGB")
        return self.annotated
            
    def annotateRect(self,rect,color='red'):
        '''
        Draws a rectangle on the annotation image
        
        @param rect: a rectangle of type Rect
        @param color: defined as ('#rrggbb' or 'name') 
        '''
        im = self.asAnnotated()
        draw = PIL.ImageDraw.Draw(im)
        box = [rect.x,rect.y,rect.x+rect.w,rect.y+rect.h]
        draw.rectangle(box,outline=color)
        del draw
        
    def annotateThickRect(self,rect,color='red',width=5):
        '''
        Draws a rectangle on the annotation image
        
        @param rect: a rectangle of type Rect
        @param color: defined as ('#rrggbb' or 'name') 
        '''
        im = self.asAnnotated()
        draw = PIL.ImageDraw.Draw(im)
        x,y,w,h = [rect.x,rect.y,rect.w,rect.h]
        line = [x,y,x+w,y]
        draw.line(line,fill=color,width=width)
        line = [x,y,x,y+h]
        draw.line(line,fill=color,width=width)
        line = [x,y+h,x+w,y+h]
        draw.line(line,fill=color,width=width)
        line = [x+w,y,x+w,y+h]
        draw.line(line,fill=color,width=width)
        del draw

    def annotateEllipse(self,rect,color='red'):
        '''
        Draws an ellipse on the annotation image
        
        @param rect: the bounding box of the elipse of type Rect
        @param color: defined as ('#rrggbb' or 'name') 
        '''
        im = self.asAnnotated()
        draw = PIL.ImageDraw.Draw(im)
        box = [rect.x,rect.y,rect.x+rect.w,rect.y+rect.h]
        draw.ellipse(box,outline=color)
        del draw
                
    def annotateLine(self,point1,point2,color='red',width=1):
        '''
        Draws a line from point1 to point2 on the annotation image
    
        @param point1: the starting point as type Point
        @param point2: the ending point as type Point
        @param color: defined as ('#rrggbb' or 'name') 
        '''
        im = self.asAnnotated()
        draw = PIL.ImageDraw.Draw(im)
        line = [point1.X(),point1.Y(),point2.X(),point2.Y()]
        draw.line(line,fill=color,width=width)
        del draw
        
    def annotatePoint(self,point,color='red'):
        '''
        Marks a point in the annotation image using a small circle
        
        @param point: the point to mark as type Point
        @param color: defined as ('#rrggbb' or 'name') 
        '''
        im = self.asAnnotated()
        draw = PIL.ImageDraw.Draw(im)
        box = [point.X()-3,point.Y()-3,point.X()+3,point.Y()+3]
        draw.ellipse(box,outline=color)
        del draw

    def annotateCircle(self,point, radius=3, color='red',fill=None):
        '''
        Marks a circle in the annotation image 
        
        @param point: the center of the circle as type Point
        @param radius: the radius of the circle
        @param color: defined as ('#rrggbb' or 'name') 
        '''
        im = self.asAnnotated()
        draw = PIL.ImageDraw.Draw(im)
        box = [point.X()-radius,point.Y()-radius,point.X()+radius,point.Y()+radius]
        draw.ellipse(box,outline=color,fill=fill)
        del draw
        
    def annotateLabel(self,point,label,color='red',mark=False):        
        '''
        Marks a point in the image with text 
        
        @param point: the point to mark as type Point
        @param label: the text to use as a string
        @param color: defined as ('#rrggbb' or 'name') 
        @param mark: of True or ['right', 'left', 'below', or 'above'] then also mark the point with a small circle
        '''
        im = self.asAnnotated()
        draw = PIL.ImageDraw.Draw(im)
        tw,th = draw.textsize(label)
        if mark in [True, 'right']:
            draw.text([point.X()+5,point.Y()-th/2],label,fill=color)
            box = [point.X()-3,point.Y()-3,point.X()+3,point.Y()+3]
            draw.ellipse(box,outline=color)
        elif mark in ['left']:
            draw.text([point.X()-tw-5,point.Y()-th/2],label,fill=color)
            box = [point.X()-3,point.Y()-3,point.X()+3,point.Y()+3]
            draw.ellipse(box,outline=color)
        elif mark in ['below']:
            draw.text([point.X()-tw/2,point.Y()+5],label,fill=color)
            box = [point.X()-3,point.Y()-3,point.X()+3,point.Y()+3]
            draw.ellipse(box,outline=color)
        elif mark in ['above']:
            draw.text([point.X()-tw/2,point.Y()-th-5],label,fill=color)
            box = [point.X()-3,point.Y()-3,point.X()+3,point.Y()+3]
            draw.ellipse(box,outline=color)
        else:
            draw.text([point.X(),point.Y()],label,fill=color)

        del draw

        
    def annotateDot(self,point,color='red'):
        '''
        Like L{annotatePoint} but only draws a point on the given pixel.
        This is useful to avoid clutter if many points are being annotated.
        
        @param point: the point to mark as type Point
        @param color: defined as ('#rrggbb' or 'name') 
        '''
        im = self.asAnnotated()
        draw = PIL.ImageDraw.Draw(im)
        draw.point([point.X(),point.Y()],fill=color)
        del draw
        
    #------------------------------------------------------------------------
    def valueNormalize(self):
        '''TODO: Deprecated remove this sometime.'''
        print "WARNING: Image.valueNormalize has been depricated."
        return self.normalize()

    ##
    # @return the type of the image
    def getType(self):
        return self.type
    
    #------------------------------------------------------------------------
    def normalize(self):
        import PIL.ImageOps
        pil = self.asPIL().copy()
        pil = PIL.ImageOps.equalize(pil.convert('L'))
        self.pil = pil
        self.matrix2d = None
        mat = self.asMatrix2D()
        mean = mat.mean()
        std = mat.std()
        mat -= mean
        mat /= std
        self.matrix2d=mat
       

    #------------------------------------------------------------------------        
    def _generateMatrix2D(self):
        '''
        Create a matrix version of the image.
        '''
        buffer = self.toBufferGray(32)
        self.matrix2d = numpy.frombuffer(buffer,numpy.float32).reshape(self.height,self.width).transpose()
                    

    def _generateMatrix3D(self):
        '''
        Create a matrix version of the image.
        '''
        buffer = self.toBufferRGB(32)
        self.matrix3d = numpy.frombuffer(buffer,numpy.float32).reshape(self.height,self.width,3).transpose()            

    def _generatePIL(self):
        '''
        Create a PIL version of the image
        '''
        if self.channels == 1:
            self.pil = PIL.Image.fromstring("L",self.size,self.toBufferGray(8))
        elif self.channels == 3:
            self.pil = PIL.Image.fromstring("RGB",self.size,self.toBufferRGB(8))
        else:
            raise NotImplementedError("Cannot convert image from type: %s"%self.type)
        
    def _generateOpenCV(self):
        '''
        Create a color opencv representation of the image.
        TODO: The OpenCV databuffer seems to be automatically swapped from RGB
              to BGR.  This is counter intuitive.
        '''
        
        w,h = self.size
        if self.channels == 1:
            gray = cv.CreateImage((w,h),cv.IPL_DEPTH_8U,1)
            cv.SetData(gray,self.toBufferGray(8))
            self.opencv = gray
        elif self.channels == 3:
            rgb = cv.CreateImage((w,h),cv.IPL_DEPTH_8U,3)
            bgr = cv.CreateImage((w,h),cv.IPL_DEPTH_8U,3)
            cv.SetData(rgb, self.toBufferRGB(8))
            # convert from RGB to BGR
            cv.CvtColor(rgb,bgr,cv.CV_RGB2BGR)
            self.opencv=bgr
        else:
            raise NotImplementedError("Cannot convert image from type: %s"%self.type)
                
        
    def toBufferGray(self,depth):
        '''
            returns the image data as a binary python string.
        '''
        buffer = None
        if self.type == TYPE_PIL:
            pil = self.pil
            if pil.mode != 'L':
                pil = pil.convert('L')
            buffer = pil.tostring()
        elif self.type == TYPE_MATRIX_2D:
            buffer = self.matrix2d.transpose().tostring()
        elif self.type == TYPE_MATRIX_RGB:
            mat = self.matrix3d
            mat = LUMA[0]*mat[0] + LUMA[1]*mat[1] + LUMA[2]*mat[2]
            buffer = mat.transpose().tostring()
        elif self.type == TYPE_OPENCV:
            if self.channels == 1:
                buffer = self.opencv.tostring()
            elif self.channels == 3:
                w,h = self.width,self.height
                gray = cv.CreateImage((w,h),cv.IPL_DEPTH_8U,1)
                cv.CvtColor( self.opencv, gray, cv.CV_BGR2GRAY );
                buffer = gray.tostring()
            else:
                raise TypeError("Operation not supported for image type.")
        else:
            raise TypeError("Operation not supported for image type.")
        
        assert buffer
            
        if depth == self.depth:
            return buffer
        
        else:
            types = {8:numpy.uint8,32:numpy.float32,64:numpy.float64}
            
            # convert the buffer to data
            data = numpy.frombuffer(buffer,types[self.depth])
            
            if depth==8:
                # Make sure the data is in a valid range
                max_value = data.max()
                min_value = data.min()
                data_range = max_value - min_value
                if max_value <= 255 and min_value >= 0 and data_range >= 150:
                    # assume the values are already in a good range for the
                    # 8 bit image
                    pass
                else:
                    # Rescale the values from 0 to 255 
                    if max_value == min_value:
                        max_value = min_value+1
                    data = (255.0/(max_value-min_value))*(data-min_value)
            
            data = data.astype(types[depth])
            return data.tostring()
        

    def toBufferRGB(self,depth):
        '''
            returns the image data as a binary python string.
        '''
        buffer = None
        if self.type == TYPE_PIL:
            pil = self.pil
            if pil.mode != 'RGB':
                pil = pil.convert('RGB')
            buffer = pil.tostring()
        elif self.type == TYPE_MATRIX_2D:
            mat = self.matrix2d.transpose()
            tmp = zeros((3,self.height,self.width),numpy.float32)
            tmp[0,:] = mat
            tmp[1,:] = mat
            tmp[2,:] = mat
            buffer = mat.tostring()            
        elif self.type == TYPE_MATRIX_RGB:
            mat = self.matrix3d.transpose()
            buffer = mat.tostring()
        elif self.type == TYPE_OPENCV:
            w,h = self.width,self.height
            if self.channels == 3:
                rgb = cv.CreateImage((w,h),cv.IPL_DEPTH_8U,3)
                cv.CvtColor( self.opencv, rgb, cv.CV_BGR2RGB );
                buffer = rgb.tostring()
            elif self.channels == 1:
                rgb = cv.CreateImage((w,h),cv.IPL_DEPTH_8U,3)
                cv.CvtColor( self.opencv, rgb, cv.CV_GRAY2RGB );
                buffer = rgb.tostring()
            else:
                raise TypeError("Operation not supported for image type.")
        else:
            raise TypeError("Operation not supported for image type.")
        
        assert buffer
            
        if depth == self.depth:
            return buffer
        
        else:
            types = {8:numpy.uint8,32:numpy.float32,64:numpy.float64}
            
            # convert the buffer to data
            data = numpy.frombuffer(buffer,types[self.depth])
            
            if depth==8:
                # Make sure the data is in a valid range
                max_value = data.max()
                min_value = data.min()
                data_range = max_value - min_value
                if max_value <= 255 and min_value >= 0 and data_range >= 50:
                    # assume the values are already in a good range for the
                    # 8 bit image
                    pass
                else:
                    # Rescale the values from 0 to 255 
                    if max_value == min_value:
                        max_value = min_value+1
                    data = (255.0/(max_value-min_value))*(data-min_value)
            
            data = data.astype(types[depth])
            return data.tostring()
        

    def toBufferRGBA(self,depth):
        '''
            returns the image data as a binary python string.
            TODO: Not yet implemented
        '''

    def save(self,filename):
        '''
        Save the image to a file.  This is performed by converting to PIL and
        then saving to a file based on on the extension.
        '''
        if filename[-4:] == ".raw":
            # TODO: save as a matrix
            raise NotImplementedError("Cannot save as a matrix")
        #elif filename[-4:] == ".mat":
            # TODO: save as a matlab file
        #    raise NotImplementedError("Cannot save in matlab format")
        else:
            self.asPIL().save(filename)
            
    def show(self):
        '''
        Displays the annotated version of the image.
        '''
        self.asAnnotated().show()
    
##
# Convert a 32bit opencv matrix to a numpy matrix
def OpenCVToNumpy(cvmat):
    #assert cvmat.depth == 32
    #assert cvmat.nChannels == 1
    
    #buffer = cvmat.imageData
    #mat = numpy.frombuffer(buffer,numpy.float32).reshape(cvmat.height,cvmat.width)        
    return np.asarray(cvmat,dtype=np.float64)

##
# Convert a numpy matrix to a 32bit opencv matrix
def NumpyToOpenCV(mat):
    #assert cvmat.depth == 32
    #assert cvmat.nChannels == 1
    #mat = mat.astype(numpy.float32)
    #buffer = mat.tostring()
    #print "MAT:",dir(mat)
    #cvmat = opencv.cvCreateImage( opencv.cvSize(mat.shape[1],mat.shape[0]), opencv.IPL_DEPTH_32F, 1 );
    #print len(cvmat.imageData)
    #print len(buffer)
    #cvmat.imageData = buffer
    #print mat
    #print cvmat
    return cv.fromarray(mat)

class _TestImage(unittest.TestCase):
    
    def setUp(self):
        # Assume these work correctly
        self.im     = Image(os.path.join(pyvision.__path__[0],"data","nonface","NONFACE_46.jpg"))
        self.pil    = self.im.asPIL()
        self.mat    = self.im.asMatrix2D()
        assert self.mat.shape[0] == 640
        assert self.mat.shape[1] == 480
        self.mat3d  = self.im.asMatrix3D()
        assert self.mat3d.shape[0] == 3
        assert self.mat3d.shape[1] == 640
        assert self.mat3d.shape[2] == 480
        self.opencv = self.im.asOpenCV()
            
    def test_PILToBufferGray(self):
        w,h = self.im.size
        buffer = self.im.toBufferGray(8)
        self.assertEqual(len(buffer),w*h)
        buffer = self.im.toBufferGray(32)
        self.assertEqual(len(buffer),4*w*h)
        buffer = self.im.toBufferGray(64)
        self.assertEqual(len(buffer),8*w*h)

    def test_Matrix3DToBufferGray(self):
        im = Image(self.mat3d)
        w,h = im.size
        buffer = im.toBufferGray(8)
        self.assertEqual(len(buffer),w*h)
        buffer = im.toBufferGray(32)
        self.assertEqual(len(buffer),4*w*h)
        buffer = im.toBufferGray(64)
        self.assertEqual(len(buffer),8*w*h)

    def test_Matrix2DToBufferGray(self):
        im = Image(self.mat)
        w,h = im.size
        buffer = im.toBufferGray(8)
        self.assertEqual(len(buffer),w*h)
        buffer = im.toBufferGray(32)
        self.assertEqual(len(buffer),4*w*h)
        buffer = im.toBufferGray(64)
        self.assertEqual(len(buffer),8*w*h)

    def test_PILToMatrix2D(self):
        im = self.im
        pil = im.asPIL().convert('L')
        pil = pil.resize((180,120))
        im = Image(pil)
        mat = im.asMatrix2D()
        for i in range(im.width):
            for j in range(im.height):
                self.assertAlmostEqual(pil.getpixel((i,j)),mat[i,j])
        
    def test_Matrix2DToPIL(self):
        im = Image(self.mat[:180,:120])
        pil = im.asPIL()
        mat = im.asMatrix2D()
        for i in range(im.width):
            for j in range(im.height):
                self.assertAlmostEqual(pil.getpixel((i,j)),mat[i,j])

    def test_PILToMatrix3D(self):
        pil = self.im.asPIL().resize((180,120))
        im = Image(pil)
        mat = im.asMatrix3D()
        for i in range(im.width):
            for j in range(im.height):
                for c in range(3):
                    self.assertAlmostEqual(pil.getpixel((i,j))[c],mat[c,i,j])

    def test_Matrix3D2PIL(self):
        im = Image(self.mat3d[:,:180,:120])
        pil = self.im.asPIL()
        mat = im.asMatrix3D()
        for i in range(im.width):
            for j in range(im.height):
                for c in range(3):
                    self.assertAlmostEqual(pil.getpixel((i,j))[c],mat[c,i,j])
        
    def test_PILToOpenCV(self):
        pil = self.im.asPIL().resize((180,120))
        im = Image(pil)
        cv = im.asOpenCV()
        #Uncomment this code to compare saved images
        #from opencv import highgui
        #highgui.cvSaveImage('/tmp/cv.png',cv)
        #pil.show()
        #Image('/tmp/cv.png').show()

        for i in range(im.width):
            for j in range(im.height):
                for c in range(3):
                    self.assertAlmostEqual(pil.getpixel((i,j))[c],ord(cv.tostring()[i*3+j*im.width*3+2-c]))
        
    def test_OpenCVToPIL(self):
        pil = self.im.asPIL().resize((180,120))
        im = Image(pil)
        cv = im.asOpenCV()
        pil = Image(cv).asPIL()

        for i in range(im.width):
            for j in range(im.height):
                for c in range(3):
                    self.assertAlmostEqual(pil.getpixel((i,j))[c],ord(cv.tostring()[i*3+j*im.width*3+2-c]))
        
    def test_OpenCVToPILGray(self):
        pil = self.im.asPIL().resize((180,120)).convert('L')
        im = Image(pil)
        cv = im.asOpenCV()
        im = Image(cv)
        pil = im.asPIL()
        
        #Uncomment this code to compare saved images
        #from opencv import highgui
        #highgui.cvSaveImage('/tmp/cv.png',cv)
        #pil.show()
        #Image('/tmp/cv.png').show()
        
        # TODO: There seems to be data loss in the conversion from pil to opencv and back.  Why?
        #for i in range(im.width):
        #    for j in range(im.height):
        #        self.assertAlmostEqual(pil.getpixel((i,j)),ord(cv.imageData[i*3+j*im.width*3]))
        
    def test_BufferToOpenCV(self):
        pil = self.im.asPIL().resize((180,120))
        im = Image(pil)
        cvim = im.asOpenCV()
        buffer = im.toBufferRGB(8)

        for i in range(im.width):
            for j in range(im.height):
                for c in range(3):
                    self.assertAlmostEqual(ord(buffer[i*3+j*im.width*3+c]),ord(cvim.tostring()[i*3+j*im.width*3+2-c]))
     
    def test_asOpenCVBW(self):
        pass #TODO: Create tests for this method.
        

