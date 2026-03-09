"""Tests for gramix.fsm — MemoryStorage, SQLiteStorage, StateContext."""
import tempfile
import os

import pytest
from gramix.fsm import MemoryStorage, SQLiteStorage, State, Step, StateContext
from gramix.exceptions import FSMError


# ---------------------------------------------------------------------------
# State definitions
# ---------------------------------------------------------------------------

class Survey(State):
    name = Step()
    age  = Step()
    city = Step()


class TwoStep(State):
    first  = Step()
    second = Step()


# ---------------------------------------------------------------------------
# MemoryStorage
# ---------------------------------------------------------------------------

def test_memory_storage_get_creates_context():
    storage = MemoryStorage()
    ctx = storage.get(1)
    assert isinstance(ctx, StateContext)
    assert not ctx.is_active


def test_memory_storage_set_and_retrieve():
    storage = MemoryStorage()
    ctx = storage.get(1)
    ctx.set(Survey.name)
    assert ctx.is_active
    assert ctx.current == "Survey.name"


def test_memory_storage_next():
    storage = MemoryStorage()
    ctx = storage.get(1)
    ctx.set(Survey.name)
    result = ctx.next()
    assert result is True
    assert ctx.current == "Survey.age"


def test_memory_storage_next_last_step_finishes():
    storage = MemoryStorage()
    ctx = storage.get(1)
    ctx.set(Survey.city)  # last step
    result = ctx.next()
    assert result is False
    assert not ctx.is_active


def test_memory_storage_prev():
    storage = MemoryStorage()
    ctx = storage.get(1)
    ctx.set(Survey.age)
    result = ctx.prev()
    assert result is True
    assert ctx.current == "Survey.name"


def test_memory_storage_prev_first_step():
    storage = MemoryStorage()
    ctx = storage.get(1)
    ctx.set(Survey.name)
    result = ctx.prev()
    assert result is False
    assert ctx.current == "Survey.name"


def test_memory_storage_finish():
    storage = MemoryStorage()
    ctx = storage.get(1)
    ctx.set(Survey.name)
    ctx.data["name"] = "Alice"
    ctx.finish()
    assert not ctx.is_active
    assert ctx.data == {}


def test_memory_storage_data_preserved_across_steps():
    storage = MemoryStorage()
    ctx = storage.get(1)
    ctx.set(Survey.name)
    ctx.data["name"] = "Bob"
    ctx.next()
    assert ctx.data["name"] == "Bob"


def test_memory_storage_matches():
    storage = MemoryStorage()
    ctx = storage.get(1)
    ctx.set(Survey.age)
    assert ctx.matches(Survey.age)
    assert not ctx.matches(Survey.name)


def test_memory_storage_delete_resets():
    storage = MemoryStorage()
    ctx = storage.get(1)
    ctx.set(Survey.name)
    storage.delete(1)
    assert not ctx.is_active


def test_memory_storage_clear_all():
    storage = MemoryStorage()
    storage.get(1).set(Survey.name)
    storage.get(2).set(Survey.age)
    storage.clear_all()
    # New contexts are inactive after clear
    assert not storage.get(1).is_active
    assert not storage.get(2).is_active


def test_memory_storage_separate_users():
    storage = MemoryStorage()
    ctx1 = storage.get(1)
    ctx2 = storage.get(2)
    ctx1.set(Survey.name)
    ctx2.set(Survey.city)
    assert ctx1.current == "Survey.name"
    assert ctx2.current == "Survey.city"


def test_fsm_error_on_unset_step_next():
    storage = MemoryStorage()
    ctx = storage.get(1)
    with pytest.raises(FSMError):
        ctx.next()


def test_two_step_full_flow():
    storage = MemoryStorage()
    ctx = storage.get(42)
    ctx.set(TwoStep.first)
    assert ctx.current == "TwoStep.first"
    ctx.next()
    assert ctx.current == "TwoStep.second"
    ctx.next()  # last step → finish
    assert not ctx.is_active


# ---------------------------------------------------------------------------
# SQLiteStorage
# ---------------------------------------------------------------------------

def test_sqlite_storage_basic():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name

    storage = SQLiteStorage(path)
    ctx = storage.get(1)
    assert not ctx.is_active

    ctx.set(Survey.name)
    assert ctx.current == "Survey.name"

    # Reload from fresh storage instance to verify persistence
    storage2 = SQLiteStorage(path)
    ctx2 = storage2.get(1)
    assert ctx2.is_active
    assert ctx2.current == "Survey.name"

    os.unlink(path)


def test_sqlite_storage_data_persistence():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name

    storage = SQLiteStorage(path)
    ctx = storage.get(5)
    ctx.set(Survey.name)
    ctx.data["name"] = "Charlie"
    storage.set(5, "Survey", "name", ctx.data)

    storage2 = SQLiteStorage(path)
    ctx2 = storage2.get(5)
    assert ctx2.data.get("name") == "Charlie"

    os.unlink(path)


def test_sqlite_storage_delete():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name

    storage = SQLiteStorage(path)
    ctx = storage.get(1)
    ctx.set(Survey.age)
    storage.delete(1)

    storage2 = SQLiteStorage(path)
    ctx2 = storage2.get(1)
    assert not ctx2.is_active

    os.unlink(path)


def test_sqlite_storage_clear_all():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name

    storage = SQLiteStorage(path)
    storage.get(1).set(Survey.name)
    storage.get(2).set(Survey.city)
    storage.clear_all()

    storage2 = SQLiteStorage(path)
    assert not storage2.get(1).is_active
    assert not storage2.get(2).is_active

    os.unlink(path)
