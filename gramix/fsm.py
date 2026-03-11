from __future__ import annotations
import json
import logging
import sqlite3
import threading
from abc import ABC, abstractmethod
from typing import Any

from gramix.exceptions import FSMError

logger = logging.getLogger(__name__)

_MAX_MEMORY_SIZE = 10_000

class Step:
    _name: str
    _owner: str

    def __set_name__(self, owner: type, name: str) -> None:
        self._name = name
        self._owner = owner.__name__

    def __repr__(self) -> str:
        return f"{self._owner}.{self._name}"

class StateMeta(type):
    def __new__(mcs, name: str, bases: tuple, namespace: dict) -> StateMeta:
        steps = [key for key, value in namespace.items() if isinstance(value, Step)]
        namespace["_steps"] = steps
        return super().__new__(mcs, name, bases, namespace)

class State(metaclass=StateMeta):
    _steps: list[str] = []

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        _register_state(cls)

class StateContext:
    __slots__ = ("_state_class", "_current_step", "data", "_user_id", "_storage")

    def __init__(
        self,
        user_id: int,
        storage: BaseStorage,
        state_class: type[State] | None = None,
        current_step: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        self._user_id = user_id
        self._storage = storage
        self._state_class = state_class
        self._current_step = current_step
        self.data: dict[str, Any] = data or {}

    @property
    def is_active(self) -> bool:
        return self._state_class is not None

    @property
    def current(self) -> str | None:
        if self._state_class and self._current_step:
            return f"{self._state_class.__name__}.{self._current_step}"
        return None

    def set(self, step: Step) -> None:
        if not hasattr(step, "_owner") or not hasattr(step, "_name"):
            raise FSMError("Step не инициализирован. Используй его как атрибут класса State.")
        state_class = _find_state_class(step._owner)
        if state_class is None:
            raise FSMError(f"Класс состояния '{step._owner}' не найден.")
        if step._name not in state_class._steps:
            raise FSMError(f"Шаг '{step._name}' не найден в '{step._owner}'.")
        self._state_class = state_class
        self._current_step = step._name
        self._storage.set(self._user_id, step._owner, step._name, self.data)
        logger.debug("FSM [%d]: → %s", self._user_id, self.current)

    def next(self) -> bool:
        if not self._state_class or not self._current_step:
            raise FSMError("Состояние не установлено.")
        steps = self._state_class._steps
        idx = steps.index(self._current_step)
        if idx + 1 >= len(steps):
            self.finish()
            return False
        self._current_step = steps[idx + 1]
        self._storage.set(self._user_id, self._state_class.__name__, self._current_step, self.data)
        logger.debug("FSM [%d]: → %s", self._user_id, self.current)
        return True

    def prev(self) -> bool:
        if not self._state_class or not self._current_step:
            raise FSMError("Состояние не установлено.")
        steps = self._state_class._steps
        idx = steps.index(self._current_step)
        if idx == 0:
            return False
        self._current_step = steps[idx - 1]
        self._storage.set(self._user_id, self._state_class.__name__, self._current_step, self.data)
        logger.debug("FSM [%d]: ← %s", self._user_id, self.current)
        return True

    def finish(self) -> None:
        logger.debug("FSM [%d]: finish", self._user_id)
        self._reset()
        self._storage.delete(self._user_id)

    def _reset(self) -> None:
        self._state_class = None
        self._current_step = None
        self.data.clear()

    def matches(self, step: Step) -> bool:
        if not self._state_class or not self._current_step:
            return False
        return self._state_class.__name__ == step._owner and self._current_step == step._name

class BaseStorage(ABC):
    @abstractmethod
    def get(self, user_id: int) -> StateContext:
        ...

    @abstractmethod
    def set(self, user_id: int, state_class: str, step: str, data: dict) -> None:
        ...

    @abstractmethod
    def delete(self, user_id: int) -> None:
        ...

    @abstractmethod
    def clear_all(self) -> None:
        ...

class MemoryStorage(BaseStorage):
    def __init__(self) -> None:
        self._storage: dict[int, StateContext] = {}
        self._lock = threading.Lock()

    def get(self, user_id: int) -> StateContext:
        with self._lock:
            if user_id not in self._storage:
                if len(self._storage) >= _MAX_MEMORY_SIZE:
                    self._evict_inactive()
                self._storage[user_id] = StateContext(user_id, self)
            return self._storage[user_id]

    def set(self, user_id: int, state_class: str, step: str, data: dict) -> None:

        pass

    def delete(self, user_id: int) -> None:
        with self._lock:
            if user_id in self._storage:
                self._storage[user_id]._reset()
                del self._storage[user_id]

    def clear_all(self) -> None:
        with self._lock:
            self._storage.clear()

    def _evict_inactive(self) -> None:

        inactive = [uid for uid, ctx in self._storage.items() if not ctx.is_active]
        for uid in inactive:
            del self._storage[uid]

FSMStorage = MemoryStorage

class SQLiteStorage(BaseStorage):
    def __init__(self, path: str = "gramix_fsm.db") -> None:
        self._path = path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        with self._lock:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS fsm_states (
                    user_id     INTEGER PRIMARY KEY,
                    state_class TEXT NOT NULL,
                    step        TEXT NOT NULL,
                    data        TEXT NOT NULL DEFAULT '{}'
                )
            """)
            self._conn.commit()

    def get(self, user_id: int) -> StateContext:
        with self._lock:
            row = self._conn.execute(
                "SELECT state_class, step, data FROM fsm_states WHERE user_id = ?",
                (user_id,),
            ).fetchone()

        if row is None:
            return StateContext(user_id, self)

        state_class = _find_state_class(row["state_class"])
        if state_class is None:
            return StateContext(user_id, self)

        try:
            data = json.loads(row["data"])
        except (json.JSONDecodeError, TypeError):
            data = {}

        return StateContext(
            user_id=user_id,
            storage=self,
            state_class=state_class,
            current_step=row["step"],
            data=data,
        )

    def set(self, user_id: int, state_class: str, step: str, data: dict) -> None:
        with self._lock:
            self._conn.execute("""
                INSERT INTO fsm_states (user_id, state_class, step, data)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    state_class = excluded.state_class,
                    step        = excluded.step,
                    data        = excluded.data
            """, (user_id, state_class, step, json.dumps(data, ensure_ascii=False)))
            self._conn.commit()

    def delete(self, user_id: int) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM fsm_states WHERE user_id = ?", (user_id,))
            self._conn.commit()

    def clear_all(self) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM fsm_states")
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def __enter__(self) -> "SQLiteStorage":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

_state_registry: dict[str, type[State]] = {}

def _register_state(cls: type[State]) -> None:
    _state_registry[cls.__name__] = cls

def _find_state_class(name: str) -> type[State] | None:
    return _state_registry.get(name)

