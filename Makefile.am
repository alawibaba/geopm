#  Copyright (c) 2015, 2016, 2017, 2018, Intel Corporation
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
#
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in
#        the documentation and/or other materials provided with the
#        distribution.
#
#      * Neither the name of Intel Corporation nor the names of its
#        contributors may be used to endorse or promote products derived
#        from this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#  OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#  THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY LOG OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

# GLOBAL SETTINGS
ACLOCAL_AMFLAGS = -I m4
AM_CPPFLAGS += -I$(top_srcdir)/src -DGEOPM_PLUGIN_PATH=\"$(pkglibdir)\" -D_POSIX_C_SOURCE=200809L -DOMPI_SKIP_MPICXX

# THINGS THAT ARE INSTALLED
lib_LTLIBRARIES = libgeopmpolicy.la
bin_PROGRAMS = geopmread \
               geopmwrite \
               geopmagent \
               #end
pkglib_LTLIBRARIES =
nodist_include_HEADERS =

if ENABLE_MPI
    lib_LTLIBRARIES += libgeopm.la
    bin_PROGRAMS += geopmctl \
                    geopmbench \
                    # end
if ENABLE_FORTRAN
    lib_LTLIBRARIES += libgeopmfort.la
endif
endif

if !ENABLE_FORTRAN
install-fortran:
	-
endif


install-exec-hook: install-python install-fortran install-openmp
dist: dist-googletest dist-openmp


include_HEADERS = src/geopm.h \
                  src/geopm_agent.h \
                  src/geopm_ctl.h \
                  src/geopm_endpoint.h \
                  src/geopm_error.h \
                  src/geopm_message.h \
                  src/geopm_version.h \
                  # end

if ENABLE_MPI
if ENABLE_FORTRAN

all-local: geopm.mod

install-fortran:
	$(INSTALL) -d $(DESTDIR)/$(libdir)/$(FC)/modules/geopm-`uname -m`
	$(INSTALL) geopm.mod $(DESTDIR)/$(libdir)/$(FC)/modules/geopm-`uname -m`

endif
endif

ronn_man = man/geopm.7 \
           man/geopmagent.1 \
           man/geopm_agent_c.3 \
           man/geopm_agent_energy_efficient.7 \
           man/geopm_agent_monitor.7 \
           man/geopm_agent_power_balancer.7 \
           man/geopm_agent_power_governor.7 \
           man/geopmanalysis.1 \
           man/geopmbench.1 \
           man/geopmctl.1 \
           man/geopm_ctl_c.3 \
           man/geopmendpoint.1 \
           man/geopm_endpoint_c.3 \
           man/geopm_error.3 \
           man/geopm_fortran.3 \
           man/geopmplotter.1 \
           man/geopm_prof_c.3 \
           man/geopmpy.7 \
           man/geopmpy_launcher.1 \
           man/geopmread.1 \
           man/geopm_sched.3 \
           man/geopm_version.3 \
           man/geopmwrite.1 \
           # end

dist_man_MANS = man/geopmaprun.1 \
                man/geopmsrun.1 \
                $(ronn_man) \
                # end


dist_doc_DATA = README \
                COPYING \
                VERSION \
                # end

EXTRA_DIST = .gitignore \
             .travis.yml \
             .travis_obs.sh \
             autogen.sh \
             ChangeLog \
             CODE_OF_CONDUCT.md \
             configure.ac \
             contrib/json11/README.md \
             contrib/json11/LICENSE.txt \
             CONTRIBUTING.md \
             copying_headers/header.BSD3-intel \
             copying_headers/header.BSD3-llnl \
             copying_headers/header.MIT-dropbox \
             copying_headers/header.NAS \
             copying_headers/MANIFEST.BSD3-llnl \
             copying_headers/MANIFEST.BSD3-intel \
             copying_headers/MANIFEST.MIT-dropbox \
             copying_headers/MANIFEST.EXEMPT \
             copying_headers/MANIFEST.NAS \
             copying_headers/test-license \
             copying_headers/test-dist \
             dox/Doxyfile \
             geopm-ohpc.spec.in \
             geopm-ohpc.spec \
             geopm-theta.spec.in \
             geopm-theta.spec \
             geopm.spec.in \
             geopm.spec \
             Makefile.am \
             MANIFEST \
             pull_request_template.md \
             README.md \
             ronn/geopmagent.1.ronn \
             ronn/geopm_agent_c.3.ronn \
             ronn/geopm_agent_energy_efficient.7.ronn \
             ronn/geopm_agent_monitor.7.ronn \
             ronn/geopm_agent_power_balancer.7.ronn \
             ronn/geopm_agent_power_governor.7.ronn \
             ronn/geopmendpoint.1.ronn \
             ronn/geopm_endpoint_c.3.ronn \
             ronn/geopm.7.ronn \
             ronn/geopmanalysis.1.ronn \
             ronn/geopmbench.1.ronn \
             ronn/geopmctl.1.ronn \
             ronn/geopm_ctl_c.3.ronn \
             ronn/geopm_error.3.ronn \
             ronn/geopm_fortran.3.ronn \
             ronn/geopmplotter.1.ronn \
             ronn/geopm_prof_c.3.ronn \
             ronn/geopmpy.7.ronn \
             ronn/geopmpy_launcher.1.ronn \
             ronn/geopmread.1.ronn \
             ronn/geopm_sched.3.ronn \
             ronn/geopm_version.3.ronn \
             ronn/geopmwrite.1.ronn \
             ronn/header.txt \
             ronn/index.txt \
             src/Comm.hpp \
             TODO \
             tracker/track \
             $(TUTORIAL_DIST) \
             test_hw/geopm_time.h \
             test_hw/Makefile \
             test_hw/rapl_pkg_limit_test.c \
             test_hw/rapl_pkg_limit_plot.py \
             test_hw/rapl_pkg_limit_sweep.sh \
             geopm-tutorial.tar.gz \
             # end

