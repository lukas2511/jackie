AUTOMAKE_OPTIONS = foreign

bin_PROGRAMS = jacknanomix

jacknanomix_SOURCES = nanomix.c db.h
AM_CFLAGS = -Wall @JACK_CFLAGS@
AM_LDFLAGS = -lm @JACK_LIBS@

EXTRA_DIST = autogen.sh TODO
