import math
import threading
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
        self.datas = [None,None]
        self.fR = 1
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
        """Can raise IOError. Data is raw (doesn't account for factor).
        """
        if len(self.streams) == 1:
            dev, strm = self.streams.items()[0]
            d = array('f', strm.read(int(duration * strm._frames_per_buffer)))
            self.datas = zip( *((d[i],d[i+1]) for i in range(0,len(d),2)) )
            return
        for i, s in enumerate(self.streams.values()):
            self.datas[i] = array('f',
                                  s.read(int(duration * s._frames_per_buffer)))

    def set_factor(self, factor):
        LOG.debug("data factor now %f", factor)
        self.fR = factor

    def get_dBu(self, duration):
        """Includes factor"""
        self.update_input(duration)
        dL, dR = self.datas
        return ( math.sqrt(sum( d         **2 for d in dL) / len(dL)),
                 math.sqrt(sum((d*self.fR)**2 for d in dR) / len(dR)) )

    def snd_ev(self, time_window, threshold):
        while self.monitoring:
            dBuL, dBuR = self.get_dBu(time_window)
            if dBuL > threshold or dBuR > threshold:
                print '***** BANG BANG *****'
                callback(dBuL, dBuR)
        self.thread = None
    def monitor_event(self, callback, ev_threshold=None, time_window=.01):
        """Starts a thread monitoring sound events on available sound channels.
        If ev_threshold is not specified, it's read from configuration.
        Callback shall accept 2 arguments: left and right dBu (aka power RMS).
        Callback will be called if the dBu is above threshold.
        Set callback to None to stop the thread.
        """
        if callback is None and self.thread:
            self.monitoring = False
        else:
            self.monitoring = True
            if ev_threshold is None:
                ev_threshold = conf.lib_audition[sensor_name]['ev_threshold']
            self.thread = threading.Thread(target=self.snd_ev, 
                                           name='sound_ev',
                                           args=(time_window,ev_threshold))
            self.thread.start()

if __name__ == "__main__":
    import sys, time, pylab

    def calibrate(audio, step=.001):
        """Assumes audio input data has no offset.
        """
        print "Qeep quiet for a moment please!"; time.sleep(.3)
        f = 1
        while True:
            dBu0, dBu1 = audio.get_dBu(.1)
            if abs(dBu0 - dBu1) < .00001:
                break
            f *= dBu0>dBu1 and 1+step or 1-step
            audio.set_factor(f)
             
    print '---'
    for dev in sorted(Audio.INFOS, key=lambda x: x['defaultLowInputLatency']):
        if dev['maxInputChannels']:
            print "#%.2i: %.3fms latency, %ichannels %sHz, %s" % (
                dev['index'],
                dev['defaultLowInputLatency'],
                dev['maxInputChannels'],
                dev['defaultSampleRate'],
                dev['name'], )

    if 1 <= len(sys.argv) <= 4:
        a = Audio()
        if len(sys.argv) == 2:
            a.use_device(int(sys.argv[1]), 2)
        else:
            a.use_device(int(sys.argv[1]), 1)
            a.use_device(int(sys.argv[2]), 1)

        calibrate(a, step=len(sys.argv)==4 and float(sys.argv[3]) or 0.001)

        datas, dBu, diff = [[],[]], [], []
        for i in range(1000):
            try:
                dBu.append(a.get_dBu(.01))
                datas[0].extend(a.datas[0])
                datas[1].extend(a.datas[1])
                diff.append(dBu[-1][0] - dBu[-1][1])
            except IOError, e:
                LOG.critical("error reading stream %s", e)
                exit(2)
            print "%.3i asymetry: %+f\r" % (i, diff[-1])

        datL, datR = datas
        dBuL, dBuR = zip(*dBu)
        datfR = [ d*a.fR for d in datR ]
        XdatL, XdatR, XdBu = range(len(datL)),range(len(datR)),range(len(dBuL))

        pylab.subplot(4,1,1)
        pylab.plot(XdatL,datL,'b', XdatR,datfR,'r')
        pylab.ylabel("adjusted")

        pylab.subplot(4,1,2)
        pylab.plot([datL[i] - datfR[i] for i in XdatL])
        pylab.ylabel("signal diff")

        pylab.subplot(4,1,3)
        pylab.plot(XdBu,dBuL,'b', XdBu,dBuR,'r')
        pylab.ylabel("dBuL/R")

        pylab.subplot(4,1,4)
        pylab.plot(diff)
        pylab.ylabel("dBu diff")
        pylab.show()
        
    else:
        print sys.argv[0]+" [device index [device index]]"
