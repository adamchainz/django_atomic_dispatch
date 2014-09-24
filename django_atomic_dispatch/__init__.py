import logging
import threading
from django.dispatch import Signal as DjangoSignal, receiver
from django_atomic_signals import signals


logger = logging.getLogger(__name__)
_thread_data = threading.local()


class ConditionalSignal(object):
    """Conditional signal.
    """

    def __init__(self, signal, sender, named, robust):
        self.signal = signal
        self.sender = sender
        self.named = named
        self.robust = robust

    def apply(self):
        """Apply the conditional signal.
        """

        if self.robust:
            self.signal.send_robust_apply(self.sender, **self.named)
        else:
            self.signal.send_apply(self.sender, **self.named)

    def replaces(self, other):
        """Test if the conditional signal replaces another signal.
        """

        if self.signal != other.signal or \
           self.sender != other.sender or \
           not self.signal.replaces:
            return

        return self.signal.replaces(self.named, other.named)

    @property
    def description(self):
        """Description.
        """

        return '%s(%r%s%s)' % (
            self.signal,
            self.sender,
            ', ' if self.named else '',
            ', '.join('%s=%r' % (k, v) for k, v in self.named.items())
        )


class SignalQueueStack(object):
    def __init__(self):
        self.stack = []

    def reset(self):
        self.stack = []

    def __len__(self):
        return len(self.stack)

    def pop(self):
        return self.stack.pop()

    def append(self, level):
        self.stack.append(level)

    def __getitem__(self, key):
        return self.stack[key]

    def __setitem__(self, key, value):
        self.stack[key] = value


class SignalQueue(object):
    """Signal queue.
    """

    def __init__(self):
        self.queue = []

    def add(self, signal):
        for i, s in enumerate(self.queue):
            if signal.replaces(s):
                self.queue[i] = signal
                logger.debug('Replaced %s with %s in signal queue' %
                             (s.description, signal.description))
                return

        self.queue.append(signal)
        logger.debug('Appended %s to signal queue' % (signal.description))

    def __iter__(self):
        return iter(self.queue)


def _get_signal_queue():
    """Get the local signal queues.
    """

    return _thread_data.__dict__.setdefault('signal_queue', SignalQueueStack())


class PostTransactionSignal(DjangoSignal):
    """Signal delayed until after the outermost atomic block is exited.

    If the atomic transaction block within which the signal is dispatched is
    successful, ie. no exception is raised and the transaction is not rolled
    back, the signal is promoted to the outside block. Otherwise, the signal is
    discarded.

    When exiting the outside block, all surviving signals are dispatched.
    """

    def __init__(self,
                 providing_args=None,
                 use_caching=False,
                 description=None,
                 replaces=None):
        super(PostTransactionSignal, self).__init__(
            providing_args=providing_args,
            use_caching=use_caching
        )
        self.replaces = replaces
        self.description = description

    def _send(self, sender, named, robust):
        signal_queue_stack = _get_signal_queue()

        s = ConditionalSignal(self, sender, named, robust=False)

        if signal_queue_stack:
            logger.debug('Dispatching signal %s if transaction block is '
                         'successful' % (s.description))
            signal_queue_stack[-1].add(s)
        else:
            logger.debug('Dispatching signal %s immediately' %
                         (s.description))
            return s.apply()

    def send(self, sender, **named):
        self._send(sender, named, False)

    def send_robust(self, sender, **named):
        self._send(sender, named, True)

    def send_apply(self, sender, **named):
        super(PostTransactionSignal, self).send(sender, **named)

    def send_robust_apply(self, sender, **named):
        super(PostTransactionSignal, self).send_robust(sender, **named)

    def __repr__(self):
        if self.description:
            return '<%s.%s: %s>' % (self.__class__.__module__,
                                    self.__class__.__name__,
                                    self.description)
        return super(PostTransactionSignal, self).__repr__()


@receiver(signals.post_enter_atomic_block)
def _post_enter_atomic_block(signal,
                             sender,
                             using,
                             outermost,
                             savepoint,
                             **kwargs):
    if not savepoint:
        return

    signal_queue_stack = _get_signal_queue()

    if outermost:
        signal_queue_stack.reset()

    signal_queue_stack.append(SignalQueue())


@receiver(signals.post_exit_atomic_block)
def _post_exit_atomic_block(signal,
                            sender,
                            using,
                            outermost,
                            savepoint,
                            successful,
                            **kwargs):
    if not savepoint:
        return

    signal_queue_stack = _get_signal_queue()

    if successful:
        signal_queue = signal_queue_stack.pop()

        if len(signal_queue_stack) == 1:
            for s in signal_queue:
                logger.debug('Dispatching %s as outer transaction block is '
                             'successful' % (s.description))
                s.apply()
        else:
            parent_signal_queue = signal_queue_stack[-1]

            for s in signal_queue:
                logger.debug('Promoting %s to outer transaction block' %
                             (s.description))
                parent_signal_queue.add(s)
    else:
        signal_queue_stack.pop()
