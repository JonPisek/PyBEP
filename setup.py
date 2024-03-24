#!/usr/bin/env python

from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='battery_OCV_decomposition',
    version='1.0.0',
    author='Jon Pišek',
    author_email='jon.pisek@gmail.com',
    description='Simple Python package with a built-in GUI that makes battery OCV decomposition a piece of cake.',  # noqa: E501
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/JonPisek/package_directory',
    packages=find_packages(),
    package_data={'': ['data/*.txt', 'LICEM/*.jpg', 'results/*.json']},
    include_package_data=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.8',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
    install_requires=[
                      'numpy',
                      'scipy',
                      'matplotlib',
                      'joblib',
                     ],
    entry_points={
        'console_scripts': [
            'run_battery_OCV_decomposition = battery_OCV_decomposition.GUI:main',  # noqa: E501
        ],
    },
)

if __name__ == "__main__":
    setup()
