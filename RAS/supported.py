"""Defines constants not part of the configuration.
"""

ORIGINS = ('face', 'gaze', 'spine', 'dynamics') # protocol keywords
VALID_AUs = ("01L","01R",                   # also easier to see (a)symetric AUs
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
