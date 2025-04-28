import abc
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, model_validator


class YnabBase(BaseModel, abc.ABC):
    """Base class for YNAB."""

    model_config = ConfigDict(from_attributes=True)


_F = TypeVar("_F")


class YnabField(BaseModel, Generic[_F], abc.ABC):
    value: _F

    @model_validator(mode="before")
    @classmethod
    def from_value(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return {"value": data}
        return data
