# from sys import stdin


class Func:
    def __init__(self):
        self.name = ""
        self.args = []
        self.block = []
        self.ret = None


class Token(object):
    kind = None
    value = None

    def printf(self, prefix):
        print(prefix + f"Variable is {self.value}")


class Lexer(object):
    RVALUE, INTEGER, STRING, IF, WHILE, FUNC, OPERAND, LBR, FLOAT,\
    RBR, LSBR, RSBR, LFBR, RFBR, SEPARATOR, EOF, COMMA, RET, LIST = range(19)

    __data__ = {
        "if": IF, "while": WHILE, "func": FUNC,
        "(": LBR, ")": RBR, "[": LSBR, "]": RSBR, "{": LFBR, "}": RFBR,
        ";": SEPARATOR, ",": COMMA, "return": RET
    }

    char = " "
    file = open("test.txt", "r")

    def getchar(self):
        self.char = self.file.read(1)
        # self.char = stdin.read(1)

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
            dels = 10
            while self.char.isdigit():
                if tok.kind == Lexer.INTEGER:
                    tok.value = tok.value * 10 + int(self.char)
                else:
                    tok.value += int(self.char) / dels
                    dels *= 10
                self.getchar()
                if self.char == '.':
                    tok.kind = Lexer.FLOAT
                    self.getchar()
                    if not self.char.isdigit():
                        self.lex_error("There is not digit after dot")
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
        elif self.char in ";(){}[],":
            tok = Token()
            tok.kind = self.__data__[self.char]
            self.getchar()
            return tok
        elif self.char in ('"', "'"):
            line = ""
            self.getchar()
            while self.char not in ('"', "'") and self.char:
                line += self.char
                self.getchar()
            if not self.char:
                self.lex_error("Infinity string")
            self.getchar()
            tok = Token()
            tok.value = line
            tok.kind = self.STRING
            return tok
        elif self.char in "qwertyuiopasdfghjklzxcvbnm":
            line = ""
            while self.char in "qwertyuiopasdfghjklzxcvbnm":
                line += self.char
                self.getchar()
            tok = Token()
            if self.__data__.get(line, 0):
                tok.kind = self.__data__[line]
                if line == "func":
                    tok.value = Func()
            else:
                tok.kind = self.RVALUE
                tok.value = line
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

    def create_list_tok(self):
        tok = Token()
        tok.kind = self.LIST
        tok.value = []
        return tok
