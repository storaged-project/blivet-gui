#----------------------#
#----Python package----#
#----------------------#
# Create python package

$ python2 setup.py sdist

# Install python package

$ cd dist
$ tar zxf blivetgui-<version>.tar.gz
$ cd blivetgui-<version>
$ sudo python2 setup.py install

# Run blivet-gui

$ sudo blivet-gui

#----------------------#
#------RPM package-----#
#----------------------#
# Create RPM package

$ python2 setup.py sdist
$ python setup.py bdist_rpm --requires="python, pygobject3, gettext, yelp, python-blivet, gtk3, gnome-icon-theme"

# Install RPM package

$ cd dist
$ sudo yum localinstall blivetgui-<version>.noarch.rpm

# Run blivet-gui

$ sudo blivet-gui