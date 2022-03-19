[![Copr build status](https://copr.fedorainfracloud.org/coprs/g/storage/blivet-daily/package/blivet-gui/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/g/storage/blivet-daily/package/blivet-gui/)

blivet-gui is a graphical tool for storage configuration using the [blivet](https://github.com/storaged-project/blivet) library

### CI status

<img alt="CI status" src="https://fedorapeople.org/groups/storage_apis/statuses/blivet-gui-master.svg" width="100%" height="225ex" />

### Licence

See [COPYING](COPYING)

### Installation

#### From Fedora repositories

blivet-gui is available in Fedora repositories. You can install it using

    $ sudo dnf install blivet-gui

#### Daily builds for Fedora

Daily builds of blivet-gui are available in `@storage/blivet-daily` Copr
repository. You can enable it using

    $ sudo dnf copr enable @storage/blivet-daily

Daily builds of _blivet_, _libblockdev_ and _libbytesize_ are also in this repo.

#### OBS repository for Ubuntu and Debian

Official packages for Debian and Ubuntu (19.04 and newer) are available in our [Open Build Service repository](https://software.opensuse.org/download.html?project=home:vtrefny&package=blivet-gui).

This repository contains blivet-gui and its dependencies that are not available in the official Ubuntu/Debian repositories. We recommend adding the repository to your system, if you want to install the packages manually, you'll also need to install [blivet](https://software.opensuse.org/download.html?project=home:vtrefny&package=python3-blivet) and [pid](https://software.opensuse.org/download.html?project=home:vtrefny&package=python3-pid) from the same source.

#### Copr repository for openSUSE, Mageia and OpenMandriva

Packages for openSUSE Tumbleweed, Mageia (8 and newer) and OpenMandriva (Cooker and Rolling) are available in our [blivet-stable Copr repository](https://copr.fedorainfracloud.org/coprs/g/storage/blivet-stable/). This repository contains the latest stable versions of both blivet-gui and blivet.

#### Manual

  * Check `blivet-gui.spec` for all dependencies (lines `Requires` and `BuildRequires`).
Main dependencies include [blivet](https://github.com/storaged-project/blivet),
[libblockdev](https://github.com/storaged-project/libblockdev) and
[libbytesize](https://github.com/storaged-project/libbytesize).
  * Clone the repo or download a [release tarball](https://github.com/storaged-project/blivet-gui/releases).
  * Run `sudo make install`
  * Detailed instructions for manual installation for some distributions are available on the [Wiki](https://github.com/storaged-project/blivet-gui/wiki).

### Development

See [CONTRIBUTING.md](CONTRIBUTING.md)

### Localization

[![Translation](https://translate.fedoraproject.org/widgets/blivet/-/blivet-gui/287x66-grey.png)](https://translate.fedoraproject.org/engage/blivet/?utm_source=widget)

### Bug reporting

Bugs should be reported to [bugzilla.redhat.com](https://bugzilla.redhat.com/enter_bug.cgi?product=Fedora&component=blivet-gui).
If it is possible, report bugs using the [Automatic Bug Reporting Tool (ABRT)](http://abrt.readthedocs.io/en/latest/) --
it automatically uploads logs and some other important information.

You can also report a bug using the [GitHub issues](https://github.com/storaged-project/blivet-gui/issues).

If you report a bug manually, attach blivet-gui logs to the report, please.
You can find the logs in `/var/log/blivet-gui`.
