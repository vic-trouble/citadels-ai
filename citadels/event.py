class EventSource:
    def __init__(self):
        self._listeners = []
        self._mute_count = 0

    def add_listener(self, listener):
        self._listeners.append(listener)

    def fire_event(self, event: str, *args, **kwargs):
        if not self.muted:
            for listener in self._listeners:
                getattr(listener, event)(*args, **kwargs)

    def mute(self):
        self._mute_count += 1

    def unmute(self):
        self._mute_count -= 1

    @property
    def muted(self):
        return self._mute_count != 0

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        self._listeners = []
        self._mute_count = 0


class EventTransaction:
    def __init__(self, event_source: EventSource, *args, **kwargs):
        self._event_source = event_source
        self._args = args
        self._kwargs = kwargs

    def __enter__(self):
        self._event_source.mute()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._event_source.unmute()
        self._event_source.fire_event(*self._args, **self._kwargs)
