/*
  Copyright 2006 Wesley J. Landaker <wjl@icecavern.net>

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program; if not, write to the Free Software
  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
*/

#include <QCoreApplication>
#include <QString>
#include <QStringList>
#include <QTextStream>
#include <QFile>
#include <QRegExp>
#include <QTime>
#include <QPair>
#include <QProcess>
#include "mms.h"
#include "mmsh.h"

const char *MMS_VERSION = "2.0.1";

class MiMMSOptions {
public:
  enum Scheme { MMS, MMST, MMSU, MMSH, HTTP, STDIN };
  QString url;
  Scheme  scheme;
  QString output;
  bool    stdout;
  bool    clobber;
  quint32 time;
  bool    verbose;
  bool    quiet;
  bool    help;
  bool    invalid;
};

class MiMMSApplication : public QCoreApplication {
public:
  MiMMSApplication(int argc, char **argv) : QCoreApplication(argc,argv) {
    __parseArgs();

    if (__options.verbose) {
      qDebug("url        = '%s'", __options.url.toUtf8().data());
      qDebug("scheme     = '%s'", 
	     __options.scheme==MiMMSOptions::MMS?"MMS":
	     __options.scheme==MiMMSOptions::MMST?"MMST":
	     __options.scheme==MiMMSOptions::MMSU?"MMSU":
	     __options.scheme==MiMMSOptions::MMSH?"MMSH":
	     __options.scheme==MiMMSOptions::HTTP?"HTTP":
	     __options.scheme==MiMMSOptions::STDIN?"STDIN":
	     "UNKNOWN"
	     );
      qDebug("output     = '%s'", __options.output.toUtf8().data());
      qDebug("stdout     = '%s'", __options.stdout?"true":"false");
      qDebug("clobber    = '%s'", __options.clobber?"true":"false");
      qDebug("time       = '%d'", __options.time);
      qDebug("verbose    = '%s'", __options.verbose?"true":"false");
      qDebug("quiet      = '%s'", __options.quiet?"true":"false");
      qDebug("help       = '%s'", __options.help?"true":"false");
      qDebug("invalid    = '%s'", __options.invalid?"true":"false");
    }

    if (__options.help) {
      QTextStream out(stdout);
      __printHelpMessage(out,0);
    } else if (__options.invalid) {
      QTextStream err(stderr);
      __printHelpMessage(err,1);
    }
  }

