#!/usr/bin/env python3

from setuptools import setup

setup(
    name='yellowball',
    version='3.0',
    description='Mega Millions lottery ticket checker',
    author="Sean O'Connell",
    author_email='sean@sdoconnell.net',
    url='https://github.com/sdoconnell/yellowball',
    license='MIT',
    python_requires='>=3.8',
    packages=['yellowball'],
    install_requires=['requests>=2.25'],
    include_package_data=True,
    entry_points={
        'console_scripts': 'yellowball = yellowball.yellowball:main'
    },
    keywords='cli lottery results',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.8',
        'Topic :: Utilities'
    ]
)
