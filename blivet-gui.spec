Summary: Tool for data storage configuration
Name: blivet-gui
Version: 0.3.0
Release: 1%{?dist}
Source0: http://github.com/rhinstaller/blivet-gui/releases/download/%{version}/%{name}-%{version}.tar.gz
License: GPLv2+
Group: Applications/System
BuildArch: noarch
BuildRequires: python3-devel
BuildRequires: desktop-file-utils
BuildRequires: intltool
BuildRequires: gettext
BuildRequires: python-setuptools
Requires: python3
Requires: python-six
Requires: pygobject3
Requires: gettext
Requires: python3-blivet >= 1:1.2
Requires: gtk3
Requires: gnome-icon-theme
Requires: polkit-gnome
Requires: yelp
Requires: python-meh
Requires: python-meh-gui
URL: http://github.com/rhinstaller/blivet-gui

%description
Graphical (GTK) tool for manipulation and configuration of data storage
(disks, LVMs, RAIDs) based on blivet library.

%prep
%setup -q

%build
make %{?_smp_mflags}

%install
make DESTDIR=%{buildroot} install

desktop-file-validate %{buildroot}/%{_datadir}/applications/blivet-gui.desktop

%find_lang %{name}

%files -f %{name}.lang
%{_mandir}/man1/blivet-gui.1*
%{python_sitelib}/*
%{_datadir}/applications/blivet-gui.desktop
%{_datadir}/polkit-1/actions/org.fedoraproject.pkexec.blivet-gui.policy
%{_datadir}/blivet-gui
%{_datadir}/help/C/blivet-gui
%{_bindir}/blivet-gui
%{_bindir}/blivet-gui-daemon

%changelog
* Mon Apr 13 2015 Vojtech Trefny <vtrefny@redhat.com> - 0.2.4-1
- Auto-ellipsize longer strings in ListPartitions (vtrefny)
- Fix widget spacing in AddLabelDialog (vtrefny)
- Better handling of raw device formats (#1207743) (vtrefny)
- Fix blivetgui.reload() function (vtrefny)
- Python3 compatibility for device visualisation (vtrefny)
- Python3 compatible re-raising exceptions (vtrefny)
- Do not allow resizing of non-existing devices. (vtrefny)
- Catch GLib.GError instead of blivet.errors.CryptoError (vtrefny)
- Fix device visualisation with russian locale (#1202955) (vtrefny)
- EditDialog: Set the value of size SpinButton to device size (vtrefny)
- Do not display current size in EditDialog (#1201706) (vtrefny)

* Fri Mar 13 2015 Vojtech Trefny <vtrefny@redhat.com> - 0.2.3-1
- Fix resizing LVs (#1201745) (vtrefny)
- Start KickstartSelectDevicesDialog with MainWindow as parent (vtrefny)
- Simplyfication of MainMenu, ActionsMenu and ActionsToolbar classes (vtrefny)
- Do not call updateSizeInfo() multiple times (vtrefny)
- Removed last dependency on blivet from BlivetGUI (vtrefny)
- EditDialog: Inform about corrupted filesystems (#1198239) (vtrefny)
- Fix python-meh handler.install (vtrefny)
- Fix returning success when editting LVM VGs (vtrefny)
- Do not refresh views when there are actions scheduled (vtrefny)
- DeviceCanvas: do not select invalid path (vtrefny)
- Re-raise exception from BlivetUtils with original traceback (vtrefny)
- Move logging from BlivetUtisl to BlivetGUI (vtrefny)
- Move thread creation and calling doIt() from ProcessingWindow (vtrefny)
- Move handling errors from BlivetUtils to BlivetGUI, part 2 (vtrefny)
- Move handling errors from BlivetUtils to BlivetGUI (vtrefny)
- ListPartitions cleanup (vtrefny)
- Fix blivet required version (>= 1.0) (vtrefny)
- Merge branch 'new_class_model' (vtrefny)
- Simplification of ListAction and undo history (vtrefny)
- New class model - preparation for root/non-root separation (vtrefny)
- New version 0.2.2 (vtrefny)
- New version 0.2.2 (vtrefny)

* Mon Feb 23 2015 Vojtech Trefny <vtrefny@redhat.com> - 0.2.2-1
- Store blivet program log too (vtrefny)
- Fix Size calling (vtrefny)
- Replace filter with regexp (vtrefny)
- blivet.size is now module (vtrefny)
- Fix covertTo to use blivet.size.parseUnits function (vtrefny)
- New version 0.2.1 (vtrefny)

* Wed Feb 18 2015 Vojtech Trefny <vtrefny@redhat.com> - 0.2.1-1
- Fix python-meh for processing window (vtrefny)
- python-meh support (vtrefny)
- Base default container name on distribution name (vtrefny)
- Removed some ununsed functions (vtrefny)
- Enable blivet logging, preparations for blivet-gui internal logging (vtrefny)
- Detect minimal device (partition and LV) size during BlivetUtils initialization (vtrefny)
- Swap is not resizable (vtrefny)
- Catch exceptions when checnking minSize on device with broken fs (vtrefny)
- Fix luks passphrase dialog spacing (vtrefny)
- Added root_check_window.ui file (vtrefny)
- 'Root privilegies required' dialog changed to window (vtrefny)
- MainMenu: partition_menu renamed to device_menu (vtrefny)
- pylint removed unallowed spaces (vtrefny)

* Thu Jan 22 2015 Vojtech Trefny <vtrefny@redhat.com> - 0.2.0-6
- GitHub release as source for spec file (vtrefny)

* Thu Jan 22 2015 Vojtech Trefny <vtrefny@redhat.com> - 0.2.0-5
- Fixed macro-in-changelog rpmlint warning (vtrefny)

* Thu Jan 22 2015 Vojtech Trefny <vtrefny@redhat.com> - 0.2.0-4
- New build 0.2.0-4
- Fedora review: updated specfile, licence added to package (vtrefny)
- %%clean section removed from spec file (vtrefny)

* Tue Jan 20 2015 Vojtech Trefny <vtrefny@redhat.com> - 0.2.0-3
- Licence file added (GPLv2) (vtrefny)
- New source location (vtrefny)

* Tue Jan 20 2015 Vojtech Trefny <vtrefny@redhat.com> - 0.2.0-2
- Version bumped to 0.2 (vtrefny)
- EditDialog: typo (vtrefny)
- Fixed generating spec file changelog (vtrefny)

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
