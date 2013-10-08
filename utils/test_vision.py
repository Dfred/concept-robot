###############################################################################
# TEST and XY_FACTORS creation
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
