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
        self.xyz = [[.0, 0]] *3         # value , attack_time (TODO: torso)
        self.rotators = { 'neck': self.server.rotate_neck,
                          'torso': self.server.set_torso_orientation }

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
        """Absolute rotation on 1 axis.
        Syntax is: AU_name, target_value, attack_time (in s.)"""
        args = argline.split()
        if len(args) != 3:
            LOG.warning('AU: expected 3 arguments (got %s)', args)
            return
        dim = ('53.5', '55.5', '51.5').index(args[0])
        self.xyz[dim] = [ float(v) for v in args[1:] ]

    def cmd_commit(self, argline):
        """from expr2"""
        self.server.animate(self.xyz, None)

    def cmd_rotate(self, argline):
        """relative rotation on 3 axis.
        Syntax is: neck|torso x y z [wait]"""
        if not argline:
            self.send_msg('rot_neck %s' % \
                              SpineBase.round(self.server.get_neck_info().rot))
            self.send_msg('rot_torso %s' % \
                              SpineBase.round(self.server.get_torso_info().rot))
            return

        args = argline.split()
        if len(args) < 4:
            raise SpineProtocolError('rotate: 4 or 5 arguments required')
        wait = len(args) == 5 and args[4] == 'wait'
        xyz = [ round(float(arg),SpineBase.PRECISION) for arg in args[1:4] ]
        try:
            self.rotators[args[0]](xyz, wait)
        except KeyError, e:
            raise SpineProtocolError("invalid body-part %s (%s)", args[0], e)

    def cmd_move(self, argline):
        """relative position on 3 axis"""
        if not argline:
#            self.send_msg('head_pos %s' % self.server.get_neck_info().pos)
            return
        args = [ float(arg) for arg in argline.split(',') ]
        self.server.set_neck_rot_pos(pos_xyz=tuple(args))


class SpineBase(object):
    """API for spine management (includes neck)."""

    PRECISION = 4       # number of digits for real part

    @staticmethod
    def round(iterable):
        """version for iterables, different signature from __builtins__.round"""
        return [ round(v, SpineBase.PRECISION) for v in iterable ]

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
    
    def set_neck_orientation(self, axis3):
        """Absolute orientation:"""
        raise NotImplemented()

    def set_torso_orientation(self, axis3):
        """Absolute orientation:"""
        raise NotImplemented()

    def set_neck_rot_pos(self, axis3_rot=None, axis3_pos=None):
        """Set head orientation and optional position from neck reference point.
        axis3_rot: triplet of floats in radians
        axis3_pos: triplet of floats in meters
        """
        # to be overriden
        raise NotImplemented()

    # TODO: poll AU values from the AU pool after each update
    def animate(self, neck_rot_attack, torso_rot_attack):
        """Set neck and torso's absolute orientation with timing information.
        neck_rot_attack:  X,Y,Z: (orientation_in_rads, attack_time_in_s)
        torso_rot_attack: X,Y,Z: (orientation_in_rads, attack_time_in_s)
        """
        # raise NotImplemented()
        self.set_neck_orientation([ rad for rad, att in neck_rot_attack])

    def rotate_neck(self, xyz, wait=True):
        """Set neck's relative orientation."""
        ptp = self.get_neck_info().rot
        xyz_ = map(float.__add__, ptp, xyz)
        LOG.debug('neck %s + %s = %s', ptp, xyz, xyz_)
        self.set_neck_orientation(xyz_, wait)

    def rotate_torso(self, xyz, wait=True):
        """Set torso's relative orientation."""
        ptp = self.get_torso_info().rot
        xyz_ = map(float.__add__, ptp, xyz)
        LOG.debug('torso %s + %s = %s', ptp, xyz, xyz_)
        self.set_torso_orientation(xyz_, wait)

    def switch_on(self):
        """Mandatory 1st call after hardware is switched on.
        Starts calibration if needed.
        """
        raise NotImplemented()

    def switch_off(self):
        """Set the robot's pose for safe hardware switch off."""
        raise NotImplemented()

    def unlock(self):
        """Unlock spine after collision detection cause locking"""
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
    while server.running:
        try:
            server.serve_forever()
        except SpineProtocolError, e:
            print 'Protocol Error:', e
    LOG.debug("Spine server done")
