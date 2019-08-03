import tree
import copy


class NodeVisitor:

    def __init__(self, error_flag, func_dict):
        self._error_flag = error_flag

        self._func_dict = func_dict

        self.scopes = {'__global' : {}

                       }

        self.basic_types = { 'int'       : int,
                             'extra_int' : str,
                             'bool'      : bool,
                             'extra_bool': str,
                             'robot'     : str,
                           }

        self.operators = {'-'  : lambda x, y: x -   y,
                          '+'  : lambda x, y: x +   y,
                          '/'  : lambda x, y: x //  y,
                          '*'  : lambda x, y: x *   y,
                          '<'  : lambda x, y: x <   y,
                          '>'  : lambda x, y: x >   y,
                          '<=' : lambda x, y: x <=  y,
                          '>=' : lambda x, y: x >=  y,
                          '='  : lambda x, y: x ==  y,
                          '!=' : lambda x, y: x !=  y,
                          '^'  : lambda x, y: x ^   y,
                          }

        self.unary_operators = {'-': lambda x: -x,
                                '#': self.sharp_operator,
                                }

        self.robot_operators = {}

        self.stack = []

    def visit(self, node, scope_name='__global'):
        method = 'visit_' + node.__class__.__name__
        return getattr(self, method, self.generic_visit)(node, scope_name=scope_name)

    def generic_visit(self, node, scope_name='__global'):
        if node is None:
            return None
        else:
            return (self.visit(c, scope_name=scope_name) for c_name, c in node.children())

    def visit_Constant(self, n, scope_name='__global'):
        return self.basic_types[n.type](n.value)

    def visit_ID(self, n, scope_name='__global', get_const=False):
        ref = self.scopes[scope_name].get(n.name)
        if ref is None:
            ref = self.scopes['__global'].get(n.name)
            if not ref:
                print("Error at {}: unresolved reference to {}".format(n.coord, n.name))
                self._error_flag = True
                return None
        return ref[1] if get_const else n.name

    def visit_ArrayRef(self, n: tree.ArrayRef, scope_name='__global', get_reference=False):  # TODO test + debug
        indices = []
        cur_node = n
        while type(cur_node) != tree.ID:
            indices.append(self.visit(cur_node.subscript, scope_name=scope_name))
            cur_node = cur_node.name
        try:
            array = self.visit_ID(cur_node, scope_name=scope_name, get_const=True)
            if array is None:
                return
            for el in reversed(indices):
                array = array[int(el)]

            return array
        except (ValueError, IndexError):
            return 'undef'

    def _build_print_args(self, name, arr, scope_name, n, flag=False):
        pass

    def visit_FuncCall(self, n, scope_name='__global'):
        if n.name.name == 'print':
            pass
        else:
            pass

    def sharp_operator(self, x) -> int:  # sum of each element in array
        cnt = 0
        for item in x:
            if hasattr(item, '__iter__'):
                cnt += self.sharp_operator(item)
            else:
                cnt += int(item)  # TODO add references to another arrays
        return cnt

    def visit_UnaryOp(self, n: tree.UnaryOp, scope_name='__global'):
        if n.op in self.robot_operators.keys():
            # if n.expr:
            #     print("Error at {}: invalid usage of robot operator {}".format(n.coord, n.op))
            #     self._error_flag = True
            # if not self._error_flag:
            #     return self.robot_operators[n.op]()
            pass
        else:
            if type(n.expr) == tree.ID:
                val = self.visit_ID(n.expr, scope_name=scope_name, get_const=True)
                if not self._error_flag:
                    return self.unary_operators[n.op](val)
            else:
                return self.unary_operators[n.op](self.visit(n.expr, scope_name=scope_name))

    def visit_BinaryOp(self, n, scope_name='__global'):
        pass

    def visit_Assignment(self, n: tree.Assignment, scope_name='__global'):
        if type(n.lvalue) == tree.ArrayRef:  # individual case for a[5] := ...
            pass
        else:
            pass

    def _visit_expr(self, n, scope_name='__global'):

        return self.visit(n, scope_name=scope_name)

    def visit_Decl(self, n, scope_name='__global'):
        pass

    def visit_ExprList(self, n, scope_name='__global'):
        visited_subexprs = []
        for expr in n.exprs:
            visited_subexprs.append(self._visit_expr(expr, scope_name=scope_name))
        return visited_subexprs

    def visit_InitList(self, n, scope_name='__global'):
        visited_subexprs = []
        for expr in n.exprs:
            visited_subexprs.append(self.visit(expr))
        return visited_subexprs

    def visit_FuncDef(self, n, scope_name='__global'):
        pass

    def visit_FileAST(self, n, scope_name='__global'):
        for ext in n.ext:
            self.visit(ext)

    def visit_Compound(self, n, func_name=None, execute_flag=False):
        pass

    def visit_EmptyStatement(self, n, scope_name='__global'):
        return

    def visit_ParamList(self, n):
        return [].extend(self.visit(param) for param in n.params)

    def visit_Return(self, n, scope_name='__global'):
        pass

    def visit_If(self, n, scope_name='__global', execute_flag=False):
        pass

    def visit_While(self, n, scope_name='__global'):
        pass
