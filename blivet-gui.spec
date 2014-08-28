%define name blivet-gui
%define version 0.1.8
%define unmangled_version 0.1.8
%define release 2
%define build_timestamp %(date +"%Y%m%d")

Summary: Tool for data storages configuration
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{unmangled_version}.tar.gz
Source1: org.fedoraproject.pkexec.blivet-gui.policy
Source2: blivet-gui.desktop
License: GPLv3
Group: Applications/System
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Vojtech Trefny <vtrefny@redhat.com>
BuildRequires: python2-devel, desktop-file-utils
Requires: python, pygobject3, gettext, yelp, python-blivet >= 0.61, gtk3, gnome-icon-theme, polkit-gnome
Provides: blivetgui
Url: http://github.com/vojtechtrefny/blivet-gui

%description
		 ...

%prep
%setup -n %{name}-%{unmangled_version}

%build
python2 setup.py build

%install
mkdir -p %{buildroot}%{_datadir}/polkit-1/actions/
cp %{SOURCE1} %{buildroot}%{_datadir}/polkit-1/actions/

desktop-file-install                                    \
--dir=${RPM_BUILD_ROOT}%{_datadir}/applications         \
%{SOURCE2}

python2 setup.py install -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES


%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
/usr/share/applications/blivet-gui.desktop
/usr/share/polkit-1/actions/org.fedoraproject.pkexec.blivet-gui.policy
