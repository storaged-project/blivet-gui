from setuptools import setup
import glob

data_files = []
ui_files = glob.glob('data/ui/*.ui')
css_files = glob.glob('data/css/*.css')
img_files = glob.glob('data/img/*.png')
polkit_files = glob.glob('org.fedoraproject.pkexec.blivet-gui.policy')
desktop_files = glob.glob('blivet-gui.desktop')
man_files = glob.glob('man/blivet-gui.1')
appdata_files = glob.glob('appdata/*.xml')

data_files.append(('share/blivet-gui/ui', ui_files))
data_files.append(('share/blivet-gui/css', css_files))
data_files.append(('share/blivet-gui/img', img_files))
data_files.append(('share/polkit-1/actions', polkit_files))
data_files.append(('share/applications', desktop_files))
data_files.append(('share/man/man1', man_files))
data_files.append(('share/appdata', appdata_files))

for size in ("16x16", "22x22", "24x24", "32x32", "48x48", "64x64", "256x256"):
    icons = glob.glob('data/icons/hicolor/' + size + '/blivet-gui.png')
    data_files.append(('share/icons/hicolor/' + size + '/apps', icons))


setup(
    name='blivet-gui',
    packages=['blivetgui'],
    version='2.6.0',
    description = 'Tool for data storages configuration',
    author='Vojtech Trefny',
    author_email='vtrefny@redhat.com',
    url='http://github.com/storaged-project/blivet-gui',
    package_dir={'blivetgui' : 'blivetgui'},
    package_data={'blivetgui' : ['visualization/*.py', 'communication/*.py',
                                 'dialogs/*.py', 'data/icons/hicolor/*/apps/blivet-gui.png']},
    data_files=data_files,
    scripts = ['blivet-gui', 'blivet-gui-daemon']
)