TUTORIAL_DIST = tutorial/agent/agent_tutorial.sh \
                tutorial/agent/agent_tutorial_config.json \
                tutorial/agent/ExampleAgent.cpp \
                tutorial/agent/ExampleAgent.hpp \
                tutorial/agent/example_policy.json \
                tutorial/agent/Makefile \
                tutorial/agent/README.md \
                tutorial/agent/tutorial_build_gnu.sh \
                tutorial/agent/tutorial_build_intel.sh \
                tutorial/contrib/json11/json11.cpp \
                tutorial/contrib/json11/json11.hpp \
                tutorial/contrib/json11/LICENSE.txt \
                tutorial/contrib/json11/README.md \
                tutorial/Exception.hpp \
                tutorial/geopm_time.h \
                tutorial/Imbalancer.cpp \
                tutorial/imbalancer.h \
                tutorial/iogroup/ExampleIOGroup.cpp \
                tutorial/iogroup/ExampleIOGroup.hpp \
                tutorial/iogroup/Makefile \
                tutorial/iogroup/README.md \
                tutorial/iogroup/tutorial_build_gnu.sh \
                tutorial/iogroup/tutorial_build_intel.sh \
                tutorial/Makefile \
                tutorial/ModelApplication.cpp \
                tutorial/ModelApplication.hpp \
                tutorial/ModelParse.cpp \
                tutorial/ModelParse.hpp \
                tutorial/ModelRegion.cpp \
                tutorial/ModelRegion.hpp \
                tutorial/README.md \
                tutorial/tutorial_0.c \
                tutorial/tutorial_0.sh \
                tutorial/tutorial_1.c \
                tutorial/tutorial_1.sh \
                tutorial/tutorial_2.c \
                tutorial/tutorial_2.sh \
                tutorial/tutorial_3.c \
                tutorial/tutorial_3.sh \
                tutorial/tutorial_4.c \
                tutorial/tutorial_4.sh \
                tutorial/tutorial_5.c \
                tutorial/tutorial_5.sh \
                tutorial/tutorial_6_config.json \
                tutorial/tutorial_6.cpp \
                tutorial/tutorial_6.sh \
                tutorial/tutorial_balanced_policy.json \
                tutorial/tutorial_build_gnu.sh \
                tutorial/tutorial_build_intel.sh \
                tutorial/tutorial_env.sh \
                tutorial/tutorial_governed_policy.json \
                tutorial/tutorial_region.c \
                tutorial/tutorial_region.h \
                # end

# EXTEND FLAGS FOR MPI TARGETS
if ENABLE_MPI
    libgeopm_la_LDFLAGS = $(AM_LDFLAGS) $(MPI_LDFLAGS) -version-info $(geopm_abi_version)
    libgeopm_la_CFLAGS = $(AM_CFLAGS) $(MPI_CFLAGS)
    libgeopm_la_CXXFLAGS = $(AM_CXXFLAGS) $(MPI_CFLAGS)

    geopmctl_LDFLAGS = $(AM_LDFLAGS) $(MPI_LDFLAGS)
    geopmctl_CFLAGS = $(AM_CFLAGS) $(MPI_CFLAGS)
    geopmctl_CXXFLAGS = $(AM_CXXFLAGS) $(MPI_CFLAGS)

