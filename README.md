blivet-gui is a graphical tool for storage configuration using blivet library

### CI status

<img alt="CI status" src="https://fedorapeople.org/groups/storage_apis/statuses/blivet-gui-master.svg" width="100%" height="225ex" />

### Licence

See [COPYING](COPYING)

### Installation

#### From Fedora repositories

blivet-gui is available in Fedora repositories. You can install it using

    $ sudo dnf install blivet-gui

#### Daily builds (for Fedora)

Daily builds of blivet-gui are available in `@storage/blivet-daily` Copr
repository. You can enable it using

    $ sudo dnf copr enable @storage/blivet-daily

Daily builds of _blivet_, _libblockdev_ and _libbytesize_ are also in this repo.

#### OBS repository (for Ubuntu and Debian)

Official packages for Debian (testing and unstable) and Ubuntu (19.04 and newer) are available through the Open Build Service.
Instructions for adding the repository are available [here](https://software.opensuse.org/download.html?project=home:vtrefny&package=blivet-gui).

#### Manual

  * Check `blivet-gui.spec` for all dependencies (lines `Requires` and `BuildRequires`).
Main dependencies include [blivet](https://github.com/storaged-project/blivet),
[libblockdev](https://github.com/storaged-project/libblockdev) and
[libbytesize](https://github.com/storaged-project/libbytesize).
  * Clone the repo or download a [release tarball](https://github.com/storaged-project/blivet-gui/releases).
  * Run `sudo make install`
  * Detailed instruction for manual installation for some distributions are available on the [Wiki](https://github.com/storaged-project/blivet-gui/wiki).

### Development

See [CONTRIBUTING.md](CONTRIBUTING.md)

### Localization

blivet-gui localization is done in the Zanata translation platform.
blivet-gui project is located [here](https://fedora.zanata.org/project/view/blivet-gui).

### Bug reporting

Bugs should be reported to [bugzilla.redhat.com](https://bugzilla.redhat.com/enter_bug.cgi?product=Fedora&component=blivet-gui).
If it is possible, report bugs using the [Automatic Bug Reporting Tool (ABRT)](http://abrt.readthedocs.io/en/latest/) --
it automatically uploads logs and some other important information.

You can also report bug using the [GitHub issues](https://github.com/storaged-project/blivet-gui/issues).

If you report a bug manually, attach blivet-gui logs to the report please.
You can find the logs in `/var/log/blivet-gui`.
