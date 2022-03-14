from Lexer import Lexer


class Block:

    def __init__(self):
        self.environment = []
        self.nodes = []

    def printf(self, prefix=""):
        if prefix:
            prefix += "\t"
        for n in self.nodes:
            n.printf(prefix)


class Node:
    TOKEN, CALL = range(2)

    """Invar - доп. информация, которую не может вычленить лексер. К примеру: вызов функции, блок кода"""
    def __init__(self, kind, invar=None, op1=None, op2=None):
        self.invar = invar
        self.kind = kind
        self.op1 = op1
        self.op2 = op2

    def printf(self, prefix):
        if self.kind.value is None:
            print(prefix + f"Op '{Lexer().printf(self.kind.kind)}':")
            self.op1.printf(prefix + '\t')
            print(prefix + "\t" + "Block:")
        else:
            if self.invar == self.CALL:
                print(prefix + f"Call {self.kind.value}({', '.join(map(str, [op.value for op in self.op1]))}):")
            else:
                print(prefix + f"Op '{self.kind.value}':")
                self.op1.printf(prefix + '\t')
        if self.op2:
            self.op2.printf(prefix + '\t')


class Parser:
    lexer = Lexer()
    token = lexer.getToken()

    def parse(self, global_venv: list, end=Lexer.RFBR, separator=Lexer.SEPARATOR):
        block = Block()
        if global_venv:
            block.environment.extend(global_venv)
        starts = []
        args_stack = []
        operators_stack = []
        while self.token.kind != end and self.token.kind != Lexer.EOF:
            if self.token.kind == separator:
                if starts:
                    self.error("Brackets are not enough")
                block.nodes.append(self.build_node(0, 0, operators_stack, args_stack))
            elif self.token.kind == Lexer.LBR:
                starts.append((len(operators_stack), len(args_stack)))
            elif self.token.kind == Lexer.FUNC:
                block.environment.append(self.declare(self.token, block.environment))
            elif self.token.kind == Lexer.LFBR:
                self.get_token()
                if not operators_stack:
                    block.nodes.append(self.parse(block.environment))
                else:
                    block.nodes.append(
                        Node(operators_stack.pop(0), Node.TOKEN, op1=args_stack.pop(0), op2=self.parse(block.environment))
                    )
            elif self.token.kind == Lexer.RBR:
                if not starts:
                    self.error("Excess ')'")
                self.create_simple_node(
                    self.build_node(*starts.pop(), operators_stack, args_stack), starts,
                    operators_stack, args_stack
                )
            elif self.token.kind in (Lexer.OPERAND, Lexer.IF, Lexer.WHILE):
                if self.token.value == "=":
                    block.environment.append(args_stack[-1])
                operators_stack.append(self.token)
            elif self.token.kind in (Lexer.RVALUE, Lexer.INTEGER, Lexer.STRING, Lexer.FLOAT):
                tok = self.token
                self.get_token()
                if self.token.kind == Lexer.LBR:
                    self.get_token()
                    node = Node(tok, Node.CALL, self.parse([], Lexer.RBR, Lexer.COMMA).nodes)
                    args_stack.append(node)
                    self.get_token()
                else:
                    self.create_simple_node(tok, starts, operators_stack, args_stack)
                continue
            self.get_token()
        return block

    def get_token(self):
        self.token = self.lexer.getToken()

    def declare(self, tok, venv):
        self.get_token()
        if self.token.kind != Lexer.RVALUE:
            self.error("Excess name of function")
        tok.value.name = self.token.value
        self.get_token()
        if self.token.kind != Lexer.LBR:
            self.error("Excess name of function")
        self.get_token()
        args = self.parse([], Lexer.RBR, Lexer.COMMA).nodes
        if args:
            tok.value.args.extend(args)
        self.get_token()
        if self.token.kind != Lexer.LFBR:
            self.error("Excess body of function")
        self.get_token()
        venv_ = []
        venv_.extend(args)
        venv_.extend(venv)
        tok.value.block = self.parse(venv_)
        return tok

    def get_plus(self):
        return self.lexer.create_plus_token()

    def create_simple_node(self, tok, brackets, op_stack, args_stack):
        if len(op_stack) and op_stack[-1].kind not in (Lexer.IF, Lexer.WHILE):
            if op_stack[-1].value == '-':
                args_stack.append(Node(op_stack.pop(), Node.TOKEN, self.get_null(), tok))
                op_stack.append(self.get_plus())
            elif op_stack[-1].value in "/*%" and (not brackets or brackets[-1][0] < len(op_stack)):
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
        return Node(op_stack.pop(o_i), Node.TOKEN, args_stack.pop(left), self.build_node(o_i, left, op_stack, args_stack))

    @staticmethod
    def error(msg: str):
        print("Parser error: " + msg)
        exit(1)
