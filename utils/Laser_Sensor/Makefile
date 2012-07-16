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


LIBNAME = URG_motionDetect
SOURCES = src/detection_motion.c $(wildcard src/URG_sdk/src/*.c)
TST_SRC = test/main.c

TARGET_DIR = .
INCLUDE_DIRS= . src/URG_sdk/include
EXTRA_OBJS = 

GCC	   = gcc
CXXFLAGS  += -Wall -fPIC
CFLAGS	  += -Wall -fPIC -std=c99
LDFLAGS   += 

TARGET     = lib$(LIBNAME).so
TARGET_DBG = lib$(LIBNAME)-debug.so
OBJS	   = $(SOURCES:.c=.o)
TST_OBJS   = $(TST_SRC:.cpp=.o)				# .c are left untouched
TST_OBJS  := $(TST_OBJS:.c=.o)				# so it's fix here.
TST_LDFLAGS= -Wl,-rpath=$(TARGET_DIR)
INCLUDE_FLAGS = $(foreach d,$(INCLUDE_DIRS), -I $(d))


.PHONY: all debug optim clean check_env test

all: CXXFLAGS += -O3
all: $(TARGET)

# fetch unstripped objs in $LIBS_DIR/debug
debug: CFLAGS += -ggdb
debug: CXXFLAGS += -ggdb -DDEBUG
debug: DEPLIBS_DIR := $(DEPLIBS_DIR)/debug
debug: TARGET_DIR := $(TARGET_DIR)/debug
debug: $(TARGET_DBG)

# I don't get yet why C*FLAGS don't keep the value set in debug:
test: CFLAGS += -ggdb
test: CXXFLAGS += -ggdb -DDEBUG
test: debug $(TST_OBJS)
	$(GCC) $(TST_LDFLAGS) -L$(TARGET_DIR) $(TARGET_DBG) $(TST_OBJS) -o $@

clean:	
	rm -f $(OBJS) *~ *# $(TARGET_DIR)/$(TARGET) $(TARGET_DIR)/$(TARGET_DBG)

%.o: %.cpp
	$(GCC) $(CXXFLAGS) $(INCLUDE_FLAGS) -c $< -o $@
%.o: %.c
	$(GCC) $(CFLAGS)  $(INCLUDE_FLAGS) -c $< -o $@

%.a: $(OBJS)
	$(AR) $(ARFLAGS) $@ $(OBJS) $(EXTRA_OBJS) > /dev/null

%.so: CXXFLAGS += -fpic
%.so: $(OBJS)
	$(GCC) -shared -o $@ $(LDFLAGS) $(OBJS) $(EXTRA_OBJS)
