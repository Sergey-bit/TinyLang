from Parser import Parser


class ItemOfTable:
    INTEGER, STRING, FUNC, FLOAT = range(4)
    
    def __init__(self, name, type_):
        self.name = name
        self.type = type_
    
    def __cmp__(self, other: str):
        return self.name == other


class Table:
    def __init__(self):
        self.table = []
    
    def add(self, item: ItemOfTable):
        self.table.append(item)
    
    def search(self, name: str):
        for item in self.table:
            if item == name:
                return item.type
        return 


class Analyse:
    def __init__(self):
        self.table = Table()
        self.program = Parser().parse([])
