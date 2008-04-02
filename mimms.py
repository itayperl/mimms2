#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# mimms - mms stream downloader
# Copyright © 2006 Wesley J. Landaker <wjl@icecavern.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

from libmms import Stream
from time import time
import sys

class Timer:
  def __init__(self):
    self.start = time()

  def restart(self):
    elapsed = self.elapsed()
    self.start = time()
    return elapsed

  def elapsed(self):
    return time() - self.start

class Timeout(Exception): pass

def bytes_to_string(bytes):
  if   bytes < 0:       return "∞ B"
  if   bytes < 1024:    return "%.2f B"   % (bytes)
  elif bytes < 1024**2: return "%.2f KiB" % (bytes/1024.0)
  elif bytes < 1024**3: return "%.2f MiB" % (bytes/1024.0**2)
  else:                 return "%.2f GiB" % (bytes/1024.0**3)

def seconds_to_string(seconds):
  if seconds < 0: return "∞ s"

  h = seconds // 60**2
  m = (seconds % 60**2) // 60
  s = seconds % 60
  return "%02d:%02d:%02d" % (h, m ,s)

def choose_filename(filename):
  pass

def download(url, bandwidth, filename, timeout=0):
  stream = Stream(url, bandwidth)
  f = open(filename, "w")

  timeout_timer  = Timer()
  duration_timer = Timer()

  bytes_in_duration = 0
  bytes_per_second  = 0
  status = ""

  for data in stream.data():
    f.write(data)
    bytes_in_duration += len(data)
    if duration_timer.elapsed() >= 1:
      bytes_per_second += bytes_in_duration / duration_timer.restart()
      bytes_per_second /= 2.0
      seconds_remaining = (stream.length() - stream.position()) / bytes_per_second
      bytes_in_duration = 0

      if stream.duration():
        length    = bytes_to_string(stream.length())
        remaining = seconds_to_string(seconds_remaining)
      else:
        length    = -1
        remaining = -1

      clear = " " * len(status)
      status = "%s / %s (%s/s, %s remaining)" % (
        bytes_to_string(stream.position()),
        bytes_to_string(length),
        bytes_to_string(bytes_per_second),
        seconds_to_string(remaining)
        )

      print "\r", clear, "\r", status,
      sys.stdout.flush()

      if timeout and timeout_timer.elapsed() > timeout:
        raise Timeout

  f.close()
  stream.close()
    
if __name__ == "__main__":
  download("mms://202.96.114.251/lstv", "output.wmv", 128*1024)

##class ProgressThread(Thread):

##  def __init__(self, total):
##    Thread.__init__(self)
##    self.queue = Queue(10)
##    self.total = total
##    self.count = 0

##  def add(self, count):
##    self.queue.put(count)

##  def run(self):
##    while True:
##      new = self.queue.get()
##      if new == -1: return
##      self.count += new
##      print "\r"
      
  