if HAVE_ICPC
    geopmbench_LDFLAGS = $(AM_LDFLAGS) $(MPI_LDFLAGS) -lm -mkl -xAVX
    geopmbench_CFLAGS = $(AM_CFLAGS) $(MPI_CFLAGS) -DTUTORIAL_ENABLE_MKL -D_GNU_SOURCE -std=c99 -xAVX
    geopmbench_CXXFLAGS = $(AM_CXXFLAGS) $(MPI_CFLAGS) -DTUTORIAL_ENABLE_MKL -D_GNU_SOURCE -std=c++11
else
    geopmbench_LDFLAGS = $(AM_LDFLAGS) $(MPI_LDFLAGS) -lm -mavx
    geopmbench_CFLAGS = $(AM_CFLAGS) $(MPI_CFLAGS) -std=gnu11 -mavx
    geopmbench_CXXFLAGS = $(AM_CXXFLAGS) $(MPI_CFLAGS) -std=gnu++11 -mavx
endif

if ENABLE_FORTRAN
    libgeopmfort_la_FCFLAGS = $(AM_FCFLAGS) $(FCFLAGS) $(MPI_FCFLAGS)
    libgeopmfort_la_CFLAGS = $(AM_CFLAGS) $(MPI_CFLAGS)
    libgeopmfort_la_LDFLAGS = $(AM_LDFLAGS) $(MPI_LDFLAGS) -version-info $(geopm_abi_version)
endif
endif

# EXTEND FLAGS FOR NON-MPI TARGETS
libgeopmpolicy_la_LDFLAGS = $(AM_LDFLAGS) -version-info $(geopm_abi_version)
geopmread_CXXFLAGS = $(AM_CXXFLAGS) -std=c++11
geopmwrite_CXXFLAGS = $(AM_CXXFLAGS) -std=c++11

# ADD LIBRARY DEPENDENCIES FOR EXECUTABLES
geopmread_LDADD = libgeopmpolicy.la
geopmwrite_LDADD = libgeopmpolicy.la
geopmagent_LDADD = libgeopmpolicy.la
if ENABLE_MPI
    geopmctl_LDADD = libgeopm.la $(MPI_CLIBS)
    geopmbench_LDADD = libgeopm.la $(MPI_CLIBS)
    libgeopm_la_LIBADD = $(MPI_CLIBS)
if ENABLE_FORTRAN
    libgeopmfort_la_LIBADD = libgeopm.la $(MPI_FLIBS)
endif
endif

