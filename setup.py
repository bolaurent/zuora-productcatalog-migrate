# -*- coding: utf-8 -*-


"""setup.py: setuptools control."""


import re
from setuptools import setup


version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('zmigrate/zmigrate.py').read(),
    re.M
    ).group(1)


with open("README.rst", "rb") as f:
    long_descr = f.read().decode("utf-8")


setup(
    name = "zuora-productcatalog-migrate",
    packages = ["zmigrate"],
    entry_points = {
        "console_scripts": ['zmigrate = zmigrate.zmigrate:main']
        },
    version = version,
    description = "Python command line for migrating zuora product catalog between instances.",
    long_description = long_descr,
    author = "Bo Laurent",
    author_email = "bo@bolaurent.com",
    url = "http://gehrcke.de/2014/02/distributing-a-python-command-line-application",
    install_requires=[
        "zuora_restful_python==0.15"
    ],
    dependency_links=['https://github.com/bolaurent/zuora_restful_python/tarball/master#egg=zuora_restful_python-0.15']
    )
