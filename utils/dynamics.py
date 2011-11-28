
"""Bijective functions only.
Currently, derivatives of functions are also required.
"""

class Dynamics(object):
  """
  """

  def __init__(self, function, derivate):
    """
    """
    self.mov_fct = function
    self.spd_fct = derivate

ENTRIES = {
  'smooth_step1' : Dynamics(lambda x: x*x(-2*x+3),              # order 1
                            lambda x: -6*x*(x-1)),
  'cos_slow' : Dynamics(lambda x: x-(sin(2*PI*x)/(2*PI)),
                        lambda x: -cosf(2*x*PI)+1),
  # the most boring one :)
  'linear' : Dynamics(lambda x: x,
                      lambda x: 1)
}

