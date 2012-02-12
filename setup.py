import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "tse",
    version = "0.0.3",
    author = "Atsuo Ishimoto",
    author_email = "ishimoto@gembook.org",
    description = "tse is an input stream editor in Python.",
    license = "MIT",
    keywords = "text filter",
    url = "https://github.com/atsuoishimoto/tse",
    long_description=read('README.rst'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Text Processing :: Filters",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
    ],
    packages = find_packages("src"),
    package_dir = {'':'src'},
    entry_points = {
        'console_scripts': ['tse = tse.main:main']
    },
    install_requires=["argparse"],
    test_suite="tests",
)
