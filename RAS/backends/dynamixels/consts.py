try:
    import dynamixel
except ImportError as e:
    print """dynamixel for python could not be imported.
 Try with easy-install or pip"""
    sys.exit(EXIT_DEPEND)

BAUD_RATES = sorted([ int(br[5:]) for br in dynamixel.BAUD_RATE.keys() ])
