from Lexer import Lexer
from Parser import Node

[INTEGER, FLOAT, RVALUE, FL, NUM, FUNC, OPERAND, IF, WHILE, STRING, RET, NOT, AND, OR, BOOL, INTF, CALL,
 TRANSFORM] = range(18)
__data__ = {
    key: item for key, item in zip(
        [Lexer.INTEGER, Lexer.FLOAT, Lexer.RVALUE, Lexer.FL, Lexer.NUM, Lexer.FUNC,
         Lexer.OPERAND, Lexer.IF, Lexer.WHILE, Lexer.STRING, Lexer.RET, Lexer.NOT,
         Lexer.AND, Lexer.OR, Lexer.BOOL, Lexer.INTF],
        range(16))
}
__data__[Lexer.NUM] = INTEGER
__data__[Lexer.FL] = FLOAT
__data__[Lexer.BOOL] = INTEGER
del NUM, FL, BOOL


class Table(dict):
    args_i = {"args": 2, "kind": 0, "type": 1, "count": 3}
    relate = {}
    reserved = {
        'printf': [None, [('format', STRING)], 1], 'exit': [None, ('successful', INTEGER, 0)],
        'getch': [None, [], 0], 'scanf': [None, [('format', STRING), ('var', INTEGER, FLOAT), 1]],
        'abs': [INTEGER, [('var', INTEGER)], 0], 'tf': [INTEGER, [('a', INTEGER), ('b', INTEGER)], 0]
    }
    anonym = {}
    anonym_f = {}

    def add(self, name, venv, kind, args, type_, count_of_arg=None, block=None):
        if type_ == Lexer.INTF:
            self.anonym[name] = [name, venv, kind, args, type_, count_of_arg]
        self[(name, venv)] = [__data__[kind], __data__[type_], args, [], block]

    def get_select_data(self, name, venv, index):
        return self.get((name, venv), [-1, -1, -1, -1])[index]

    def get_all_data(self, name, venv):
        return self.get((name, venv), 0)

    def __str__(self):
        ret = ""
        for key, item in self.items():
            ret += f"name={key[0]} | kind={item[0]} | type={item[1]} | args={[el[0] for el in item[2]]}" + \
             "| count_of_args={item[3]}\n"
        return ret

