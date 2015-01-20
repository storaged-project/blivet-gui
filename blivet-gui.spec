Summary: Tool for data storage configuration
Name: blivet-gui
Version: 0.2.0
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
Requires: python-blivet
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
%{_mandir}/man1/blivet-gui.1*
%{python_sitelib}/*
/usr/share/applications
/usr/share/polkit-1/actions
/usr/share/blivet-gui
/usr/share/help/C/blivet-gui
/usr/bin/blivet-gui
/usr/bin/blivet-gui_pkexec

%changelog
* Mon Jan 19 2015 Vojtech Trefny <vtrefny@redhat.com> - 0.1.11-1
- New version 0.1.11 (vtrefny)
- bumpver target for makefile (vtrefny)
- Merge branch 'master' of github.com:vojtechtrefny/blivet-gui (vtrefny)
- Specific binary file for desktop file (vtrefny)
- User help update (vtrefny)
- Fix python-blivet required version (vtrefny)
- Fix long device names (vtrefny)
- Suppress broad-except pylint errors. (amulhern)
- Change relative to absolute imports. (amulhern)
- Omit or hide unused variables and computations. (amulhern)
- main.py moved to blivet-gui file (vtrefny)
- Omit needless imports. (amulhern)
- Move % operator outside translation. (amulhern)
- Do not use wildcard import. (amulhern)
- Do not use builtin name format as parameter name. (amulhern)
- Fix bad indentation. (amulhern)
- Initial pylint setup. (amulhern)
- Support lvm inside extended partitions (vtrefny)
- pylint (vtrefny)
- AddDialog: Move btrfs type chooser above parents view (vtrefny)
- Do not clear actions after apply in ks mode (vtrefny)
- blivet-gui man page (vtrefny)
- Fix embedded function and example (vtrefny)
- fedora-review fixes for spec and desktop file (vtrefny)
- Python binary file (vtrefny)
- Check if file exists while saving ks (vtrefny)
- Mountpoint support for btrfs in ks mode (vtrefny)
- Don't allow editing mdmember partitions (vtrefny)
- Version 0.1.10 (vtrefny)
- Do not sort child devices on disks with raw device (vtrefny)
- Fix unicode converting bug (vtrefny)
