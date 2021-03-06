#!/usr/bin/env python
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


packages = [
    'django_atomic_dispatch',
]

requires = [
]

tests_require = [
    'flake8',
    'django-nose',
    'rednose',
]

with open('README.rst') as readme_file:
    readme = readme_file.read()

setup(
    name='django-atomic-dispatch',
    version='2.0.0',
    description='Atomic transaction aware signals for Django 1.6+',
    long_description=readme,
    author='Nick Bruun',
    author_email='nick@bruun.co',
    maintainer='Adam Johnson',
    maintainer_email='me@adamj.eu',
    url='https://github.com/adamchainz/django_atomic_dispatch',
    packages=packages,
    package_data={'': ['LICENSE']},
    package_dir={'django_atomic_dispatch': 'django_atomic_dispatch'},
    include_package_data=True,
    tests_require=tests_require,
    install_requires=requires,
    license=open('LICENSE').read(),
    zip_safe=True,
    classifiers=(
        'Development Status :: 7 - Inactive',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ),
)
