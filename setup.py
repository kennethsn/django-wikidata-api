import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()

setup(
    name='django-wikidata-api',
    version='0.0.0',
    packages=['django_wikidata_api'],
    description='ORM for interfacing with Wikidata within a Django Project',
    long_description=README,
    author='Kenneth Seals-Nutt',
    author_email='kenneth@seals-nutt.com',
    url='https://github.com/kennethsn/django-wikidata-api',
    license='AGPL-3.0',
    install_requires=[
        'Django>=2.2,<2.3',
    ]
)
