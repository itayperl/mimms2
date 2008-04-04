from distutils.core import setup
setup(
  name='mimms',
  version='3.0',
  description='mimms is an mms (e.g. mms://) stream downloader',
  author='Wesley J. Landaker',
  author_email='wjl@icecavern.net.',
  py_modules=['libmimms'],
  scripts=['mimms'],
  data_files=[('usr/share/man/man1','mimms.1')]
  )
