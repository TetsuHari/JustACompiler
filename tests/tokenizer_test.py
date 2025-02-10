from compiler.tokenizer import tokenize, Token, L, Location, TokenType

# Shorthand for TT identifiers
ident = TokenType.IDENTIFIER
int_l = TokenType.INT_LITERAL
oper = TokenType.OPERATOR
punc = TokenType.PUNCTUATION


def test_tokenizer_basics() -> None:
    basicTestPairs: list[tuple[str, list[Token]]] = [
        (
            "if (a > b)",
            [
                Token(ident, "if", L),
                Token(punc, "(", L),
                Token(ident, "a", L),
                Token(oper, ">", L),
                Token(ident, "b", L),
                Token(punc, ")", L),
            ],
        ),
        ("hello", [Token(ident, "hello", L)]),
        ("", []),
    ]
    for testPair in basicTestPairs:
        assert tokenize(testPair[0]) == testPair[1]
