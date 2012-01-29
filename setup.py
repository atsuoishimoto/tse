import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "pss",
    version = "0.0.1",
    author = "Atsuo Ishimoto",
    author_email = "ishimoto@gembook.org",
    description = "pss is an input stream editor in Python.",
    license = "BSD",
    keywords = "text filter",
    url = "http://packages.python.org/an_example_pypi_project",
    long_description=read('README'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Text Processing :: Filters",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
    packages = find_packages("src"),
    package_dir = {'':'src'},
    entry_points = {
        'console_scripts': ['pss = pss.main:main']
    },
    install_requires=["argparse"],
)
