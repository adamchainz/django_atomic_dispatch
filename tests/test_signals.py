import logging
from django.db import transaction
from django.test import TestCase
from django_atomic_dispatch.testing import DjangoAtomicDispatchTestCaseMixin
from django_atomic_dispatch import PostTransactionSignal


logger = logging.getLogger(__name__)


class DummySender(object):
    """Dummy sender.
    """

    def __init__(self, ref):
        self.ref = ref

    def __repr__(self):
        return '<DummySender: %s>' % (self.ref)


sender_a = DummySender('a')
sender_b = DummySender('b')

signal_a = PostTransactionSignal(description='a')
signal_b = PostTransactionSignal(providing_args=['a', 'b'],
                                 description='b')
signal_c = PostTransactionSignal(providing_args=['a', 'b'],
                                 description='c',
                                 replaces=lambda sn, on: sn['a'] == on['a'])


class SignalTestCase(DjangoAtomicDispatchTestCaseMixin, TestCase):
    """Test case for signals.
    """

    def log_dispatches(self, dispatches, description):
        logger.debug('%s = [%s%s%s]' %
                     (description,
                      '\n    ' if dispatches else '',
                      ',\n    '.join('(%r, %r, %r)' % d for d in dispatches),
                      '\n' if dispatches else ''))

    def assertNoDispatched(self):
        """Assert that no signals are dispatched.
        """

        self.log_dispatches([], 'assertNoDispatched: expected dispatches')
        self.log_dispatches(self.dispatches,
                            'assertNoDispatched: actual dispatches')

        self.assertEqual(len(self.dispatches), 0)

    def assertDispatched(self, dispatches):
        """Assert a set of specific dispatches were made.

        :param dispatches:
            iterable of :class:`tuple` instances of
            ``(<signal>, <sender>, <named>)``.
        """

        self.log_dispatches(dispatches,
                            'assertDispatched: expected dispatches')
        self.log_dispatches(self.dispatches,
                            'assertDispatched: actual dispatches')

        self.assertEqual(len(self.dispatches), len(dispatches))

        for i, (a_signal, a_sender, a_named) in enumerate(self.dispatches):
            e_signal, e_sender, e_named = dispatches[i]

            self.assertEqual(e_signal, a_signal)
            self.assertEqual(e_sender, a_sender)
            self.assertEqual(e_named, a_named)

        self.dispatches = []

    def receiver(self, signal, sender, **kwargs):
        self.dispatches.append((signal, sender, kwargs))

    def setUp(self):
        super(SignalTestCase, self).setUp()

        self.dispatches = []
        signal_a.connect(self.receiver, dispatch_uid='receive_a')
        signal_b.connect(self.receiver, dispatch_uid='receive_b')
        signal_c.connect(self.receiver, dispatch_uid='receive_c')

    def tearDown(self):
        signal_a.disconnect(dispatch_uid='receive_a')
        signal_b.disconnect(dispatch_uid='receive_b')
        signal_c.disconnect(dispatch_uid='receive_c')

        super(SignalTestCase, self).tearDown()

    def _test_simple(self, signal, sender, named, call):
        # Signal dispatched outside transaction block is dispatched
        # immediately.
        self.assertNoDispatched()
        call(sender, **named)
        self.assertDispatched([(signal, sender, named)])

        # Signal dispatched inside successful atomic transaction block is
        # dispatched after outermost transaction block is left.
        self.assertNoDispatched()
        with transaction.atomic():
            call(sender, **named)
            self.assertNoDispatched()
        self.assertDispatched([(signal, sender, named)])

        self.assertNoDispatched()
        with transaction.atomic():
            call(sender, **named)
            self.assertNoDispatched()
            with transaction.atomic():
                call(sender, **named)
                self.assertNoDispatched()
            self.assertNoDispatched()
        self.assertDispatched([(signal, sender, named),
                               (signal, sender, named)])

        # Signal dispatches inside failed atomic transaction block is not
        # dispatched.
        self.assertNoDispatched()
        with self.assertRaises(ValueError):
            with transaction.atomic():
                call(sender, **named)
                raise ValueError('Testing')
        self.assertNoDispatched()

        self.assertNoDispatched()
        with transaction.atomic():
            call(sender, **named)
            with self.assertRaises(ValueError):
                with transaction.atomic():
                    call(sender, **named)
                    raise ValueError('Testing')
            self.assertNoDispatched()
        self.assertDispatched([(signal, sender, named)])

    def _test_replacement(self, send_from):
        # Most recent signal dispatched inside successful atomic transaction
        # block is dispatched after outermost transaction block is left.
        self.assertNoDispatched()
        with transaction.atomic():
            send_from(signal_a, sender_a)
            send_from(signal_c, sender_a, a=1, b=1)
            send_from(signal_c, sender_a, a=2, b=1)
            send_from(signal_c, sender_a, a=1, b=2)
            send_from(signal_a, sender_a)
            send_from(signal_c, sender_b, a=1, b=1)
            self.assertNoDispatched()
        self.assertDispatched([
            (signal_a, sender_a, {}),
            (signal_c, sender_a, {'a': 1, 'b': 2}),
            (signal_c, sender_a, {'a': 2, 'b': 1}),
            (signal_a, sender_a, {}),
            (signal_c, sender_b, {'a': 1, 'b': 1}),
        ])

        # Signal dispatched inside successful atomic transaction block is
        # dispatched after outermost transaction block is left.
        self.assertNoDispatched()
        with transaction.atomic():
            send_from(signal_a, sender_a)
            send_from(signal_c, sender_a, a=1, b=1)
            send_from(signal_c, sender_a, a=2, b=1)
            self.assertNoDispatched()
            with transaction.atomic():
                send_from(signal_c, sender_a, a=1, b=2)
                send_from(signal_a, sender_a)
                send_from(signal_c, sender_b, a=1, b=1)
                self.assertNoDispatched()
            self.assertNoDispatched()
        self.assertDispatched([
            (signal_a, sender_a, {}),
            (signal_c, sender_a, {'a': 1, 'b': 2}),
            (signal_c, sender_a, {'a': 2, 'b': 1}),
            (signal_a, sender_a, {}),
            (signal_c, sender_b, {'a': 1, 'b': 1}),
        ])

        # Signal dispatches inside failed atomic transaction block is not
        # dispatched.
        self.assertNoDispatched()
        with self.assertRaises(ValueError):
            with transaction.atomic():
                send_from(signal_a, sender_a)
                send_from(signal_c, sender_a, a=1, b=1)
                send_from(signal_c, sender_a, a=2, b=1)
                raise ValueError('Testing')
        self.assertNoDispatched()

        self.assertNoDispatched()
        with transaction.atomic():
            send_from(signal_a, sender_a)
            send_from(signal_c, sender_a, a=1, b=1)
            send_from(signal_c, sender_a, a=2, b=1)
            with self.assertRaises(ValueError):
                with transaction.atomic():
                    send_from(signal_c, sender_a, a=1, b=2)
                    send_from(signal_a, sender_a)
                    send_from(signal_c, sender_b, a=1, b=1)
                    raise ValueError('Testing')
            self.assertNoDispatched()
        self.assertDispatched([
            (signal_a, sender_a, {}),
            (signal_c, sender_a, {'a': 1, 'b': 1}),
            (signal_c, sender_a, {'a': 2, 'b': 1}),
        ])

    def test_send(self):
        """Signal(..).send(..)
        """

        self._test_simple(signal_a, sender_a, {}, signal_a.send)
        self._test_simple(signal_b,
                          sender_a,
                          {'a': 1, 'b': 2},
                          signal_b.send)

        def send_from(signal, sender, **named):
            signal.send(sender, **named)

        self._test_replacement(send_from)

    def test_send_robust(self):
        """Signal(..).send_robust(..)
        """

        self._test_simple(signal_a, sender_a, {}, signal_a.send_robust)
        self._test_simple(signal_b,
                          sender_a,
                          {'a': 1, 'b': 2},
                          signal_b.send_robust)

        def send_from(signal, sender, **named):
            signal.send_robust(sender, **named)

        self._test_replacement(send_from)
