from collections.abc import Callable, Iterable, Mapping
from typing import Generic, Self, SupportsIndex, TypeVar, cast, overload, override

from pydantic import BaseModel, RootModel
from pydantic_core.core_schema import ListSchema, ModelSchema

_ModelT = TypeVar("_ModelT", bound=BaseModel)
_T = TypeVar("_T")


def _get_or_raise(obj: Mapping[str, _T], attr: str) -> _T:
    result = obj[attr]
    if result is None:
        raise AttributeError(f"Attribute '{attr}' not found in {obj}")
    return result


class ListRootModel(RootModel[list[_ModelT]], Generic[_ModelT]):
    @classmethod
    def empty(cls) -> "ListRootModel[_ModelT]":
        """Creates an empty ListRootModel."""
        return cls(root=[])

    @override
    def __iter__(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return iter(self.root)

    @overload
    def __getitem__(self, item: SupportsIndex, /) -> _ModelT: ...
    @overload
    def __getitem__(self, item: slice, /) -> list[_ModelT]: ...
    def __getitem__(self, item: SupportsIndex | slice) -> _ModelT | list[_ModelT]:
        return self.root[item]

    @overload
    def __setitem__(self, key: SupportsIndex, value: _ModelT) -> None: ...
    @overload
    def __setitem__(self, key: slice, value: Iterable[_ModelT]) -> None: ...
    def __setitem__(self, key: SupportsIndex | slice, value: _ModelT | Iterable[_ModelT]) -> None:
        try:
            self.root[key] = value  # pyright: ignore[reportCallIssue, reportArgumentType]
        except TypeError as e:
            raise TypeError(
                f"Invalid types for __setitem__: key={type(key)}, value={type(value)}"
            ) from e

    @property
    def base_type(self) -> type[_ModelT]:
        """Get the base type of the items in the root list."""
        core_schema = self.__class__.__pydantic_core_schema__
        schema = cast("ListSchema", _get_or_raise(core_schema, "schema"))
        items_schema = cast("ModelSchema", _get_or_raise(schema, "items_schema"))
        return cast("type[_ModelT]", _get_or_raise(items_schema, "cls"))

    def append(self, item: _ModelT):
        """Append an item to the end of class."""
        self.root.append(item)

    def __add__(self, other: "ListRootModel[_ModelT] | Iterable[_ModelT]") -> Self:
        root: list[_ModelT] = self.root.copy()
        if isinstance(other, ListRootModel):
            root += other.root
        else:
            root += list(other)

        self.root: list[_ModelT] = root

        return self

    def __len__(self) -> int:
        return len(self.root)

    @override
    def __repr__(self):
        return f"{self.__class__.__name__}({self.root})"

    def filter(self, predicate: Callable[[_ModelT], bool]) -> None:
        """Filters the root list by a predicate function."""
        self.root = list(filter(predicate, self.root))


_KV = TypeVar("_KV")
_VT = TypeVar("_VT")


class DictRootModel(RootModel[dict[_KV, _VT]], Generic[_KV, _VT]):
    @classmethod
    def empty(cls) -> "DictRootModel[_KV, _VT]":
        """Creates an empty DictRootModel."""
        return cls(root={})

    def __len__(self) -> int:
        """Returns the number of items in the dict."""
        return len(self.root)
