#
# The spine module controls orientation and position of the robot torso and neck
# It provides a high-level API and relies on the backend implemented in the
#  module 'spine_backend'
#
# The API is limited to hardware implementation and indeed results are hardware-
#  dependant. However as long as the hardware provides the required DOF and
#  backend provides required functions, the end-result should be similar.
#
import comm
import logging
LOG = logging.getLogger(__package__)


class SpineProtocolError(comm.ProtocolError):
    pass

class SpineError(comm.CmdError):
    pass

class NotImplemented(SpineError):
    pass


class SpineElementInfo(object):
    """Capabilities and Information about an element of the spine"""

    def __init__(self):
        self.origin = [.0,]*3   # global coordinates of origin
        self.limits_rot = []    # min and max orientation values for each axis
        self.limits_pos = []    # min and max position values for each axis
        self.rot = [None,]*3
        self.pos = [None,]*3

class TorsoInfo(SpineElementInfo):
    pass
class NeckInfo(SpineElementInfo):
    pass


class SpineComm(object):
    """
    """

    def __init__(self):
        self.map = ('53.5', '55.5', '51.5') 
        self.xyz = [('.0', '0'),('.0','0'),('.0','0')]

    def cmd_switch(self, argline):
        args = argline.split()
        try:
            fct = getattr(self.server, 'switch_'+args[0])
        except AttributeError :
            LOG.debug('no switch_%s function available', args[0])
            return
        if len(args)>1:
            fct(int(args[1]))
        else:
            fct()

    def cmd_AU(self, argline):
        """from expr2: AU, target, attack_time"""
        args = argline.split()
        self.xyz[self.map.index(args[0])] = args[1:]

    def cmd_rotate(self, argline):
        """relative rotation on 3 axis.
        Syntax is: neck|torso x y z [wait]"""
        if not argline:
            self.send_msg('head_rot %s' % self.server.get_neck_info().rot)
            return
        args = argline.split()
        if len(args) < 4:
            raise SpineProtocolError('4 arguments required')
        xyz = [ float(arg) for arg in args[1:4] ]
        wait = len(args) == 5 and args[4] == 'wait'
        if args[0] == 'neck':
            self.server.set_neck_orientation(xyz, wait)
        elif args[0] == 'torso':
            self.server.set_torso_orientation(xyz, wait)
        else:
            raise SpineProtocolError("invalid body-part %s", args[0])

    def cmd_move(self, argline):
        """relative position on 3 axis"""
        if not argline:
#            self.send_msg('head_pos %s' % self.server.get_neck_info().pos)
            return
        args = [ float(arg) for arg in argline.split(',') ]
        self.server.set_neck_rot_pos(pos_xyz=tuple(args))

    def cmd_commit(self, argline):
        """from expr2"""
        self.cmd_rotate('neck '+' '.join([value for time, value in self.xyz]))


class SpineBase(object):
    """API for spine management (includes neck)."""

    def __init__(self):
        """torso_info and neck_info are readonly properties"""
        self._torso_info = TorsoInfo()
        self._neck_info  = NeckInfo()
        self._speed = 0.0        # in radians/s
        self._accel = 0.0        # speed increment /s
        self._tolerance = 0.0    # in radians
        self._motors_on = False
        self._lock_handler = None

    # Note: property decorators are great but don't allow child class to define
    #       just the setter...

    def get_torso_info(self):
        """Returns TorsoInfo instance"""
        return self._torso_info

    def get_neck_info(self):
        """Returns NeckInfo instance"""
        return self._neck_info

    def get_tolerance(self):
        """In radians"""
        return self._tolerance

    def set_tolerance(self, value):
        """In radians"""
        self._tolerance = value

    def set_lock_handler(self, handler):
        """function to call upon collision detection locking"""
        self._lock_handler = handler
    
    def switch_on(self):
        raise NotImplemented()

    def switch_off(self):
        raise NotImplemented()

    def unlock(self):
        """Unlock spine after collision detection cause locking"""
        raise NotImplemented()

    def set_neck_orientation(self, axis3):
        raise NotImplemented()

    def set_torso_orientation(self, axis3):
        raise NotImplemented()

    def set_neck_rot_pos(self, axis3_rot=None, axis3_pos=None):
        """Set head orientation and optional position from neck reference point.
        axis3_rot: triplet of floats in radians
        axis3_pos: triplet of floats in meters
        """
        # to be overriden
        raise NotImplemented()

    def set_all(self, axis3_no, axis3_np, axis3_to):
        """Set orientation, position for neck and torso's orientation in one go.
        axis3_no: neck orientation (triplet of floats in radians)
        axis3_np: neck position (triplet of floats in meters)
        axis3_to: torso orientation
        """
        raise NotImplemented()

try:
    from spine.backend import SpineHW as Spine
except ImportError, e:
    print 
    print '*** SPINE MISCONFIGURATION ***'
    print 'Make sure the SPINE backend link points to your backend!'
    print 'for your information:', e
    raise 

__all__ = ['SpineHw', 'TorsoInfo', 'NeckInfo', 'NotImplemented', 'SpineException']


if __name__ == '__main__':
    import sys
    import conf
    try:
        comm.set_default_logging(debug=True)
        conf.load()
        server = comm.create_server(Spine, SpineComm, conf.conn_spine,
                                    (False,False))
    except (conf.LoadException, UserWarning), err:
        comm.LOG.error("FATAL ERROR: %s (%s)", sys.argv[0], ':'.join(err))
        exit(-1)
    server.start()
    server.serve_forever()
    LOG.debug("Spine server done")
