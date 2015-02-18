from distutils.core import setup
import glob

data_files = []
ui_files = glob.glob('data/ui/*.ui')
help_files = glob.glob('help/C/*.page')
help_files += glob.glob('help/C/*.xml')
image_files = glob.glob('help/C/images/*.png')
icon_files = glob.glob('help/C/icons/*.png')
polkit_files = glob.glob('org.fedoraproject.pkexec.blivet-gui.policy')
desktop_files = glob.glob('blivet-gui.desktop')
man_files = glob.glob('man/blivet-gui.1')
data_files.append(('/usr/share/blivet-gui/ui', ui_files))
data_files.append(('/usr/share/help/C/blivet-gui', help_files))
data_files.append(('/usr/share/help/C/blivet-gui/images', image_files))
data_files.append(('/usr/share/help/C/blivet-gui/icons', icon_files))
data_files.append(('/usr/share/polkit-1/actions', polkit_files))
data_files.append(('/usr/share/applications', desktop_files))
data_files.append(('/usr/share/man/man1', man_files))

print data_files

setup(
	name='blivet-gui',
	packages=['blivetgui'],
	version='0.2.1',
	description = 'Tool for data storages configuration',
	author='Vojtech Trefny',
	author_email='vtrefny@redhat.com',
	url='http://github.com/vojtechtrefny/blivet-gui',
	package_dir={'blivetgui' : 'blivetgui'},
	package_data={'blivetgui' : ['help/C/*.page',
			'help/C/*.xml', 'help/C/icons/*', 'help/C/images/*',
			'devicevisualization/*.py', 'dialogs/*.py']},
	data_files=data_files,
	scripts = ['blivet-gui', 'blivet-gui_pkexec']
)
