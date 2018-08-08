import unittest
import os
from setuptools import setup
from distutils.core import Command

HERE = os.path.abspath(os.path.dirname(__file__))
README = os.path.join(HERE, "README.rst")

classifiers = [
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Natural Language :: English',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'Intended Audience :: Education',
    'Intended Audience :: Information Technology',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
]

with open(README, 'r') as f:
    long_description = f.read()

setup(
    name='poacher',
    version='0.1',
    description=('Watches github.com for new public repositories'),
    long_description=long_description,
    url='http://github.com/eriknyquist/GithubPoacher',
    author='Erik Nyquist',
    author_email='eknyquist@gmail.com',
    license='Apache 2.0',
    packages=['poacher'],
    scripts=['bin/poacher-monitor'],
    classifiers = classifiers,
    include_package_data=True,
    zip_safe=False
)
