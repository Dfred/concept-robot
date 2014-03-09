"""iCub backend: AUs to Yarp ports mapper.
* eyes: /head -- [3,4,5]
* neck: /head -- [0,1,2]
* eyelids: /face/raw/in -- 'S'
* eyebrows and mouth: /face/raw/in -- 'L','R','M'
"""

import yarp

from RAS.face import FaceHandlerMixin, FaceServerMixin
from RAS.spine import SpineServerMixin

yarp.Network.init()

#XXX keep order as it's used for mapping
#XXX iCub also has vergence as the last (6th) DOF.
AUs = [ '53.5', '55.5', '51.5', '63.5', 
        '61.5'                                  ## for both eyes
        ]

## mandatory function returning server mixin and handler mixin classes.
def get_networking_classes():
  return (SrvMix_iCub, FaceHandlerMixin)


class SrvMix_iCub(FaceServerMixin, SpineServerMixin):
  """This script is our entry point. See towards the end below.
  Handles the head and neck of iCub's body.
  """
  def __init__(self, conf):
    """
    """
    self.name = 'iCub'
    super(SrvMix_iCub,self).__init__(conf)      ## sets self.SW_limits
    root = conf['yarp_root']+'/'
    self.__init_head(root)
    self.__init_facialFeatures(root)
    if not self.set_available_AUs(AUs,):
      raise StandardError("Error setting AUs")      

  def __init_head(self, root):
    name = "head"
    props = yarp.Property()
    props.put("device","remote_controlboard")
    props.put("local", "/ARAS/"+name)
    props.put("remote",root+name)
    self.driver = yarp.PolyDriver(props)
    if not self.driver.isValid():
      raise StandardError("Can't connect to Yarp or its port. "
                          "If started, check its log.")
    self.iPos = self.driver.viewIPositionControl()
    self.iVel = self.driver.viewIVelocityControl()
    self.iPID = self.driver.viewIPidControl()
    self.iEnc = self.driver.viewIEncoders()
    self.iLim = self.driver.viewIControlLimits()
    self.nbr_axis = self.iPos.getAxes()         ## remember vector size
    encs = self.get_encoders()
    print "%i neck encoders:" % self.nbr_axis, [
      "%.3f"%encs.get(i) for i in range(self.nbr_axis)]

  def __init_facialFeatures(self, root):
    name = "facialFeatures"
    # props = yarp.Property()
    # props.put("device","remote_controlboard")
    # props.put("local", "/ARAS/"+name)
    # props.put("remote",root+"/face/eyelids")
    self.ff_port = yarp.BufferedPortBottle()
    self.ff_port.open(root+"/face/eyelids")     ## for writing

  def _read_cb(self, bottle):
    """Read a bottle (ascii/bin interface to communication).
    """
    print bottle

  def _nval2enc(self, nval, axis):
    """Translates from normalized AU value to iCub value.
    Return: iCub value
    """

  # def commit_AUs(self, triplets_fifo):
  #   """Called upon reception of command 'commit'. Checks and commit AU updates.
  #   >triplets_fifo: fifo of triplets, i.e: (AU, value, duration).
  #   Return: None
  #   """
  #   encs = [ self._nval2enc(val,i) for i,(AU,val,delay) in 
  #            enumerate(triplets_fifo) ]
  #   self.set_encoders(encs)

  def get_AU__vals(self):
    """Read robot values and translate them to RAS internal AU format.
    Return: ( (AU,val), ... )
    """
    encs = self.get_encoders()
    print encs[0], encs[1]
    AU__vals = zip(AUs, [encs.get(i) for i in range(self.nbr_axis)] )
    ## normalize. Thankfully, a positive rotation is the same for iCub and RAS.
    #TDL: normalize
    return AU__vals

  def get_encoders(self):
    """Read current encoder values.
    Return: yarp Vector
    """
    tmp_encs = yarp.Vector(self.nbr_axis)
    self.iEnc.getEncoders(tmp_encs.data())
    return tmp_encs

  def values_from_triplets(self, nvals):
    """Translates from nvals (and index in iterable) to iCub internal value.
    >nvals: normalized values from triplets
    Return: a yarp vector.
    """
    pass
#    return [ self.SW_limits[
