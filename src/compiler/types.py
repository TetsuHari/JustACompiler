from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class Type:
    """Base class for types"""


@dataclass(frozen=True)
class Any(Type):
    """Base class for types"""

    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self))


@dataclass(frozen=True)
class Int(Any):
    """Int type"""


@dataclass(frozen=True)
class Bool(Any):
    """Bool type"""


@dataclass(frozen=True)
class Unit(Any):
    """Unit type"""


@dataclass(frozen=True)
class FunType(Any):
    """Function type"""

    arguments: list[Type]
    return_value: Type

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FunType):
            return False

        return (
            self.arguments == other.arguments
            and self.return_value == other.return_value
        )


@dataclass
class SymTab:
    parent: Self | None
    locals: dict[str, Type]
