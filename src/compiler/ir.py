from dataclasses import dataclass, fields
from typing import Any, Self

from compiler.tokenizer import Location


@dataclass(frozen=True)
class IRVar:
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass
class SymTab:
    parent: None | Self
    locals: dict[str, IRVar]

    def require(self, str: str) -> IRVar:
        mVar: IRVar | None = self.locals.get(str, None)
        par = self.parent
        while mVar is None and par is not None:
            mVar = par.locals.get(str, None)
            par = par.parent

        if mVar is None:
            raise Exception(f"IR Symtab Error: Could not find {str} in symtab")
        return mVar


@dataclass(frozen=True)
class Instruction:
    location: Location

    def __str__(self) -> str:
        """Returns a string representation similar to
        our IR code examples, e.g. 'LoadIntConst(3, x1)'"""

        def format_value(v: Any) -> str:
            if isinstance(v, list):
                return f'[{", ".join(format_value(e) for e in v)}]'
            else:
                return str(v)

        args = ", ".join(
            format_value(getattr(self, field.name))
            for field in fields(self)
            if field.name != "location"
        )
        return f"{type(self).__name__}({args})"


@dataclass(frozen=True)
class Label(Instruction):
    """Marks the destination of a jump instruction."""

    name: str


@dataclass(frozen=True)
class LoadBoolConst(Instruction):
    value: bool
    dest: IRVar


@dataclass(frozen=True)
class LoadIntConst(Instruction):
    """Loads a constant value to `dest`."""

    value: int
    dest: IRVar


@dataclass(frozen=True)
class Copy(Instruction):
    """Copies a value from one variable to another."""

    source: IRVar
    dest: IRVar


@dataclass(frozen=True)
class Call(Instruction):
    """Calls a function or built-in."""

    fun: IRVar
    args: list[IRVar]
    dest: IRVar


@dataclass(frozen=True)
class Jump(Instruction):
    """Unconditionally continues execution from the given label."""

    label: Label


@dataclass(frozen=True)
class CondJump(Instruction):
    """Continues execution from `then_label` if `cond` is true, otherwise from `else_label`."""

    cond: IRVar
    then_label: Label
    else_label: Label
