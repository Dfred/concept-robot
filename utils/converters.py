import struct

def bytestring2shorts(data):
    return struct.unpack("%dh"%(len(data)/2), data)
def bytestring2floats(data):
    return struct.unpack("%df"%(len(data)/4), data)
