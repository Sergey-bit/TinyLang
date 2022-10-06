from Table import *
from random import choice
from Parser import Block, Node
from Lexer import Func, Data, Token

CLOSE, FREE = range(2)


class Generator:
    # Header file for FASM
    header = 'header.txt'
    op = {
        "-": "sub",
        "+": "add",
        "==": 'je',
        "!=": "jne",
        ">=": "jge",
        "<=": "jle",
        ">": "jg",
        "<": "jl"
    }

    def __init__(self, program, table):
        self.program = program
        self.table = table
        self.registers = {"ecx": FREE, "ebx": FREE, "edx": FREE}
        self.stack = []
        self.addresses = dict()
        self.related = {}
        self.section_data = []
        self.section_code = []
        self.tmp = {}
        self.reserved = 0
        self.prefix = ''
        self.ids = []

    def to_stack(self, item):
        self.section_code.append(f"push {self.get_item(item)}")
        self.stack.append(item)

    def get_item(self, item):
        if type(item) == str and '__tmp__' in item:
            ret = self.related.get(item)
        elif type(item) == Data:
            ret = " " + f'[{item.name}]'
        elif type(item) == str:
            return item
        elif type(item) in (int, str, float):
            ret = f"{item}"
        elif type(item.value) in (int, str, float):
            ret = f"{item.value}"
        else:
            ret = "dword " + f'[{item.value.name}]'
        return ret

    def check_tmp(self, name: str):
        if self.tmp.get(name):
            self.tmp[name] -= 1
            if self.tmp[name] == 0:
                self.to_free_register(self.related[name])
                del self.tmp[name], self.related[name]
                return 1
            return 0
        return -1

    def call(self, node):
        for reg, access in self.registers.items():
            if access == CLOSE:
                self.section_code.append(f"push " + reg)
        # self.section_code.append("pushf")

        if type(node.kind) == str:
            mode = 0
            if node.kind == 'scanf':
                data = ''
                for n in node.op1:
                    if isinstance(n, Token) and isinstance(n.value, Data):
                        if not self.prefix:
                            data += f', {n.value.name}'
                        else:
                            data += f', ghdsfetbglg'
                            mode = n.value.name
                    else:
                        data += f", {self.get_item(n)}"
                self.section_code.append(f"invoke {node.kind} {data}")
                if mode:
                    self.section_code.append('mov eax, [ghdsfetbglg]')
                    self.section_code.append(f'mov dword [{mode}], eax')
            else:
                if node.kind not in ("abs", "tf"):
                    self.section_code.append(f"invoke {node.kind}, {', '.join(map(self.get_item, node.op1))}")
                else:
                    self.section_code.append(f"ccall {node.kind}, {', '.join(map(self.get_item, node.op1))}")
            self.section_code.append(f"sub esp, {hex(4 * len(node.op1))}")
        elif self.table.anonym.get(node.kind.value.name):
            self.section_code.append(
                f"invoke {node.kind.value.name}, {', '.join(reversed(list(map(self.get_item, node.op1))))}")
        elif self.table.anonym_f.get(node.kind.value.name):
            indexes = self.table.anonym_f[node.kind.value.name]
            data = ''
            for i, name in enumerate(node.op1):
                if i in indexes:
                    data += f', {name.value.name}'
                else:
                    data += f', {self.get_item(name)}'
            self.section_code.append(f"ccall {node.kind.value.name}{data}")
        else:
            self.section_code.append(
                f"ccall {node.kind.value.name}, {', '.join(map(self.get_item, node.op1))}")
        # self.section_code.append("popf")
        for reg, access in reversed(self.registers.items()):
            if access == CLOSE:
                self.section_code.append(f"pop " + reg)
        for reg in node.op1:
            if type(reg) == str and "__tmp__" in reg:
                self.check_tmp(reg)

    def to_close_register(self):
        free = list(filter(lambda x: self.registers[x] == FREE, self.registers))
        if not free:
            print("Error: make the expression smaller")
            exit(1)
        ret = choice(free)
        self.stack.append(ret)
        self.section_code.append(f"push {ret}")
        self.registers[ret] = CLOSE
        return ret

    def to_free_register(self, reg):
        if self.stack[-1] == reg:
            self.section_code.append(f"pop {reg}")
            self.stack.pop()
        self.registers[reg] = FREE

    def in_order(self, tmp1, tmp2):
        if self.get_item(tmp1).isdigit():
            return tmp2, tmp1
        return tmp1, tmp2

    def eq(self, node):
        if node.kind.kind == OPERAND and len(node.kind.value) == 2 and node.kind.value != '==':
            if node.kind.value[0] in '+-':
                if isinstance(node.op2, str):
                    if self.related.get(node.op2) is None:
                        self.related[node.op2] = self.to_close_register()
                    name = self.get_item(node.op2)
                    self.section_code.append(f"{self.op[node.kind.value[0]]} {self.get_item(node.op1)}, {name}")
                    self.check_tmp(node.op2)
                else:
                    reg = self.to_close_register()
                    self.section_code.append(f"mov {reg}, {self.get_item(node.op2)}")
                    self.section_code.append(f"{self.op[node.kind.value[0]]} {self.get_item(node.op1)}, {reg}")
                    self.to_free_register(reg)
            elif node.kind.value[0] == '%':
                self.section_code.append("push eax")
                if self.related.get(node.op1) != 'edx':
                    self.section_code.append("push edx")
                self.section_code.append(f"mov eax, {self.get_item(node.op1)}")
                self.section_code.append(f"cdq")
                self.section_code.append(f"div {self.get_item(node.op2)}")
                if self.related.get(node.op1) != 'edx':
                    self.section_code.append(f"mov {self.get_item(node.op1)}, edx")
                    self.section_code.append(f"pop edx")
                self.section_code.append(f"pop eax")
                if isinstance(node.op1, str):
                    self.check_tmp(node.op1)
                if isinstance(node.op2, str):
                    self.check_tmp(node.op2)
            elif node.kind.value[0] == '/':
                if self.related.get(node.op1) != "edx":
                    self.section_code.append("push edx")
                self.section_code.append("push eax")
                self.section_code.append(f"mov eax, {self.get_item(node.op1)}")
                self.section_code.append(f"cdq")
                self.section_code.append(f"idiv {self.get_item(node.op2)}")
                self.section_code.append(f"mov {self.get_item(node.op1)}, eax")
                self.section_code.append(f"pop eax")
                if self.related.get(node.op1) != "edx":
                    self.section_code.append(f"pop edx")
                if isinstance(node.op1, str):
                    self.check_tmp(node.op1)
                if isinstance(node.op2, str):
                    self.check_tmp(node.op2)
            elif node.kind.value[0] == '*':
                if self.related.get(node.op1) != "edx":
                    self.section_code.append(f"push edx")
                self.section_code.append("push eax")
                self.section_code.append(f"mov eax, {self.get_item(node.op2)}")
                self.section_code.append(f"imul {self.get_item(node.op1)}")
                self.section_code.append(f"mov {self.get_item(node.op1)}, eax")
                self.section_code.append("pop eax")
                if self.related.get(node.op1) != "edx":
                    self.section_code.append(f"pop edx")
                if isinstance(node.op1, str):
                    self.check_tmp(node.op1)
                if isinstance(node.op2, str):
                    self.check_tmp(node.op2)
        elif isinstance(node.op2, str):
            if isinstance(node.op1, str) and self.related.get(node.op1) is None:
                self.related[node.op1] = self.to_close_register()
            self.section_code.append(f"mov {self.get_item(node.op1)}, {self.get_item(node.op2)}")
            if type(node.op1) == str:
                self.check_tmp(node.op1)
            self.check_tmp(node.op2)
        elif isinstance(node.op2.kind, Token) and node.op2.kind.value == '*':
            op1, op2 = self.in_order(node.op2.op1, node.op2.op2)
            if isinstance(node.op1, str) and self.related.get(node.op1) is None:
                self.related[node.op1] = self.to_close_register()
            if self.related.get(node.op1) != "edx":
                self.section_code.append("push edx")
            self.section_code.append("push eax")
            self.section_code.append(f"mov eax, {self.get_item(op2)}")
            self.section_code.append(f"imul {self.get_item(op1)}")
            self.section_code.append(f"mov {self.get_item(node.op1)}, eax")
            self.section_code.append("pop eax")
            if self.related.get(node.op1) != "edx":
                self.section_code.append("pop edx")
            if isinstance(node.op1, str):
                self.check_tmp(node.op1)
            if isinstance(node.op2.op1, str):
                self.check_tmp(node.op2.op1)
            if isinstance(node.op2.op2, str):
                self.check_tmp(node.op2.op2)
        elif isinstance(node.op2.kind, Token) and node.op2.kind.value == "/":
            op1, op2 = self.in_order(node.op2.op1, node.op2.op2)
            if isinstance(node.op1, str) and self.related.get(node.op1) is None:
                self.related[node.op1] = self.to_close_register()
            self.section_code.append("push eax")
            if self.related[node.op1] != "edx":
                self.section_code.append("push edx")
            self.section_code.append(f"mov eax, {self.get_item(op1)}")
            self.section_code.append(f"cdq")
            self.section_code.append(f"idiv {self.get_item(op2)}")
            self.section_code.append(f"mov {self.get_item(node.op1)}, eax")
            if self.related[node.op1] != "edx":
                self.section_code.append(f"pop edx")
            self.section_code.append(f"pop eax")
            if isinstance(node.op1, str):
                self.check_tmp(node.op1)
            if isinstance(node.op2.op1, str):
                self.check_tmp(node.op2.op1)
            if isinstance(node.op2.op2, str):
                self.check_tmp(node.op2.op2)
        elif isinstance(node.op2.kind, Token) and node.op2.kind.value == "%":
            op1, op2 = self.in_order(node.op2.op1, node.op2.op2)
            if isinstance(node.op1, str) and self.related.get(node.op1) is None:
                self.related[node.op1] = self.to_close_register()
            self.section_code.append("push eax")
            if self.related.get(node.op1) != 'edx':
                self.section_code.append("push edx")
            self.section_code.append(f"mov eax, {self.get_item(op1)}")
            self.section_code.append(f"cdq")
            self.section_code.append(f"div {self.get_item(op2)}")
            if self.related.get(node.op1) != 'edx':
                self.section_code.append(f"mov {self.get_item(node.op1)}, edx")
                self.section_code.append(f"pop edx")
            self.section_code.append(f"pop eax")
            if isinstance(node.op1, str):
                self.check_tmp(node.op1)
            if isinstance(node.op2.op1, str):
                self.check_tmp(node.op2.op1)
            if isinstance(node.op2.op2, str):
                self.check_tmp(node.op2.op2)
        elif isinstance(node.op2, Token):
            if isinstance(node.op1, str):
                reg = self.to_close_register()
                self.related[node.op1] = reg
                self.section_code.append(f"mov {reg}, {self.get_item(node.op2)}")
                self.check_tmp(node.op1)
            else:
                reg = self.to_close_register()
                self.section_code.append(f"mov {reg}, {self.get_item(node.op2)}")
                self.section_code.append(f"mov {self.get_item(node.op1)}, {reg}")
                self.to_free_register(reg)
        elif isinstance(node.op2, Node) and node.op2.invar == CALL:
            if self.related.get(node.op1) is None:
                self.related[node.op1] = self.to_close_register()
            self.call(node.op2)
            self.section_code.append(f"mov {self.get_item(node.op1)}, eax")
            self.check_tmp(node.op1)
        elif isinstance(node.op2, Node) and node.op2.kind.kind == NOT:
            if isinstance(node.op1, Token) and isinstance(node.op1.value, Data) and isinstance(node.op2.op1, Token):
                self.section_code.append(f"mov eax, {self.get_item(node.op2.op1)}")
                self.section_code.append(f"cmp eax, 0")
                self.section_code.append(f"jne @f")
                self.section_code.append("mov eax, -1")
                self.section_code.append(f"mov {self.get_item(node.op1)}, eax")
                self.section_code.append(f"jmp NOT_{self.reserved}")
                self.section_code.append(f"@@:")
                self.section_code.append(f"xor eax, eax")
                self.section_code.append(f"mov {self.get_item(node.op1)}, eax")
                self.section_code.append(f"NOT_{self.reserved}:")
            else:
                if isinstance(node.op1, str) and self.related.get(node.op1) is None:
                    self.related[node.op1] = self.to_close_register()
                self.section_code.append(f"mov {self.get_item(node.op1)}, {self.get_item(node.op2.op1)}")
                self.section_code.append(f"cmp {self.get_item(node.op1)}, 0")
                self.section_code.append(f"jne @f")
                self.section_code.append(f"mov {self.get_item(node.op1)}, -1")
                self.section_code.append(f"jmp NOT_{self.reserved}")
                self.section_code.append(f"@@:")
                self.section_code.append(f"mov {self.get_item(node.op1)}, 0")
                self.section_code.append(f"NOT_{self.reserved}:")
                if type(node.op1) == str:
                    self.check_tmp(node.op1)
                if type(node.op2.op1) == str:
                    self.check_tmp(node.op2.op1)
        elif isinstance(node.op2, Node) and node.op2.kind.kind == AND:
            if isinstance(node.op2.op1, str) or isinstance(node.op2.op2, str):
                if isinstance(node.op1, str) and self.related.get(node.op1) is None:
                    self.related[node.op1] = self.to_close_register()
                s = node.op2.op1
                t = node.op2.op2
                if isinstance(node.op2.op2, str):
                    s = node.op2.op2
                    t = node.op2.op1
                self.section_code.append(f"and {self.get_item(s)}, {self.get_item(t)}")
                self.section_code.append(f"mov {self.get_item(node.op1)}, {self.get_item(s)}")
                self.check_tmp(s)
                if isinstance(t, str):
                    self.check_tmp(t)
            elif isinstance(node.op1, str):
                if self.related.get(node.op1) is None:
                    self.related[node.op1] = self.to_close_register()
                reg = self.related[node.op1]
                self.section_code.append(f"mov {reg}, -1")
                self.section_code.append(f"and {reg}, {self.get_item(node.op2.op1)}")
                if isinstance(node.op2.op1, str):
                    self.check_tmp(node.op2.op1)
                self.section_code.append(f"and {reg}, {self.get_item(node.op2.op2)}")
                if isinstance(node.op2.op2, str):
                    self.check_tmp(node.op2.op2)
                self.check_tmp(node.op1)
            else:
                self.section_code.append(f"mov eax, {self.get_item(node.op2.op1)}")
                self.section_code.append(f"and eax, {self.get_item(node.op2.op2)}")
                self.section_code.append(f"mov {self.get_item(node.op1)}, eax")
        elif isinstance(node.op2, Node) and node.op2.kind.kind == OR:
            if isinstance(node.op2.op1, str) or isinstance(node.op2.op2, str):
                if isinstance(node.op1, str) and self.related.get(node.op1) is None:
                    self.related[node.op1] = self.to_close_register()
                s = node.op2.op1
                t = node.op2.op2
                if isinstance(node.op2.op2, str):
                    s = node.op2.op2
                    t = node.op2.op1
                self.section_code.append(f"or {self.get_item(s)}, {self.get_item(t)}")
                if isinstance(t, str):
                    self.check_tmp(t)
                self.section_code.append(f"mov {self.get_item(node.op1)}, {self.get_item(s)}")
                self.check_tmp(s)
                self.check_tmp(node.op1)
            elif isinstance(node.op1, str):
                if self.related.get(node.op1) is None:
                    self.related[node.op1] = self.to_close_register()
                reg = self.related[node.op1]
                self.section_code.append(f"xor {reg}, {reg}")
                self.section_code.append(f"or {reg}, {self.get_item(node.op2.op1)}")
                if isinstance(node.op2.op1, str):
                    self.check_tmp(node.op2.op1)
                self.section_code.append(f"or {reg}, {self.get_item(node.op2.op2)}")
                if isinstance(node.op2.op2, str):
                    self.check_tmp(node.op2.op2)
                self.check_tmp(node.op1)
            else:
                self.section_code.append(f"mov eax, {self.get_item(node.op2.op1)}")
                self.section_code.append(f"or eax, {self.get_item(node.op2.op2)}")
                self.section_code.append(f"mov {self.get_item(node.op1)}, eax")
        elif isinstance(node.op2, Node) and node.op2.kind.value in "+-":
            if isinstance(node.op1, str):
                if self.related.get(node.op1) is None:
                    self.related[node.op1] = self.to_close_register()
                res_reg = self.related[node.op1]
                self.section_code.append(f"mov {res_reg}, {self.get_item(node.op2.op1)}")
                self.section_code.append(f"{self.op[node.op2.kind.value]} {res_reg}, {self.get_item(node.op2.op2)}")
                self.check_tmp(node.op1)
                if isinstance(node.op2.op1, str):
                    self.check_tmp(node.op2.op1)
                if isinstance(node.op2.op2, str):
                    self.check_tmp(node.op2.op2)
            else:
                if isinstance(node.op2.op1, str):
                    self.section_code.append(
                        f"{self.op[node.op2.kind.value]} {self.get_item(node.op2.op1)}, {self.get_item(node.op2.op2)}")
                    self.section_code.append(f'mov {self.get_item(node.op1)}, {self.get_item(node.op2.op1)}')
                    self.check_tmp(node.op2.op1)
                    if isinstance(node.op2.op2, str):
                        self.check_tmp(node.op2.op2)
                else:
                    inter_reg = self.to_close_register()
                    self.section_code.append(f"mov {inter_reg}, {self.get_item(node.op2.op1)}")
                    self.section_code.append(
                        f"{self.op[node.op2.kind.value]} {inter_reg}, {self.get_item(node.op2.op2)}")
                    self.section_code.append(f"mov {self.get_item(node.op1)}, {inter_reg}")
                    self.to_free_register(inter_reg)
        elif isinstance(node.op2, Node) and node.op2.kind.value in (">", "<", "!=", ">=", "<=", "=="):
            if self.related.get(node.op1) is None:
                self.related[node.op1] = self.to_close_register()
            reg = self.related[node.op1]
            if isinstance(node.op2.op1, Token) and isinstance(node.op2.op2, Token):
                self.section_code.append(f"mov {reg}, {self.get_item(node.op2.op1)}")
                self.section_code.append(f"cmp {reg}, {self.get_item(node.op2.op2)}")
            else:
                tmp1 = node.op2.op1
                tmp2 = node.op2.op2
                if isinstance(node.op2.op2, str):
                    tmp1 = node.op2.op2
                    tmp2 = node.op2.op1
                self.section_code.append(f"cmp {self.get_item(tmp1)}, {self.get_item(tmp2)}")
            self.section_code.append(f"{self.op[node.op2.kind.value]} @f")
            self.section_code.append(f"xor {reg}, {reg}")
            self.section_code.append(f"jmp {self.prefix}after{self.reserved}")
            self.section_code.append("@@:")
            self.section_code.append(f"mov {reg}, -1")
            self.section_code.append(f"{self.prefix}after{self.reserved}:")
            self.reserved += 1
            self.check_tmp(node.op1)
            if isinstance(node.op2.op1, str):
                self.check_tmp(node.op2.op1)
            if isinstance(node.op2.op2, str):
                self.check_tmp(node.op2.op2)

    def grown_reserved(self):
        self.reserved += 1
        return self.reserved - 1

    def analyze(self, node):
        if node.invar == CALL:
            self.call(node)
        elif node.kind.kind == IF:
            reserved = self.grown_reserved()
            if isinstance(node.op1, str):
                self.section_code.append(f"cmp {self.get_item(node.op1)}, {0}")
                self.check_tmp(node.op1)
            else:
                reg = self.to_close_register()
                self.section_code.append(f"xor {reg}, {reg}")
                self.section_code.append(f"cmp {self.get_item(node.op1)}, {reg}")
                self.to_free_register(reg)
            self.section_code.append(f"je {self.prefix}if{reserved}")
            self.walk(node.op2)
            self.check_tmp(node.op1)
            self.section_code.append(f"{self.prefix}if{reserved}:")
        elif node.kind.kind == WHILE:
            reserved = self.grown_reserved()
            length, reg = node.op1

            self.section_code.append(f"{self.prefix}while{reserved}:")
            if type(reg) == str:
                self.tmp[reg] += 1
                for el in node.op2.nodes[:length]:
                    self.analyze(el)
                self.section_code.append(f"cmp {self.get_item(reg)}, 0")
                self.check_tmp(reg)
                self.section_code.append(f"je @f")
                for el in node.op2.nodes[length:]:
                    self.analyze(el)
                self.section_code.append(f"jmp {self.prefix}while{reserved}")
                self.section_code.append("@@:")
            else:
                regi = self.to_close_register()
                self.section_code.append(f"xor {regi}, {regi}")
                self.section_code.append(f"cmp {regi}, {self.get_item(reg)}")
                self.to_free_register(regi)
                self.section_code.append(f"je @f")
                self.walk(node.op2)
                self.section_code.append(f"jmp {self.prefix}while{reserved}")
                self.section_code.append("@@:")
                self.check_tmp(reg)
        elif node.kind.kind == RET:
            self.section_code.append(f"mov eax, {self.get_item(node.op1)}")
            if type(node.op1) == str:
                self.check_tmp(node.op1)
            for reg in self.registers.keys():
                if self.registers[reg] == CLOSE:
                    self.registers[reg] = FREE
                    self.section_code.append(f"pop {reg}")
            self.section_code.append(f"jmp .return")
        elif node.kind.kind == OPERAND:
            self.eq(node)

    def add(self, n):
        if self.tmp.get(n) is None:
            self.tmp[n] = 0
        self.tmp[n] += 1

    def inter(self, node):
        if type(node.op1) == str:
            self.add(node.op1)
        if type(node.op2) == str:
            self.add(node.op2)

    def count(self, block):
        self.ids.append(block.id)
        for node in block.nodes:
            if isinstance(node.kind, str) and node.invar == CALL:
                for i, item in enumerate(node.op1):
                    if type(item) == str:
                        self.add(item)
                    elif item.kind == STRING:
                        if node.kind == 'scanf':
                            self.section_data.append(f"__str__{self.reserved} db  '{item.value}', 0")
                        else:
                            self.section_data.append(f"__str__{self.reserved} db  '{item.value}', 10, 0")
                        node.op1[i] = f"__str__{self.reserved}"
                        self.reserved += 1
                continue
            self.inter(node)
            if type(node.op2) == Node:
                self.inter(node.op2)
                if node.op2.invar == CALL:
                    for arg in node.op2.op1:
                        if type(arg) == str:
                            self.add(arg)
            elif node.kind.kind in (IF, WHILE):
                if node.kind.kind == WHILE:
                    pass
                self.count(node.op2)

    def walk(self, block):
        for node in block.nodes:
            self.analyze(node)

    def run(self):
        self.walk(self.program)
        self.section_code.append("invoke exit, 0")
        vars = []
        self.section_data.append("ghdsfetbglg dd ?")
        for item in self.program.environment:
            if isinstance(item, Data):
                vars.append(item.name)
                k = f"{item.name} dd ?"
                if k not in self.section_data:
                    self.section_data.append(k)
            else:
                self.section_code.append(f"proc {item.name} c")
                self.prefix = '.'
                if item.args:
                    if len(item.args) - 1:
                        self.section_code[-1] += ', ' + ', '.join(map(lambda x: x[0], item.args))
                    else:
                        self.section_code[-1] += ', ' + item.args[0][0]
                p = 0
                for ins_item in item.block.environment:
                    if isinstance(ins_item, Data):
                        mode = 1
                        for a in item.args:
                            if a[0] == ins_item.name:
                                mode = 0
                        if ins_item.name in vars:
                            mode = 0
                        if mode:
                            if p == 0:
                                self.section_code.append('locals')
                                p = 1
                            self.section_code.append(f"{ins_item.name} dd ?")
                if p == 1:
                    self.section_code.append('endl')
                for register in self.registers.keys():
                    self.registers[register] = FREE
                self.walk(item.block)
                self.section_code.append(".return:")
                self.section_code.append("ret")
                self.section_code.append('endp')
        return self.merger()

    def merger(self):
        data = ''
        if self.section_data:
            data = "section '.data' data readable writeable\n"
            for var in self.section_data:
                data += '\t' + var + '\n'
        data += "section '.code' code readable executable\n\tstart:\n"
        prefix = ''
        for command in self.section_code:
            if command.split()[0] == 'proc':
                prefix += '\t'
                data += '\t' + command + '\n'
                continue
            elif command == 'endp':
                prefix = ''
                data += '\t' + command + '\n'
                continue
            elif command[-1] != ":" and command != 'locals' and command != 'endl':
                data += '\t'
            data += prefix + '\t' + command + '\n'
        return data
