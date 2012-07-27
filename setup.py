# -*- coding: utf-8 -*-
from distutils.core import setup

setup(
    name='django-hiver',
    version='0.1.0',
    author=u'Twined',
    author_email='www.twined.net',
    packages=['hiver'],
    url='http://github.com/twined/hiver',
    license='BSD licence, see LICENCE.txt',
    description='A simple redis view cacher ' + \
                'for Django.',
    long_description=open('README.txt').read(),
    install_requires=[
        "Django >= 1.3.0",
    ],
    zip_safe=False,
)
