# --- Variables ---
PKGNAME=$(shell basename *.spec .spec)
VERSION?=0.0.0# assign zeros only if not specified from cmdline by make {target} VERSION=1.2.3
GROUP?=com.example# used when uploading to artifact repository
WORKDIR:=/tmp/
RELEASE=$(shell grep -oP '(?<=^Release: ).*' $(PKGNAME).spec | xargs rpm --eval)
BUILDARCH=$(shell grep -oP '(?<=^BuildArch: ).*' $(PKGNAME).spec)
RPMDIR=$(shell rpm --eval %{_rpmdir})
prefix=$(DESTDIR)$(shell rpm --eval %{_prefix})
bindir=$(DESTDIR)$(shell rpm --eval %{_bindir})
datadir_short=$(shell rpm --eval %{_datadir})
datadir=$(DESTDIR)$(datadir_short)
pkgdatadir_short=$(datadir_short)/$(PKGNAME)
pkgdatadir=$(datadir)/$(PKGNAME)
libdir=$(DESTDIR)$(shell rpm --eval %{_libdir})
defaultdocdir=$(DESTDIR)$(shell rpm --eval %{_defaultdocdir})
initrddir=$(DESTDIR)$(shell rpm --eval %{_initrddir})
sysconfdir:=$(DESTDIR)$(shell rpm --eval %{_sysconfdir})
pythonsitedir:=$(DESTDIR)$(shell python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")
SRPMDIR=$(shell rpm --eval '%{_srcrpmdir}')
OS_VERSIONS = 6 7
RESULTDIR = .

# --- Deprecated variables ---
DISTTAG=$(shell rpm --eval '%{dist}' | tr -d '.')

# --- Helper functions ---
# They are functions so they can be overrided
# takes the content of current working directory and packs it to tgz
define do-distcwd
	# make --no-print-directory -s changelog | grep -v '^$$' > ChangeLog
	rm -f $(WORKDIR)/$(PKGNAME).tgz
	tar cvzf $(WORKDIR)/$(PKGNAME).tgz --transform "s,^\.,$(PKGNAME)-$(VERSION)," .
endef

# --- TARGETS ---
distcwd:
	$(do-distcwd)

# Builds RPM package only for your OS version. Much faster than make rpms, good for basic testing of your spec/makefile
rpm: distcwd
	rpmbuild --define "VERSION $(VERSION)" -ta $(WORKDIR)/$(PKGNAME).tgz

srpm: distcwd
	rpmdev-wipetree
	rpmbuild --define "VERSION $(VERSION)" -ts ${WORKDIR}/$(PKGNAME).tgz

# Build RPMs for all os versions defined on OS_VERIONS
rpms: srpm
	$(foreach os_version, $(OS_VERSIONS), \
	    mkdir -p $(RESULTDIR)/$(os_version) && \
	    rm -rf $(RESULTDIR)/$(os_version)/* && \
	    /usr/bin/mock \
	      --resultdir $(RESULTDIR)/$(os_version) \
	      --define "dist .el$(os_version)" \
	      --define "VERSION $(VERSION)" \
	      --rebuild \
	      -r epel-$(os_version)-x86_64 \
	      $(SRPMDIR)/*.src.rpm; \
	)

# Upload RPMs for all os versions to Sonatype Nexus
# Requires package repository-tools
uploadrpms: rpms
	$(foreach os_version, $(OS_VERSIONS), \
	    artifact upload \
	      $(UPLOAD_OPTIONS) \
	      $(RESULTDIR)/$(os_version)/$(PKGNAME)-$(VERSION)-*.$(BUILDARCH).rpm \
	      packages-el$(os_version) \
	      $(GROUP); \
	)

# Shows VCS changes, can be used to generate changelog
changelog:
	git log --pretty=format:"%d%n    * %s [%an, %ad]"  --date=short

# Adds changelog to package
installChangelog:
	mkdir -p $(defaultdocdir)/$(PKGNAME)-$(VERSION)
	install -m 644 ChangeLog $(defaultdocdir)/$(PKGNAME)-$(VERSION)

# ----- deprecated targets ---
# requires repository-tools for uploading to Sonatype Nexus
define do-upload
	artifact upload $(UPLOAD_OPTIONS) $(RPMDIR)/$(BUILDARCH)/$(PKGNAME)-$(VERSION)-$(RELEASE).$(BUILDARCH).rpm packages-$(DISTTAG) $(GROUP)
endef

upload: rpm
	$(do-upload)


.PHONY: distcwd rpm srpm rpms upload uploadrpms changelog installChangelog
