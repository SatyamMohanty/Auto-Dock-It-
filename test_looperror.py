import pytest
import signal

def test_fake_infinite_loop():
    with pytest.raises(TimeoutError):
        signal.alarm(1)  # Timeout after 1 second
        while True:
            pass