Summary: Tool for data storage configuration
Name: blivet-gui
Version: 1.3.0
Release: 1%{?dist}
Source0: http://github.com/rhinstaller/blivet-gui/releases/download/%{version}/%{name}-%{version}.tar.gz
License: GPLv2+
Group: Applications/System
BuildArch: noarch
BuildRequires: python3-devel
BuildRequires: desktop-file-utils
BuildRequires: gettext >= 0.18.3
BuildRequires: python-setuptools
BuildRequires: libappstream-glib
Requires: python3
Requires: pygobject3
Requires: gettext
Requires: python3-blivet >= 1:2.0
Requires: gtk3
Requires: polkit-gnome
Requires: python3-meh
Requires: python3-meh-gui
Requires: python3-pid
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
appstream-util validate-relax --nonet %{buildroot}/%{_datadir}/appdata/blivet-gui.appdata.xml

%find_lang %{name}

%post
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :

%postun
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi

%posttrans
/usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :

%files -f %{name}.lang
%{_mandir}/man1/blivet-gui.1*
%{python3_sitelib}/*
%{_datadir}/applications/blivet-gui.desktop
%{_datadir}/polkit-1/actions/org.fedoraproject.pkexec.blivet-gui.policy
%{_datadir}/icons/hicolor/*/apps/blivet-gui.png
%{_datadir}/appdata/blivet-gui.appdata.xml
%{_datadir}/blivet-gui
%{_bindir}/blivet-gui
%{_bindir}/blivet-gui-daemon

