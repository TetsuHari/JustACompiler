from compiler.tokenizer import tokenize, Token, L, TokenType, Location
import compiler.ast as ast


def parse(tokens: list[Token]) -> ast.Expression:
    pos: int = 0

    if len(tokens) == 0:
        return ast.Block(Location(0, 0), expressions=[])

    left_associative_binary = {
        2: ["or"],
        3: ["and"],
        4: ["==", "!="],
        5: ["<", "<=", ">", ">="],
        6: ["+", "-"],
        7: ["*", "/", "%"],
    }

    # 'peek()' returns the token at 'pos',
    # or a special 'end' token if we're past the end
    # of the token list.
    # This way we don't have to worry about going past
    # the end elsewhere.
    def peek(lookahead: int = 0) -> Token:
        if pos + lookahead < len(tokens) and len(tokens) != 0:
            return tokens[pos + lookahead]
        else:
            return Token(
                location=L,
                type=TokenType.END,
                text="",
            )

    def lookback(amount: int = 1) -> Token:
        if pos - amount > 0:
            return tokens[pos - amount]
        else:
            return Token(
                location=L,
                type=TokenType.END,
                text="",
            )

    # 'consume(expected)' returns the token at 'pos'
    # and moves 'pos' forward.
    #
    # If the optional parameter 'expected' is given,
    # it checks that the token being consumed has that text.
    # If 'expected' is a list, then the token must have
    # one of the texts in the list.
    def consume(expected: str | list[str] | None = None) -> Token:
        nonlocal pos
        token = peek()
        if isinstance(expected, str) and token.text != expected:
            raise Exception(f'{token.location}: expected "{expected}"')
        if isinstance(expected, list) and token.text not in expected:
            comma_sep = ", ".join([f'"{e}"' for e in expected])
            raise Exception(f"{token.location}: expected one of : {comma_sep}")
        pos += 1
        return token

    def parse_int_lit() -> ast.Literal:
        if peek().type != TokenType.INT_LITERAL:
            raise Exception(f"{peek().location}: expected an integer literal")
        token = consume()
        return ast.Literal(location=token.location, value=int(token.text))

    def parse_bool_lit() -> ast.Literal:
        if peek().type != TokenType.BOOL_LITERAL:
            raise Exception(f"{peek().location}: expected a boolean literal")
        token = consume()
        return ast.Literal(location=token.location, value=token.text == "true")

    def parse_identifier() -> ast.Identifier:
        if peek().type != TokenType.IDENTIFIER:
            raise Exception(f"{peek().location}: expected an identifier")
        token = consume()
        return ast.Identifier(location=token.location, name=token.text)

    def parse_parenthesized() -> ast.Expression:
        consume("(")
        # print("Consumed (")
        # Recursively call the top level parsing function
        # to parse whatever is inside the parentheses.
        expr = parse_expression()
        consume(")")
        # print("Consumed )")
        return expr

    def parse_conditional() -> ast.Expression:
        if_tok = consume("if")
        condition = parse_expression()
        # print(f"\n###############\nParsed condition {condition}\n")
        consume("then")
        then = parse_expression()
        # print(f"\n#################\nparsed then {then}\n")
        otherwise = None
        if peek().text == "else":
            consume("else")
            otherwise = parse_expression()

        return ast.Branch(
            location=if_tok.location,
            condition=condition,
            then=then,
            otherwise=otherwise,
        )

    def parse_block(top_level_block: bool = False) -> ast.Expression:
        if not top_level_block:
            block_start = consume("{")

        print(f"PARSING BLOCK")
        statements: list[ast.Expression | None]
        if peek().text == "}":
            statements = [None]
        else:
            statements = [parse_expression(block_call=True)]
            breakpoint
            while peek().text == ";" or lookback().text == "}":
                if peek().text == ";":
                    consume(";")
                expr = parse_expression(block_call=True)
                print(
                    f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Block Expression that parsed is {expr}, exprs is not none? {expr is not None}"
                )
                if expr != ast.Literal(L, None):
                    statements.append(expr)
                    print(f"Appended expr to statements, now is {statements}")
                else:
                    if lookback().text == ";" or peek().text != "}":
                        statements.append(ast.Literal(lookback().location, None))
                    break

        if not top_level_block:
            consume("}")
        print(f"BLOCK PARSE FINISHED")
        return ast.Block(location=block_start.location, expressions=statements)

    def parse_loop() -> ast.Expression:
        w = consume("while")
        conditional = parse_expression()
        consume("do")
        loop = parse_expression()
        return ast.Loop(location=w.location, condition=conditional, loop=loop)

    def parse_var() -> ast.Expression:
        var = consume("var")
        ident = parse_identifier()
        consume("=")
        expression = parse_expression()

        return ast.VarDeclaration(
            location=var.location, identifier=ident, expression=expression
        )

    def parse_function(ident: ast.Identifier) -> ast.Expression:
        f = consume("(")
        if peek().text == ")":
            argList = []
        else:
            argList = [parse_expression()]
        while peek().text == ",":
            consume(",")
            argList.append(parse_expression())

        consume(")")
        return ast.FuncCall(location=f.location, identifier=ident, arguments=argList)

    def parse_expression(
        precedence_level: int = 1,
        top_level_call: bool = False,
        block_call: bool = False,
    ) -> ast.Expression:

        right: ast.Expression | None = None
        term: ast.Expression | None = None

        toReturn: ast.Expression | None = None

        match precedence_level:
            case 1:
                right = None
                left = parse_expression(2, top_level_call, block_call)

                # print(f'On level {precedence_level}, looking at "="')
                # print(f"peek is: {peek().text}")

                while peek().text in ["="]:

                    operator = consume()

                    # print(f"Operator consumed: {operator.text}")

                    if isinstance(left, ast.Identifier):
                        right = ast.Assignment(
                            location=operator.location,
                            identifier=left,
                            expression=parse_expression(),
                        )
                    else:
                        raise Exception(
                            f"Failed to parse assignment, {left} not an identifier"
                        )

                term = right if right is not None else left

                statements: list[ast.Expression | None] = [term]
                while top_level_call and peek().text == ";":
                    consume(";")
                    statements.append(
                        parse_expression(top_level_call=False, block_call=True)
                    )

                # #print(f'Term is currently {term}, \n statements are {statements}')

                # #print(f"Current peek is: {peek()}")

                # #print(f"In a toplevel call? {top_level_call}")
                # #print(f"Peek is: {peek().text} it it not allowed in non-top-level call: {peek().text not in ["", ";", ")", "}", "then", "else", "do"]}")
                if (
                    peek().text not in ["", ",", ";", ")", "}", "then", "else", "do"]
                    and not top_level_call
                ):
                    # #print("Wat")
                    if lookback().text != "}":
                        raise Exception(f"Trailing garbage at {peek().location}")

                if peek().type != TokenType.END and top_level_call:
                    # #print("wat2")
                    raise Exception(f"Trailing garbage at {peek().location}")

                if 1 < len(statements):
                    toReturn = ast.Block(
                        location=tokens[0].location, expressions=statements
                    )
                else:
                    toReturn = term

            case l if 2 <= l < 8:
                left = parse_expression(l + 1, top_level_call, block_call)

                # print(f"On level {l}, looking at {left_associative_binary[l]}")
                # print(f"peek is: {peek().text}")
                # print(
                #    f"{peek().text} in {left_associative_binary[l]} == {peek().text in left_associative_binary[l]}"
                # )
                while peek().text in left_associative_binary[l]:
                    operator = consume()

                    # print(f"Operator consumed: {operator.text}")

                    right = parse_expression(l + 1)

                    left = ast.BinaryOp(
                        location=operator.location,
                        op=operator.text,
                        left=left,
                        right=right,
                    )

                toReturn = left
            case 8:
                while peek().text in ["-", "not"]:
                    operator = consume()
                    # print(f"Operator consumed: {operator.text}")

                    term = ast.UnaryOp(
                        location=operator.location,
                        op=operator.text,
                        parameter=parse_expression(l),
                    )

                if term is not None:
                    toReturn = term
                else:
                    toReturn = parse_expression(l + 1, top_level_call, block_call)

            case _:
                match peek():
                    case t if t.text == "if":
                        toReturn = parse_conditional()
                    case t if t.text == "while":
                        toReturn = parse_loop()
                    case t if t.text == "var":
                        if not (top_level_call or block_call):
                            raise Exception(
                                f"Vars only supported in top level or blocks: {t.location}"
                            )
                        toReturn = parse_var()
                    case t if t.text == "{":
                        toReturn = parse_block()
                    case t if t.text == "(":
                        toReturn = parse_parenthesized()
                    case t if t.type == TokenType.IDENTIFIER:
                        toReturn = parse_identifier()
                        if peek().text == "(":
                            toReturn = parse_function(ident=toReturn)
                    case t if t.type == TokenType.BOOL_LITERAL:
                        toReturn = parse_bool_lit()
                    case t if t.type == TokenType.INT_LITERAL:
                        toReturn = parse_int_lit()

        # print(
        #    f"On level {precedence_level} and toplevel? = {top_level_call}. \n Returning {toReturn} \n\n\n"
        # )
        return (
            toReturn if toReturn is not None else ast.Literal(lookback().location, None)
        )

    parsed = parse_expression(top_level_call=True)
    return parsed
