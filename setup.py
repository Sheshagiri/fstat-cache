from distutils.core import setup

setup(
    name='FStatCache',
    version='0.0.1',
    author='Sheshagiri',
    author_email='msheshagirirao@gmail.com',
    url='http://pypi.python.org/pypi/TowelStuff/',
    packages=['fstat_cache'],
    license='LICENSE.txt',
    description='os.cache implementation using inotify from linux kernel'   ,
    long_description=open('README.md').read(),
    install_requires=[
        "inotify-simple==1.2.1",
    ],
)
