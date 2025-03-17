import compiler.ast as ast
from compiler.types import Int, Bool, Unit, SymTab, Type, FunType, Any

"<=", ">=", "<", ">"

import compiler.parser

top_level_SymTab = SymTab(
    None,
    {
        "or": FunType([Bool(), Bool()], Bool()),
        "and": FunType([Bool(), Bool()], Bool()),
        "+": FunType([Int(), Int()], Int()),
        "-": FunType([Int(), Int()], Int()),
        "/": FunType([Int(), Int()], Int()),
        "*": FunType([Int(), Int()], Int()),
        "<=": FunType([Int(), Int()], Bool()),
        ">=": FunType([Int(), Int()], Bool()),
        "<": FunType([Int(), Int()], Bool()),
        ">": FunType([Int(), Int()], Bool()),
        "==": FunType([Any(), Any()], Bool()),
        "!=": FunType([Any(), Any()], Bool()),
        "print_int": FunType([Int()], Unit()),
        "print_bool": FunType([Bool()], Unit()),
        "read_int": FunType([], Int()),
    },
)


def mkSym(symtab: SymTab) -> SymTab:
    return SymTab(symtab, {})


def typecheck(node: ast.Expression, symtab: SymTab = top_level_SymTab) -> Type:
    retVal: Type = Unit()
    match node:
        case ast.Literal():
            # print(type(node.value))
            if isinstance(node.value, bool):
                retVal = Bool()
            elif isinstance(node.value, int):
                retVal = Int()
            else:
                retVal = Unit()

        case ast.Identifier():
            ident_type = symtab.locals.get(node.name, None)
            parent = symtab.parent
            while ident_type is None and parent is not None:
                ident_type = parent.locals.get(node.name)
                parent = parent.parent

            if ident_type is None:
                raise Exception(
                    f"Type error at {node.location}: identifier {node.name} not found in symbolic table"
                )

            retVal = ident_type if ident_type is not None else Unit()

        case ast.Assignment():
            ident_type = typecheck(node.identifier, symtab)
            expr_type = typecheck(node.expression, symtab)

            if ident_type != expr_type:
                raise Exception(
                    f"Type Error at {node.location}: Trying to assign type {expr_type} to variable with type {ident_type}"
                )

            retVal = expr_type

        case ast.VarDeclaration():
            expr_type = typecheck(node.expression, symtab)
            symtab.locals[node.identifier.name] = expr_type
            ident_type = typecheck(node.identifier, symtab)
            retVal = expr_type

        case ast.Branch():
            localSymtab = mkSym(symtab)
            t1 = typecheck(node.condition, localSymtab)
            if t1 != Bool():
                raise Exception(
                    f"Type error at {node.condition.location}, Branch condition must be of type Bool() not {t1}"
                )

            t2 = typecheck(node.then, symtab)
            t3 = (
                typecheck(node.otherwise, localSymtab)
                if node.otherwise is not None
                else t2
            )
            if t2 != t3:
                raise Exception(
                    f"Type error at {node.location}, branch types differ: then is {t2} and otherwise is {t3}"
                )
            retVal = t2

        case ast.Block():
            localSymtab = mkSym(symtab)
            finalType: Type = Unit()
            for expr in node.expressions:
                finalType = typecheck(expr, localSymtab) if expr is not None else Unit()
            retVal = finalType

        case ast.UnaryOp():
            expr_type = typecheck(node.parameter, symtab)
            if node.op == "-" and expr_type != Int:
                raise Exception(
                    f"Type Error at {node.location}, unary - expecting Int(), got {expr_type}"
                )
            elif node.op == "not" and expr_type != Bool:
                raise Exception(
                    f"Type Error at {node.location}, unary not expecting Bool(), got {expr_type}"
                )

            retVal = expr_type

        case ast.BinaryOp():

            op_type: Type | None = symtab.locals.get(node.op, None)
            parent = symtab.parent
            while op_type is None and parent is not None:
                op_type = parent.locals.get(node.op, None)
                parent = parent.parent

            left_type = typecheck(node.left, symtab)
            right_type = typecheck(node.right, symtab)

            if op_type is None or not isinstance(op_type, FunType):
                raise Exception(
                    f"Type Error at {node.location}: Could not find operator type in Symbolic table"
                )

            if [left_type, right_type] != op_type.arguments:
                raise Exception(
                    f"Type Error at {node.location}: Operator types don't match arguments, expected {op_type.arguments}, got {[left_type, right_type]}"
                )

            retVal = op_type.return_value

        case ast.Loop():
            cond_type = typecheck(node.condition, symtab)
            if cond_type != Bool:
                raise Exception(f"Type Error at {node.location}")

            typecheck(node.loop, symtab)

            retVal = Unit()

        case ast.FuncCall():
            arg_types: list[Type] = []
            for arg in node.arguments:
                arg_types.append(typecheck(arg, symtab))

            supposed_type: Type | None = symtab.locals.get(node.identifier.name, None)
            parent = symtab.parent
            while supposed_type is None and parent is not None:
                supposed_type = parent.locals.get(node.identifier.name, None)
                parent = parent.parent

            if supposed_type is None or not isinstance(supposed_type, FunType):
                raise Exception(
                    f"Type Error at {node.location}, could not find function type"
                )

            if supposed_type.arguments != arg_types:
                raise Exception(f"Type Error at {node.location}")

            retVal = supposed_type.return_value

    node.type = retVal

    # print(f"node was {node}, returning {retVal}")

    return retVal
