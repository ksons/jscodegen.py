from enum import Enum, IntEnum


class Syntax(Enum):
    BlockStatement = "BlockStatement"
    Program = "Program"
    ExpressionStatement = "ExpressionStatement"

STATEMENTS = {Syntax.BlockStatement, Syntax.Program}


class Precedence(IntEnum):
    Sequence = 0
    Yield = 1
    Await = 1
    Assignment = 1
    Conditional = 2
    ArrowFunction = 2
    LogicalOR = 3
    LogicalAND = 4
    BitwiseOR = 5
    BitwiseXOR = 6
    BitwiseAND = 7
    Equality = 8
    Relational = 9
    BitwiseSHIFT = 10
    Additive = 11
    Multiplicative = 12
    Unary = 13
    Postfix = 14
    Call = 15
    New = 16
    TaggedTemplate = 17
    Member = 18
    Primary = 19


BinaryPrecedence = {
    '||': Precedence.LogicalOR,
    '&&': Precedence.LogicalAND,
    '|': Precedence.BitwiseOR,
    '^': Precedence.BitwiseXOR,
    '&': Precedence.BitwiseAND,
    '==': Precedence.Equality,
    '!=': Precedence.Equality,
    '===': Precedence.Equality,
    '!==': Precedence.Equality,
    'is': Precedence.Equality,
    'isnt': Precedence.Equality,
    '<': Precedence.Relational,
    '>': Precedence.Relational,
    '<=': Precedence.Relational,
    '>=': Precedence.Relational,
    'in': Precedence.Relational,
    'instanceof': Precedence.Relational,
    '<<': Precedence.BitwiseSHIFT,
    '>>': Precedence.BitwiseSHIFT,
    '>>>': Precedence.BitwiseSHIFT,
    '+': Precedence.Additive,
    '-': Precedence.Additive,
    '*': Precedence.Multiplicative,
    '%': Precedence.Multiplicative,
    '/': Precedence.Multiplicative
}


class CodeGenerator:

    @staticmethod
    def program(stmt):
        result = []
        for b in stmt['body']:
            result += generate_statement(b)
        return "".join(result)

    @staticmethod
    def expressionstatement(stmt):
        result = [generate_expression(stmt['expression'], Precedence.Sequence)]
        return " ".join(result)

    @staticmethod
    def binaryexpression(expr, precedence):
        operator = expr['operator']
        current_precedence = BinaryPrecedence[operator]
        result = [
            generate_expression(expr['left'], current_precedence),
            operator,
            generate_expression(expr['right'], current_precedence)
        ]
        return parenthesize(" ".join(result), current_precedence, precedence)

    @staticmethod
    def unaryexpression(expr, precedence):
        operator = expr['operator']
        result = operator + (" " if len(operator) > 2 else "") + generate_expression(expr['argument'], Precedence.Unary)
        return parenthesize(result, Precedence.Unary, precedence)

    @staticmethod
    def updateexpression(expr, precedence):
        operator = expr['operator']
        if expr["prefix"]:
            return parenthesize(operator + generate_expression(expr['argument'], Precedence.Unary), Precedence.Unary, precedence)
        else:
            return parenthesize(generate_expression(expr['argument'], Precedence.Postfix) + operator, Precedence.Postfix, precedence)

    @staticmethod
    def memberexpression(expr, precedence):
        result = [ generate_expression(expr['object'], Precedence.Call) ]
        if expr['computed']:
            result += ["[", generate_expression(expr['property'], Precedence.Sequence), "]"]
        else:
            result += [".", generate_expression(expr['property'], Precedence.Sequence)]

        return parenthesize("".join(result), Precedence.Member, precedence);

    @staticmethod
    def callexpression(expr, precedence):
        result = [ generate_expression(expr['callee'], Precedence.Call), '(' ]
        args = []
        for arg in expr['arguments']:
            args.append(generate_expression(arg, Precedence.Assignment))

        result.append(", ".join(args))
        result.append(')')
        return "".join(result)

    @staticmethod
    def identifier(expr, current_precedence):
        name = expr['name']
        # print(value)
        return name

    @staticmethod
    def literal(expr, current_precedence):
        value = expr['value']
        # print(value)
        return str(value)

    @staticmethod
    def variabledeclaration(stmt):
        kind = stmt["kind"]
        declarations = []
        for declaration in stmt['declarations']:
            declarations.append(generate_expression())
        return kind + " " + ", ".join(declarations) + ";"

def parenthesize(text, current, should):
    if current < should:
        return '(' + text + ')'
    return text


def is_statement(node):
    return Syntax(node["type"]) in STATEMENTS


def generate_expression(expr, precedence):
    node_type = expr["type"]
    attr = getattr(CodeGenerator, node_type.lower())
    # print(attr, precedence)
    return attr(expr, precedence)


def generate_statement(stmt):
    node_type = stmt["type"]
    attr = getattr(CodeGenerator, node_type.lower())
    # print(attr)
    return attr(stmt)


def generate(node, options=None):
    if is_statement(node):
        return generate_statement(node)
    else:
        print("Unknown", node["type"])
    pass