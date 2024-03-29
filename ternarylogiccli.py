#!/usr/bin/env python3

import sys
import argparse
import re
from tokenize import tokenize, untokenize, TokenInfo, \
                     NAME, OP, ENCODING, ENDMARKER, NEWLINE, ERRORTOKEN
from itertools import product
from io import BytesIO


def main():
    args = parse_args()

    try:
        fun = parse_expression(args.expr, args.vars)
    except InvalidExpression as e:
        print(e)
        return 1

    def print_table():
        la = len(str(fun.var_a)) + 2
        lb = len(str(fun.var_b)) + 2
        lc = len(str(fun.var_c)) + 2
        le = len(str(fun.expression)) + 1

        def line(n):
            return '-' * n

        print(f" # | {fun.var_a} | {fun.var_b} | {fun.var_c} | {fun.expression}")
        print( "---+%s+%s+%s+-%s" % (line(la), line(lb), line(lc), line(le)))
        value = 0
        for i, (a, b, c, result) in enumerate(fun.table):
            print(f" {i} |{a:^{la}}|{b:^{lb}}|{c:^{lc}}| {result:^{le}}")
            if result:
                value |= (1 << i)

    def print_program():
        print(f"C/C++  : _mm512_ternarylogic_epi32({fun.var_a}, {fun.var_b}, {fun.var_c}, 0x{fun.value:02x})")
        print(f"GNU as : vpternlogd $0x{fun.value:02x}, {fun.var_a}, {fun.var_b}, {fun.var_c}")
        print(f"GO asm : VPTERNLOGD $0x{fun.value:02x}, {fun.var_a}, {fun.var_b}, {fun.var_c}")


    def print_value():
        print(f"0x{fun.value:02x}")


    if args.quiet:
        print_value()
    else:
        print_table()
        print()
        print_program()

    return 0;


def parse_args():
    ap = argparse.ArgumentParser(description="Derive constant for AVX512 ternary functions")
    ap.add_argument("-q", "--quiet",
                    action='store_true',
                    dest="quiet",
                    help="display only constant")
    ap.add_argument("--vars", "--order",
                    help="give variables in order from the most significant to least signficant; "
                         "1-3 vars allowed, separated with the comma")
    ap.add_argument("expr",
                    metavar="EXPR",
                    nargs='+',
                    help="boolean expression with at most three variables")

    args = ap.parse_args()
    args.expr = ' '.join(args.expr)

    if args.vars is not None:
        variables = args.vars.split(',')
        k = len(variables)
        if not (1 <= k <= 3):
            ap.error(f"--vars options requires one, two or three arguments, {k} given")

        for i, var in enumerate(variables):
            if not var:
                ap.error(f"variable #{i + 1} must not be empty")
            if not re.match("[a-zA-Z_][a-zA-Z0-9_]*", var):
                ap.error(f"'{var}' is not a valid variable name")
        else:
            args.vars = variables

    return args


def parse_expression(expr, variables):
    p = Parser(variables)
    tokens, mapping = p.parse(expr)
    expr_string = untokenize(tokens).decode('utf-8')

    return calculate_function(expr_string, mapping)


class Function:
    __slots__ = ['table', 'value', 'var_a', 'var_b', 'var_c', 'expression']


def calculate_function(expr_str, var_mapping):

    def evaluate(a, b, c):
        env = {var_mapping['a']: a,
               var_mapping['b']: b,
               var_mapping['c']: c}

        return eval(expr_str, env) & 0x01


    fun = Function()
    fun.expression = expr_str
    fun.var_a = var_mapping['a']
    fun.var_b = var_mapping['b']
    fun.var_c = var_mapping['c']
    fun.value = 0
    fun.table = []
    for i, (a, b, c) in enumerate(product([0, 1], [0, 1], [0, 1])):
        v = evaluate(a, b, c)
        fun.table.append((a, b, c, v))

        if v:
            fun.value |= (1 << i)

    return fun


class InvalidExpression(ValueError):
    pass


class Parser:
    def __init__(self, variables):
        self.mapping = {}
        self.variables = variables


    def parse(self, expr):
        tokens = tokenize(BytesIO(expr.encode('utf-8')).readline)
        tokens = self.__replace_operators(tokens)
        if self.variables:
            tokens = self.__validate_vars(tokens)
        else:
            tokens = self.__collect_vars(tokens)

        return (tokens, self.mapping)


    def __collect_vars(self, tokens):
        free_vars = ["a", "b", "c"]
        tokens = list(tokens)
        for token in tokens:
            if token.type == NAME and token.string not in self.mapping.values():
                if len(self.mapping) == 3:
                    raise InvalidExpression(f"Up to three variables are allowed")

                self.mapping[free_vars[0]] = token.string
                del free_vars[0]

        # we're fine with unary and binary functions too
        for v in free_vars:
            self.mapping[v] = f"-"

        return tokens


    def __validate_vars(self, tokens):
        tokens = list(tokens)
        for token in tokens:
            if token.type == NAME and token.string not in self.variables:
                raise InvalidExpression(f"Unknown variable '{token.string}'")

        self.mapping['a'] = self.variables[0]
        try:
            self.mapping['b'] = self.variables[1]
        except IndexError:
            self.mapping['b'] = f"-"

        try:
            self.mapping['c'] = self.variables[2]
        except IndexError:
            self.mapping['c'] = f"-"

        return tokens


    def __replace_operators(self, tokens):
        VALID_OPS  = {"(", ")", "~", "|", "^", "&"}
        OP_TRANSLATE = {
            'and': "&",
            'or' : "|",
            'xor': "^",
            'not': "~",
        }

        for token in tokens:
            if token.type == OP:
                if token.string in VALID_OPS:
                    yield token
                else:
                    raise InvalidExpression(f"Operator '{token.string}' is not allowed")

            elif token.type == NAME:
                try:
                    op = OP_TRANSLATE[token.string.lower()]
                    yield TokenInfo(OP, op, token.start, token.end, token.line)
                except KeyError:
                    yield token

            elif token.type == ERRORTOKEN:
                raise InvalidExpression(f"Invalid syntax")

            elif token.type not in {ENCODING, ENDMARKER, NEWLINE}:
                raise InvalidExpression(f"Invalid syntax '{token.string}'")

            else:
                yield token


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Unhandled exception: {e}")
        sys.exit(2)
