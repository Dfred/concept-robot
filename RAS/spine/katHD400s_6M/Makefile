# LightHead is a programm part of CONCEPT, a HRI PhD project at the University
#  of Plymouth. LightHead is a Robotic Animation System including face, eyes,
#   head and other supporting algorithms for vision and basic emotions.
# Copyright (C) 2010-2011 Frederic Delaunay, frederic.delaunay@plymouth.ac.uk
#
#  This program is free software: you can redistribute it and/or
#   modify it under the terms of the GNU General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

################################################################################

#  Makefile for our custom KNI wrapper.
#  This will build a (big) shared object including all required KNI libs. Hence,
#  your applications just need to be linked with LH_KNI_wrapper.so .

#
#  Builds optimized version by default. Use `make debug` for unstripped version.
#  You need a properly configured gcc toolchain.
#
#  Note 1: you need to define BASE_DIR in your environment. This directory shall
#          have include/ and lib/linux/ directories
#
#  Note 2: the debug rule expects non-stripped dependencies to be in
#  	   $(DEPLIBS_DIR)/debug/
#

LIBNAME = LH_KNI_wrapper
SOURCES = LH_KNI_wrapper.cpp
TST_SRC = test.c

TARGET_DIR = .
INCLUDE_DIR= $(BASE_DIR)/include
DEPLIBS_DIR= $(BASE_DIR)/lib/linux
EXTRA_OBJS = $(DEPLIBS_DIR)/libKNIBase.a    \
	     $(DEPLIBS_DIR)/libKNI_LM.a	    \
	     $(DEPLIBS_DIR)/libKNI_InvKin.a \
	     $(DEPLIBS_DIR)/libKinematics.a

GCC	   = gcc
CXXFLAGS  += -Wall
CFLAGS	  += -Wall -std=c99
LDFLAGS   += -lstdc++ -L $(DEPLIBS_DIR)

TARGET     = lib$(LIBNAME).so
TARGET_DBG = lib$(LIBNAME)-debug.so
OBJS	   = $(SOURCES:.cpp=.o)
TST_OBJS   = $(TST_SRC:.cpp=.o)				# .c are left untouched
TST_OBJS  := $(TST_OBJS:.c=.o)				# so it's fix here.
TST_LDFLAGS= -Wl,-rpath=$(TARGET_DIR)

.PHONY: all debug optim check_env test

all: CXXFLAGS += -O3
all: check_env $(TARGET)

# fetch unstripped objs in $LIBS_DIR/debug
debug: CFLAGS += -ggdb
debug: CXXFLAGS += -ggdb -DDEBUG
debug: DEPLIBS_DIR := $(DEPLIBS_DIR)/debug
debug: TARGET_DIR := $(TARGET_DIR)/debug
debug: check_env $(TARGET_DBG)

# I don't get yet why C*FLAGS don't keep the value set in debug:
test: CFLAGS += -ggdb
test: CXXFLAGS += -ggdb -DDEBUG
test: debug $(TST_OBJS)
	$(GCC) $(TST_LDFLAGS) -L$(TARGET_DIR) -l$(LIBNAME)-debug $(TST_OBJS) -o $@

clean:	
	rm -rf *.o *~ *# $(TARGET_DIR)/$(TARGET) $(TARGET_DIR)/$(TARGET_DBG)

check_env:
ifndef BASE_DIR						# condition: no tab
	$(error "define BASE_DIR in environment.")	# command: requires tab
endif							# condition: you get it.
	@echo "Using BASE_DIR as: $(BASE_DIR)"

%.o: %.cpp
	$(GCC) $(CXXFLAGS) -I$(INCLUDE_DIR) -c $<
%.o: %.c
	$(GCC) $(CFLAGS)   -I$(INCLUDE_DIR) -c $< 

%.a: $(OBJS)
	$(AR) $(ARFLAGS) $@ $(OBJS) $(EXTRA_OBJS) > /dev/null

%.so: CXXFLAGS += -fpic
%.so: $(OBJS)
	$(GCC) -shared -o $@ $(LDFLAGS) $(OBJS) $(EXTRA_OBJS)
