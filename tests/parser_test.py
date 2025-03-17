from compiler.tokenizer import tokenize, Token, TokenType, L, Location
from compiler.parser import parse
import compiler.ast as ast

import pytest


def test_parser_basics() -> None:
    testPairs = [  #: list[tuple[list[Token], ast.Expression | None]] = [
        # c = a + b - (-7 * 4)
        (
            tokenize("c = a + b - (-7 * 4)"),
            ast.Assignment(
                L,
                ast.Identifier(L, "c"),
                ast.BinaryOp(
                    L,
                    "-",
                    ast.BinaryOp(
                        L, "+", ast.Identifier(L, "a"), ast.Identifier(L, "b")
                    ),
                    ast.BinaryOp(
                        L,
                        "*",
                        ast.UnaryOp(L, "-", ast.Literal(L, 7)),
                        ast.Literal(L, 4),
                    ),
                ),
            ),
        ),
        # 1 - 2 - 3 - 4 - 6 == ( ( ( 1 - 2 ) - 3  ) - 4 ) - 6
        (
            tokenize("1-2-3-4-6"),
            ast.BinaryOp(
                L,
                "-",
                ast.BinaryOp(
                    L,
                    "-",
                    ast.BinaryOp(
                        L,
                        "-",
                        ast.BinaryOp(L, "-", ast.Literal(L, 1), ast.Literal(L, 2)),
                        ast.Literal(L, 3),
                    ),
                    ast.Literal(L, 4),
                ),
                ast.Literal(L, 6),
            ),
        ),
        # empty input
        ([], ast.Block(L, [])),
        # var n = 5;
        # n = 5 - 7;
        # while n > 1 do {
        #   if n % 2 == 0 then {
        #     n = n / 2;
        #   } else {
        #     n = 3 * n + 1;
        #   };
        #   n * 6
        # }
        (
            tokenize(
                "var n = 5; n = 5 - 7; while n > 1 do { if n % 2 == 0 then { n = n/2; } else {n = 3 * n + 1}; n = n* 6}"
            ),
            ast.Block(
                L,
                [
                    ast.VarDeclaration(L, ast.Identifier(L, "n"), ast.Literal(L, 5)),
                    ast.Assignment(
                        L,
                        ast.Identifier(L, "n"),
                        ast.BinaryOp(L, "-", ast.Literal(L, 5), ast.Literal(L, 7)),
                    ),
                    ast.Loop(
                        L,
                        ast.BinaryOp(L, ">", ast.Identifier(L, "n"), ast.Literal(L, 1)),
                        ast.Block(
                            L,
                            [
                                ast.Branch(
                                    L,
                                    ast.BinaryOp(
                                        L,
                                        "==",
                                        ast.BinaryOp(
                                            L,
                                            "%",
                                            ast.Identifier(L, "n"),
                                            ast.Literal(L, 2),
                                        ),
                                        ast.Literal(L, 0),
                                    ),
                                    ast.Block(
                                        L,
                                        [
                                            ast.Assignment(
                                                L,
                                                ast.Identifier(L, "n"),
                                                ast.BinaryOp(
                                                    L,
                                                    "/",
                                                    ast.Identifier(L, "n"),
                                                    ast.Literal(L, 2),
                                                ),
                                            ),
                                            ast.Literal(L, None),
                                        ],
                                    ),
                                    ast.Block(
                                        L,
                                        [
                                            ast.Assignment(
                                                L,
                                                ast.Identifier(L, "n"),
                                                ast.BinaryOp(
                                                    L,
                                                    "+",
                                                    ast.BinaryOp(
                                                        L,
                                                        "*",
                                                        ast.Literal(L, 3),
                                                        ast.Identifier(L, "n"),
                                                    ),
                                                    ast.Literal(L, 1),
                                                ),
                                            )
                                        ],
                                    ),
                                ),
                                ast.Assignment(
                                    L,
                                    ast.Identifier(L, "n"),
                                    ast.BinaryOp(
                                        L,
                                        "*",
                                        ast.Identifier(L, "n"),
                                        ast.Literal(L, 6),
                                    ),
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        ),
        # { {a} {b}}
        (
            tokenize("{{a}{b}}"),
            ast.Block(
                L,
                [
                    ast.Block(L, [ast.Identifier(L, "a")]),
                    ast.Block(L, [ast.Identifier(L, "b")]),
                ],
            ),
        ),
        (
            tokenize("{ if true then { a } b }"),
            ast.Block(
                L,
                [
                    ast.Branch(
                        L,
                        ast.Literal(L, True),
                        ast.Block(L, [ast.Identifier(L, "a")]),
                        None,
                    ),
                    ast.Identifier(L, "b"),
                ],
            ),
        ),
        (
            tokenize("{ if true then {a}; b}"),
            ast.Block(
                L,
                [
                    ast.Branch(
                        L,
                        ast.Literal(L, True),
                        ast.Block(L, [ast.Identifier(L, "a")]),
                        None,
                    ),
                    ast.Identifier(L, "b"),
                ],
            ),
        ),
        (
            tokenize("{ if true then {a} b; c}"),
            ast.Block(
                L,
                [
                    ast.Branch(
                        L,
                        ast.Literal(L, True),
                        ast.Block(L, [ast.Identifier(L, "a")]),
                        None,
                    ),
                    ast.Identifier(L, "b"),
                    ast.Identifier(L, "c"),
                ],
            ),
        ),
        (
            tokenize("{ if true then {a} else {b} c}"),
            ast.Block(
                L,
                [
                    ast.Branch(
                        L,
                        ast.Literal(L, True),
                        ast.Block(L, [ast.Identifier(L, "a")]),
                        ast.Block(L, [ast.Identifier(L, "b")]),
                    ),
                    ast.Identifier(L, "c"),
                ],
            ),
        ),
        # 1 + if true then 2 else 3
        (
            tokenize("1 + if true then 2 else 3"),
            ast.BinaryOp(
                L,
                "+",
                ast.Literal(L, 1),
                ast.Branch(
                    L, ast.Literal(L, True), ast.Literal(L, 2), ast.Literal(L, 3)
                ),
            ),
        ),
        # f(x, y + z)
        (
            tokenize("f(x, y + z)"),
            ast.FuncCall(
                L,
                ast.Identifier(L, "f"),
                [
                    ast.Identifier(L, "x"),
                    ast.BinaryOp(
                        L, "+", ast.Identifier(L, "y"), ast.Identifier(L, "z")
                    ),
                ],
            ),
        ),
        # not not not x
        (
            tokenize("not not not x"),
            ast.UnaryOp(
                L,
                "not",
                ast.UnaryOp(L, "not", ast.UnaryOp(L, "not", ast.Identifier(L, "x"))),
            ),
        ),
        (
            tokenize("not if a == b then true"),
            ast.UnaryOp(
                L,
                "not",
                ast.Branch(
                    L,
                    ast.BinaryOp(
                        L, "==", ast.Identifier(L, "a"), ast.Identifier(L, "b")
                    ),
                    ast.Literal(L, True),
                ),
            ),
        ),
        # a = b = c = 2
        (
            tokenize("a = b = c = 2"),
            ast.Assignment(
                L,
                ast.Identifier(L, "a"),
                ast.Assignment(
                    L,
                    ast.Identifier(L, "b"),
                    ast.Assignment(L, ast.Identifier(L, "c"), ast.Literal(L, 2)),
                ),
            ),
        ),
        (
            tokenize(
                """
        {
          while f() do {
            x = 10;
            y = if g(x) then {
              x = x + 1;
              x
            } else {
              g(x)
            }
            g(y);
          }
          123
        }
        """
            ),
            ast.Block(
                L,
                [
                    ast.Loop(
                        L,
                        ast.FuncCall(L, ast.Identifier(L, "f"), []),
                        ast.Block(
                            L,
                            [
                                ast.Assignment(
                                    L, ast.Identifier(L, "x"), ast.Literal(L, 10)
                                ),
                                ast.Assignment(
                                    L,
                                    ast.Identifier(L, "y"),
                                    ast.Branch(
                                        L,
                                        ast.FuncCall(
                                            L,
                                            ast.Identifier(L, "g"),
                                            [ast.Identifier(L, "x")],
                                        ),
                                        ast.Block(
                                            L,
                                            [
                                                ast.Assignment(
                                                    L,
                                                    ast.Identifier(L, "x"),
                                                    ast.BinaryOp(
                                                        L,
                                                        "+",
                                                        ast.Identifier(L, "x"),
                                                        ast.Literal(L, 1),
                                                    ),
                                                ),
                                                ast.Identifier(L, "x"),
                                            ],
                                        ),
                                        ast.Block(
                                            L,
                                            [
                                                ast.FuncCall(
                                                    L,
                                                    ast.Identifier(L, "g"),
                                                    [ast.Identifier(L, "x")],
                                                )
                                            ],
                                        ),
                                    ),
                                ),
                                ast.FuncCall(
                                    L, ast.Identifier(L, "g"), [ast.Identifier(L, "y")]
                                ),
                                ast.Literal(L, None),
                            ],
                        ),
                    ),
                    ast.Literal(L, 123),
                ],
            ),
        ),
        (
            tokenize("var x = { {f(a)} {b}}"),
            ast.VarDeclaration(
                L,
                ast.Identifier(L, "x"),
                ast.Block(
                    L,
                    [
                        ast.Block(
                            L,
                            [
                                ast.FuncCall(
                                    L, ast.Identifier(L, "f"), [ast.Identifier(L, "a")]
                                )
                            ],
                        ),
                        ast.Block(L, [ast.Identifier(L, "b")]),
                    ],
                ),
            ),
        ),
    ]
    testPairsError: list[tuple[list[Token], Exception]] = [
        # a + b c
        (
            [
                Token(TokenType.IDENTIFIER, "a", L),
                Token(TokenType.OPERATOR, "+", L),
                Token(TokenType.IDENTIFIER, "b", L),
                Token(TokenType.IDENTIFIER, "c", L),
            ],
            Exception(f"Malformed input at {L}"),
        ),
        # a + (c
        (
            [
                Token(TokenType.IDENTIFIER, "a", L),
                Token(TokenType.OPERATOR, "+", L),
                Token(TokenType.PUNCTUATION, "(", L),
                Token(TokenType.IDENTIFIER, "c", L),
            ],
            Exception(f'{L}: expected ")"'),
        ),
        # {a b}
        (tokenize("{a b}"), Exception()),
        #
        (tokenize("{ if true then {a} b c}"), Exception()),
        (tokenize("if a then var x = 3"), Exception()),
    ]

    for testPair in testPairs:
        print(parse(testPair[0]))
        assert parse(testPair[0]) == testPair[1]

    # for testPairE in testPairsError:
    #   with pytest.raises(Exception) as e_info:
    #     parse(testPairE[0])

    # block = [ast.Block(L, [
    #   ast.VarDeclaration(L, ast.Identifier(L, "a"), ast.Literal(L, 5))
    # ])]
    # block2 = [ast.Block(Location(100, 100), [
    #   ast.VarDeclaration(Location(100, 101), ast.Identifier(Location(100, 100), "a"), ast.Literal(Location(100,100), 5))
    # ])]

    # assert block == block2
