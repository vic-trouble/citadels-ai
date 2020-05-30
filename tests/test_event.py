from unittest.mock import Mock

from citadels.event import EventSource, EventTransaction


def test_fire_event():
    # arrange
    source = EventSource()

    passed_required = None
    passed_optional = None

    def on_test_event(required, optional=None):
        nonlocal passed_required
        nonlocal passed_optional
        passed_required = required
        passed_optional = optional

    listener = Mock()
    listener.on_test_event = Mock(side_effect=on_test_event)

    source.add_listener(listener)

    # act
    source.fire_event('on_test_event', 'required', optional='optional')

    # assert
    assert passed_required == 'required'
    assert passed_optional == 'optional'


def test_transaction():
    # arrange
    source = EventSource()

    listener = Mock()
    listener.test_event = Mock()
    listener.super_event = Mock()

    source.add_listener(listener)

    # act
    with EventTransaction(source, 'super_event'):
        source.fire_event('test_event')
        source.fire_event('test_event')

    # assert
    assert not listener.test_event.called
    assert listener.super_event.called
