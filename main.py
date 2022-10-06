FASMfrom Analyse import Analyse
from intermediateGenerator import IntermediateGenerator
from Parser import Parser, Func
from Generator import Generator
from os import system


def main():
    program = Parser().parse([])
    table = Analyse(program).table

    program = IntermediateGenerator(program, table).run()
    gen = Generator(program, table)

    gen.count(program)

    for f in program.environment:
        if type(f) == Func:
            gen.count(f.block)

    src = gen.run()
    with open(rf"{gen.header}", 'r') as file:
        asm = file.read().split("#%&=!")

    with open(r"program.asm", "w") as file:
        file.write(asm[0] + src + asm[1])

    system(r'FASM.EXE program.asm')


if __name__ == '__main__':
    main()
