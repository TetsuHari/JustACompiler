from compiler import ast
from compiler.ir import *
from compiler.types import Bool, Int, Type, Unit, FunType
from compiler.tokenizer import L

root_types: dict[IRVar, Type] = {
    IRVar("or"): FunType([Bool(), Bool()], Bool()),
    IRVar("and"): FunType([Bool(), Bool()], Bool()),
    IRVar("+"): FunType([Int(), Int()], Int()),
    IRVar("-"): FunType([Int(), Int()], Int()),
    IRVar("/"): FunType([Int(), Int()], Int()),
    IRVar("*"): FunType([Int(), Int()], Int()),
    IRVar("<="): FunType([Int(), Int()], Bool()),
    IRVar(">="): FunType([Int(), Int()], Bool()),
    IRVar("<"): FunType([Int(), Int()], Bool()),
    IRVar(">"): FunType([Int(), Int()], Bool()),
    IRVar("print_int"): FunType([Int()], Unit()),
    IRVar("print_bool"): FunType([Bool()], Unit()),
    IRVar("read_int"): FunType([], Int()),
    IRVar("unary_not"): FunType([Bool()], Bool()),
    IRVar("unary_-"): FunType([Int()], Int()),
}


def generate_ir(
    # 'root_types' parameter should map all global names
    # like 'print_int' and '+' to their types.
    root_types: dict[IRVar, Type],
    root_expr: ast.Expression,
) -> list[Instruction]:
    var_types: dict[IRVar, Type] = root_types.copy()

    # 'var_unit' is used when an expression's type is 'Unit'.
    var_unit = IRVar("unit")
    var_types[var_unit] = Unit()

    labels: list[Label] = []

    def new_var(t: Type) -> IRVar:
        # Create a new unique IR variable and
        # add it to var_types
        var = IRVar("x" + str(len(var_types.keys())))
        var_types[var] = t
        return var

    def new_label() -> Label:
        label = Label(L, "L" + str(len(labels)))
        labels.append(label)
        return label

    # We collect the IR instructions that we generate
    # into this list.
    ins: list[Instruction] = []

    # This function visits an AST node,
    # appends IR instructions to 'ins',
    # and returns the IR variable where
    # the emitted IR instructions put the result.
    #
    # It uses a symbol table to map local variables
    # (which may be shadowed) to unique IR variables.
    # The symbol table will be updated in the same way as
    # in the interpreter and type checker.
    def visit(st: SymTab, expr: ast.Expression) -> IRVar:
        loc = expr.location

        match expr:
            case ast.Literal():
                # Create an IR variable to hold the value,
                # and emit the correct instruction to
                # load the constant value.
                match expr.value:
                    case bool():
                        var = new_var(Bool())
                        ins.append(LoadBoolConst(loc, expr.value, var))
                    case int():
                        var = new_var(Int())
                        ins.append(LoadIntConst(loc, expr.value, var))
                    case None:
                        var = var_unit
                    case _:
                        raise Exception(
                            f"{loc}: unsupported literal: {type(expr.value)}"
                        )

                # Return the variable that holds
                # the loaded value.
                return var

            case ast.Identifier():
                # Look up the IR variable that corresponds to
                # the source code variable.
                return st.require(expr.name)

            case ast.VarDeclaration():
                var = visit(st, expr.expression)
                st.locals[expr.identifier.name] = var
                return var

            case ast.BinaryOp():
                # Ask the symbol table to return the variable that refers
                # to the operator to call.
                var_op = st.require(expr.op)
                # Recursively emit instructions to calculate the operands.
                var_left = visit(st, expr.left)
                short_circuit = (
                    expr.op == "or" and expr.left == ast.Literal(L, True, type=Bool())
                ) or (
                    expr.op == "and" and expr.left == ast.Literal(L, False, type=Bool())
                )
                if not short_circuit:
                    var_right = visit(st, expr.right)
                    # Generate variable to hold the result.
                    var_result = new_var(expr.type)
                    # Emit a Call instruction that writes to that variable.
                    ins.append(Call(loc, var_op, [var_left, var_right], var_result))
                else:
                    var_result = var_left
                return var_result

            case ast.UnaryOp():
                var_op = st.require("unary_" + expr.op)
                var_arg = visit(st, expr.parameter)

                var_result = new_var(expr.type)
                ins.append(Call(loc, var_op, [var_arg], var_result))

                return var_result

            case ast.Branch():
                if expr.otherwise is None:
                    l_then = new_label()
                    l_end = new_label()

                    var_cond = visit(st, expr.condition)

                    ins.append(CondJump(loc, var_cond, l_then, l_end))

                    ins.append(l_then)

                    visit(st, expr.then)

                    ins.append(l_end)

                    return var_unit
                else:
                    l_then = new_label()
                    l_otherwise = new_label()
                    l_end = new_label()

                    var_cond = visit(st, expr.condition)

                    ins.append(CondJump(loc, var_cond, l_then, l_otherwise))

                    ins.append(l_then)

                    visit(st, expr.then)

                    ins.append(Jump(loc, l_end))

                    ins.append(l_otherwise)

                    visit(st, expr.otherwise)

                    ins.append(l_end)

                    return var_unit

            case ast.Loop():
                l_check_cond = new_label()
                l_start = new_label()
                l_end = new_label()

                var_cond = visit(st, expr.condition)

                ins.append(l_check_cond)

                ins.append(CondJump(loc, var_cond, l_start, l_end))

                ins.append(l_start)

                visit(st, expr.loop)

                ins.append(Jump(loc, l_check_cond))

                ins.append(l_end)

                return var_unit

            case ast.Block():
                final_var = var_unit
                for exp in expr.expressions:
                    print(f"looking at {exp}")
                    final_var = visit(st, exp) if exp is not None else var_unit
                    print(f"type is: {var_types[final_var]}")
                return final_var

            case ast.Assignment():
                target = st.require(expr.identifier.name)

                right_side = visit(st, expr.expression)

                ins.append(Copy(loc, right_side, target))

            case ast.FuncCall():
                var_fun = st.require(expr.identifier.name)
                arg_vars = []
                for arg in expr.arguments:
                    arg_vars.append(visit(st, arg))

                res_var = new_var(expr.type)

                ins.append(Call(loc, var_fun, arg_vars, res_var))

                return res_var

        return var_unit

        # Other AST node cases (see below)

    # Convert 'root_types' into a SymTab
    # that maps all available global names to
    # IR variables of the same name.
    # In the Assembly generator stage, we will give
    # definitions for these globals. For now,
    # they just need to exist.
    root_symtab = SymTab(parent=None, locals={})
    for v in root_types.keys():
        root_symtab.locals[v.name] = v

    # Start visiting the AST from the root.
    var_final_result = visit(root_symtab, root_expr)

    if var_types[var_final_result] == Int():
        ins.append(
            Call(L, root_symtab.require("print_int"), [var_final_result], var_unit)
        )
    elif var_types[var_final_result] == Bool():
        ins.append(
            Call(L, root_symtab.require("print_bool"), [var_final_result], var_unit)
        )
    return ins
