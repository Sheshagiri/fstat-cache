from setuptools import setup

setup(
    name='FStatCache',
    version='0.0.1',
    author='Sheshagiri',
    author_email='msheshagirirao@gmail.com',
    url='http://pypi.python.org/pypi/FStatCache/',
    packages=['fstat_cache'],
    license='LICENSE.txt',
    description='an abstraction layer of os.stat implemented using inotify feature from linux kernel',
    long_description=open('README.md').read(),
    install_requires=[
        "inotify-simple==1.2.1",
    ],
)
