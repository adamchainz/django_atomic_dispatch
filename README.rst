django_atomic_dispatch - Atomic transaction aware signals for Django
====================================================================

.. image:: https://travis-ci.org/adamchainz/django_atomic_dispatch.png?branch=master
        :target: https://travis-ci.org/adamchainz/django_atomic_dispatch

``django_atomic_dispatch`` provides a Django 1.6-1.7 compatible approach to transactionally aware signal dispatch.


Installation
------------

To install ``django_atomic_dispatch``, do yourself a favor and don't use anything other than `pip <http://www.pip-installer.org/>`_:

.. code-block:: bash

   $ pip install django-atomic-dispatch

Add ``django_atomic_dispatch`` along with its dependency, ``django_atomic_signals``, to the list of installed apps in your settings file:

.. code-block:: python

   INSTALLED_APPS = (
       'django_atomic_signals',
       'django_atomic_dispatch',
       ..
   )
