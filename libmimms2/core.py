# -*- coding: utf-8 -*-
#
# mimms - mms stream downloader
# Copyright © 2008 Wesley J. Landaker <wjl@icecavern.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
This module contains the core implementation of mimms. This exists
primarily to make it easier to use mimms from other python programs.
"""

from __future__ import division
import multiprocessing.dummy as multiprocessing
import progressbar
import os
import sys
from contextlib import closing
from functools import partial

from optparse import OptionParser
from urlparse import urlparse

from . import libmms

VERSION="1.0"

# Terminology:
# Part - a part of the stream downloaded in parallel
# Chunk - amount of data to buffer in each thread before writing to disk
CHUNK_SIZE = 16 * 1024

class Timeout(Exception):
  "Raised when a user-defined timeout has occurred."
  pass

class NonSeekableError(Exception):
  "Raised when multiconnection download is attempted on a non-seekable stream."
  pass

def seconds_to_string(seconds):
  "Given a number of seconds, return a string representation."
  if seconds < 0: return "∞ s"

  h = seconds // 60**2
  m = (seconds % 60**2) // 60
  s = seconds % 60
  return "%02d:%02d:%02d" % (h, m ,s)

def get_filename(options):
  "Based on program options, choose an appropriate filename."

  # if we are given a filename, use it; otherwise, synthesize from url
  if options.filename: filename = options.filename
  else:
    filename = os.path.basename(urlparse(options.url).path)
    # assume .wmv if there is no extention
    if filename.find(".") == -1: filename += ".wmv"

  # if we are clobbering or resuming a file, use the filename directly
  if options.clobber: return filename

  # otherwise, we need to pick a new filename that isn't used
  new_filename = filename
  i = 1
  while os.path.exists(new_filename):
    new_filename = "%s.%d" % (filename, i)
    i += 1
  return new_filename

def download_threaded(url, bandwidth, filename, conn_count=1, timeout=0, verbose=True):
  with closing(libmms.Stream(url, bandwidth)) as stream:
    if not stream.seekable():
      conn_count = 1
    stream_size = stream.length()

    part_size = stream_size // conn_count
    parts = []
    start = 0

    for _ in xrange(conn_count - 1):
      end = stream.seek(start + part_size)
      parts.append((url, bandwidth, start, end))
      start = end
    parts.append((url, bandwidth, start, stream_size))

  queue = multiprocessing.Queue()
  pool = multiprocessing.Pool(conn_count)
  # The callback may prevent q.get() from blocking indefinitely.
  result = pool.map_async(partial(download_stream_part, queue=queue), parts, callback=lambda result: queue.put(('', 0)))

  if verbose:
      pbar_widgets = ['Downloading: ', progressbar.Percentage(), ' ', progressbar.Bar(), 
                    ' ', progressbar.ETA(), ' ', progressbar.FileTransferSpeed()]
  else:
      pbar_widgets = []
  progress = progressbar.ProgressBar(widgets=pbar_widgets, maxval=stream_size).start()

  with open(filename, "wb") as outfile:
    while not (result.ready() and queue.empty()):
      data, offset = queue.get()
      outfile.seek(offset)
      outfile.write(data)

      progress.update(progress.currval + len(data))

      # if we are running with a user-defined timeout, we always have an
      # upper bound on how much time is remaining
      if timeout and progress.seconds_elapsed > timeout * 60:
        raise Timeout

  if not result.successful():
      # print traceback
      result.get()

  if verbose:
    print
    print "Download time: {}".format(seconds_to_string(progress.seconds_elapsed))

def download(options):
  "Using the given options, download the stream to a file."

  conn_count = options.connections_count

  filename = get_filename(options)
  if not options.quiet:
    print "%s => %s" % (options.url, filename)

  download_threaded(options.url, options.bandwidth, filename,
                    conn_count=conn_count, timeout=options.time, verbose=not options.quiet)

def download_stream_part(part, queue):
  url, bandwidth, start, end = part
  if start == end:
    return

  with closing(libmms.Stream(url, bandwidth)) as stream:
    new_pos = stream.seek(start)
    # Odd bug, ugly workaround.
    if new_pos != start and start > 0:
      new_pos = stream.seek(start - 1)
    assert new_pos == start, 'Seek failed!'

    cur_chunk = b''
    chunk_offset = start
    for data in stream:
      prev_pos = stream.position() - len(data)
      cur_chunk += data[:end - prev_pos]
        
      if len(cur_chunk) >= CHUNK_SIZE or stream.position() >= end:
        queue.put((cur_chunk, chunk_offset))
        cur_chunk = b''
        chunk_offset = stream.position()
      if stream.position() >= end:
        break

def main():
  "Run the main mimms program with the given command-line arguments."

  usage = "usage: %prog [options] <url> [filename]"
  parser = OptionParser(
    usage=usage,
    version=("%%prog %s" % VERSION),
    description="mimms2 is an mms (e.g. mms://) stream downloader")
  parser.add_option(
    "-n", "--num-connections",
    type="int", dest="connections_count",
    help=("number of parallel connections to use [default=10]"))
  parser.add_option(
    "-c", "--clobber",
    action="store_true", dest="clobber",
    help="automatically overwrite an existing file")
  parser.add_option(
    "-b", "--bandwidth",
    type="float", dest="bandwidth",
    help="the desired bandwidth for stream selection in BANDWIDTH bytes/s")
  parser.add_option(
    "-t", "--time",
    type="int", dest="time",
    help="stop downloading after TIME minutes")
  parser.add_option(
    "-v", "--verbose",
    action="store_true", dest="verbose",
    help="print verbose debug messages to stderr")
  parser.add_option(
    "-q", "--quiet",
    action="store_true", dest="quiet",
    help="don't print progress messages to stdout")

  parser.set_defaults(time=0, bandwidth=1e6, connections_count=10)
  (options, args) = parser.parse_args(sys.argv[1:])
  if len(args) < 1:
    parser.error("url must be specified")
  elif not args[0].startswith("mms"):
    # TODO: handle http:// urls to .asx files that contain mms urls
    parser.error("only mms urls (i.e. mms://, mmst://, mmsh://) are supported")
  elif len(args) > 2:
    parser.error("unknown extra arguments: %s" % ' '.join(args[2:]))
  
  options.url = args[0]
  if len(args) > 1: options.filename = args[1]
  else: options.filename = None
    
  try:
    download(options)
  except Timeout:
    if not options.quiet:
      print "Download stopped after user-specified timeout."
  except KeyboardInterrupt:
    if not options.quiet:
      print >>sys.stderr, "Download aborted by user."
  except libmms.Error, e:
    print >>sys.stderr, "libmms error: {}".format(e.message)
  except NonSeekableError:
    print "Cannot use parallel connections on non-seekable stream"
  else:
    if not options.quiet:
      print "Download complete!"
