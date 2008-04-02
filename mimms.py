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

VERSION="3.0"

import os
import sys

from libmms import Stream
from optparse import OptionParser
from time import time
from urlparse import urlparse

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

def get_filename(options):
  if options.filename: filename = options.filename
  else:
    filename = os.path.basename(urlparse(options.url).path)
    if not filename.endwidth(".wmv"): filename += ".wmv"
  if options.clobber: return filename
  new_filename = filename
  i = 1
  while os.path.exists(new_filename):
    new_filename = "%s.%d" % (filename, i)
  return new_filename

def download(options):
  status = "Connecting ..."
  if not options.quiet: print status,
  stream = Stream(options.url, options.bandwidth)
  filename = get_filename()
  f = open(filename, "w")

  clear = " " * len(status)
  status = "%s => %s" % (url, filename)
  if not options.quiet: print "\r", clear, "\r", status
  sys.stdout.flush()  

  timeout_timer  = Timer()
  duration_timer = Timer()

  bytes_in_duration = 0
  bytes_per_second  = 0

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

      if not options.quiet: print "\r", clear, "\r", status,
      sys.stdout.flush()

      if options.time and timeout_timer.elapsed() > (options.time*60):
        raise Timeout

  f.close()
  stream.close()
    
usage = "usage: %prog [options] <url> [filename]"
parser = OptionParser(usage=usage,
                      version=("%%prog %s" % VERSION),
                      description="mimms is an mms (e.g. mms://) stream downloader")
parser.add_option("-c", "--clobber",
                  action="store_true", dest="clobber",
                  help="automatically overwrite a existing files")
parser.add_option("-b", "--bandwidth",
                  type="float", dest="bandwidth",
                  help="the desired bandwidth for stream selection in BANDWIDTH bytes/s")
parser.add_option("-t", "--time",
                  type="int", dest="time",
                  help="stop downloading after TIME minutes")
parser.add_option("-v",
                  action="store_true", dest="verbose",
                  help="print verbose debug messages to stderr")
parser.add_option("-q",
                  action="store_true", dest="quiet",
                  help="don't print progress messages to stdout")

parser.set_defaults(time=0, bandwidth=1e6)
(options, args) = parser.parse_args()
if len(args) < 1:
  parser.error("url must be specified")
elif not args[0].startswith("mms"):
  parser.error("only mms urls are supported")
elif len(args) > 2:
  parser.error("unknown extra arguments: %s" % ' '.join(args[2:]))
 options.url = args[0]
if len(args) > 2: options.filename = args[1]
  
try:
  #"mms://202.96.114.251/lstv", "output.wmv", 128*1024)
  download(options)
except Timeout:
  if not options.quiet:
    print
    print "Download stopped after user-specified timeout."
else:
  if not options.quiet:
    print
    print "Download complete!"
