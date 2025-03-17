from typing import Optional

import re

from dataclasses import dataclass
from enum import Enum
from functools import partial


class TokenType(Enum):
    IDENTIFIER = 1
    INT_LITERAL = 2
    BOOL_LITERAL = 3
    OPERATOR = 4
    PUNCTUATION = 5
    END = 6
    OTHER = 9


@dataclass
class Location:
    line: int
    column: int

    def __eq__(self, other: object) -> bool:

        if not isinstance(other, Location):
            return False

        if (self.line == -1 and self.column == -1) or (
            other.line == -1 and other.column == -1
        ):
            return True

        if self.line == other.line and self.column == other.column:
            return True

        return False


L: Location = Location(-1, -1)


@dataclass
class Token:
    """Class for language tokens"""

    type: TokenType
    text: str
    location: Location


identifierR = r"(?P<identifier>(?:_|[a-z]|[A-Z])(?:_|[a-z]|[A-Z]|[0-9])*)"
int_lit = r"(?P<int_lit>[0-9]+)"
bool_lit = r"(?P<bool_lit>true|false)"
operator = r"(?P<operator>==|!=|<=|>=|\+|\-|\*|\/|=|<|>|%|or|and|not)"
punctuation = r"(?P<punctuation>\(|\)|\{|\}|,|\.|;)"
comment = r"\/\/.*|#.*"


def tupleToToken(
    row: int, line: str, tuple: tuple[str, str, str, str, str]
) -> Optional[Token]:
    (bool, oper, ident, int, punct) = tuple

    if tuple == ("", "", "", "", ""):
        return None

    if ident != "":
        tokenType = TokenType.IDENTIFIER
        tok = ident

    if int != "":
        tokenType = TokenType.INT_LITERAL
        tok = int

    if bool != "":
        tokenType = TokenType.BOOL_LITERAL
        tok = bool

    if oper != "":
        tokenType = TokenType.OPERATOR
        tok = oper

    if punct != "":
        tokenType = TokenType.PUNCTUATION
        tok = punct

    col = line.find(tok) + 1  # Adding one to get first column to be one.

    return Token(tokenType, tok, Location(row, col))


def tokenize(source_code: str) -> list[Token]:
    regexStringList = [comment, bool_lit, operator, identifierR, int_lit, punctuation]

    codeLines = source_code.splitlines()

    matcher = re.compile("|".join(regexStringList))

    tokens: list[Token] = []
    row = 1
    for line in codeLines:
        tokenTuples = matcher.findall(line)
        tupToToken = partial(tupleToToken, row, line)
        tokens += filter(None, map(tupToToken, tokenTuples))
        row += 1

    return tokens
