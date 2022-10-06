from Parser import Block, Node
from Lexer import Token, Func, Data, Lexer
from Table import *


keys = {
    "==": lambda x, y: x == y,
    "!=": lambda x, y: x != y,
    ">=": lambda x, y: x >= y,
    "<=": lambda x, y: x <= y,
    ">": lambda x, y: x > y,
    "<": lambda x, y: x < y,
    '+': lambda x, y: x + y,
    '-': lambda x, y: x - y,
    '*': lambda x, y: x * y,
    '%': lambda x, y: x % y,
    '/': lambda x, y: x / y,
    '!': lambda x: not x,
    OR: lambda x, y: x or y,
    AND: lambda x, y: x and y
}


class IntermediateGenerator:
    def __init__(self, program, table):
        self.program = program
        self.table = table
        self.root = Block()
        self.tmp = "__tmp__0"
        self.called_f = []

    def run(self):
        self.walk_on_f()
        self.walks(self.program, self.root)
        return self.root

    def walks(self, block, n_b):
        self.table.relate[n_b] = block
        n_b.environment.extend([el.value for el in block.environment if type(el) == Token and el.kind != FUNC])
        for code in block.nodes:
            if type(code) == Block:
                self.walks(code, Block())
            else:
                self.cell_parse(code, n_b)

    def create_token_eq(self, node, op2):
        tok = Token()
        tok.kind, tok.value = OPERAND, "="
        name = self.tmp
        if type(op2) == Node and type(op2.op1) == Token and isinstance(op2.op1.value, int) and \
                (op2.kind.kind == NOT or (type(op2.op2) == Token and isinstance(op2.op2.value, int))):
            add_t = Token()
            if op2.kind.kind == NOT:
                op2 = keys["!"](op2.op1.value)
                add_t.kind = INTEGER
                add_t.value = op2
                op2 = add_t
            elif type(op2.op2) and op2.kind.value is None:
                op2 = keys[op2.kind.kind](op2.op1.value, op2.op2.value)
                add_t.kind = INTEGER
                add_t.value = op2
                op2 = add_t
            elif type(op2.op2):
                op2 = keys[op2.kind.value](op2.op1.value, op2.op2.value)
                t = type(op2)
                if t in (int, bool):
                    t = INTEGER
                else:
                    t = FLOAT
                add_t.kind = t
                add_t.value = op2
                op2 = add_t
        if type(node.kind) == Token and type(node.op1) == Token and type(node.op1.value) in (Func, Data) and \
                node.kind.value == "=":
            name = node.op1
        return Node(tok, Node.TOKEN, name, op2)

    def walk_on_f(self):
        for f in self.program.environment:
            if f.kind == FUNC:
                d = Data()
                d.name = f.value.name
                value = Func(d)
                d.type = self.table.get((f.value.name, self.program))
                value.args = self.table[(f.value.name, self.program)][2]
                value.block = Block()
                self.root.environment.append(value)
                self.walks(self.table[(f.value.name, self.program)][-1], value.block)

    def transform(self, node, n_b):
        if type(node.op1) == Token:
            tok = Token()
            tok.kind, tok.value = RVALUE, self.__relate_func__[(node.op2, node.kind)]
            n_b.nodes.append(self.create_token_eq(node, Node(tok, CALL, [node.op1])))
        else:
            self.cell_parse(node.op1, n_b)
            n_b.nodes.append(self.create_token_eq(
                node, Node(self.__relate_func__[(node.op2, node.kind)], CALL, f"__tmp__{int(self.tmp[7:]) - 1}")
            ))

    def call_func(self, node, n_b):
        args = []
        mode = 1
        for i in self.root.environment:
            if isinstance(i, Func) and i.name == node.kind.value.name:
                mode = 0
                break
        if mode:
            if self.table.reserved.get(node.kind.value.name):
                for arg in reversed(node.op1):
                    if type(arg) == Node:
                        self.cell_parse(arg, n_b)
                        args.append(f"__tmp__{int(self.tmp[7:]) - 1}")
                    else:
                        args.append(arg)
                if node.kind.value.name not in ('tf', 'abs'):
                    n_b.nodes.append(Node(node.kind.value.name, CALL, args))
                else:
                    n_b.nodes.append(self.create_token_eq(node, Node(node.kind.value.name, CALL, args)))
                return
        for arg in reversed(node.op1):
            if type(arg) == Node:
                self.cell_parse(arg, n_b)
                args.append(f"__tmp__{int(self.tmp[7:]) - 1}")
            else:
                args.append(arg)
        n_b.nodes.append(self.create_token_eq(node, Node(node.kind, CALL, args)))

    def token(self, node, n_b):
        if node.kind.value == '=' and (type(node.op2) == Token or
                                       (type(node.op2) == Node and node.op2.invar == Node.TOKEN and
                                        type(node.op2.op1) == Token and type(node.op2.op2) == Token)):
            n_b.nodes.append(node)
        elif node.kind.value in ("*=", "/=", "%=", "-=", "+="):
            if type(node.op2) == Node:
                self.cell_parse(node.op2, n_b)
                node.op2 = f"__tmp__{int(self.tmp[7:]) - 1}"
            n_b.nodes.append(node)

        elif node.kind.kind in (IF, WHILE):
            b = Block()
            if type(node.op1) == Node:
                if node.kind.kind == WHILE:
                    self.cell_parse(node.op1, b)
                    node.op1 = [len(b.nodes), f"__tmp__{int(self.tmp[7:]) - 1}"]
                else:
                    self.cell_parse(node.op1, n_b)
                    node.op1 = f"__tmp__{int(self.tmp[7:]) - 1}"
            else:
                if node.kind.kind == WHILE:
                    node.op1 = [len(b.nodes), node.op1.value]
            self.walks(node.op2, b)
            node.op2 = b
            n_b.nodes.append(node)
        elif node.kind.kind == RET:
            if type(node.op1) == Node:
                self.cell_parse(node.op1, n_b)
                name = f"__tmp__{int(self.tmp[7:]) - 1}"
            else:
                name = node.op1
            node.op1 = name
            n_b.nodes.append(node)
        elif node.kind.value == "=":
            name = node.op2
            if type(node.op2) == Node:
                self.cell_parse(node.op2, n_b)
                name = f"__tmp__{int(self.tmp[7:]) - 1}"
            n_b.nodes.append(self.create_token_eq(node, name))
        else:
            self.f(node, n_b)

    def f(self, node, n_b):
        if type(node.op1) == Node:
            self.cell_parse(node.op1, n_b)
            name1 = f"__tmp__{int(self.tmp[7:]) - 1}"
        else:
            name1 = node.op1
        if type(node.op2) == Node:
            self.cell_parse(node.op2, n_b)
            name2 = f"__tmp__{int(self.tmp[7:]) - 1}"
        else:
            name2 = node.op2
        if node.kind.value != '=':
            n_b.nodes.append(self.create_token_eq(node, Node(node.kind, Node.TOKEN, name1, name2)))
        else:
            n_b.nodes.append(Node(node.kind, Node.TOKEN, name1, name2))

    def cell_parse(self, node, n_b):
        if node.invar == TRANSFORM:
            self.transform(node, n_b)
        elif node.invar == CALL:
            self.call_func(node, n_b)
        else:
            self.token(node, n_b)
        self.tmp = f"__tmp__{int(self.tmp[7:]) + 1}"
