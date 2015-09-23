from __future__ import print_function

from distutils.core import setup
import glob

data_files = []
ui_files = glob.glob('data/ui/*.ui')
css_files = glob.glob('data/css/*.css')
img_files = glob.glob('data/img/*.png')
# help_files = glob.glob('help/C/*.page')
# help_files += glob.glob('help/C/*.xml')
# image_files = glob.glob('help/C/images/*.png')
# icon_files = glob.glob('help/C/icons/*.png')
polkit_files = glob.glob('org.fedoraproject.pkexec.blivet-gui.policy')
desktop_files = glob.glob('blivet-gui.desktop')
man_files = glob.glob('man/blivet-gui.1')
appdata_files = glob.glob('appdata/*.xml')

data_files.append(('/usr/share/blivet-gui/ui', ui_files))
data_files.append(('/usr/share/blivet-gui/css', css_files))
data_files.append(('/usr/share/blivet-gui/img', img_files))
# data_files.append(('/usr/share/help/C/blivet-gui', help_files))
# data_files.append(('/usr/share/help/C/blivet-gui/images', image_files))
# data_files.append(('/usr/share/help/C/blivet-gui/icons', icon_files))
data_files.append(('/usr/share/polkit-1/actions', polkit_files))
data_files.append(('/usr/share/applications', desktop_files))
data_files.append(('/usr/share/man/man1', man_files))
data_files.append(('/usr/share/appdata', appdata_files))

for size in ("16x16", "22x22", "24x24", "32x32", "48x48", "64x64", "256x256"):
    icons = glob.glob('data/icons/hicolor/' + size + '/blivet-gui.png')
    data_files.append(('/usr/share/icons/hicolor/' + size + '/apps', icons))

print(data_files)

setup(
    name='blivet-gui',
    packages=['blivetgui'],
    version='1.1',
    description = 'Tool for data storages configuration',
    author='Vojtech Trefny',
    author_email='vtrefny@redhat.com',
    url='http://github.com/rhinstaller/blivet-gui',
    package_dir={'blivetgui' : 'blivetgui'},
    # package_data={'blivetgui' : ['help/C/*.page', 'help/C/*.xml', 'help/C/icons/*',
    #                              'help/C/images/*', 'visualization/*.py',
    #                              'communication/*.py', 'dialogs/*.py',
    #                              'data/icons/hicolor/*/apps/blivet-gui.png']},
    package_data={'blivetgui' : ['visualization/*.py', 'communication/*.py',
                                 'dialogs/*.py', 'data/icons/hicolor/*/apps/blivet-gui.png']},
    data_files=data_files,
    scripts = ['blivet-gui', 'blivet-gui-daemon']
)
