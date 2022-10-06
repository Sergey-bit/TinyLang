# from sys import stdin
from sys import exit


class Data:
    def __init__(self):
        self.name = ""
        self.type = None

    def printf(self):
        return self.name


class Func:
    def __init__(self, data):
        self.name = data.name
        self.type = data.type
        self.block = []
        self.args = []

    def printf(self):
        return f"{self.type} {self.name}( {self.args} )"


class Token(object):
    def __init__(self):
        self.kind = None
        self.value = None

    def printf(self):
        if self.value:
            out = self.value
            if type(self.value) in (Data, Func):
                out = self.value.printf()
        else:
            out = self.kind
        return out


class Lexer(object):
    RVALUE, INTEGER, STRING, IF, WHILE, FUNC, OPERAND, LBR, FLOAT,\
    RBR, LSBR, RSBR, LFBR, RFBR, SEPARATOR, EOF, COMMA, RET, NUM, FL, NOT, OR, AND, BOOL, INTF = range(25)

    __data__ = {
        "if": IF, "while": WHILE,
        "(": LBR, ")": RBR, "[": LSBR, "]": RSBR, "{": LFBR, "}": RFBR,
        ";": SEPARATOR, ",": COMMA, "return": RET, "int": NUM,
        "!": NOT, "|": OR, "&": AND, "bool": BOOL, 'intfunc': INTF
    }

    char = " "
    file = open("test.txt", "r")

    def getchar(self):
        self.char = self.file.read(1)

    def getToken(self):
        if self.char == "":
            tok = Token()
            tok.kind = self.EOF
            self.file.close()
            return tok
        elif self.char.isspace():
            self.getchar()
            return self.getToken()
        elif self.char.isdigit():
            tok = Token()
            tok.kind = self.INTEGER
            tok.value = 0
            while self.char.isdigit():
                tok.value = tok.value * 10 + int(self.char)
                self.getchar()
            return tok
        elif self.char in "-+*=/%><":
            tok = Token()
            tok.value = self.char
            tok.kind = self.OPERAND
            self.getchar()
            if self.char == "=":
                tok.value += "="
                self.getchar()
            return tok
        elif self.char in ";(){}[],!|&":
            tok = Token()
            tok.kind = self.__data__[self.char]
            t = self.char
            self.getchar()
            if self.char == "=" and t == "!":
                tok.kind = self.OPERAND
                tok.value = "!="
                self.getchar()
            return tok
        elif self.char in ('"', "'"):
            line = ""
            p = self.char
            self.getchar()
            while self.char != p and self.char:
                line += self.char
                self.getchar()
            if not self.char:
                self.lex_error("Infinity string")
            self.getchar()
            tok = Token()
            tok.value = line
            tok.kind = self.STRING
            return tok
        elif self.char.lower() in "qwertyuiopasdfghjklzxcvbnm_":
            line = ""
            while self.char.lower() in "qwertyuiopasdfghjklzxcvbnm1234567890_":
                line += self.char
                self.getchar()
            tok = Token()
            if line in ("false", 'true'):
                tok.kind = self.INTEGER
                tok.value = 0 if line == 'false' else 1
            elif self.__data__.get(line, 0):
                tok.kind = self.__data__[line]
            else:
                tok.kind = self.RVALUE
                tok.value = Data()
                tok.value.name = line
            return tok
        else:
            self.lex_error("Unknown symbol '{}'".format(self.char))

    @staticmethod
    def lex_error(msg):
        print("Lexer error: " + msg)
        exit(1)

    def create_plus_token(self):
        tok = Token()
        tok.kind = self.OPERAND
        tok.value = '+'
        return tok

    def printf(self, lex):
        for d in self.__data__:
            if self.__data__[d] == lex:
                return d

    def create_nul_token(self):
        tok = Token()
        tok.kind = self.INTEGER
        tok.value = 0
        return tok
