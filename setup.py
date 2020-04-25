# -*- coding: utf-8 -*-

import setuptools

setuptools.setup(
    name="clipl",
    version="0.1",
    author="Thomas Müller",
    author_email="tho.mueller1@gmail.com",
    description="Command Line Interface Plotting Tool",
    long_description="Command Line Interface Plotting Tool",
    long_description_content_type="text/markdown",
    url="https://github.com/thomas-mueller/clipl/wiki",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='<=2.7.17',
)
