# setup.py
import sys
import os.path

if sys.version_info[0:2] < (3, 3):
    raise ImportError('pydigree requires python >3.2')

from setuptools import setup

from distutils.extension import Extension
from distutils.log import warn, error

from Cython.Build import cythonize
from Cython.Distutils import build_ext
import numpy

cyprofile = False

if cyprofile:
    from Cython.Compiler.Options import directive_defaults
    directive_defaults['linetrace'] = True
    directive_defaults['binding'] = True


cysources = ['pydigree/cydigree/cyfuncs.pyx',
             'pydigree/cydigree/datastructures.pyx']
if not all(os.path.exists(x) for x in cysources):
    error('ERROR: Cython sources not found! Giving up.')
    exit(1)

if cyprofile:
    macros = [('CYTHON_TRACE', '1')]
else:
    macros = None

cyext = Extension('pydigree.cydigree.cyfuncs',
                  sources=['pydigree/cydigree/cyfuncs.pyx'],
                  include_dirs=[numpy.get_include()],
                  extra_compile_args=['-Wno-unused-function'],
                  define_macros=macros)

dsext = Extension('pydigree.cydigree.datastructures',
                  sources=['pydigree/cydigree/datastructures.pyx'],
                  extra_compile_args=['-Wno-unused-function'],
                  define_macros=macros)

vtext = Extension('pydigree.cydigree.varianttree',
                  sources=['pydigree/cydigree/varianttree.pyx'],
                  extra_compile_args=['-Wno-unused-function'],
                  define_macros=macros)

vcfext = Extension('pydigree.cydigree.vcfparse',
                   sources=['pydigree/cydigree/vcfparse.pyx'],
                   extra_compile_args=['-Wno-unused-function'],
                   define_macros=macros)

with open('LICENSE.txt') as f:
    license = f.read()

setup(
    name='pydigree',
    version='0.6',
    description='A package for operations on pedigree and genotype data',
    author='James Hicks',
    url='https://github.com/jameshicks/pydigree',
    license=license,
    packages=['pydigree'],
    ext_modules=cythonize([cyext, dsext, vtext, vcfext]),
    requires=['numpy', 'scipy', 'pandas', 'cython'],
    classifiers=['Programming Language :: Python :: 3 :: Only',
                 'Programming Language :: Cython',
                 'Intended Audience :: Science/Research',
                 'Topic :: Scientific/Engineering :: Bio-Informatics',
                 'Topic :: Scientific/Engineering :: Mathematics',
                 'Topic :: Sociology :: Genealogy',
                 'Topic :: Software Development :: Libraries :: Python Modules',
                 'Development Status :: 4 - Beta',
                 'License :: OSI Approved :: Apache Software License']
)
