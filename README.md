 blivet-gui is a graphical tool for storage configuration using blivet library

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

#### Manual

  * Check `blivet-gui.spec` for all dependencies (lines `Requires` and `BuildRequires`).
Main dependencies include [blivet](https://github.com/storaged-project/blivet),
[libblockdev](https://github.com/storaged-project/libblockdev) and
[libbytesize](https://github.com/storaged-project/libbytesize). Note that these
are probably not packaged for other distributions than Fedora.
  * Clone the repo or download a [release tarball](https://github.com/storaged-project/blivet-gui/releases).
  * Run `sudo make install`

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
