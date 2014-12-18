Summary: Tool for data storage configuration
Name: blivet-gui
Version: 0.1.9
Release: 3
Source0: https://github.com/vojtechtrefny/blivet-gui/archive/%{name}-%{version}.tar.gz
License: GPLv3
Group: Applications/System
BuildArch: noarch
BuildRequires: python2-devel, desktop-file-utils, intltool, gettext, python-setuptools
Requires: python, pygobject3, gettext, yelp, python-blivet >= 0.61, gtk3, gnome-icon-theme, polkit-gnome, python-pyudev
Url: http://github.com/vojtechtrefny/blivet-gui

%description
Graphical (GTK) tool for manipulation and configuration of data storage
(disks, LVMs, RAIDs) based on blivet library.

%prep
%setup -q

%build
make

%install
make DESTDIR=%{buildroot} install

%check
desktop-file-validate %{buildroot}/%{_datadir}/applications/blivet-gui.desktop

%find_lang %{name}

%clean
rm -rf %{buildroot}

%files -f %{name}.lang
%defattr(-,root,root,-)
%{python_sitelib}/*
/usr/share/applications
/usr/share/polkit-1/actions
/usr/share/blivet-gui
/usr/share/help/C/blivet-gui
/usr/bin/blivet-gui