  const MiMMSOptions &options() { return __options; }

private:
  void __parseArgs() {
    QStringList args = arguments();
    bool literal_mode = false;

    __options.stdout  = false;
    __options.clobber = false;
    __options.time    = 0;
    __options.verbose = false;
    __options.quiet   = false;
    __options.help    = false;
    __options.invalid = false;

    if (args.size() < 2) __options.invalid = true;

    for (int i=1; i<args.size(); ++i) {
      if (!literal_mode && args[i] == "-c" || args[i] == "--clobber") {
	__options.clobber = true;
      } else if (!literal_mode && args[i] == "-t" || args[i] == "--time") {
	bool ok = false;
	if (i<args.size()-1) {
	  __options.time = args[i+1].toUInt(&ok);
	}
	if (!ok) {
	  qWarning("Invalid argument to %s: '%s'",
		   args[i].toUtf8().data(),
		   args.value(i+1).toUtf8().data());
	  __options.invalid = true;
	} else {
	  ++i;
	}
      } else if (!literal_mode && args[i] == "-v" || args[i] == "--verbose") {
	__options.verbose = true;
      } else if (!literal_mode && args[i] == "-q" || args[i] == "--quiet") {
	__options.quiet = true;
      } else if (!literal_mode && args[i] == "-h" || args[i] == "--help") {
	__options.help = true;
      } else if (!literal_mode && args[i] == "--") {
	literal_mode = true;
      } else if (!literal_mode && args[i].contains(QRegExp("^-.+"))) {
	qWarning("Invalid argument: '%s'", args[i].toUtf8().data());
	__options.invalid = true;
      } else {
	if (__options.url.isEmpty()) {
	  __options.url = args[i];
	  if (__options.url == "-") {
	    __options.scheme = MiMMSOptions::STDIN;
	  } else {
	    QRegExp rx("^([a-z]+)://");
	    if (rx.indexIn(__options.url) == -1) {
	      qWarning("Unparseable URL: '%s'", 
		       __options.url.toUtf8().data());
	      __options.invalid = true;
	    } else {
	      QString scheme = rx.cap(1);
	      if (scheme == "mms") {
		__options.scheme = MiMMSOptions::MMS;
	      } else if (scheme == "mmst") {
		__options.scheme = MiMMSOptions::MMST;
	      } else if (scheme == "mmsu") {
		qWarning("mmsu:// URL scheme not supported");
		__options.scheme = MiMMSOptions::MMSU;
		__options.invalid = true;
	      } else if (scheme == "mmsh") {
		__options.scheme = MiMMSOptions::MMSH;
	      } else if (scheme == "http") {
		__options.scheme = MiMMSOptions::HTTP;
	      } else {
		qWarning("Unsupported URL: '%s'",
			 __options.url.toUtf8().data());
		__options.invalid = true;
	      }
	    }
	  }
	} else if (__options.output.isEmpty()) {
	  __options.output = args[i];
	  if (__options.output == "-") {
	    __options.quiet = true;
	    __options.stdout = true;
	  }
	} else {
	  qWarning("Too many arguments: '%s'", args[i].toUtf8().data());
	  __options.invalid = true;
	}
      }
    }
  }

  void __printHelpMessage(QTextStream &o, int exit_code) {
    o << "MiMMS " << MMS_VERSION << " - MiMMS isn't an MMS Message Sender.\n"
      << "It's an MMS (e.g. mms://) stream downloader.\n"
      << "Usage: mimms [options] <url> [output]\n"
      << "Options:\n"
      << "  -c, --clobber          Allow overwriting an existing file;\n"
      << "                           by default, this is not allowed.\n"
      << "  -t, --time <minutes>   Record for the given number of minutes;\n"
      << "                           by default, record until the end.\n"
      << "  -v, --verbose          Print verbose debug messages on stderr.\n"
      << "  -q, --quiet            Don't print status messages on stdout.\n"
      << "  -h, --help             Show this help message on stdout.\n"
      << "URL Argument:\n"
      << "  mms  (MMS)             i.e. mms://<host>[:port]/<path>\n"
      << "                           will try all supported methods.\n"
      << "  mmst (MMS TCP)         i.e. mmst://<host>[:port]/<path>\n"
      << "                           will only try TCP method.\n"
      << "  mmsu (MMS UDP)         Not currently supported; (poorly suited\n"
      << "                           for streaming downloads anyway).\n"
      << "  mmsh (MMS HTTP)        i.e. mmsh://<host>[:port]/<path>\n"
      << "                           will only try HTTP method.\n"
      << "  http (ASX HTTP)        i.e. http://<host>[:port]/<path>[.asx]\n"
      << "                           only the first supported URL is used.\n"
      << "  -    (stdin)           i.e. look for an MMS URL on stdin;\n"
      << "                           only the first supported URL is used.\n"
      << "Output Argument:\n"
      << "  none                   Streams to file named based on the URL.\n"
      << "  filename               Streams to the given file.\n"
      << "  -                      Streams to stdout. (Implies --quiet.)\n";
      o.flush();
      ::exit(exit_code);
  }

private:
  MiMMSOptions __options;
};

QString bytes_to_string(double bytes) {
  if (bytes < 1024) {
    return QString().sprintf("%.2f B",bytes);
  } else if (bytes < 1024.0*1024.0) {
    return QString().sprintf("%.2f KiB",bytes/1024.0);
  } else if (bytes < 1024.0*1024.0*1024.0) {
    return QString().sprintf("%.2f MiB",bytes/(1024.0*1024.0));
  } else {
    return QString().sprintf("%.2f GiB",bytes/(1024.0*1024.0*1024.0));
  }
}

