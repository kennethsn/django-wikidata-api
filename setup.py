# coding=utf-8
""" Setup script to build django-wikidata-api """
import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()

setup(
    name='django-wikidata-api',
    version='0.0.2',
    packages=['django_wikidata_api'],
    description='Python Package for interfacing with Wikidata within a Django App',
    long_description=README,
    long_description_content_type="text/markdown",
    author='Kenneth Seals-Nutt',
    author_email='kenneth@seals-nutt.com',
    url='https://github.com/kennethsn/django-wikidata-api',
    license='AGPL-3.0',
    install_requires=[
        'Django>=2.2,<2.3',
        'djangorestframework>=3.10.3',
        'drf-yasg>=1.17',
        'mock',
        'wikidataintegrator>=0.4.2, <0.4.3',
        # Wikidataintegrator packages that aren't tied down
        'pandas>=0.25.2',
        'tqdm>=4.36.1',
    ],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Natural Language :: English",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Framework :: Django",
        "Framework :: Django :: 2.2",
        "License :: OSI Approved :: GNU Affero General Public License v3"
    ],
    python_requires='>=3.6',
)
