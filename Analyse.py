from Parser import Block, Node
from Table import __data__
from Table import *
from sys import exit


class Analyse:
    def __init__(self, program: Block):
        self.program = program
        self.table = Table()
        self.top_up_table(self.program)
        self.analyse(self.program)

    def top_up_table(self, block, count=0):
        for item in block.environment:
            args = []
            if __data__[item.kind] == FUNC:
                if count != 1:
                    self.top_up_table(item.value.block, 1)
                    self.analyse(item.value.block)
                args = [(el.value.name, item.value.block) for el in item.value.args]
                self.table.add(item.value.name, block, item.kind, args, item.value.type, len(args), item.value.block)
            else:
                self.table.add(item.value.name, block, RVALUE, args, item.value.type, len(args))

    def analyse(self, program, parent=None):
        if parent is None:
            parent = program
        for block in program.nodes:
            if type(Block) == Block:
                self.top_up_table(block)
                self.analyse(block)
            else:
                self.node_analyse(block, parent)

    def node_analyse(self, node, venv):
        if type(node) == Node:
            match node.invar:
                case Node.CALL:
                    node.kind.kind = __data__[node.kind.kind]
                    node.invar = CALL
                    if self.table.reserved.get(node.kind.value.name):
                        for i in range(len(node.op1)):
                            self.node_analyse(node.op1[i], venv)
                        return self.table.reserved.get(node.kind.value.name)[0]
                    ret = self.table.get_select_data(node.kind.value.name, venv, self.table.args_i["type"])
                    args = self.table.get_select_data(node.kind.value.name, venv, self.table.args_i["args"])
                    if ret == -1:
                        self.error(f"unknown function '{node.kind.value.name}'")
                    elif len(args) != len(node.op1) and ret != INTF:
                        self.error(f"expected {len(args)} args, but got {len(node.op1)} args")
                    for i in range(len(node.op1)):
                        if ret == INTF:
                            self.node_analyse(node.op1[i], venv)
                            continue
                        tm = self.node_analyse(node.op1[i], venv)
                        tmp = self.table[args[i]][self.table.args_i["type"]]
                        if tm in (INTEGER, STRING):
                            if tmp == STRING and tmp != tm:
                                self.error("unacceptable type")
                            elif tmp == INTF:
                                if self.table.anonym_f.get(node.kind.value.name):
                                    self.table.anonym_f[node.kind.value.name].append(i)
                                else:
                                    self.table.anonym_f[node.kind.value.name] = [i]
                        else:
                            self.error("unacceptable type")
                    if ret == INTF:
                        return INTEGER
                    return ret
                case Node.TOKEN:
                    node.kind.kind = __data__[node.kind.kind]
                    if node.kind.kind in (IF, WHILE):
                        self.node_analyse(node.op1, venv)
                        self.analyse(node.op2, venv)
                        return
                    elif node.kind.kind == RET:
                        ret = self.node_analyse(node.op1, venv)
                        t = self.table.get_select_data(venv.environment[0].value.name, venv, self.table.args_i["type"])
                        if ret != t:
                            self.error(f"expected type '{t}', go type '{ret}'")
                    elif node.kind.kind in (OR, AND):
                        p = self.node_analyse(node.op1, venv)
                        k = self.node_analyse(node.op2, venv)
                        if p == STRING or k == STRING or p is None or k is None:
                            self.error("unexpected string")
                        return INTEGER
                    elif node.kind.kind == NOT:
                        p = self.node_analyse(node.op1, venv)
                        if p == STRING or p is None:
                            self.error("unexpected string")
                        return INTEGER
                    match node.kind.value:
                        case "=":
                            if node.op1.kind != Lexer.RVALUE:
                                self.error("left of assignment must be a rvalue")
                            must_t = self.table.get_select_data(node.op1.value.name, venv, self.table.args_i["type"])
                            if must_t == -1:
                                self.error(f"Unknown variable '{node.op1.value.name}'")
                            k = self.node_analyse(node.op2, venv)
                            if k != must_t:
                                self.error("unacceptable type ")
                        case "%":
                            t1 = self.node_analyse(node.op1, venv)
                            t2 = self.node_analyse(node.op2, venv)
                            if not (t1 == t2 and t1 == INTEGER):
                                self.error("unacceptable type")
                            return INTEGER
                        case "-" | "+" | "*":
                            t1 = self.node_analyse(node.op1, venv)
                            t2 = self.node_analyse(node.op2, venv)
                            if t1 == STRING or t2 == STRING or t1 is None or t2 is None:
                                self.error("unacceptable type")
                            return INTEGER
                        case "/":
                            t1 = self.node_analyse(node.op1, venv)
                            t2 = self.node_analyse(node.op2, venv)
                            if t1 == STRING or t2 == STRING or t1 is None or t2 is None:
                                self.error("unacceptable type")
                            return INTEGER
                        case "%=":
                            if node.op1.kind != Lexer.RVALUE:
                                self.error("left of assignment must be a rvalue")
                            must_t = self.table.get_select_data(node.op1.value.name, venv, self.table.args_i["type"])
                            if must_t == -1:
                                self.error(f"Unknown variable '{node.op1.value.name}'")
                            if must_t != INTEGER:
                                self.error("unacceptable type")
                            p = self.node_analyse(node.op2, venv)
                            if must_t != p or p is None:
                                self.error("unacceptable type")
                        case "/=" | "-=" | "*=" | "+=":
                            if node.op1.kind != Lexer.RVALUE:
                                self.error("left of assignment must be a rvalue")
                            k = self.node_analyse(node.op2, venv)
                            if k == STRING:
                                self.error("unacceptable type")
                            must_t = self.table.get_select_data(node.op1.value.name, venv, self.table.args_i["type"])
                            if must_t == -1:
                                self.error(f"Unknown variable '{node.op1.value.name}'")
                        case ">=" | "<=" | ">" | "<" | "!=" | "==":
                            k = self.node_analyse(node.op1, venv)
                            p = self.node_analyse(node.op2, venv)
                            if STRING in (k, p) or None in (k, p):
                                self.error("unacceptable type")
                            return INTEGER
        else:
            node.kind = __data__[node.kind]
            if node.kind == RVALUE:
                ret = self.table.get_select_data(node.value.name, venv, self.table.args_i["type"])
                node.value.type = ret
                if ret == -1:
                    self.error(f"Unknown variable '{node.value.name}'")
                return ret
            return node.kind

    @staticmethod
    def error(msg):
        print(f"Error: {msg}")
        exit(1)
