import sys
import time

class SimpleFPS(object):
    """
    """

    def __init__(self, rate = 5):
        """
        """
        self.fps = 0
        self.rate = rate
        self.update_nbr = 0
        self.prev_time = time.time()

    def update(self):
        """
        """
        if self.update_nbr >= self.rate:
            now = time.time()
            self.fps = self.update_nbr/(now - self.prev_time)
            self.update_nbr = 0
            self.prev_time = now
        else:
            self.update_nbr += 1
        return self.fps

    def show(self):
        """
        """
        sys.stdout.write('FPS: %s\r' % self.fps)
        sys.stdout.flush()
