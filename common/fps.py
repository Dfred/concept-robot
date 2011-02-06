import sys
import time

class SimpleFPS(object):
    """
    """

    def __init__(self, rate = 5):
        """
        """
        self.rate = rate
        self.print_nbr = 0
        self.prev_time = time.time()

    def update(self):
        """
        """
        now = time.time()
        if self.print_nbr >= self.rate:
            sys.stdout.write('FPS: %s\r' % (1.0/(now - self.prev_time)))
            sys.stdout.flush()
            self.print_nbr = 1
        else:
            self.print_nbr += 1
        self.prev_time = now
