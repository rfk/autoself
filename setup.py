#
#  This is the autoself setuptools script.
#  Originally written by Ryan Kelly, 2007.
#
#  This script is placed in the public domain.
#

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages

import autoself

NAME = "autoself"
DESCRIPTION = "Automagically add method definition boilerplate"
AUTHOR = "Ryan Kelly"
AUTHOR_EMAIL = "ryan@rfk.id.au"
URL = "http://www.rfk.id.au/software/autoself/"
LICENSE = "Public Domain"
KEYWORDS = "self cls method"

PACKAGES = find_packages()

setup(name=NAME,
      version=autoself.__version__,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      url=URL,
      description=DESCRIPTION,
      long_description=autoself.__doc__,
      license=LICENSE,
      keywords=KEYWORDS,
      packages=PACKAGES,
      test_suite="autoself.testsuite",
     )

