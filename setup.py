from distutils.core import setup

setup(
	name = "blivet-gui",
	packages = ["blivetgui"],
	version = "0.1.8",
	description = "Tool for data storages configuration",
	author = "Vojtech Trefny",
	author_email = "vtrefny@redhat.com",
	url = "http://github.com/vojtechtrefny/blivet-gui",
	package_dir = {'blivetgui' : 'blivetgui'},
	package_data = {'blivetgui' : ['data/ui/*.ui', 'help/C/*.page',
			'help/C/*.xml', 'help/C/icons/*', 'help/C/images/*',
			'devicevisualization/*.py'], 'dialogs/*.py'},
	classifiers = [
		'Development Status :: 4 - Beta',
		'Environment :: X11 Applications :: GTK',
		'Intended Audience :: End Users/Desktop',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: GNU General Public License (GPL)',
		'Operating System :: POSIX :: Linux',
		'Programming Language :: Python',
		'Topic :: Desktop Environment',
	],
	scripts = ['blivet-gui'],
	long_description = """\
		...
	"""
)
