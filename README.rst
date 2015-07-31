django_atomic_dispatch - Atomic transaction aware signals for Django
====================================================================

.. image:: https://travis-ci.org/adamchainz/django_atomic_dispatch.png?branch=master
        :target: https://travis-ci.org/adamchainz/django_atomic_dispatch

Don't Use This Library
----------------------

This library uses `django-atomic-signals`_. Unfortunately that library is deprecated, and is a bit too hacky. There is
plenty of extra description why on `django-atomic-signals' README <django-atomic-signals>`_, and also on the similar
library `django-transaction-signals`_, by Django core developer Aymeric.

.. _django-atomic-signals: https://github.com/adamchainz/django_atomic_signals
.. _django-transaction-signals: https://github.com/aaugustin/django-transaction-signals

If you want a supported method of executing a signal dispatch only when the current transaction commits, then:

- on Django >= 1.9, use the built-in on_commit_ hook
- on Django < 1.9, use `django-transaction-hooks`_ (the original source of 1.9's ``on_commit``)

.. _on_commit: https://docs.djangoproject.com/en/dev/topics/db/transactions/#django.db.transaction.on_commit
.. _django-transaction-hooks: https://django-transaction-hooks.readthedocs.org/

Both give examples so you are in good hands. In most cases you will just need to use a regular signal and make its
``send()`` happen inside a lambda that is passed to ``on_commit``.

If your project is still using this library, please migrate. You will need to remove `django-atomic-signals` as well as
`django-atomic-dispatch`. A new, "don't use me" version that breaks on import will be pushed soon to PyPI to propagate
this warning.

Old Readme Continues
--------------------

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