libgeopmpolicy_la_SOURCES = src/Agent.cpp \
                            src/Agent.hpp \
                            src/Agg.cpp \
                            src/Agg.hpp \
                            src/ApplicationIO.cpp \
                            src/ApplicationIO.hpp \
                            src/CircularBuffer.hpp \
                            src/CombinedSignal.cpp \
                            src/CombinedSignal.hpp \
                            src/Comm.cpp \
                            src/Comm.hpp \
                            src/ControlMessage.cpp \
                            src/ControlMessage.hpp \
                            src/CpuinfoIOGroup.cpp \
                            src/CpuinfoIOGroup.hpp \
                            src/DefaultProfile.cpp \
                            src/Environment.cpp \
                            src/EnergyEfficientAgent.cpp \
                            src/EnergyEfficientAgent.hpp \
                            src/EnergyEfficientRegion.cpp \
                            src/EnergyEfficientRegion.hpp \
                            src/EpochRuntimeRegulator.cpp \
                            src/EpochRuntimeRegulator.hpp \
                            src/Exception.cpp \
                            src/Exception.hpp \
                            src/IOGroup.cpp \
                            src/IOGroup.hpp \
                            src/geopm.h \
                            src/geopm_agent.h \
                            src/geopm_endpoint.h \
                            src/geopm_env.h \
                            src/geopm_error.h \
                            src/geopm_hash.c \
                            src/geopm_hash.h \
                            src/geopm_message.h \
                            src/geopm_plugin.c \
                            src/geopm_sched.c \
                            src/geopm_sched.h \
                            src/geopm_signal_handler.h \
                            src/geopm_time.h \
                            src/geopm_version.c \
                            src/geopm_version.h \
                            src/Helper.hpp \
                            src/Helper.cpp \
                            src/ManagerIO.cpp \
                            src/ManagerIO.hpp \
                            src/Controller.cpp \
                            src/Controller.hpp \
                            src/MonitorAgent.cpp \
                            src/MonitorAgent.hpp \
                            src/MSR.cpp \
                            src/MSR.hpp \
                            src/MSRIO.cpp \
                            src/MSRIO.hpp \
                            src/MSRIOGroup.cpp \
                            src/MSRIOGroup.hpp \
                            src/msr_hsx.cpp \
                            src/msr_knl.cpp \
                            src/msr_skx.cpp \
                            src/msr_snb.cpp \
                            src/OMPT.cpp \
                            src/OMPT.hpp \
                            src/PlatformIO.cpp \
                            src/PlatformIO.hpp \
                            src/PlatformIOInternal.hpp \
                            src/PlatformTopo.cpp \
                            src/PlatformTopo.hpp \
                            src/PluginFactory.hpp \
                            src/PowerGovernor.hpp \
                            src/PowerGovernor.cpp \
                            src/PowerBalancer.hpp \
                            src/PowerBalancer.cpp \
                            src/PowerBalancerAgent.hpp \
                            src/PowerBalancerAgent.cpp \
                            src/PowerGovernorAgent.hpp \
                            src/PowerGovernorAgent.cpp \
                            src/Profile.cpp \
                            src/Profile.hpp \
                            src/ProfileIO.cpp \
                            src/ProfileIO.hpp \
                            src/ProfileTable.cpp \
                            src/ProfileTable.hpp \
                            src/ProfileThread.cpp \
                            src/ProfileThread.hpp \
                            src/ProfileSampler.cpp \
                            src/ProfileSampler.hpp \
                            src/RegionAggregator.cpp \
                            src/RegionAggregator.hpp \
                            src/Reporter.cpp \
                            src/Reporter.hpp \
                            src/SampleRegulator.cpp \
                            src/SampleRegulator.hpp \
                            src/SampleScheduler.cpp \
                            src/SampleScheduler.hpp \
                            src/SharedMemory.cpp \
                            src/SharedMemory.hpp \
                            src/SignalHandler.cpp \
                            src/TimeIOGroup.cpp \
                            src/TimeIOGroup.hpp \
                            src/Tracer.cpp \
                            src/Tracer.hpp \
                            src/TreeComm.cpp \
                            src/TreeComm.hpp \
                            src/TreeCommLevel.cpp \
                            src/TreeCommLevel.hpp \
                            contrib/json11/json11.cpp \
                            contrib/json11/json11.hpp \
                            src/ProfileIOGroup.cpp \
                            src/ProfileIOGroup.hpp \
                            src/ProfileIOSample.cpp \
                            src/ProfileIOSample.hpp \
                            src/RuntimeRegulator.cpp \
                            src/RuntimeRegulator.hpp \
                            # end

geopmread_SOURCES = src/geopmread_main.cpp \
                    #end
geopmwrite_SOURCES = src/geopmwrite_main.cpp \
                     #end
geopmagent_SOURCES = src/geopmagent_main.c \
                     src/geopm_agent.h \
                     src/geopm_version.h \
                     src/geopm_error.h \
                     src/geopm_env.h \
                     # end

if ENABLE_MPI
    # All source files that are compiled into libgeopmpolicy are also
    # compiled into libgeopm.  We either have to do this or require
    # users to link to both libgeopm and libgeopmpolicy when calling
    # into application facing APIs.
    libgeopm_la_SOURCES = $(libgeopmpolicy_la_SOURCES) \
                          src/geopm_ctl.h \
                          src/geopm_mpi_comm_split.h \
                          src/geopm_pmpi.h \
                          src/geopm_pmpi.c \
                          src/MPICommSplit.cpp \
                          src/MPIComm.cpp \
                          src/MPIComm.hpp \
                          # end
if ENABLE_FORTRAN
    libgeopmfort_la_SOURCES = src/geopm.f90 \
                              src/geopm_pmpi_fortran.c \
                              # end
endif

    geopmctl_SOURCES = src/geopmctl_main.c \
                       src/geopm_version.h \
                       # end
endif

if ENABLE_MPI
    geopmbench_SOURCES = tutorial/imbalancer.h \
                         tutorial/Imbalancer.cpp \
                         tutorial/ModelApplication.cpp \
                         tutorial/ModelApplication.hpp \
                         tutorial/ModelParse.cpp \
                         tutorial/ModelParse.hpp \
                         tutorial/ModelRegion.cpp \
                         tutorial/ModelRegion.hpp \
                         tutorial/tutorial_6.cpp \
                         # end
endif

# CLEAN TARGETS
DISTCLEANFILES = VERSION MANIFEST

CLEAN_LOCAL_TARGETS= clean-local-coverage \
                     clean-local-man \
                     clean-local-fortran \
                     clean-local-googletest \
                     clean-local-openmp \
                     # end

clean-local: $(CLEAN_LOCAL_TARGETS)

