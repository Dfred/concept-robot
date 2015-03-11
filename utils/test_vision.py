################################################################################
# This software is provided for academic research only: it is OSS but not GPL!
# In such a case, you can redistribute this software and/or modify it,
# provided you do not modify this license. Any other use is not permitted.

# ARAS is the open source software (OSS) version of the basic component of
# LightHead's software suite. 

# ARAS stands for Abstract Robotic Animation System, and features actuator,
# sensor, animation and remote management high-level interfaces.
# In particular, ARAS helps animating a head (virtual or physical), provides
# supporting algorithms for vision and hearing, as well as contributions from
# other scholars.
# Copyright 2009 - Frédéric Delaunay: dr.frederic.delaunay@gmail.com

# This software is the low-level Human-Robot-Interaction part of the CONCEPT
# project, which took place at the University of Plymouth (UK).
# The project stemed from by Frédéric Delaunay's PhD, himself under the
# supervision of professor Tony Belpaeme. The PhD project started in late 2008
# and ended in late 2011 but this part of the software is still maintained.
# Visit http://www.tech.plym.ac.uk/SoCCE/CONCEPT/ for more information.

# This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  General Public License for more details.
################################################################################

#
if __name__ == "__main__":
    import sys, time
    import argparse
    import logging

    from utils import LOGFORMATINFO
    logging.basicConfig(level=logging.DEBUG, **LOGFORMATINFO)

    from utils import conf
    from utils.vision import CamUtils

    def run(cap):
        faces = cap.find_faces()
        if faces:
            cap.mark_rects(faces)
            print("Width: {0:.6f} measure cam - face distance (in m.)".format(
                faces[0].w/float(cap.camera.size[0])))
            try:
                print(cap.get_face_3Dfocus(faces)[0][2])
            except AssertionError:
                pass
#        my_fps.show()

    conf.set_name('lighty')
    conf.load(required_entries='lib_vision')

    parser = argparse.ArgumentParser(description='test this vision module')
    parser.add_argument('-c', help='camera resolution', type=int, nargs=2,
                        metavar=('Width', 'Height'))
    parser.add_argument('-r', help='enable record', action='store_true')
    args = parser.parse_args(sys.argv[1:])
 
    cap = CamUtils('laptop')
    if args.c:
        print("using camera resolution: %sx%s" % args.c)
        cap.set_device(resolution=args.c)
    if args.r:
        fname = time.strftime("vision-%H:%M:%S.avi")
        print("recording vision as "+fname)
        cap.toggle_record(fname)
    cap.toggle_face_detection(True)
    cap.toggle_fps(True)
    cap.gui_create()
    cap.gui_loop(run, [cap])
    print("done")
