import sys
from time import time

class SimpleFPS(object):
    """
    """

    def __init__(self, rate = 5):
        """
        """
        self.fps = 0
        self.rate = rate
        self.update_nbr = 0
        self.prev_time = time()

    def update(self):
        """
        """
        self.update_nbr += 1
        if self.update_nbr >= self.rate:
            now = time()
            self.fps = self.update_nbr/(now - self.prev_time)
            self.update_nbr = 0
            self.prev_time = now
        return self.fps

    def show(self):
        """
        """
        sys.stdout.write('FPS: %s\r' % self.fps)
        sys.stdout.flush()


if __name__ == "__main__":
    # use timeit for proper profiling
    for fps in (SimpleFPS(),):
        print fps
        for i in range(100000):
            fps.update()
            fps.show()
        print
    
