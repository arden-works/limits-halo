from abc import ABC, abstractmethod
from models import LimitState


class LimitProvider(ABC):
    name = "Provider"
    is_mock = False

    @abstractmethod
    def get_state(self) -> LimitState:
        """Return a snapshot; called on a worker, never on the UI thread."""
        raise NotImplementedError

    def close(self):
        """Release provider resources after the worker has finished."""

    def stop_new_work(self):
        """Prevent new subprocess work before Controller waits for workers."""
