# -*- coding: utf-8 -*-
import site
import os.path
import glob
from setuptools import setup, find_packages
from wxtruss import __version__


MODULE_NAME = "wxtruss"

setup(
    name= MODULE_NAME,
    version = __version__,
    description='A simple Python application for 2D-Truss analysis.',
    author='Pedro Jorge De Los Santos',
    author_email='delossantosmfq@gmail.com',
    license = "MIT",
    keywords=["Truss","FEA"],
    install_requires=["matplotlib","numpy","wxpython","pandas"], # Also required wxPython
    url='https://github.com/JorgeDeLosSantos/wxtruss',
    packages=["wxtruss",],#find_packages(),
    entry_points = {
        'console_scripts': [
            'wxtruss=wxtruss.app:run',
        ]
    },
    classifiers=[
      "Development Status :: 2 - Pre-Alpha",
      "Intended Audience :: Education",
      "Intended Audience :: Science/Research",
      "Intended Audience :: End Users/Desktop",
      "Environment :: Win32 (MS Windows)",
      "License :: OSI Approved :: MIT License",
      "Operating System :: OS Independent",
      "Programming Language :: Python",
      "Programming Language :: Python :: 2.7",
      "Programming Language :: Python :: Implementation :: CPython",
      "Topic :: Desktop Environment",
      "Topic :: Scientific/Engineering :: Visualization",
      "Topic :: Multimedia :: Graphics",
      "Topic :: Utilities",
    ],
    package_data={"wxtruss": ["img/*","data/*"]}
)

