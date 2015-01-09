Summary: Tool for data storage configuration
Name: blivet-gui
Version: 0.1.10
Release: 1%{?dist}
Source0: https://github.com/vojtechtrefny/blivet-gui/archive/%{name}-%{version}.tar.gz
License: GPLv3
Group: Applications/System
BuildArch: noarch
BuildRequires: python2-devel
BuildRequires: desktop-file-utils
BuildRequires:intltool
BuildRequires: gettext
BuildRequires: python-setuptools
Requires: python
Requires: pygobject3
Requires: gettext
Requires: python-blivet >= 0.73
Requires: gtk3
Requires: gnome-icon-theme
Requires: polkit-gnome
Requires: yelp
Url: http://github.com/vojtechtrefny/blivet-gui

%description
Graphical (GTK) tool for manipulation and configuration of data storage
(disks, LVMs, RAIDs) based on blivet library.

%prep
%setup -q

%build
make %{?_smp_mflags}

%install
make DESTDIR=%{buildroot} install

%check
desktop-file-validate %{buildroot}/%{_datadir}/applications/blivet-gui.desktop

%find_lang %{name}

%clean
rm -rf %{buildroot}

%files -f %{name}.lang
%{python_sitelib}/*
/usr/share/applications
/usr/share/polkit-1/actions
/usr/share/blivet-gui
/usr/share/help/C/blivet-gui
/usr/bin/blivet-gui