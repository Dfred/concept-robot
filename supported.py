"""Defines constants not part of the configuration.
"""
from math import pi

## backends. Some backends can be run along others.
BACKENDS = ('blender', 'katHD400s_6M', 'iCub', 'dynamixels')

## protocol keywords
SECTION_FACE = 'face'
SECTION_GAZE = 'gaze'
SECTION_SPNE = 'spine'
SECTION_LIPS = 'lips'
SECTION_DYNM = 'dynamics'
SECTIONS = (SECTION_FACE, SECTION_GAZE, SECTION_LIPS, SECTION_SPNE, SECTION_DYNM)

## HW libraries
LIB_VISION = 'vision'
LIB_HEARING = 'hearing'

## list of AUs recognized by the system. These are mostly based on FACS.
## 2 column definition makes it easier to see (a)symetric AUs
VALID_AUs = ("01L","01R",
             "02L","02R",
             "04L","04R",
             "05L","05R",
             "06L","06R",
             "07L","07R",
             "08L","08R",
             "09L","09R",
             "10L","10R",
             "11L","11R",
             "12L","12R",
             "13L","13R",
             "14L","14R",
             "15L","15R",
             "16L","16R",
             "17",
             "18L","18R",
             "20L","20R",
             "21L","21R",
             "22L","22R",
             "23L","23R",
             "24L","24R",
             "25","26","27",
             "28L","28R",
             "31",
             "32L","32R",
             "33L","33R",
             "38L","38R",
             "39L","39R",
             "51.5","53.5","55.5",              # Neck
             "61.5L","61.5R","63.5",            # Eyes orientation
             "93X","93Y","93Z","93mZ","93bT",   # Tongue position
             "94","95",                         # Tongue shape
             "SYL","SYR", "SZL","SZR",          # Shoulders
             "ePS",                             # Eye, Pupil Stretcher
             "skB","skS",                       # Skin Effects
             "thB",                             # Thorax Breather
             "TX","TY","TZ",
             )

## defaults
DEFAULTS = {
  "katHD400s_6M" : {
    "sections" : (SECTION_SPNE,),
    "hardware_addr" : "192.168.168.232",
    "pose_rest" : (6350, 5600, 1800, 24900, None, None),
    "pose_neutral" : (6350, -8500, -7500, 27300, None, None),
    ## software axis range
    "axis_limits" : { 'TX'  :(-.3 ,  .1 ),
                      'TZ'  :(-.5 ,  .5 ),
                      '53.5':(-.12 , .6, True),         ## extra: inversed rot.
                      '55.5':(-.25,  .25),
                      '51.5':(-.4 ,  .4, True)
      },
    },

  "blender" : {
    "sections" : (SECTION_FACE, SECTION_GAZE, SECTION_LIPS, SECTION_SPNE),
    "proj_matrix" : ( ( 17.50, -0.30,   .12,    .7 ),
                      (- 0.18,  8.91,   .33,   1.9 ),
                      (- 0.10,  0.  , -0.10, - 0.2 ),
                      (- 0.10, -0.6 ,  1.26,  16.78) ),
    "axis_limits" : {'51.5' : (-15*pi, 15*pi),
                     '53.5' : (-22*pi, 25*pi),
                     '55.5' : (-15*pi, 15*pi),
                     'TX'   : (-20*pi, 30*pi),
                     'TY'   : (-17*pi, 15*pi),
                     'TZ'   : (-15*pi, 15*pi),
                     'SY'   : (-17*pi, 15*pi),
                     'SZ'   : (-17*pi, 15*pi)
                     },
    },

  "iCub" : {
    "sections" : (SECTION_FACE, SECTION_GAZE, SECTION_LIPS, SECTION_SPNE),
    "yarp_root" : '/icubSim',
    "axis_limits" : {
      ## iCub v1's neck is under dimensioned, so be gentle.
      '51.5' : (-30*pi, 30*pi),                         ## Z, really [-50, 50]
      '53.5' : (-30*pi, 20*pi),                         ## X, really [-40, 30]
      '55.5' : (-40*pi, 40*pi),                         ## Y, really [-60, 60]
      ## also include camera orientations
      '61.5' : (-50*pi, 50*pi),
      '63.5' : (-35*pi, 15*pi), },
    "pose_rest" : (0, 0, 0, 0, 0, 0),
    "pose_neutral" : (0, 0, 0, 0, 0),
    },
}

## Description of supported hardware. "label" is a required field.
HW_LIBRARIES = {
  ## entries' identifiers are built with vendor_id:device_id
  LIB_VISION : {
    "408:2fb1" : { "description" : "Quanta Computer HD Camera",
                   "dev_index" : 0,
                   "resolution" : (800,600),
                   "XY_factors" : (.2, .1),
                   "depth_fct" : "0.105*x**-1.364",
                   },
    },

  LIB_HEARING : {
    "8086:1c20" : { "description":"Intel 6 Series/C200 Series HD Audio (rev 5)",
                    "dev_index" : (6,6),                ## stereo capable
                    "dB_factor" : .1,
                    },
    },
  }