QString seconds_to_string(double seconds) {
  if (seconds < 60) {
    return QString().sprintf("%.2f s",seconds);
  } else if (seconds < 60.0*60.0) {
    return QString().sprintf("%.2f min",seconds/60.0);
  } else {
    return QString().sprintf("%.2f hours",seconds/(60.0*60.0));
  }
}

int main(int argc, char **argv) {
  MiMMSApplication app(argc, argv);
  QTextStream out(stdout);

  QString url = app.options().url;
  
  mms_t *mms   = 0;
  mmsh_t *mmsh = 0;
  
  if (app.options().scheme == MiMMSOptions::HTTP ||
      app.options().scheme == MiMMSOptions::STDIN) {

    if (!app.options().quiet && !app.options().stdout) {
      out << "Searching for MMS URL...";
      out.flush();
    }

    QString data;
    if (app.options().scheme == MiMMSOptions::HTTP) {
      if (app.options().verbose) {
	qDebug("retreiving HTTP URL with wget");
      }
      QProcess wget;
      QStringList args;
      args << "wget" << "-O" << "-" << app.options().url;
      wget.start("wget",args);
      wget.waitForFinished();
      if (app.options().verbose) {
	qDebug("wget output: %s",qPrintable(QString(wget.readAllStandardError())));
      }
      data = wget.readAllStandardOutput();
    } else {
      if (app.options().verbose) {
	qDebug("searching for URL in stdin data");
      }
      QTextStream in(stdin);
      data = in.readAll();
    }
    QRegExp url_grabber("(?:^|[ \"'<]|\\s)(mms.?://[^\t\n\v\f\r \"'>]+)");
    if (url_grabber.indexIn(data) != -1) {
      url = url_grabber.cap(1).simplified();
      if (app.options().verbose) {
	qDebug("using grabbed mms url = %s",qPrintable(url));
      }
    }
  }

  QFile file;
  if (app.options().output == "-") {
    file.open(stdout,QFile::WriteOnly);
  } else {
    if (app.options().output.isEmpty()) {
      file.setFileName("mimms.wmv");
      QStringList url_parts = url.split("/");
      if (!url_parts.last().isEmpty() && !url_parts.last().contains('?')) {
	file.setFileName(url_parts.last());
      }
    } else {
      file.setFileName(app.options().output);
    }
    if (file.exists() && !app.options().clobber) {
      if (QFile("mimms.wmv").exists()) {
	qFatal("File exists and clobber not set: '%s'",
	       file.fileName().toUtf8().data());
      } else {
	qWarning("File exists and clobber not set: '%s'; using 'mimms.wmv'",
		 file.fileName().toUtf8().data());
      }
      file.setFileName("mimms.wmv");
    }
  }

  if (!app.options().quiet && !app.options().stdout) {
    out << "\r                                                              ";
    out << "\r<" << url << ">  =>  " << "'" << file.fileName() << "'" << endl;
  }

  if (!app.options().quiet && !app.options().stdout) {
    out << "Connecting...";
    out.flush();
  }

  if (app.options().scheme == MiMMSOptions::MMS || 
      app.options().scheme == MiMMSOptions::MMST) {

    if (app.options().verbose) {
      qDebug("trying mmst transport");
    }

    mms = mms_connect(0,0,url.toUtf8().data(),128*1024);
    
    if (!mms && app.options().scheme == MiMMSOptions::MMST) {
      qFatal("libmms connection error");
    }

  }

  if (app.options().scheme == MiMMSOptions::MMSH || (!mms)) {
    mmsh = mmsh_connect(0,0,url.toUtf8().data(),128*1024);
    if (!mmsh) {
      qFatal("libmms connection error");
    }
  }

  if (app.options().verbose) {
    qDebug("connected (mms=%p, mmsh=%p)",mms,mmsh);
  }

  quint32 stream_length;
  stream_length = mms ? mms_get_length(mms) : mmsh_get_length(mmsh);

  if (app.options().verbose) {
    qDebug("mms[h]_get_length = %u", stream_length);
  }

  if (app.options().verbose) {
    qDebug("Opening file '%s'", qPrintable(file.fileName()));
  }
  file.open(QFile::WriteOnly);

  QDateTime endDateTime;
  {
    quint32 minutes = app.options().time;
    if (minutes) {
      endDateTime = QDateTime::currentDateTime();
      while (minutes) {
	if (minutes < (1<<24)) {
	  endDateTime = endDateTime.addSecs(minutes*60);
	  minutes = 0;
	} else {
	  endDateTime = endDateTime.addSecs((1<<24)*60);
	  minutes -= 1<<24;
	}
      }
      if (app.options().verbose) {
	qDebug("now = %s",qPrintable(QDateTime::currentDateTime().toString()));
	qDebug("end = %s",qPrintable(endDateTime.toString()));
      }
    }
  }



  const size_t buffer_size = 1000;
  char *buffer = new char[buffer_size];
  int bytes;
  QTime duration;
  unsigned long bytes_in_duration = 0;
  QString status;

  double bytes_per_second = 0;

  duration.start();
  while (mms 
	 ? ((bytes = mms_read(0,mms,buffer,buffer_size)) > 0)
	 : ((bytes = mmsh_read(0,mmsh,buffer,buffer_size)) > 0)
	 ) {

    if (endDateTime.isValid()) {
      if (QDateTime::currentDateTime() > endDateTime) {
	if (!app.options().quiet && !app.options().stdout) {
	  qDebug("\rRecording time limit exceeded.");
	  break;
	}  
      }
    }

    if (!app.options().quiet && !app.options().stdout) {
      off_t pos = mms ? mms_get_current_pos(mms) : mmsh_get_current_pos(mmsh);

      bytes_in_duration += bytes;

      if (duration.elapsed() > 2500) {
	int delta = duration.restart();
	double bytes_received = pos;
	double bytes_total    = stream_length;
	bytes_per_second  += bytes_in_duration/(delta/1000.0);
	bytes_per_second  /= 2.0;
	double seconds_remaining = (bytes_total-bytes_received)/bytes_per_second;

	bytes_in_duration = 0;

	QString s_bytes_received    = bytes_to_string(bytes_received);
	QString s_bytes_total       = bytes_to_string(bytes_total);
	QString s_bytes_per_second  = bytes_to_string(bytes_per_second);
	QString s_seconds_remaining = seconds_to_string(seconds_remaining);

	out << "\r";
	for (int i=0; i<status.size(); ++i) {
	  out << " ";
	}
	
	status.sprintf("%s / %s (%s/s, %s remaining)",
		       qPrintable(s_bytes_received), 
		       qPrintable(s_bytes_total),
		       qPrintable(s_bytes_per_second), 
		       qPrintable(s_seconds_remaining));

	out << "\r" << status;
	out.flush();
      }

    }
    char *wptr = buffer;
    int wbytes;
    if (app.options().verbose) {
      qDebug("writing to file");
    }
    while ((wbytes = file.write(wptr,bytes)) > 0) {
      if (app.options().verbose) {
	qDebug("%d bytes", wbytes);
      }
      bytes -= wbytes;
      wptr  += wbytes;
    }
    if (wbytes == -1) {
      qFatal("Write error");
    }
  }
  if (bytes == -1) {
    qFatal("Read error");
  }

  if (app.options().verbose) {
    qDebug("closing file");
  }
  file.close();
  delete buffer;

  if (!app.options().quiet && !app.options().stdout) {
    out << "\rStream download completed.\n";
    out.flush();
  }
}
