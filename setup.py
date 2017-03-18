import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="tse",
    version="0.0.14",
    author="Atsuo Ishimoto",
    author_email="ishimoto@gembook.org",
    description="tse is an input stream editor in Python.",
    license="MIT",
    keywords="text filter",
    url="https://github.com/atsuoishimoto/tse",
    long_description=read('README.rst'),
    classifiers=[
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Topic :: Text Processing :: Filters",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
    ],
    packages=['tse'],
    entry_points={
        'console_scripts': ['tse = tse.main:main']
    },
    install_requires=["argparse", "six"],
    test_suite="tests",
)
