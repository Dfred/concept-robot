import math
import pyaudio
import logging
from array import array
from utils import set_logging_default
from utils import conf

LOG = logging.getLogger(__package__)
set_logging_default(2)


class Audio(object):
    """
    """
    P = pyaudio.PyAudio()
    INFOS = [P.get_device_info_by_index(i) for i in range(P.get_device_count())]
    def __init__(self, sensor_name=None):
        self.streams = {}
        self.datas = []
        if sensor_name:
            devs = conf.lib_audition[sensor_name]['dev_index']
            if devs[0] == devs[1]:
                self.use_device(devs[0], 2)
            else:
                self.use_device(devs[0], 1)
                self.use_device(devs[1], 1)
        
    def use_device(self, dev_index, channels):
        """dev_indices: tuple of one or more inde
        """
        LOG.debug("opening stream %s", self.INFOS[dev_index])
        sr = int(self.INFOS[dev_index]['defaultSampleRate'])
        self.streams[dev_index] = self.P.open(rate = sr,
                                              channels = channels,
                                              format = pyaudio.paFloat32,
                                              input = True,
                                              input_device_index = dev_index,
                                              frames_per_buffer = sr * channels)
            
    def cleanup(self):
        for s in self.streams.values():
            s.handle.stop_stream()
            s.handle.close()
        self.pa.terminate()

    def update_input(self, duration):
        """Can raise IOError, if so device index is in e[0].
        """
        if len(self.streams) == 1:
            dev, strm = self.streams.items()[0]
            d = array('f', strm.read(int(duration*strm._frames_per_buffer)))
            self.datas = zip( *( (d[i],d[i+1]) for i in range(0,len(d),2) ))
            return
        i = 0
        for dev_i, stream in self.streams.items():
            try:
                self.datas[i] = bytestring2floats( stream.read(
                    int(duration * stream._frames_per_buffer)) )
            except IOError, e:
                raise IOError(dev_i, e)
            i += 1

    def set_factor(self, factor):
        LOG.debug("data factor now %f", factor)
        self.f1 = factor

    def get_datas(self):
        return self.datas

    def get_asymetry(self, duration):
        self.update_input(duration)
        dL, dR = self.datas
        return (math.sqrt(sum( d         **2 for d in dL) / len(dL)) -
                math.sqrt(sum((d*self.f1)**2 for d in dR) / len(dR)) )


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
        while True:
            audio.update_input(.1)
            s0, s1 = audio.get_datas()
            fixed_d0 = [ s**2 for s in s0 ]
            fixed_d1 = [ (s*f)**2 for s in s1 ]
            dBu0 = math.sqrt( sum(fixed_d0) / len(s0) )
            dBu1 = math.sqrt( sum(fixed_d1) / len(s1) )
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

    if 1 <= len(sys.argv) < 3:
        a = Audio()
        if len(sys.argv) == 2:
            a.use_device(int(sys.argv[1]), 2)
        else:
            a.use_device(int(sys.argv[1]), 1)
            a.use_device(int(sys.argv[2]), 1)
        a.set_factor(calibrate(a))
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
    else:
        print sys.argv[0]+" [device index [device index]]"
