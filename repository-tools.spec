Name: repository-tools
Version: %{VERSION}
Release: 1%{?dist}
Summary: Tools for uploading to repository etc.
Source0: %{name}.tgz
License: ASL 2.0
BuildArch: noarch

BuildRequires: python-virtualenv
Requires: python-argparse
Requires: python-requests
Requires: python-six

%description
%{summary}

%prep
%setup -q

%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --skip-build --root %{buildroot}

%files
%{python_sitelib}/*
%{_bindir}/*
