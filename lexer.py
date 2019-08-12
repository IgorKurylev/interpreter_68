import sys

from ply import lex
from ply.lex import TOKEN


class Lexer:
    def __init__(self, error_func, on_lbrace_func, on_rbrace_func,
                 type_lookup_func):

        self.error_func = error_func
        self.on_lbrace_func = on_lbrace_func
        self.on_rbrace_func = on_rbrace_func
        self.type_lookup_func = type_lookup_func
        self.filename = ''

        self.last_token = None

    def build(self, **kwargs):
        self.lexer = lex.lex(object=self, **kwargs)

    def reset_lineno(self):
        self.lexer.lineno = 1

    def input(self, text):
        self.lexer.input(text)

    def token(self):
        self.last_token = self.lexer.token()
        return self.last_token

    def find_tok_column(self, token):
        last_cr = self.lexer.lexdata.rfind('\n', 0, token.lexpos)
        return token.lexpos - last_cr

    def _error(self, msg, token):
        location = self._make_tok_location(token)
        self.error_func(msg, location[0], location[1])
        self.lexer.skip(1)

    def _make_tok_location(self, token):
        return (token.lineno, self.find_tok_column(token))

    keywords = (
        'WHILE', 'IF', 'ELDEF', 'ELUND', 'DO',
        'FINISH', 'DONE',
        'FORWARD', 'BACKWARD', 'LEFT', 'RIGHT', 'LOAD', 'DROP', 'LOOK', 'TEST',
        'FUNCTION', 'RETURN',

        'INF', 'NAN', 'TRUE', 'FALSE', 'UNDEF',
        'CELL', 'EMPTY', 'WALL', 'BOX', 'EXIT',
        'VAR', 'INT', 'BOOL',
    )

    keyword_map = {}
    for keyword in keywords:
        keyword_map[keyword.lower()] = keyword

    tokens = keywords + (
        # Identifiers
        'ID',

        # Operators
        'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
        'LT', 'LE', 'GT', 'GE', 'EQ', 'NE',
        'SHARP', 'XOR', 'AND',

        # Assignment
        'ASSIGN',

        # Delimeters
        'LPAREN', 'RPAREN',         # ( )
        'LBRACKET', 'RBRACKET',     # [ ]
        'COMMA',                    # ,

        'OPEN_BRACKET', 'CLOSE_BRACKET',  # DO, DONE

        # Constants
        'INT_CONST',  # TODO 16 digit constants
        '_NEWLINE',
    )

    identifier = r'[a-zA-Z_][0-9a-zA-Z_]*'

    decimal_constant = r'0|([1-9][0-9]*)'

    t_ignore = ' \t'

    newline = r'\n+'

    # Operators
    t_PLUS              = r'\+'
    t_MINUS             = r'-'
    t_LT                = r'<'
    t_GT                = r'>'
    t_EQ                = r'='

    t_SHARP             = r'\#'
    t_XOR               = r'\^'

    # Added
    t_AND               = r'&'
    t_NE                = r'!='
    t_LE                = r'<='
    t_GE                = r'>='
    t_TIMES             = r'\*'
    t_DIVIDE            = r'/'

    # Assignment operators
    t_ASSIGN            = r':='

    # Delimeters
    t_LPAREN            = r'\('
    t_RPAREN            = r'\)'
    t_LBRACKET          = r'\['
    t_RBRACKET          = r'\]'
    t_COMMA             = r','

    t_OPEN_BRACKET      = r'{'
    t_CLOSE_BRACKET     = r'}'

    @TOKEN(identifier)
    def t_ID(self, t):
        t.type = self.keyword_map.get(t.value, "ID")
        return t

    @TOKEN(decimal_constant)
    def t_INT_CONST(self, t):
        return t

    @TOKEN(newline)
    def t__NEWLINE(self, t):
        t.lexer.lineno += t.value.count("\n")
        return t

    def t_error(self, t):
        msg = 'Illegal character %s' % repr(t.value[0])
        self._error(msg, t)
