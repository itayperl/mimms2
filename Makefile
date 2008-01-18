PREFIX=/usr/local
BINDIR=$(PREFIX)/bin
MANDIR=$(PREFIX)/share/man
DESTDIR=

QMAKE=qmake-qt4
TXT2MAN=txt2man
INSTALL=install

all: build

changelog:
	cvs2cl --utc -P -t

build: Makefile.qmake
	$(MAKE) -f Makefile.qmake

install: build
	$(INSTALL) -m755 -D mimms   $(DESTDIR)/$(BINDIR)/mimms
	$(INSTALL) -m644 -D mimms.1 $(DESTDIR)/$(MANDIR)/man1/mimms.1

clean:
	rm -f Makefile.qmake *.o mimms *~ 

Makefile.qmake:
	$(QMAKE) -o $@
