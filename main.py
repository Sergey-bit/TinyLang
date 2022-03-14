from Parser import Parser


def main() -> None:
    parser = Parser()
    data = parser.parse([])
    data.printf()


if __name__ == '__main__':
    main()
