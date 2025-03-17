from dataclasses import dataclass
from compiler.tokenizer import Location, L


@dataclass
class Expression:
    """Base class for AST nodes representing expressions."""

    location: Location


@dataclass
class Literal(Expression):
    value: int | bool | None


@dataclass
class Identifier(Expression):
    name: str


@dataclass
class Assignment(Expression):
    identifier: Identifier
    expression: Expression


@dataclass
class UnaryOp(Expression):
    """AST node for a unary operator, '-' or 'not'"""

    op: str
    parameter: Expression


@dataclass
class BinaryOp(Expression):
    """
    AST node for a binary operation.

    Supported binary operations, in order of precedence level:

    1. '=' (note that this is right associative)
    2. 'or'
    3. 'and'
    4. '==', '!='
    5. '<', '<=', '>', '>='
    6. '+', '-'
    7. '*', '/', '%'

    """

    op: str
    left: Expression
    right: Expression


@dataclass
class Branch(Expression):
    condition: Expression
    then: Expression
    otherwise: Expression | None = None


@dataclass
class Loop(Expression):
    condition: Expression
    loop: Expression


@dataclass
class Block(Expression):
    expressions: list[Expression | None]


@dataclass
class VarDeclaration(Expression):
    identifier: Identifier
    expression: Expression


@dataclass
class TypedVarDeclaration(Expression):
    identifier: Identifier
    expression: Expression
    type: str


@dataclass
class FuncCall(Expression):
    identifier: Identifier
    arguments: list[Expression]
