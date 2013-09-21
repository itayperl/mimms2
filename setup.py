from distutils.core import setup
setup(
  name='mimms2',
  version='1.0',
  description='mimms2 is an mms (e.g. mms://) stream downloader',
  author='Wesley J. Landaker, Itay Perl',
  author_email='wjl@icecavern.net',
  license='GPLv3',
  url='http://savannah.nongnu.org/projects/mimms/',
  packages=['libmimms2'],
  install_requires=['progressbar==2.3'],
  entry_points={
    'console_scripts': 'mimms2 = libmimms2.core:main',
  },
  use_2to3=True,
  data_files=[
    ('share/man/man1', ['mimms2.1'])
    ]
  )
