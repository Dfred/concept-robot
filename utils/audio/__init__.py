import pyaudio
import logging
from utils import set_logging_default

LOG = logging.getLogger(__package__)
set_logging_default(2)

CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 5

class Audio(object):
    """
    """
    P = pyaudio.PyAudio()
    INFOS = [P.get_device_info_by_index(i) for i in range(P.get_device_count())]


    def __init__(self, dev_indices):
        self.streams = []
        for i in dev_indices:
            LOG.debug("opening stream %s", self.INFOS[i])
            s = self.P.open(rate = int(self.INFOS[i]['defaultSampleRate']),
                            channels = CHANNELS,
                            format = FORMAT,
                            input = True,
                            input_device_index = i,
                            frames_per_buffer = CHUNK_SIZE)
            self.streams.append(s)
            
    def cleanup(self):
        for s in self.streams:
            s.stop_stream()
            s.close()
        self.pa.terminate()

    def update(self):
        datas = [ stream.read(CHUNK_SIZE) for stream in self.streams ]
        print "min/max:", [ (min(d), max(d)) for d in datas ]



if __name__ == "__main__":
    import sys

    print '---'
    for dev in sorted(Audio.INFOS, key=lambda x: x['defaultLowInputLatency']):
        if dev['maxInputChannels']:
            print "#%.2i: %.3fms latency, %ichannels %s, %sHz" % (
                dev['index'],
                dev['defaultLowInputLatency'],
                dev['maxInputChannels'],
                dev['defaultSampleRate'],
                dev['name'], )

    if len(sys.argv) > 1:
        a = Audio([ int(arg) for arg in sys.argv[1:] ])
        a.update()
        
