from __future__ import print_function
from setuptools import setup
from setuptools.command.test import test as TestCommand
import io
import sys

import ptpip


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = read('README.md')


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

setup(
    name='ptpip',
    version=ptpip.__version__,
    url='http://github.com/mmattes/ptpip/',
    license='Apache Software License',
    author='Markus Mattes',
    tests_require=['pytest'],
    install_requires=[],
    cmdclass={'test': PyTest},
    author_email='markus@mmattes.de',
    description='Communication API to PTP/IP Devices',
    long_description=long_description,
    packages=['ptpip'],
    include_package_data=True,
    platforms='any',
    extras_require={
        'testing': ['pytest'],
    }
)
