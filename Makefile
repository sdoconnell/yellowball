PREFIX = /usr/local
BINDIR = $(PREFIX)/bin
MANDIR = $(PREFIX)/share/man/man1
DOCDIR = $(PREFIX)/share/doc/yellowball

.PHONY: all install uninstall

all:

install:
	install -m755 -d $(BINDIR)
	install -m755 -d $(MANDIR)
	install -m755 -d $(DOCDIR)
	gzip -c doc/yellowball.1 > yellowball.1.gz
	install -m755 yellowball/yellowball.py $(BINDIR)/yellowball
	install -m644 yellowball.1.gz $(MANDIR)
	install -m644 README.md $(DOCDIR)
	rm -f yellowball.1.gz

uninstall:
	rm -f $(BINDIR)/yellowball
	rm -f $(MANDIR)/yellowball.1.gz
	rm -rf $(DOCDIR)
