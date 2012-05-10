import math
import pyaudio
import logging
from utils import set_logging_default
from utils.converters import bytestring2floats

LOG = logging.getLogger(__package__)
set_logging_default(2)


class Audio(object):
    """
    """
    P = pyaudio.PyAudio()
    INFOS = [P.get_device_info_by_index(i) for i in range(P.get_device_count())]
    def __init__(self, dev_indices):
        self.streams = {}
        self.datas = []
        for i in dev_indices:
            LOG.debug("opening stream %s", self.INFOS[i])
            sr = int(self.INFOS[i]['defaultSampleRate'])
            self.streams[i] = self.P.open(rate = sr,
                                          channels = 1,
                                          format = pyaudio.paFloat32,
                                          input = True,
                                          input_device_index = i,
                                          frames_per_buffer = sr)
#        print dir(self.streams.values()[0])
            
    def cleanup(self):
        for s in self.streams.values():
            s.handle.stop_stream()
            s.handle.close()
        self.pa.terminate()

    def update_input(self, duration):
        """Can raise IOError, if so device index is in e[0].
        """
        for dev_i, stream in self.streams.items():
            try:
                stream.data = bytestring2floats( stream.read(
                    int(duration * stream._frames_per_buffer)) )
            except IOError, e:
                raise IOError(dev_i, e)

    def set_factor(self, dev_index, factor):
        LOG.debug("stream #%i: data factor now %f", dev_index, factor)
        self.f1 = factor

    def get_asymetry(self, duration):
        self.update_input(duration)
        s0, s1 = self.streams.values()
        return (math.sqrt( sum(s**2 for s in s0.data) / len(s0.data) ) -
                math.sqrt(sum((s*self.f1)**2 for s in s1.data) / len(s1.data)))


if __name__ == "__main__":
    import sys

    def plot_sig(sigs):
        import pylab
        pylab.plot(sigs)
        pylab.show()

    def calibrate(audio):
        """Assumes audio input data has no offset.
        """
        import time; print "Qeep quiet for a moment please!"; time.sleep(.5)
        f = 1
        s0, s1 = audio.streams.values()
        while True:
            audio.update_input(.1)
            fixed_d0 = [ s**2 for s in s0.data ]
            fixed_d1 = [ (s*f)**2 for s in s1.data ]
            dBu0 = math.sqrt( sum(fixed_d0) / len(s0.data) )
            dBu1 = math.sqrt( sum(fixed_d1) / len(s1.data) )
            print "fixed data diff %+.6f, factor %f, dBu diff: %.6f" % (
                abs(sum(fixed_d0))-abs(sum(fixed_d1)), f, abs(dBu0 - dBu1) )
            if abs(dBu0 - dBu1) < .00001:
                break
            f *= dBu0>dBu1 and 1.05 or 0.95
        return f
            
    print '---'
    for dev in sorted(Audio.INFOS, key=lambda x: x['defaultLowInputLatency']):
        if dev['maxInputChannels']:
            print "#%.2i: %.3fms latency, %ichannels %sHz, %s" % (
                dev['index'],
                dev['defaultLowInputLatency'],
                dev['maxInputChannels'],
                dev['defaultSampleRate'],
                dev['name'], )

    if len(sys.argv) > 1:
        devs_i = [ int(arg) for arg in sys.argv[1:] ]
        a = Audio(devs_i)
        factor = calibrate(a)
        a.set_factor(devs_i[1], factor)
        i, diff = 1, []
        while True:
            if i % 100 == 0:
                plot_sig(diff)
                diff = []
            try:
                diff.append(a.get_asymetry(.1))
            except IOError, e:
                LOG.critical("error reading stream %s", e)
                exit(2)
            print "asymetry: %+f\r" % diff[-1]
            i += 1
