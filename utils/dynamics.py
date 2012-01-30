
"""Monotonically increasing functions only with f(0)=0 and f(1)=1.
Currently, derivatives of functions are also required.
"""


class Profile(object):
  """
  """

  def __init__(self, function, derivate):
    """
    """
    self.fct_expr = function
    self.drv_expr = derivate


ENTRIES = {
  'smooth_step1' : Profile("x*x*(-2*x+3)","-6*x*(x-1)"),
  'cos_slow' : Profile("x-(sin(2*PI*x)/(2*PI))","-cosf(2*x*PI)+1"),
  'linear' : Profile("x","1")
}

