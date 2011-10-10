#
#  Makefile for our custom KNI wrapper.
#  Use this file if you have a properly configured gcc toolchain.
#  This will build a (big) shared object. As this includes required libs, your
# applications just need to link with this one. E.g: no need for libKNI_LM.so...
#
# ----!---- You would need to define KNI_SDK_DIR in your environment ----!---- 
#

LIBNAME = LH_KNI_wrapper
SOURCES = LH_KNI_wrapper.cpp

TARGET_DIR  = .
TARGET      = lib$(LIBNAME).so

BASE_DIR    = $(KNI_SDK_DIR)

INCLUDE_DIR = $(BASE_DIR)/include
LIBS_DIR    = $(BASE_DIR)/lib/linux
EXTRA_OBJS  = $(LIBS_DIR)/kni.a $(LIBS_DIR)/libKNIBase.a \
	      $(LIBS_DIR)/libKNI_LM.a $(LIBS_DIR)/libKNI_InvKin.a \
	      $(LIBS_DIR)/libKinematics.a

CXX	   = g++
CXXFLAGS  += -Wall
LDFLAGS    = -L $(LIBS_DIR)
OBJS	   = $(SOURCES:.cpp=.o)

.PHONY: all debug

.SUFFIXES: .cpp.o

.cpp.o:
	$(CXX) $(CXXFLAGS) -I$(INCLUDE_DIR) -c $< 

CHECK_ENV:
ifndef KNI_SDK_DIR					# condition: no tab
	$(error "define KNI_SDK_DIR in environment.")	# command: requires tab
endif

all: CHECK_ENV $(TARGET)				# keep this before debug

debug: CXXFLAGS += -DDEBUG -g
debug: all

optim: CXXFLAGS += -O3
optim: all

%.a: $(OBJS)
	$(AR) $(ARFLAGS) $@ $(OBJS) $(EXTRA_OBJS) > /dev/null

%.so: $(OBJS)
	$(CXX) -shared -o $@ $(OBJS) $(EXTRA_OBJS)

clean:	
	rm -rf *.o *~ *# $(TARGET_DIR)/$(TARGET)
