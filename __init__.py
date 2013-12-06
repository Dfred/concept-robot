"""Entry point for most backends. Should also ensure conf is properly loaded
before starting the show.
"""
from utils import print_remaining_threads

if __name__ == "__main__":
  import time
  import RAS
  ## threaded server flag , threaded clients flag 
  RAS_THREAD_INFO = (False, True)
  try:
    server = RAS.initialize(RAS_THREAD_INFO,"lighty")
  except StandardError as e:
    print "error initializing the RAS:", e
    exit(1)

  print "starting the RAS"
  server.serve_forever()
  time.sleep(.5)
  print_remaining_threads(prefix="remaining threads:\n\t")
  print "RAS finished"
