# -*- coding: utf-8 -*-
class EdgeType:
    MEMBERSHIP = 'µ'
    PREDICATE = 'θ'
    SELECTION = 'σ'
    FUNCTION = 'f'
    TRANSFORMATION = 'r'
    ORDER = 'o'
    GROUPING = 'γ'
    HAVING = 'h'
    JOIN = 'j'
    NESTED_IN = 'IN'
    NESTED_EXISTS = 'EXISTS'


class NodeType:
    RELATION, ATTRIBUTE, VALUE, FUNCTION = range(4)


class PredType:
    EQ = '='
    NE = '<>'
    LT = '<'
    LE = '<='
    GT = '>'
    GE = '>='
    LIKE = 'LIKE'
