from django.db import DEFAULT_DB_ALIAS
from django_atomic_dispatch import (
    _post_enter_atomic_block,
    _post_exit_atomic_block,
)


class DjangoAtomicDispatchTestCaseMixin(object):
    """Django atomic dispatch test case mixin.

    Counters Django's behavior of running all test cases in atomic
    transactions, which makes it impossible to test behavior based on
    Django atomic dispatch in transactions.
    """

    def setUp(self):
        super(DjangoAtomicDispatchTestCaseMixin, self).setUp()
        _post_exit_atomic_block(signal=None,
                                sender=None,
                                using=DEFAULT_DB_ALIAS,
                                outermost=True,
                                savepoint=True,
                                successful=True)

    def tearDown(self):
        _post_enter_atomic_block(signal=None,
                                 sender=None,
                                 using=DEFAULT_DB_ALIAS,
                                 outermost=True,
                                 savepoint=True)
        super(DjangoAtomicDispatchTestCaseMixin, self).tearDown()
