from Lexer import Lexer, Func
from sys import exit
from random import randint


class Block:

    def __init__(self):
        self.environment = []
        self.nodes = []
        self.id = randint(-1000000000000000000000000, 1000000000000000000000000000)

    def printf(self, prefix):
        return self.__str__(prefix)

    def eq__(self, other):
        return self.id == other.id

    def __str__(self, prefix=""):
        ret = ""
        for node in self.nodes:
            p1 =p2=p3=''
            if type(node.op1) in (str, int):
                p1 = node.op1
            elif type(node.op1) == list:
                for el in node.op1:
                    if type(el) in (str, int):
                        p1 = el
                    else:
                        p1 = el.printf()
            else:
                p1 = node.op1.printf()
            if type(node.op2) in (str, int):
                p2 = node.op2
            elif type(node.op2) == Block:
                p2 = "\n" + node.op2.printf(prefix + "\t")
            elif node.op2:
                p2 = node.op2.printf()
            else:
                p2 = ""
            if type(node.kind) in (int, str):
                p3 = node.kind
            else:
                p3 = node.kind.printf()
            ret += prefix + f"{p1} {p3} {p2}\n"
        return ret


class Node:
    TOKEN, CALL, TRANSFORM = range(3)

    """Invar - доп. информация, которую не может вычленить лексер. К примеру: вызов функции, блок кода"""
    def __init__(self, kind, invar=None, op1=None, op2=None):
        self.invar = invar
        self.kind = kind
        self.op1 = op1
        self.op2 = op2

    def printf(self):
        if type(self.op1) in (str, int):
            p1 = self.op1
        elif type(self.op1) == list:
            p1 = ""
            for el in self.op1:
                if type(el) in (str, int):
                    p1 += str(el)
                else:
                    p1 += str(el.printf())
                p1 += ", "
            if p1:
                p1 = p1[:-2]
        else:
            p1 = self.op1.printf()
        if type(self.op2) in (str, int):
            p25 = self.op2
        elif type(self.op2) == Block:
            p25 = self.op2.printf("\t")
        elif self.op2:
            p25 = self.op2.printf()
        else:
            p25 = None
        if type(self.kind) in (int, str):
            p3 = self.kind
            if type(self.kind) == str:
                p25, p1 = p1, p25
                p25 = f'({p25})'
                p1 = ''
        else:
            p3 = self.kind.printf()
            if self.kind.kind == 2:
                p25, p1 = p1, p25
                p25 = f'({p25})'
                p1 = ''
        return f"{p1} {p3} {p25}"


