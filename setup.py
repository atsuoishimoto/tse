import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="tse",
    version="0.1.0",
    author="Atsuo Ishimoto",
    author_email="atsuoishimoto@gmail.com",
    description="tse is an input stream editor in Python.",
    license="MIT",
    keywords="text filter",
    url="https://github.com/atsuoishimoto/tse",
    long_description=read('README.rst'),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 5 - Production/Stable",
        "Topic :: Text Processing :: Filters",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
    ],
    packages=['tse'],
    entry_points={
        'console_scripts': ['tse = tse.main:main']
    },
    install_requires=["six"],
    test_suite="tests",
    project_urls={
        'Source': 'https://github.com/atsuoishimoto/tse',
    },
    python_requires='>=3.4',
)
