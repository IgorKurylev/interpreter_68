from ply import yacc


import tree
from lexer import Lexer


class Coord:
    __slots__ = ('file', 'line', 'column', '__weakref__')

    def __init__(self, file, line, column=None):
        self.file = file
        self.line = line
        self.column = column

    def __str__(self):
        str = "%s:%s" % (self.file, self.line)
        if self.column: str += ":%s" % self.column
        return str


class ParseError(Exception):
    pass


class Parser:
    def __init__(
            self,
            lexer=Lexer,
            yacc_debug=True,
            taboutputdir=''):

        self.lex = lexer(
            error_func=self._lex_error_func,
            on_lbrace_func=self._lex_on_lbrace_func,
            on_rbrace_func=self._lex_on_rbrace_func,
            type_lookup_func=self._lex_type_lookup_func)

        self.lex.build(
            outputdir=taboutputdir)
        self.tokens = self.lex.tokens

        self.parser = yacc.yacc(
            module=self,
            start='translation_unit_or_empty',
            debug=yacc_debug,
            outputdir=taboutputdir)

        self._scope_stack = [dict()]

        self._last_yielded_token = None

        self.func_dict = {}
        self._err_flag = False

    def parse(self, text, filename='', debuglevel=True):
        self.lex.filename = filename
        self.lex.reset_lineno()
        self._scope_stack = [dict()]
        self._last_yielded_token = None
        return self.parser.parse(
                input=text,
                lexer=self.lex,
                debug=debuglevel)

    def _coord(self, lineno, column=None):
        return Coord(
            file=self.lex.filename,
            line=lineno,
            column=column)

    def _token_coord(self, p, token_idx):
        last_cr = p.lexer.lexer.lexdata.rfind('\n', 0, p.lexpos(token_idx))
        if last_cr < 0:
            last_cr = -1
        column = (p.lexpos(token_idx) - (last_cr))
        return self._coord(p.lineno(token_idx), column)

    def _parse_error(self, msg, coord):
        raise ParseError("%s: %s" % (coord, msg))

    def _push_scope(self):
        self._scope_stack.append(dict())

    def _pop_scope(self):
        assert len(self._scope_stack) > 1
        self._scope_stack.pop()

    def _add_identifier(self, name, coord):
        if self._scope_stack[-1].get(name, False):
            self._parse_error(
                "Non-typedef %r previously declared as typedef "
                "in this scope" % name, coord)
        self._scope_stack[-1][name] = False

    def _is_type_in_scope(self, name):

        for scope in reversed(self._scope_stack):
            # If name is an identifier in this scope it shadows typedefs in
            # higher scopes.
            in_scope = scope.get(name)
            if in_scope is not None: return in_scope
        return False

    def _lex_error_func(self, msg, line, column):
        self._parse_error(msg, self._coord(line, column))

    def _lex_on_lbrace_func(self):
        self._push_scope()

    def _lex_on_rbrace_func(self):
        self._pop_scope()

    def _lex_type_lookup_func(self, name):
        is_type = self._is_type_in_scope(name)
        return is_type

    def _get_yacc_lookahead_token(self):
        return self.lex.last_token

    def _type_modify_decl(self, decl, modifier):

        modifier_head = modifier
        modifier_tail = modifier

        while modifier_tail.type:
            modifier_tail = modifier_tail.type

        if isinstance(decl, tree.TypeDecl):
            modifier_tail.type = decl
            return modifier
        else:
            decl_tail = decl

            while not isinstance(decl_tail.type, tree.TypeDecl):
                decl_tail = decl_tail.type

            modifier_tail.type = decl_tail.type
            decl_tail.type = modifier_head
            return decl

    def _fix_decl_name_type(self, decl, typename):
        type = decl
        while not isinstance(type.type, tree.TypeDecl):
            type = type.type

        decl.name = type.type.declname

        if not typename:
            type.type = None
        else:
            type.type = tree.IdentifierType(
                typename[0].name[0],
                coord=typename[0].coord)
        return decl

    def _add_declaration_specifier(self, declspec, newspec, kind, append=False):
        spec = declspec or dict(qual=[], storage=[], type=[], function=[])

        if append:
            spec[kind].append(newspec)
        else:
            spec[kind].insert(0, newspec)

        return spec

    def _build_declarations(self, spec, decls, typedef_namespace=False):
        declarations = []

        for decl in decls:
            assert decl['decl'] is not None
            declaration = tree.Decl(
                name=None,
                type=decl['decl'],
                init=decl.get('init'),
                coord=decl['decl'].coord,
            )

            if isinstance(declaration.type, tree.IdentifierType):
                fixed_decl = declaration
            else:
                if spec:
                    fixed_decl = self._fix_decl_name_type(declaration, spec['type'])
                else:
                    fixed_decl = self._fix_decl_name_type(declaration, None)

            if typedef_namespace:
                self._add_identifier(fixed_decl.name, fixed_decl.coord)

            declarations.append(fixed_decl)

        return declarations

    def _build_function_definition(self, spec, decl, param_decls, body):
        declaration = self._build_declarations(
            spec=spec,
            decls=[dict(decl=decl, init=None)],
            typedef_namespace=True)[0]

        return tree.FuncDef(
            decl=declaration,
            param_decls=param_decls,
            body=body,
            coord=decl.coord)

    precedence = (
        ('right', 'ASSIGN'),
        ('left', 'EQ', 'NE'),
        ('left', 'GT', 'GE', 'LT', 'LE'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE')
    )

    def p_translation_unit_or_empty(self, p):
        """ translation_unit_or_empty   : translation_unit
                                        | empty
        """
        if p[1] is None:
            p[0] = tree.FileAST([])
        else:
            p[0] = tree.FileAST(p[1])

    def p_translation_unit_1(self, p):
        """ translation_unit    : external_declaration
        """

        p[0] = p[1]

    def p_translation_unit_3(self, p):
        """ translation_unit    : translation_unit external_declaration
        """
        p[1].extend(p[2])
        p[0] = p[1]

    def p_external_declaration_1(self, p):
        """ external_declaration    : function_definition
        """
        p[0] = [p[1]]

    def p_external_declaration_2(self, p):
        """ external_declaration    : declaration
                                   
        """  # TODO remove statement
        p[0] = p[1]

    def p_external_declaration_4(self, p):
        """ external_declaration    : _NEWLINE
        """

        p[0] = []

    def p_function_definition(self, p):
        """ function_definition : FUNCTION id_declarator declaration_list _NEWLINE compound_statement
                                | FUNCTION id_declarator empty _NEWLINE compound_statement
        """
        p[0] = self._build_function_definition(
            spec=None,
            decl=p[2],
            param_decls=p[3],
            body=p[5])
        if self.func_dict.get(p[0].decl.name) and self.func_dict.get(p[0].decl.name) != "def":
            print("ERROR at %s : function definition is already exists" % self._coord(p[0].coord))
            self._err_flag = True

        else:
            self.func_dict[p[0].decl.name] = p[0]



    def p_statement(self, p):
        """ statement   : expression_statement
                        | compound_statement
                        | selection_statement
                        | iteration_statement
                        | jump_statement
        """
        p[0] = p[1]

    def p_declaration(self, p):
        """ declaration       : type_specifier init_declarator_list _NEWLINE
        """
        spec = p[1]
        if p[2] is None:
            decls = self._build_declarations(
                spec=spec,
                decls=[dict(decl=None, init=None)],
                typedef_namespace=True)

        else:
            decls = self._build_declarations(
                spec=spec,
                decls=p[2],
                typedef_namespace=True)

        p[0] = decls



    def p_declaration_list(self, p):
        """ declaration_list    : declaration
                                | declaration_list declaration
        """
        p[0] = p[1] if len(p) == 2 else p[1] + p[2]

    def p_type_specifier(self, p):
        """ type_specifier            : INT
                                      | BOOL
                                      | CELL
                                      | VAR
        """

        buf = tree.IdentifierType([p[1]], coord=self._token_coord(p, 1))
        p[0] = self._add_declaration_specifier(None, buf, 'type')

    def p_init_declarator_list(self, p):
        """ init_declarator_list    : init_declarator
                                    | init_declarator_list COMMA init_declarator
        """
        if len(p) == 4:
            for item in p[1]:
                item['init'] = p[3]['init']

            p[0] = p[1] + [p[3]]

        else:
            p[0] = [p[1]]

    def p_initializer_1(self, p):
        """ initializer : assignment_expression
        """
        p[0] = p[1]

    def p_initializer_2(self, p):
        """ initializer : OPEN_BRACKET initializer_list CLOSE_BRACKET
                        | OPEN_BRACKET initializer_list COMMA CLOSE_BRACKET
        """
        if p[2] is None:
            p[0] = tree.InitList([], self._token_coord(p, 1))
        else:
            p[0] = p[2]

    def p_initializer_list(self, p):
        """ initializer_list    : initializer
                                | initializer_list COMMA initializer
        """
        if len(p) == 2:  # single initializer

            p[0] = tree.InitList([p[1]], p[1].coord)
        else:
            init = p[3]
            p[1].exprs.append(init)
            p[0] = p[1]

    def p_init_declarator(self, p):
        """ init_declarator : declarator
                            | declarator ASSIGN initializer
        """

        p[0] = dict(decl=p[1], init=(p[3] if len(p) > 2 else None))

    def p_declarator(self, p):
        """ declarator  : id_declarator
        """
        p[0] = p[1]

    def p_id_declarator_1(self, p):
        """ id_declarator  : direct_id_declarator
        """
        p[0] = p[1]

    def p_direct_id_declarator_1(self, p):
        """ direct_id_declarator   : ID
        """
        p[0] = tree.TypeDecl(
            declname=p[1],
            type=None,

            coord=self._token_coord(p, 1))

    def p_direct_id_declarator_2(self, p):
        """ direct_id_declarator   : LPAREN id_declarator RPAREN
        """
        p[0] = p[2]

    def p_direct_id_declarator_3(self, p):
        """ direct_id_declarator   : direct_id_declarator LPAREN parameter_type_list RPAREN
                                   | direct_id_declarator LPAREN identifier_list RPAREN
                                   | direct_id_declarator LPAREN empty RPAREN
        """

        func = tree.FuncDecl(
            args=p[3],
            type=None,
            coord=p[1].coord)

        self.func_dict[p[1].declname] = "def"
        if self._get_yacc_lookahead_token().type == "LBRACE":
            if func.args is not None:
                for param in func.args.params:
                    self._add_identifier(param.name, param.coord)

        f = self._type_modify_decl(decl=p[1], modifier=func)
        p[0] = f

    def p_parameter_type_list(self, p):
        """ parameter_type_list : parameter_list
        """

        p[0] = p[1]

    def p_parameter_list(self, p):
        """ parameter_list  : parameter_declaration
                            | parameter_list COMMA parameter_declaration
        """
        if len(p) == 2: # single parameter
            p[0] = tree.ParamList([p[1]], p[1].coord)
        else:
            p[1].params.append(p[3])
            p[0] = p[1]


    def p_parameter_declaration_1(self, p):
        """ parameter_declaration   :  id_declarator
        """

        p[0] = self._build_declarations(
            spec=None,
            decls=[dict(decl=p[1])])[0]

    def p_identifier_list(self, p):
        """ identifier_list : identifier
                            | identifier_list COMMA identifier
        """
        if len(p) == 2:  # single parameter
            p[0] = tree.ParamList([p[1]], p[1].coord)
        else:
            p[1].params.append(p[3])
            p[0] = p[1]


    def p_block_item(self, p):
        """ block_item  : declaration
                        | statement
                        | function_definition
        """

        if p[1] == '\n':
            return
        p[0] = p[1] if isinstance(p[1], list) else [p[1]]

    def p_block_item_list(self, p):
        """ block_item_list : block_item
                            | block_item_list block_item
        """
        if len(p) == 2 and p[1] is None:
            p[0] = []
            return
        elif len(p) == 3 and p[2] is None:
            p[0] = p[1]
            return

        p[0] = p[1] if (len(p) == 2 or p[2] == [None]) else p[1] + p[2]

    def p_compound_statement(self, p):
        """ compound_statement : brace_open block_item_list brace_close _NEWLINE
                               | brace_open empty brace_close _NEWLINE
        """

        p[0] = tree.Compound(
            block_items=p[2],
            coord=self._token_coord(p, 1))

    def p_selection_statement_1(self, p):
        """ selection_statement : IF expression _NEWLINE statement """
        if p[2] is None:
            print("ERROR at {}:{} : wrong format of check".format(p[4].coord.line, 10))
            self._err_flag = True
        p[0] = tree.If(cond=p[2], iftrue=p[4], coord=self._token_coord(p, 1))

    def p_selection_statement_2(self, p):
        """ selection_statement : IF expression _NEWLINE statement ELDEF _NEWLINE statement """
        p[0] = tree.If(cond=p[2], iftrue=p[4], iffalse=p[7], coord=self._token_coord(p, 1))

    def p_selection_statement_3(self, p):
        """ selection_statement : IF expression _NEWLINE statement ELUND _NEWLINE statement """
        p[0] = tree.If(cond=p[2], iftrue=p[4], ifundef=p[7], coord=self._token_coord(p, 1))

    def p_selection_statement_4(self, p):
        """ selection_statement : IF expression _NEWLINE statement ELDEF _NEWLINE statement ELUND _NEWLINE statement """

        p[0] = tree.If(cond=p[2], iftrue=p[4], iffalse=p[7], ifundef=p[10], coord=self._token_coord(p, 1))

    def p_iteration_statement_1(self, p):
        """ iteration_statement : WHILE expression _NEWLINE statement """
        p[0] = tree.While(p[2], p[4], None, self._token_coord(p, 1))

    def p_iteration_statement_2(self, p):
        """ iteration_statement : WHILE expression _NEWLINE statement FINISH _NEWLINE statement """
        p[0] = tree.While(p[2], p[4], p[7], self._token_coord(p, 1))

    def p_jump_statement(self, p):
        """ jump_statement  : RETURN expression _NEWLINE
                            | RETURN _NEWLINE
        """
        p[0] = tree.Return(p[2] if len(p) == 4 else None, self._token_coord(p, 1))

    def p_expression_statement(self, p):
        """ expression_statement : expression _NEWLINE

                                 | _NEWLINE
        """

        if p[1] is '\n':
            p[0] = tree.EmptyStatement(self._token_coord(p, 1))
        else:
            p[0] = p[1]

    def p_expression(self, p):
        """ expression  : assignment_expression
                        | expression COMMA assignment_expression
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            if not isinstance(p[1], tree.ExprList):
                p[1] = tree.ExprList([p[1]], p[1].coord)

            p[1].exprs.append(p[3])
            p[0] = p[1]

    def p_assignment_expression(self, p):
        """ assignment_expression   : binary_expression
                                    | unary_expression ASSIGN initializer
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = tree.Assignment(p[2], p[1], p[3], p[1].coord)

    def p_assignment_operator(self, p):
        """ assignment_operator : ASSIGN
        """
        p[0] = p[1]

    def p_binary_expression(self, p):
        """ binary_expression   : cast_expression
                                | binary_expression TIMES binary_expression
                                | binary_expression DIVIDE binary_expression
                                | binary_expression PLUS binary_expression
                                | binary_expression MINUS binary_expression
                                | binary_expression LT binary_expression
                                | binary_expression LE binary_expression
                                | binary_expression GE binary_expression
                                | binary_expression GT binary_expression
                                | binary_expression EQ binary_expression
                                | binary_expression NE binary_expression
                                | binary_expression XOR binary_expression
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = tree.BinaryOp(p[2], p[1], p[3], p[1].coord)

    def p_cast_expression_1(self, p):
        """ cast_expression : unary_expression
                            | robot_expression
        """
        p[0] = p[1]

    def p_robot_expression(self, p):
        """ robot_expression : LEFT
                             | RIGHT
                             | LOOK
                             | TEST
        """
        p[0] = tree.UnaryOp(p[1], None, self._token_coord(p, 1))

    def p_robot_operator(self, p):
        """
        robot_operator    : FORWARD
                          | BACKWARD
                          | LOAD
                          | DROP
        """
        p[0] = p[1]

    def p_unary_expression_1(self, p):
        """ unary_expression    : postfix_expression """
        p[0] = p[1]

    def p_unary_expression_2(self, p):
        """ unary_expression    : unary_operator cast_expression
        """
        p[0] = tree.UnaryOp(p[1], p[2], p[2].coord)

    def p_unary_operator_1(self, p):
        """ unary_operator  : robot_operator
                            | PLUS
                            | MINUS
                            | SHARP
        """
        p[0] = p[1]

    def p_postfix_expression_1(self, p):
        """ postfix_expression  : identifier
                                | constant
        """
        p[0] = p[1]

    def p_postfix_expression_2(self, p):
        """ postfix_expression  : postfix_expression LPAREN argument_expression_list RPAREN
                                | postfix_expression LPAREN RPAREN
        """
        if self.func_dict.get(p[1].name) is None:
            if p[1].name != 'print':
                print("ERROR at {} : function {} is not already defined" .format(self._coord(p[1].coord), p[1].name))
                self._err_flag = True
        p[0] = tree.FuncCall(p[1], p[3] if len(p) == 5 else None, p[1].coord)

    def p_postfix_expression_3(self, p):
        """ postfix_expression  : postfix_expression LBRACKET expression RBRACKET
                                | postfix_expression LBRACKET RBRACKET
        """
        if p[3] is None:
            print("ERROR at {}:{} : empty index occured".format(p[1].coord.line, p[1].coord.column + 1))
            self._err_flag = True
        p[0] = tree.ArrayRef(p[1], p[3], p[1].coord)

    def p_postfix_expression_4(self, p):
        """ postfix_expression  : LPAREN expression RPAREN """
        p[0] = p[2]

    def p_argument_expression_list(self, p):
        """ argument_expression_list    : assignment_expression
                                        | argument_expression_list COMMA assignment_expression
        """
        if len(p) == 2:  # single expr
            p[0] = tree.ExprList([p[1]], p[1].coord)
        else:
            p[1].exprs.append(p[3])
            p[0] = p[1]

    def p_identifier(self, p):
        """ identifier  : ID """
        p[0] = tree.ID(p[1], self._token_coord(p, 1))

    def p_constant_1(self, p):
        """ constant    : INT_CONST
        """
        p[0] = tree.Constant(
            'int', p[1], self._token_coord(p, 1))

    def p_constant_2(self, p):
        """ constant    :  EMPTY
                        |  WALL
                        |  BOX
                        |  EXIT
        """
        p[0] = tree.Constant(
            'robot', p[1], self._token_coord(p, 1))

    def p_constant_3(self, p):
        """ constant    : INF
                        | MINUS INF
                        | NAN
        """
        p[0] = tree.Constant(
            'extra_int', p[1], self._token_coord(p, 1))

    def p_constant_4(self, p):
        """ constant    : TRUE
                        | FALSE
        """
        p[0] = tree.Constant(
            'bool', p[1], self._token_coord(p, 1))

    def p_constant_5(self, p):
        """ constant    : UNDEF
        """
        p[0] = tree.Constant(
            'extra_bool', p[1], self._token_coord(p, 1))

    def p_brace_open(self, p):
        """ brace_open  :   DO
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_brace_close(self, p):
        """ brace_close :   DONE
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_empty(self, p):
        """empty : """
        p[0] = None

    def p_error(self, p):
        if p:
            self._parse_error(
                'before: %s' % p.value,
                self._coord(lineno=p.lineno,
                            column=self.lex.find_tok_column(p)))
        else:
            self._parse_error('At end of input', self.lex.filename)
