from abc import ABC, abstractmethod
from typing import Any


class BaseAdapter(ABC):
    @abstractmethod
    def prepare(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
