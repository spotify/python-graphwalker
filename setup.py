# -*- coding: utf-8 -*-
# Copyright (c) 2013 Spotify AB
from distutils.core import setup


setup(
    name='graphwalker',
    version='1.0.3',
    maintainer='Anders Eurenius',
    maintainer_email='aes@spotify.com',
    packages=['graphwalker', 'graphwalker.test'],
    package_data={'graphwalker.test': ['examples/*.*']},
    scripts=['bin/graphwalker'],
    url='http://pypi.python.org/pypi/graphwalker/',
    license='LICENSE.txt',
    description='Finite state machine based testing tool.',
    long_description=open('README.txt').read(),
    requires=["pydot(>=1.0.2)", "docopt"],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Testing',
    ],
)
