from enum import IntEnum
from syntax import Syntax, Statements

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
    space = " "

    def __init__(self, options):
        pass


    def program(self, stmt):
        result = []
        for b in stmt['body']:
            result += self.generate_statement(b)
        return "".join(result)

    def expressionstatement(self, stmt):
        result = self.generate_expression(stmt['expression'], Precedence.Sequence)
        return result + ";"

    def forstatement(self, stmt):
        result = "for ("
        if stmt['init']:
            result += self.generate_expression(stmt['init'], Precedence.Sequence)
        result += ";"

        if stmt['test']:
            result += self.space + self.generate_expression(stmt['test'], Precedence.Sequence)
        result += ";"

        if stmt['update']:
            result += self.space + self.generate_expression(stmt['update'], Precedence.Sequence)
        result += ")"

        result += self.space + self.generate_statement(stmt["body"])
        return result

    def assignmentexpression(self, expr, precedence):
        left = self.generate_expression(expr['left'], Precedence.Call)
        right = self.generate_expression(expr['right'], Precedence.Assignment)
        return self.parenthesize(left + self.space + expr['operator'] + self.space + right, Precedence.Assignment, precedence)

    def binaryexpression(self, expr, precedence):
        operator = expr['operator']
        current_precedence = BinaryPrecedence[operator]
        result = [
            self.generate_expression(expr['left'], current_precedence),
            self.space,
            operator,
            self.space,
            self.generate_expression(expr['right'], current_precedence)
        ]
        return self.parenthesize("".join(result), current_precedence, precedence)

    def unaryexpression(self, expr, precedence):
        operator = expr['operator']
        result = operator + (" " if len(operator) > 2 else "") + self.generate_expression(expr['argument'], Precedence.Unary)
        return self.parenthesize(result, Precedence.Unary, precedence)

    def updateexpression(self, expr, precedence):
        operator = expr['operator']
        if expr["prefix"]:
            return self.parenthesize(operator + self.generate_expression(expr['argument'], Precedence.Unary), Precedence.Unary, precedence)
        else:
            return self.parenthesize(self.generate_expression(expr['argument'], Precedence.Postfix) + operator, Precedence.Postfix, precedence)

    def newexpression(self, expr, precedence):
        result = 'new '
        result += self.generate_expression(expr['callee'], Precedence.New)
        result += "("
        result += ", ".join([self.generate_expression(x, Precedence.Assignment) for x in expr['arguments']])
        return result + ")"

    def conditionalexpression(self, expr, precedence):
        result = self.generate_expression(expr['test'], Precedence.LogicalOR)
        result += self.space + '?' + self.space
        result += self.generate_expression(expr['consequent'], Precedence.Assignment)
        result += self.space + ':' + self.space
        result += self.generate_expression(expr['alternate'], Precedence.Assignment)
        return result

    def breakstatement(self, stmt):
        if stmt['label']:
            return "break %s;" % stmt['label']
        else:
            return "break;"

    def ifstatement(self, stmt):
        result = "if" + self.space + "(%s)" % self.generate_expression(stmt['test'], Precedence.Sequence) + self.space
        result += self.generate_statement(stmt['consequent'])
        if stmt['alternate']:
            result += self.space + "else" + self.space
            result += self.generate_statement(stmt['alternate'])
        return result

    def whilestatement(self, stmt):
        result = "while" + self.space + "(%s)" % self.generate_expression(stmt['test'], Precedence.Sequence) + self.space
        result += self.generate_statement(stmt['body'])
        return result

    def arrayexpression(self, expr, precedence):
        elements = expr['elements']
        if not len(elements):
            return "[]"
        elements = [self.generate_expression(e, Precedence.Assignment) for e in elements]
        return "[%s]" % (","+self.space).join(elements)

    def memberexpression(self, expr, precedence):
        result = [self.generate_expression(expr['object'], Precedence.Call) ]
        if expr['computed']:
            result += ["[", self.generate_expression(expr['property'], Precedence.Sequence), "]"]
        else:
            result += [".", self.generate_expression(expr['property'], Precedence.Sequence)]

        return self.parenthesize("".join(result), Precedence.Member, precedence);

    def callexpression(self, expr, precedence):
        result = [self.generate_expression(expr['callee'], Precedence.Call), '(' ]
        args = []
        for arg in expr['arguments']:
            args.append(self.generate_expression(arg, Precedence.Assignment))

        result.append(", ".join(args))
        result.append(')')
        return "".join(result)

    def identifier(self, expr, precedence):
        return self.generate_identifier(expr)

    def literal(self, expr, precedence):
        value = expr['value']
        if isinstance(value, str):
            return "'%s'" % value
        return str(value)

    def variabledeclaration(self, stmt):
        kind = stmt["kind"]
        declarations = []
        for declaration in stmt['declarations']:
            declarations.append(self.generate_statement(declaration))
        return kind + " " + ", ".join(declarations) + ";"

    def variabledeclarator(self, stmt):
        result = self.generate_expression(stmt['id'], Precedence.Assignment)
        if stmt['init']:
            result += " = " + self.generate_expression(stmt['init'], Precedence.Assignment)
        return result

    def functionexpression(self, expr, precedence):
        result = ['function']
        if expr['id']:
            result.append(self.generate_identifier(expr['id']))

        result.append(self.generate_function_body(expr))
        result.append(self.space)
        result.append(self.generate_statement(expr["body"]))
        return "".join(result)

    def blockstatement(self, stmt):
        result = ["{"]
        body = stmt['body']
        for bstmt in body:
            result.append(self.generate_statement(bstmt))
        result.append("}")
        return "\n".join(result)

    def parenthesize(self, text, current, should):
        if current < should:
            return '(' + text + ')'
        return text

    def is_statement(self, node):
        return Syntax(node["type"]) in Statements


    def generate_function_params(self, node):
        params = []
        for param in node['params']:
            params.append(self.generate_identifier(param))
        return '(' + ", ".join(params) + ')'

    def generate_function_body(self, node):
        result = self.generate_function_params(node)
        return result

    def generate_expression(self, expr, precedence):
        node_type = expr["type"]
        attr = getattr(self, node_type.lower())
        return attr(expr, precedence)

    def generate_statement(self, stmt):
        node_type = stmt["type"]
        attr = getattr(self, node_type.lower())
        # print(attr)
        return attr(stmt)

    def generate_identifier(self, node):
        return str(node["name"])

    def generate(self, node):
        if self.is_statement(node):
            return self.generate_statement(node)
        else:
            print("Unknown", node["type"])
        pass


def generate(node, options=None):
    g = CodeGenerator(options)
    return g.generate(node)
