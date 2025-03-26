import compiler.ir as ir
import dataclasses

from compiler.intrinsics import all_intrinsics, IntrinsicArgs


def get_all_ir_variables(instructions: list[ir.Instruction]) -> list[ir.IRVar]:
    result_list: list[ir.IRVar] = []
    result_set: set[ir.IRVar] = set()

    def add(v: ir.IRVar) -> None:
        if v not in result_set:
            result_list.append(v)
            result_set.add(v)

    for insn in instructions:
        for field in dataclasses.fields(insn):
            value = getattr(insn, field.name)
            if isinstance(value, ir.IRVar):
                add(value)
            elif isinstance(value, list):
                for v in value:
                    if isinstance(v, ir.IRVar):
                        add(v)
    return result_list


class Locals:
    _var_to_location: dict[ir.IRVar, str]
    _stack_used: int

    def __init__(self, variables: list[ir.IRVar]) -> None:
        self._var_to_location = {}
        self._stack_used = len(variables) * 8
        for i, var in enumerate(variables):
            self._var_to_location[var] = f"-{(i+1)*8}(%rbp)"

    def get_ref(self, v: ir.IRVar) -> str:
        return self._var_to_location[v]

    def stack_used(self) -> int:
        return self._stack_used


def generate_assembly(instructions: list[ir.Instruction]) -> str:
    lines = []

    def emit(line: str) -> None:
        lines.append(line)

    locals = Locals(variables=get_all_ir_variables(instructions))

    # ... Emit initial declarations and stack setup here ...

    emit(".extern print_int")
    emit(".extern print_bool")
    emit(".extern read_int")
    emit(".global main")
    emit(".type main, @function")
    emit("")
    emit(".section .text")
    emit("")
    emit("main:")
    emit("pushq %rbp")
    emit("movq %rsp, %rbp")
    emit(f"subq ${locals.stack_used()}, %rsp")

    for insn in instructions:
        emit("# " + str(insn))
        match insn:
            case ir.Label():
                emit("")
                # ".L" prefix marks the symbol as "private".
                # This makes GDB backtraces look nicer too:
                # https://stackoverflow.com/a/26065570/965979
                emit(f".L{insn.name}:")
            case ir.LoadIntConst():
                if -(2**31) <= insn.value < 2**31:
                    emit(f"movq ${insn.value}, {locals.get_ref(insn.dest)}")
                else:
                    # Due to a quirk of x86-64, we must use
                    # a different instruction for large integers.
                    # It can only write to a register,
                    # not a memory location, so we use %rax
                    # as a temporary.
                    emit(f"movabsq ${insn.value}, %rax")
                    emit(f"movq %rax, {locals.get_ref(insn.dest)}")
            case ir.Jump():
                emit(f"jmp .L{insn.label.name}")
            case ir.LoadBoolConst():
                emit(f"movq ${int(insn.value)}, {locals.get_ref(insn.dest)}")
            case ir.Copy():
                emit(f"movq {locals.get_ref(insn.source)}, %rax")
                emit(f"movq %rax, {locals.get_ref(insn.dest)}")
            case ir.Call():
                mIntrinsic = all_intrinsics.get(insn.fun.name, None)
                arg_refs = list(map(locals.get_ref, insn.args))
                dest_ref = locals.get_ref(insn.dest)
                if mIntrinsic is not None:
                    mIntrinsic(IntrinsicArgs(arg_refs, "%rdi", emit))
                    emit(f"movq %rdi, {dest_ref}")
                else:
                    registers = ["%rdi", "%rsi", "%rdx", "%rcx", "%r8", "%r9"]
                    for i, arg_ref in enumerate(arg_refs):
                        emit(f"movq {arg_ref}, {registers[i]}")
                    emit(f"callq {insn.fun.name}")

            case ir.CondJump():
                emit(f"cmpq $0, {locals.get_ref(insn.cond)}")
                emit(f"jne .L{insn.then_label.name}")
                emit(f"jmp .L{insn.else_label.name}")

    emit("movq %rbp, %rsp")
    emit("popq %rbp")
    emit("ret")
    return "\n".join(lines)
