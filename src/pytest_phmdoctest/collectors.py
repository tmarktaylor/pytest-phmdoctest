"""Build pytest collectors instances per pytest versions."""
from packaging.version import Version
from pathlib import Path
from typing import Iterable
from typing import NewType
from typing import Optional
from typing import Tuple
from typing import Union

import py
import pytest
from pytest import Collector
from pytest import Item
from pytest import Module


pytest_version = Version(pytest.__version__)
PYTEST_GE_7 = pytest_version >= Version("7.0")


class Pathy:
    """Handles filename differences both pre and post pytest 7.0."""

    def __init__(self, value: Union[py.path.local, Path]):
        """Store value of type appopriate for the pytest version."""
        self.value = value
        if PYTEST_GE_7:
            assert isinstance(value, Path), "Must be type pathlib.Path."
            self.extension = self.value.suffix
            self.as_path = value
        else:
            # intended for pytest >=5 and <7
            assert isinstance(value, py.path.local), "Must be type py.path.local."
            self.extension = self.value.ext
            self.as_path = Path(value)


class EmptyCollector(Collector):
    """Collector returns no items."""

    def collect(self) -> Iterable[Union[Item, Collector]]:
        """Override parent. Return empty Iterable."""
        return tuple()


def empty_collector(parent: Collector, pathy: Pathy, name: str) -> EmptyCollector:
    """pytest version 6.2 - 7.0 difference in path type for from_parent()."""
    if PYTEST_GE_7:
        return EmptyCollector.from_parent(
            parent,
            path=pathy.value,
            name=name,
        )
    else:
        # intended for pytest >=5 and <7
        return EmptyCollector.from_parent(
            parent,
            fspath=pathy.value,
            name=name,
        )


# This satisfies flake8.
DoctestModule = NewType("DoctestModule", Collector)
"DoctestModule is a non-public pytest class. We only try import if needed."

Bundle = Tuple["DoctestModule", Module]
"""Two Modules for collection created from one generated test file."""


class BundledCollector(Collector):
    """Collector for a DoctestModule and a Module bundled together."""

    _collectibles = (
        []  # type: ignore # Avoid mypy Incompatible types in assignment
    )  # type: Bundle  # Avoid IDE nag "Instance attribute not def in __init__".

    def collect(self) -> Iterable[Union[Item, Collector]]:
        """Override parent."""
        return self._collectibles

    def add_collectibles(self, docmod: "DoctestModule", mod: Module) -> None:
        """Set the sequence of DoctestModule, Module to be collected."""
        self._collectibles = (docmod, mod)


PluginCollector = Union[BundledCollector, Module, "DoctestModule", EmptyCollector]
"""pytest plugin pytest_collect_file() hook return type."""


def module(parent: Collector, pathlib_path: Path) -> Module:
    """Create Module collector for the test file at pathlib_path."""
    if PYTEST_GE_7:
        mod = Module.from_parent(parent, path=pathlib_path)
    else:
        # intended for pytest >=5 and <7
        pypath = py.path.local(str(pathlib_path))
        mod = Module.from_parent(parent, fspath=pypath)
    return mod


def doctest_module(parent: Collector, pathlib_path: Path) -> Optional["DoctestModule"]:
    """Create DoctestModule collector for the test file at pathlib_path.

    DoctestModule is not listed in the pytest API reference.
    To anticipate future breaking changes in pytest > 7, we catch exceptions
    when importing and using the DoctestModule class.
    """
    if PYTEST_GE_7:
        try:
            from _pytest.doctest import DoctestModule

            docmod = DoctestModule.from_parent(parent, path=pathlib_path)
        except (TypeError, AttributeError, ModuleNotFoundError, ImportError):
            docmod = None
    else:
        # intended for pytest >=5 and <7
        pypath = py.path.local(str(pathlib_path))
        from _pytest.doctest import DoctestModule

        docmod = DoctestModule.from_parent(parent, fspath=pypath)
    return docmod


def bundled_collector(
    parent: Collector, pathlib_path: Path, name: str
) -> BundledCollector:
    """Create collector to bundle Module and DoctestModule."""
    if PYTEST_GE_7:
        bc = BundledCollector.from_parent(
            parent, path=pathlib_path, name=name
        )  # type: BundledCollector
    else:
        # intended for pytest >=5 and <7
        pypath = py.path.local(str(pathlib_path))
        bc = BundledCollector.from_parent(
            parent, fspath=pypath, name=name
        )  # type: BundledCollector
    return bc
