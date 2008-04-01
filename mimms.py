#!/usr/bin/python
# -*- coding: utf-8 -*-

from ctypes import *

libmms = cdll.LoadLibrary("libmms.so.0")

# opening and closing the stream
libmms.mmsx_connect.argtypes = [c_void_p, c_void_p, c_char_p, c_int]
libmms.mmsx_connect.restype = c_void_p

libmms.mmsx_close.argtypes = [c_void_p]
libmms.mmsx_close.restype = None

# querying length and position
libmms.mmsx_get_current_pos.argtypes = [c_void_p]
libmms.mmsx_get_current_pos.restype = c_longlong

libmms.mmsx_get_length.argtypes = [c_void_p]
libmms.mmsx_get_length.restype = c_uint

libmms.mmsx_get_time_length.argtypes = [c_void_p]
libmms.mmsx_get_time_length.restype = c_double

# seeking
libmms.mmsx_get_seekable.argtypes = [c_void_p]
libmms.mmsx_get_seekable.restype = c_int

libmms.mmsx_seek.argtypes = [c_void_p, c_void_p, c_longlong, c_int]
libmms.mmsx_seek.restype = c_longlong

libmms.mmsx_time_seek.argtypes = [c_void_p, c_void_p, c_double]
libmms.mmsx_time_seek.restype = c_int

# reading data
libmms.mmsx_read.argtypes = [c_void_p, c_void_p, c_char_p, c_int]
libmms.mmsx_read.restype = c_int

class MMSError(Exception): pass

class MMSStream:

  def __init__(self, url, bandwidth):
    self.mms = libmms.mmsx_connect(None, None, url, bandwidth)
    if not self.mms:
      raise MMSError("libmms connection error")

  def length(self):
    return libmms.mmsx_get_length(self.mms)

  def duration(self):
    return libmms.mmsx_get_time_length(self.mms)

  def seekable(self):
    return libmms.mmsx_get_seekable(self.mms)

  def read(self):
    buffer = create_string_buffer(4096)
    count = libmms.mmsx_read(0, self.mms, buffer, 4096)
    if bytes < 0:
      raise MMSError("libmms read error")
    return buffer[:count]

  def data(self):
    while True:
      data = self.read()
      if data:
        yield data
      else:
        break

  def close(self):
    libmms.mmsx_close(self.mms)

if __name__ == "__main__":
  stream = MMSStream("mms://demandcnn.stream.aol.com/cnn/world/2002/01/21/jb.shoe.bomb.cafe.cnn.low.asf", 128*1024)
  print "length =", stream.length()
  print "duration =", stream.duration()
  print "seekable =", stream.seekable()
  for data in stream.data():
    print "read %d bytes" % len(data)