%changelog
* Tue Apr 12 2016 Vojtech Trefny <vtrefny@redhat.com> - 1.3.0
- Fix visualization CSS styles (vtrefny@redhat.com)
- Fix visualization of group devices inside VG (#1326175) (vtrefny@redhat.com)
- Translations moved from translate.zanata.org to fedora.zanata.org (vtrefny@redhat.com)
- Remove gnome-icon-theme from requires (vtrefny@redhat.com)
- Fix adding a new device into an existing mdarray (vtrefny@redhat.com)
- Add make ci target and test dependencies (vtrefny@redhat.com)
- Fix methods for locating CSS and UI files (vtrefny@redhat.com)
- SizeChooserAreaTest: Libbytesize support related fixes (vtrefny@redhat.com)
- Use property instead of setter method for luks decrypt passphrase (vtrefny@redhat.com)
- CacheArea: Fix displaying parent name in pv chooser (vtrefny@redhat.com)
- Pylint/PEP8 fixes, fix AddDialog test cases (vtrefny@redhat.com)
- Skip ListPartitionsTest when X server is not available (vtrefny@redhat.com)
- Remove remaining user documentation related code (vtrefny@redhat.com)
- AddDialog: do not allow to set size when adding vg to pvs (vtrefny@redhat.com)
- Do not try to display (meta)data level for btrfs subvolumes (vtrefny@redhat.com)
- Fix adding lvm thinpools (vtrefny@redhat.com)
- Libbytesize support changes (vtrefny@redhat.com)
- Set communication socket to be owned by user not root (vtrefny@redhat.com)
- Remove obsolte/unused methods from BlivetUtils (vtrefny@redhat.com)
- Fix editting volume groups (vtrefny@redhat.com)
- Pylint and PEP8 fixes (vtrefny@redhat.com)
- Always remove format when removing device (vtrefny@redhat.com)
- Hide second raid chooser for non LVs (vtrefny@redhat.com)
- LVM RAID support -- utils part (vtrefny@redhat.com)
- SizeArea,AddDialog -- LVM RAID support, part 2 (vtrefny@redhat.com)
- Temporary disable device name validation (vtrefny@redhat.com)
- Move supported fs types to EditDialog (vtrefny@redhat.com)
- Add RAID chooser into ParentArea when adding new LV (vtrefny@redhat.com)
- Do not display parent size chooser for LVs (vtrefny@redhat.com)
- AddLabelDialog: Fix available disklabels (vtrefny@redhat.com)
- SizeArea -- RAID support, part 1 (vtrefny@redhat.com)
- Raise exception in client when accesing blivet attribute failed (vtrefny@redhat.com)
- AddDialog: Do not offer full PVs as possible parents for LVs (vtrefny@redhat.com)
- AddDialog: Switch to single SizeArea model (vtrefny@redhat.com)
- Fix ParentArea for non-LVM parents (vtrefny@redhat.com)
- AddDialog: Fix checking for lvmlv and lvmthinlv device types (vtrefny@redhat.com)
- AddDialog: Change _get_selected_device_type to property (vtrefny@redhat.com)
- Remove support for adding btrfs as a disklabel (vtrefny@redhat.com)
- Refactor add_partition method (vtrefny@redhat.com)
- Fix passing selected and free devices to AddDialog (vtrefny@redhat.com)
- Move supported types (fs, raid levels, disklabels) to AddDialog (vtrefny@redhat.com)
- SizeChooser: Update main size chooser when changing size for parents (vtrefny@redhat.com)
- SizeChooser: Add ParentArea for parents size selection (vtrefny@redhat.com)
- Merge branch 'master' of github.com:rhinstaller/blivet-gui (vtrefny@redhat.com)
- Merge pull request #14 from dashea/eintr (vtrefny@redhat.com)
- Remove the removal of the eintr checker, which has been removed (dshea@redhat.com)
- Use new_lv instead of LVM objects constructors (vtrefny@redhat.com)
- Fix adding devices on DASD and zFCP disks (#1305495) (vtrefny@redhat.com)
- Make LUKS encrypted partitions resizable (vtrefny@redhat.com)
- Use list of children for devices instead of get_children (vtrefny@redhat.com)
- Fix visualization of raw format LUKS devices (#1288943) (vtrefny@redhat.com)
- Size area refactoring (vtrefny@redhat.com)
- Fix updateSizeInfo on BIOSBoot partitions (#1286616) (vtrefny@redhat.com)
- Add cache info to device info dialog (vtrefny@redhat.com)
- Reimplement size area using Glade (vtrefny@redhat.com)
- LVM cache support -- utils part (vtrefny@redhat.com)
- LVM cache support -- UI part (vtrefny@redhat.com)
- Allow nested ProxyDataContainer in server-cleint communication (vtrefny@redhat.com)
- Add tests for recently found bugs (vtrefny@redhat.com)
- Fix allow creating lvm snapshots (vtrefny@redhat.com)
- AddDialog: Fix min size for vg children (vtrefny@redhat.com)
- AddDialog: Fix parent type when adding LMV LV (vtrefny@redhat.com)
- Don't allow adding btrfs volume to devices smaller than 256 MiB (vtrefny@redhat.com)
- Do not call get_children more than necessary (vtrefny@redhat.com)
- New version 1.2 (vtrefny@redhat.com)

* Wed Nov 18 2015 Vojtech Trefny <vtrefny@redhat.com> - 1.2-1
- Add PEP8 compliance check to 'make check' (vtrefny)
- Fix PEP8 violations. (vtrefny)
- Remove some obsolete/debug prints and imports (vtrefny)
- Catch blivet.errors.LUKSError instead of BlockDev.CryptoError (vtrefny)
- Add test for adding device to partitions list (vtrefny)
- EditDialog: add test for formatting extended partitions (vtrefny)
- Add test for communication.proxy_utils (vtrefny)
- Fix BlivetProxyObjectTest (vtrefny)
- Add tests for new FreeSpaceDevice features (vtrefny)
- Fix check for allowed max partitions count (vtrefny)
- AddDialog: fix displaying parents for MDArray PVs (vtrefny)
- Fix 'disk' attribute for FreeSpaceDevices (vtrefny)
- Visualization: add protected icon to protected devices (vtrefny)
- Do not allow deleting/editting protected devices (vtrefny)
- Remove pocketlint from BuildRequires (vtrefny)
- Remove 'check' from 'make release' target (vtrefny)
- Run mkfs.ntfs with '-f' option (fast formatting) (#1253013) (vtrefny)
- Add support for creating NTFS format (vtrefny)
- Fix visualisation of group devices with 0 size (#1275815) (vtrefny)
- Visualization: do not allocate remaing space when there is no space left (vtrefny)
- Fix device visualisation with high contrast theme (vtrefny)
- Properly catch and reraise exceptions from BlivetUtils initialization (vtrefny)
- Fix tests to work with localization (vtrefny)
- Add make coverage target (vtrefny)
- Add loading window when starting blivet-gui (vtrefny)
- Fix make po-pull/push target (vtrefny)
- Set translation domain for glade files (vtrefny)

* Wed Sep 23 2015 Vojtech Trefny <vtrefny@redhat.com> - 1.1-1
- Fix make bumpver to work with 1.x versions (vtrefny)
- Fix finished actions visualisation in processing window (vtrefny)
- Remove MANIFEST file from git (vtrefny)
- Fix visualization for non-existing encrypted partitions (vtrefny)
- Add "local" target to Makefile (vtrefny)
- Use zanata-python-client instead of zanata-cli (vtrefny)
- AddDialog: Always display at least one size area (vtrefny)
- Fix max size of KickstartSelectDevicesDialog (vtrefny)
- Fix dialogs with actions list height (vtrefny)
- Allow shrinking extended partitions (vtrefny)
- Fix bug description when reporting using python-meh (vtrefny)
- AddDialog: Add a second passphrase entry for verification (vtrefny)
- Remove obsolete test run mode from BlivetUtils (vtrefny)
- Allow deleting of active formats in kickstart mode (vtrefny)

* Wed Sep 02 2015 Vojtech Trefny <vtrefny@redhat.com> - 1.0-1
- Update man page (vtrefny)
- Add AppData validation to spec file (vtrefny)
- Add tags to desktop file (vtrefny)
- Add AppData for blivet-gui (vtrefny)
- Fix few typos and grammar in strings (vtrefny)
- Add first test for ListPartitions (vtrefny)
- Fix adding LVM Thin LVs (vtrefny)
- Remove help from package (vtrefny)
- ListParents: fix checking parents for logical partitions (vtrefny)
- Add icons to %files in spec file (vtrefny)
- DeviceInfoDialog: add special info for mdarrays (vtrefny)
- Fix maximal size for thinpools (vtrefny)
- Add desktop icon for blivet-gui (vtrefny)
- Selection unit tests for AddDialog (vtrefny)
- More tests for AddDialog and PartitionEditDialog (vtrefny)
- Fix check_mountpoint method (vtrefny)
- Do not run unittests without X server (vtrefny)
- More unit tests for AddDialog (vtrefny)
- ProcessingWindow: Center on blivet-gui main window. (vtrefny)
- PhysicalView: Double click to select parent device (vtrefny)
- Fix logical and physical view for mdarrays with lvm (vtrefny)
- Fix adding lvmvg to MD raid (vtrefny)
- AddDialog: Fix minimal size when changing device type (vtrefny)
- AddDialog: Delete content of Gtk.Entry when hiding it (vtrefny)
- Fix physical view for devices with logical partitions as parents (vtrefny)
- Fix spelling in isUninitializedDisk method name (vtrefny)
- Add unittest for AddDialog (vtrefny)
- Add test for fslabel validity check (vtrefny)
- AddDialog, PartitionEditDialog: Add fslabel validity check (#1236112) (vtrefny)
- Do not allow to add lvmvg to lvmpv with insufficient size (vtrefny)
- Fix allowed pesizes for lvmvg in AddDialog (vtrefny)
- Allow resizing of extended partitions (vtrefny)
- Reimplement ActionsMenu using Glade (vtrefny)
- Add test for ListActions (vtrefny)
- Fix visualization for logical group devices (vtrefny)
- In kickstart mode show future mountpoints in partition list (vtrefny)
- EditDialog: Add mountpoint validity check (vtrefny)
- AddDialog: Fix mountpoint validation (vtrefny)
- Fix actions dialogs width (vtrefny)
- AddDialog: Update min size limit for encrypted devices (vtrefny)
- AddDialog: Update min size limit based on selected pesize (vtrefny)
- AddDialog: Add method to update size limits (vtrefny)
- AddDialog: allow empty device name (vtrefny)
- AddDialog: Do not offer PESize larger than free space available (vtrefny)
- Fix visualization for live usb deviceFix visualization for live usb devicess (vtrefny)
- Fix free space regions for unitialized disks (vtrefny)
- Do not refresh views after cancelling delete action (vtrefny)
- Fix displaying number of pending actions after applying them (vtrefny)
- Quit 'nicely' on Ctrl-C (vtrefny)
- Add test for fslabel in PartitionEditDialog (vtrefny)
- PartitionEditDialog: allow setting fslabel when changing format (vtrefny)
- Add test for FreeSpaceDevice (vtrefny)
- Add name validation for devices in AddDialog (vtrefny)
- Fix displaying device info icons (vtrefny)
- Add ID and format to FreeSpaceDevice and RawFormatDevice (vtrefny)
- Preselect filesystem type for add/edit dialog (vtrefny)
- Visualization size corresponding with device size (vtrefny)
- Don't allow to add more than 4 partitions on msdos disklabels (vtrefny)
- Call blivet.partitioning.getFreeRegions with align=True (vtrefny)
- Move i18n definitions to one file (vtrefny)
- Display number of pending actions in statusbar (vtrefny)
- Add information icons to devices in logical view (vtrefny)
- Switch to device logical view by double-clicking on it (vtrefny)
- First unittest for blivet_utils (vtrefny)
- Remove python.six, python3 only support now (vtrefny)
- Fix visualization update after resizing device (vtrefny)
- Add device size to visualization (vtrefny)
- Hide physical view for disks (vtrefny)
- Use python3-pid for pidfile creation (vtrefny)
- New version 0.3.6 (vtrefny)

* Thu Aug 06 2015 Vojtech Trefny <vtrefny@redhat.com> - 0.3.6-1
- Fix visualisation for extended partitions with single child (vtrefny)
- Fix parent visualization for encrypted LVMs (vtrefny)
- Allow adding new VG to an empty LVMPV (vtrefny)
- Remove obsolete definiton of locate_ui_file method (vtrefny)
- Do not allow displaying device info for raw format devices (vtrefny)
- Remove old visualization files (vtrefny)
- Display context menu for logical view visualization (vtrefny)
- New UI, part 4: Physical View -- parents visualization (vtrefny)
- Fix visualization for raw format devices (vtrefny)
- Tweak device visualisation in logical view using CSS (vtrefny)
- Move various GUI helper functions into one file (vtrefny)
- New UI, part 3: New device visualisation for logical view (vtrefny)
- BlivetUtilsServer: quit when recieve empty message (vtrefny)
- Renaming few files and folders (vtrefny)

* Wed Jul 29 2015 Vojtech Trefny <vtrefny@redhat.com> - 0.3.5-1
- Fix displaying btrfs as a disklabel (vtrefny)
- Fix adding btrfs as a disklabel (vtrefny)
- Small UI fixes (vtrefny)
- Few stylistic fixes (vtrefny)
- New UI, part 2: listing of device children in logical view (vtrefny)
- Catch AttirbuteErrors during remote utils calls (vtrefny)
- PartitionEditDialog: Do not offer formats that are not supported (vtrefny)
- Fix context menu for partitions list (vtrefny)
- Add test for PartitionEditDialog (vtrefny)
- Fix AddDialog tests (vtrefny)
- AddDialog: Do not offer formats that are not supported (vtrefny)
- Display MDarrays and Btrfs Volumes in device list (vtrefny)
- Remove custom method to detect extended partition on disk (vtrefny)
- Allow displaying disks withou disklabel in AddDialog (vtrefny)
- Fix creating extended partitions (vtrefny)
- Remove unused import (vtrefny)
- Fix pocketlint settings (vtrefny)
- Do not allow adding snapshot when there is not enough free space (vtrefny)
- Fix converting ProxyDataContainer to IDs (vtrefny)
- Move all tests to one folder (vtrefny)
- Add tests to test server-client functions (vtrefny)
- Fix catching exceptions in client-server communication (vtrefny)
- BlivetGUIClient: fix sending ProxyDataContainer (vtrefny)
- New version 0.3.4 (vtrefny)

* Thu Jul 16 2015 Vojtech Trefny <vtrefny@redhat.com> - 0.3.4-1
- Pylint fixes (vtrefny)
- Use pocketlint for blivet-gui (vtrefny)
- Recreate list of actions using Glade (vtrefny)
- Completely separate toolbar for blivet actions and for device actions (vtrefny)
- Add device information button to DeviceToolbar (vtrefny)
- Separate ActionsToolbar and DeviceToolbar (vtrefny)
- New UI, part 1 (vtrefny)
- Use gi.require_version when importing from gi.repository (vtrefny)
- Few pylint overrides and fixes (vtrefny)
- Reimplement AddDisklabelDialog using Glade (vtrefny)
- Add unittest to test AdvancedOptions from AddDialog (vtrefny)
- Add "test" rule to Makefile (vtrefny)
- Add unittest to test SizeChooserArea from AddDialog (vtrefny)
- Move SizeChooserArea to own module (vtrefny)
- Fix name suggestion for thinlvs (vtrefny)
- Fix progress bar fraction during applying changes (vtrefny)
- Do not allow editing of non-existing LVM VGs (vtrefny)
- EditDialog: Do not allow select "None" as format (vtrefny)
- Fix removing parents for encrypted devices and btrfs volumes (vtrefny)
- Delete existing partition table when adding btrfs as a disklabel (vtrefny)
- Align target size before resizing partitions (#1207798) (vtrefny)
- Fix device visualisation selection after window resize (vtrefny)
- Allow adding encrypted logical partitions (vtrefny)
- DeviceInfoDialog: auto-ellipsize long labels (vtrefny)
- Do not display disks without disklabel in AddDialog (vtrefny)
- Move exception catching to add_device method (vtrefny)
- Do not allow adding new LV to an incomplete VG (vtrefny)
- Do not allow to create an extended partition on GPT disks (vtrefny)

* Thu May 21 2015 Vojtech Trefny <vtrefny@redhat.com> - 0.3.3-1
- Require newest blivet (python-blivet 1.4) (vtrefny)
- Allow using of free space inside extended partitions for LVM (vtrefny)
- Use sys.exit instead of blivetgui.quit in certain situations (vtrefny)
- AddDialog: fix size selection for btrfs disks (vtrefny)
- Remove obsolete option to embedd blivet-gui to another app (vtrefny)
- Remove some obsolete/unused BlivetUtils methods (vtrefny)

* Thu May 14 2015 Vojtech Trefny <vtrefny@redhat.com> - 0.3.2-1
- Devel branch for l10n on Zanata (vtrefny)
- Use currentSize instead of partedDevice.length for empty disks (vtrefny)
- add_device method refactoring (vtrefny)
- Display progress in ProcessingWindow dialog (vtrefny)
- BlivetGUI: Call the blivet_do_it method with progress report support (vtrefny)
- Add progress callback support in BlivetUtils.blivet_do_it (vtrefny)
- Fix Makefile and spec for python3 (vtrefny)
- Add thinlv support to DeviceInformationDialog (vtrefny)
- Do not try to display information about unknown devices (vtrefny)
- Added support for creating LVM thinpools and thinlvs (vtrefny)
- Pylint fixes (vtrefny)
- Fix displaying parents in device information dialog (vtrefny)
- Add version information to the AboutDialog (vtrefny)
- Fix adding encrypted partitions (vtrefny)
- Fix displaying future mountpoint in kickstart mode (vtrefny)
- Pylint fixes (vtrefny)
- Fix 'None' as disk.model in kickstart dialogs (vtrefny)
- New option to show device information (vtrefny)
- Do not (de)activate non-existing options in menus/toolbars (vtrefny)
- Do not allow to resize lvs with snapshots (vtrefny)
- AddDialog refactoring (vtrefny)
- Add support for creating LVM snapshots (vtrefny)
- Python 3 compatible localisation support (vtrefny)

* Mon Apr 27 2015 Vojtech Trefny <vtrefny@redhat.com> - 0.3.1-1
- Fix catching exception when trying to decrypt LUKS device (vtrefny)
- Fix python-meh requirement to Python 3 version (vtrefny)
- Remove obsolete methon convert_to_size (vtrefny)
- Fix None disk.model in description (vtrefny)
- Use format.systemMountpoint instead of format.mountpoint (vtrefny)
- New version 0.3.0 (vtrefny)

* Wed Apr 22 2015 Vojtech Trefny <vtrefny@redhat.com> - 0.3.0-1
- Add translator credits to AboutDialog (vtrefny)
- Merge branch 'separate-processes' into devel (vtrefny)
- Advanced logging and python-meh support (vtrefny)
- Check if the server starts in blivet-gui main() (vtrefny)
- Fix returning of BlivetProxyObject and id to it (vtrefny)
- Pylint checks and docstrings (vtrefny)
- Logging server communication (vtrefny)
- Add message verification with a secret "key" (vtrefny)
- Remove temp directories atexit of server (vtrefny)
- Do not use Gio.Settings to obtaion default system font (vtrefny)
- Store blivet logs on server site (vtrefny)
- Delete udisks_loop.py file (no longer used) (vtrefny)
- Use blivet's ParentList for FreeSpaceDevice parents (vtrefny)
- Autorun server part, PID file for server (vtrefny)
- Update setup.py with new package_data (vtrefny)
- Use ProxyDataContainer instead of ReturnList (vtrefny)
- Use ProxyDataContainer for old_mountpoints (vtrefny)
- Fix EditDialog using non-existing UserSelection class (vtrefny)
- More detailed information for proxy objects AttributeError (vtrefny)
- Create instance of BlivetUtils upon client request (vtrefny)
- Use ProxyDataContainer instead of ResizeInfo namedtuple (vtrefny)
- Catch exception raised during BlivetUtils calls (vtrefny)
- Send message length in messages and use it in recv (vtrefny)
- Do not forward LUKS decrypt exceptions to client (vtrefny)
- Use GLib.timeout_add instead of GObject.timeout_add (vtrefny)
- Delete socket file using atexit (vtrefny)
- Catch GLib.GError instead of blivet.errors.CryptoError (vtrefny)
- Pickle only whitelisted objects (vtrefny)
- Mutex-protected server calls (vtrefny)
- Proper catching and reraising exception during doIt() (vtrefny)
- Use UnixStreamServer instead of TCPServer (vtrefny)
- Close server on client exit (vtrefny)
- Fix blivetgui.reload() function (vtrefny)
- Use GLib.idle_add instead of GObject.idle_add (vtrefny)
- New way of re-raising exceptions from BlivetUtils (vtrefny)
- Remove unused functions; mark some functions as private (vtrefny)
- Replace BlivetUtils calls with BlivetGUIClient calls (vtrefny)
- Replace UserSelection with ProxyDataContainer (vtrefny)
-"Binary" file for server/daemon part (vtrefny)
- blivet-gui process separation (vtrefny)
- Do not check root privilegies for blivet-gui (client part) (vtrefny)

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
