#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = ["panflute>=2.1", "numpy>=1.20"]
test_requirements = ["pytest>=6.2"]

setup(
    author="Tingkai Liu",
    author_email="tingkai.liu.21st@gmail.com",
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    description="LaTeX to MyST converter",
    install_requires=requirements,
    license="BSD 3-Clause license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="latex_to_myst",
    name="latex_to_myst",
    packages=find_packages(include=["latex_to_myst", "latex_to_myst"]),
    entry_points={"console_scripts": ["latex2myst = latex_to_myst:main"]},
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/TK-21st/latex-to-myst",
    version="0.0.1",
    zip_safe=False,
)