distclean-local: distclean-local-ruby

clean-local-coverage:
	rm -f `find -name \*.gcno` `find -name \*.gcda`

clean-local-man:
	rm -rf man ronn/*.html ronn/*.1 ronn/*.3 ronn/*.7

clean-local-fortran:
	rm -rf geopm.mod

distclean-local-ruby:
	rm -rf ruby

# FORTRAN MODULE TARGET
if ENABLE_FORTRAN
geopm.mod: src/geopm.f90
	$(FC) $(AM_FCFLAGS) $(FCFLAGS) $(MPI_FCFLAGS) -c $<
endif

# RPM TARGET
rpm_topdir ?= $(HOME)/rpmbuild
rpm: dist
	mkdir -p $(rpm_topdir)/SOURCES
	mkdir -p $(rpm_topdir)/SPECS
	cp geopm-$(VERSION).tar.gz $(rpm_topdir)/SOURCES/geopm.tar.gz
	cp geopm.spec $(rpm_topdir)/SPECS/geopm.spec
	rpmbuild $(rpmbuild_flags) -ba $(rpm_topdir)/SPECS/geopm.spec

rpm-theta: dist
	mkdir -p $(rpm_topdir)/SOURCES
	mkdir -p $(rpm_topdir)/SPECS
	cp geopm-$(VERSION).tar.gz $(rpm_topdir)/SOURCES/
	cp geopm-theta.spec $(rpm_topdir)/SPECS/geopm-$(VERSION).spec
	rpmbuild $(rpmbuild_flags) --buildroot=$(rpm_topdir)-root --define "_sourcedir $(rpm_topdir)/SOURCES" -ba $(rpm_topdir)/SPECS/geopm-$(VERSION).spec

if ENABLE_DOC

# DOXYGEN TARGET
doxygen:
	doxygen dox/Doxyfile

# MAN TARGET
BUILT_SOURCES = ruby/bin/ronn

geopm-tutorial.tar.gz: $(TUTORIAL_DIST)
	tar --transform='s|^|geopm-|' -zcf $@ $^

ruby/bin/ronn:
	mkdir -p ruby/bin; \
	which ronn >& /dev/null && \
	ln -sf `which ronn` ruby/bin/ronn || \
	gem install ronn -i ruby
	if [ ! -f $@ ]; then pushd ruby/bin && ln -sf ronn.ruby* ronn && popd; fi

$(ronn_man): man/%: ruby/bin/ronn ronn/%.ronn ronn/index.txt ronn/header.txt
	mkdir -p man
	export GEM_PATH=`readlink -f $(top_srcdir)/ruby`:$$GEM_PATH && \
	cd ronn && \
	../ruby/bin/ronn --date=`date "+%Y-%m-%d"` \
	                 --organization="Intel Corporation" \
	                 `basename $@`.ronn
	cat ronn/header.txt ronn/`basename $@` | \
	    sed -e 's/\(#include.*\) \\fIhttp.*/\1\\fR/g' > $@

# GH_PAGES TARGET
gh-pages: doxygen $(dist_man_MANS)
	mkdir -p gh-pages/dox
	mkdir -p gh-pages/man
	cp -rf dox/html/* gh-pages/dox/.
	cp ronn/*.html gh-pages/man/.

else

BUILT_SOURCES =

$(ronn_man): man/%: ronn/%.ronn
	mkdir -p man
	sed 's|^\[//\]: #|.\\\"|' ronn/`basename $@`.ronn > $@
endif

man/geopmsrun.1: man/geopmpy_launcher.1
	cp $^ $@
	if [ -f ronn/geopmpy_launcher.1.html ]; then cp ronn/geopmpy_launcher.1.html ronn/geopmsrun.1.html; fi

man/geopmaprun.1: man/geopmpy_launcher.1
	cp $^ $@
	if [ -f ronn/geopmpy_launcher.1.html ]; then cp ronn/geopmpy_launcher.1.html ronn/geopmaprun.1.html; fi

checkprogs: gtest-checkprogs pytest-checkprogs $(check_PROGRAMS) $(check_LTLIBRARIES)

# INCLUDES
check_PROGRAMS =
check_LTLIBRARIES =
noinst_PROGRAMS =
noinst_LTLIBRARIES =
TESTS =

PHONY_TARGETS = clean-local \
                clean-local-coverage \
                clean-local-man \
                distclean-local \
                rpm \
                doxygen \
                gh_pages \
                # end

include test/Makefile.mk
include test_integration/Makefile.mk
include examples/Makefile.mk
include scripts/Makefile.mk
include openmp.mk

.PHONY: $(PHONY_TARGETS)
