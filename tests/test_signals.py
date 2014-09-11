from django.db import transaction
from django.test import TestCase
from django_atomic_dispatch.testing import DjangoAtomicDispatchTestCaseMixin
from django_atomic_dispatch import Signal


class DummySender(object):
    """Dummy sender.
    """


sender_a = DummySender()

signal_a = Signal()
signal_b = Signal(providing_args=['a', 'b'])


class SignalTestCase(DjangoAtomicDispatchTestCaseMixin, TestCase):
    """Test case for signals.
    """

    def assertNoDispatched(self):
        """Assert that no signals are dispatched.
        """

        self.assertEqual(len(self.dispatches), 0)

    def assertDispatched(self, dispatches):
        """Assert a set of specific dispatches were made.

        :param dispatches:
            iterable of :class:`tuple` instances of
            ``(<signal>, <sender>, <named>)``.
        """

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

    def tearDown(self):
        signal_a.disconnect(dispatch_uid='receive_a')
        signal_b.disconnect(dispatch_uid='receive_b')

        super(SignalTestCase, self).tearDown()

    def _test_behavior(self, signal, sender, named, call):
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

    def test_send(self):
        """Signal(..).send(..)
        """

        self._test_behavior(signal_a, sender_a, {}, signal_a.send)
        self._test_behavior(signal_b,
                            sender_a,
                            {'a': 1, 'b': 2},
                            signal_b.send)

    def test_send_robust(self):
        """Signal(..).send_robust(..)
        """

        self._test_behavior(signal_a, sender_a, {}, signal_a.send_robust)
        self._test_behavior(signal_b,
                            sender_a,
                            {'a': 1, 'b': 2},
                            signal_b.send_robust)