class Parser(object):
    lexer = Lexer()
    token = lexer.getToken()

    def parse(self, global_venv: list, end=Lexer.RFBR, separator=Lexer.SEPARATOR):
        block = Block()
        if global_venv:
            block.environment.extend(global_venv)
        starts = []
        args_stack = []
        operators_stack = []
        commas = 0
        while self.token.kind != end and self.token.kind != Lexer.EOF:
            if self.token.kind == separator:
                if operators_stack and operators_stack[0].kind == Lexer.RET:
                    starts.pop()
                    block.nodes.append(Node(operators_stack.pop(0), Node.TOKEN, self.build_node(0, 0, operators_stack, args_stack)))
                elif len(args_stack) != 0 or (len(args_stack) != 0 and len(operators_stack) != 0):
                    block.nodes.append(self.build_node(0, 0, operators_stack, args_stack))
                if starts:
                    self.error("Brackets are not enough")
            elif self.token.kind == Lexer.COMMA:
                commas += 1
                args_stack.append(self.build_node(starts[-1][0], starts[-1][1], operators_stack, args_stack))
                starts[-1] = [starts[-1][0], starts[-1][1] + 1]
            elif self.token.kind == Lexer.LBR:
                starts.append([len(operators_stack), len(args_stack)])
            elif self.token.kind == Lexer.LFBR:
                self.get_token()
                if not operators_stack:
                    block.nodes.append(self.parse(block.environment))
                elif starts and operators_stack[starts[-1][0] - 1].kind in (Lexer.IF, Lexer.WHILE):
                    args_stack.append(self.build_node(*starts.pop(), operators_stack, args_stack))
                    block.nodes.append(
                        Node(operators_stack.pop(0), Node.TOKEN, args_stack.pop(0), self.parse(block.environment))
                    )
                elif len(operators_stack) and operators_stack[-1].kind == Lexer.FUNC:
                    venv = []
                    tok = operators_stack.pop()
                    venv.extend(block.environment)
                    venv.extend(tok.value.args)
                    venv.append(tok)
                    tok.value.block = self.parse(venv)
                    block.environment.append(tok)
            elif self.token.kind == Lexer.RBR:
                if not starts:
                    self.error("Excess ')'")
                elif operators_stack[-1].kind == Lexer.FUNC:
                    starts.pop()
                elif operators_stack[starts[-1][0] - 1].kind == Lexer.RVALUE:
                    args = []
                    d = starts.pop()
                    data = starts.pop()
                    if data[1] < len(args_stack):
                        args.append(self.build_node(d[0], d[1], operators_stack, args_stack))
                        for _ in range(data[1], len(args_stack)):
                            if len(args_stack) == 0:
                                self.error("These args are not enough")
                            args.append(args_stack.pop())
                            commas -= 1
                    self.create_simple_node(Node(operators_stack.pop(), Node.CALL, args), starts, operators_stack, args_stack)
                else:
                    self.create_simple_node(
                        self.build_node(*starts.pop(), operators_stack, args_stack), starts,
                        operators_stack, args_stack
                    )
            elif self.token.kind in (Lexer.NUM, Lexer.FL, Lexer.BOOL, Lexer.INTF):
                p = self.token
                self.get_token()
                if self.token.kind == Lexer.LBR:
                    operators_stack.append(p)
                    continue
                elif self.token.kind == Lexer.RVALUE:
                    self.token.value.type = p.kind
                    tok = self.token
                    self.get_token()
                    if self.token.kind != Lexer.LBR:
                        if self.token.kind == separator:
                            block.environment.append(tok)
                        elif operators_stack and operators_stack[starts[-1][0] - 1].kind == Lexer.FUNC:
                            operators_stack[starts[-1][0] - 1].value.args.append(tok)
                            if self.token.kind == Lexer.RBR:
                                starts.pop()
                        else:
                            self.error("Expected ';'")
                    else:
                        tok.kind = Lexer.FUNC
                        tok.value = Func(tok.value)
                        operators_stack.append(tok)
                        starts.append([len(operators_stack), len(args_stack)])
                        self.get_token()
                        continue
            elif self.token.kind in (Lexer.OPERAND, Lexer.AND, Lexer.OR, Lexer.NOT):
                operators_stack.append(self.token)
            elif self.token.kind in (Lexer.IF, Lexer.WHILE, Lexer.RET):
                operators_stack.append(self.token)
                starts.append([len(operators_stack), len(args_stack)])
            elif self.token.kind in (Lexer.RVALUE, Lexer.INTEGER, Lexer.STRING, Lexer.FLOAT):
                tok = self.token
                self.get_token()
                if self.token.kind == Lexer.LBR:
                    operators_stack.append(tok)
                    starts.append([len(operators_stack), len(args_stack)])
                    starts.append([len(operators_stack), len(args_stack)])
                    self.get_token()
                else:
                    self.create_simple_node(tok, starts, operators_stack, args_stack)
                continue
            self.get_token()
        if len(args_stack) != 0 or len(operators_stack) != 0:
            self.error("separators are not enough")
        return block

    def get_token(self):
        self.token = self.lexer.getToken()

    def get_plus(self):
        return self.lexer.create_plus_token()

    def create_simple_node(self, tok, brackets, op_stack, args_stack):
        if not op_stack or (brackets and brackets[-1] == [len(op_stack), len(args_stack)]):
            args_stack.append(tok)
        elif op_stack[-1].kind in (Lexer.NOT, Lexer.FL, Lexer.NUM, Lexer.BOOL, Lexer.INTF):
            if op_stack[-1].kind == Lexer.NOT:
                args_stack.append(Node(op_stack.pop(), Node.TOKEN, tok))
            else:
                args_stack.append(Node(op_stack.pop().kind, Node.TRANSFORM, tok))
        elif op_stack[-1].kind not in (Lexer.IF, Lexer.WHILE, Lexer.RET, Lexer.OR, Lexer.RVALUE):
            if op_stack[-1].kind == Lexer.AND:
                args_stack.append(Node(op_stack.pop(), Node.TOKEN, tok, args_stack.pop()))
            elif op_stack[-1].value == '-':
                args_stack.append(Node(op_stack.pop(), Node.TOKEN, self.get_null(), tok))
                if brackets and len(op_stack[brackets[-1][0]:]) + 2 == len(args_stack[brackets[-1][1]:]):
                    op_stack.append(self.get_plus())
                elif not brackets and len(op_stack) + 2 == len(args_stack):
                    op_stack.append(self.get_plus())
            elif type(op_stack[-1].value) == str and op_stack[-1].value in "/*%" and (not brackets or brackets[-1][1] < len(args_stack)):
                args_stack.append(Node(op_stack.pop(), Node.TOKEN, args_stack.pop(), tok))
            else:
                args_stack.append(tok)
        else:
            args_stack.append(tok)

    def get_null(self):
        return self.lexer.create_nul_token()

    # o_i - index of start of operations
    # left - index of start of args
    def build_node(self, o_i: int, left: int, op_stack: list, args_stack: list) -> Node:
        if len(args_stack[left:]) == 1:
            return args_stack.pop(left)
        elif len(op_stack) == 0:
            self.error("syntax error")
        return Node(
            op_stack.pop(o_i), Node.TOKEN, args_stack.pop(left), self.build_node(o_i, left, op_stack, args_stack)
        )

    @staticmethod
    def error(msg: str):
        print("Parser error: " + msg)
        exit(1)
