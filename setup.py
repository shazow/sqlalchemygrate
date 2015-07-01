#!/usr/bin/python

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages


long_description = open('README.rst').read()

setup(
    name = "sqlalchemygrate",
    version = "0.3",
    packages = find_packages(exclude=["migrate.tests*"]),
    include_package_data = True,
    description = "Silly (but effective) database schema and data migration framework using SQLAlchemy.",
    long_description = long_description,
    install_requires = ['SQLAlchemy >= 0.5'],
    author = "Andrey Petrov",
    author_email = "andrey.petrov@shazow.net",
    url = "http://github.com/shazow/sqlalchemygrate",
    license = "MIT",
    entry_points="""
    # -*- Entry points: -*-
    """,
    scripts=['bin/grate'],
)
