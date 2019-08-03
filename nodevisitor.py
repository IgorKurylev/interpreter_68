import tree
import copy


class NodeVisitor:

    def __init__(self, error_flag, func_dict):
        self._error_flag = error_flag

        self._func_dict = func_dict

        self.scopes = {'__global' : {}

                       }

        self.scopes['__global']['0prev'] = self.scopes

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

        self.unary_operators = {'-': lambda x: -x if isinstance(x, (bool, int)) else '-' + x,
                                '#': self.sharp_operator,
                                }

        self.robot_operators = {}

        self.stack = []

    def visit(self, node, entry_point: dict):
        method = 'visit_' + node.__class__.__name__
        return getattr(self, method, self.generic_visit)(node, entry_point)

    def generic_visit(self, node, entry_point: dict):
        if node is None:
            return None
        else:
            return (self.visit(c, entry_point) for c_name, c in node.children())

    def visit_Constant(self, n, entry_point: dict):
        return self.basic_types[n.type](n.value)

    def visit_ID(self, n: tree.ID, entry_point: dict, get_obj=False, no_msg=False):  # if get_obj is true we need a variable or a scope
        cur = entry_point                                     # else we need only to check if object exists
        while cur != self.scopes:  # we must check every parent scope
            res = cur.get(n.name)
            if res is not None:
                return res if get_obj else n.name
            cur = cur['0prev']  # go to parent scope
        else:
            if no_msg is False:
                print(f'Error at {n.coord}: invalid ID {n.name}')
                self._error_flag = True
            return

    def visit_ArrayRef(self, n: tree.ArrayRef, entry_point: dict, get_reference=False):  # TODO test + debug
        """
        :param get_reference: for assignment we need a reference
        (it's enough only to return an index before last)
        :return: none or element of array if get_reference=False
                 else return last subscript and reference
        """
        indices = []
        cur_node = n
        while type(cur_node) != tree.ID:
            indices.append(self.visit(cur_node.subscript, entry_point))  # after a[1][2][3] indices will be [3, 2, 1]
            cur_node = cur_node.name
        try:

            array = self.visit_ID(cur_node, entry_point, get_obj=True)
            if get_reference and len(indices) == 1 and type(array) != dict:
                return indices[0], array
            if array is None or type(array) == dict:  # we need only variable, not scope
                print(f'Error at {n.coord}: invalid type of object {cur_node.name}')
                self._error_flag = True
                return
            for num, index in enumerate(reversed(indices)):
                if get_reference and num == len(indices) - 2:
                    return index, array
                array = array[int(index)]

            return array
        except IndexError:
            return 'undef'
        except ValueError:
            return None

    def _build_print_args(self, name, arr, scope_name, n, flag=False):  # creates a list of printed objects

        pass

    def visit_FuncCall(self, n: tree.FuncCall, entry_point: dict):
        if n.name.name == 'print':
            arglist = self.visit(n.args, entry_point)
            if None in arglist:
                return  # Error is already occured
            print(', '.join(str(arg) for arg in arglist))
        else:
            try:
                scope = self.visit_ID(n.name, entry_point, get_obj=True)
                if scope is None:
                    return  # Error is already occured
                cnt = 0
                while entry_point.get(str(cnt) + n.name.name) is not None:  # find correct identificator (only for recursion)
                    cnt += 1
                new_name = str(cnt) + n.name.name
                new_scope = copy.deepcopy(scope)  # correct copy of the scope (without references)
                entry_point[new_name] = new_scope
                arglist = self.visit(n.args, entry_point)
                if arglist:
                    for arg, param in zip(arglist, new_scope['0self'].decl.type.args.params):  # copying arguments to scope
                        if arg is None:
                            return  # Error is already occured
                        new_scope[param.name] = arg
                self.visit_Compound(new_scope['0self'].body, new_scope, execute_flag=True)  # launching function
                del entry_point[new_name]
            except RecursionError:
                print(f'Error at {n.coord}: maximum recursion depth exceeded')
                self._error_flag = True

    def sharp_operator(self, x) -> int:  # sum of each element in array
        cnt = 0
        for item in x:
            if hasattr(item, '__iter__'):
                cnt += self.sharp_operator(item)
            else:
                cnt += int(item)  # TODO add references to another arrays
        return cnt

    def visit_UnaryOp(self, n: tree.UnaryOp, entry_point: dict, ):
        if n.op in self.robot_operators.keys():
            # if n.expr:
            #     print("Error at {}: invalid usage of robot operator {}".format(n.coord, n.op))
            #     self._error_flag = True
            # if not self._error_flag:
            #     return self.robot_operators[n.op]()
            pass
        else:
            if type(n.expr) == tree.ID:
                val = self.visit_ID(n.expr, entry_point, get_obj=True)
                if val is not None:
                    return self.unary_operators[n.op](val)
            else:
                return self.unary_operators[n.op](self.visit(n.expr, entry_point))

    def visit_BinaryOp(self, n, entry_point: dict):
        pass

    def visit_Assignment(self, n: tree.Assignment, entry_point: dict):
        if type(n.rvalue) == tree.ID:  # preparing for right operand
            rvalue = self.visit_ID(n.rvalue, entry_point, get_obj=True)
        else:
            rvalue = self.visit(n.rvalue, entry_point)
        if rvalue is None:
            return

        if type(n.lvalue) == tree.ArrayRef:  # individual case for a[5] := ...
            res = self.visit_ArrayRef(n.lvalue, entry_point, get_reference=True)
            if res == 'undef':
                print(f'Error at {n.coord}: invalid assignment')
                self._error_flag = True
                return

            subscript, array = res[0], res[1]

            try:
                array[subscript] = rvalue
            except IndexError:
                print(f'Error at {n.coord}: invalid assignment')
                self._error_flag = True
                return
        else:

            ref = self.visit_ID(n.lvalue, entry_point, get_obj=False, no_msg=True)
            if ref is None:
                if type(rvalue) in self.basic_types.values():
                    rvalue = [rvalue]
                entry_point[n.lvalue.name] = rvalue
                return entry_point[n.lvalue.name]
            entry_point[ref] = rvalue
            return ref

    def visit_Decl(self, n, entry_point: dict):
        pass

    def visit_ExprList(self, n, entry_point: dict):
        visited_subexprs = []
        for expr in n.exprs:
            if type(expr) == tree.ID:
                res = self.visit_ID(expr, entry_point, get_obj=True)
            else:
                res = self.visit(expr, entry_point)
            visited_subexprs.append(res)
        return visited_subexprs

    def visit_InitList(self, n, entry_point: dict):
        visited_subexprs = []
        for expr in n.exprs:
            visited_subexprs.append(self.visit(expr, entry_point))
        return visited_subexprs

    def visit_FuncDef(self, n: tree.FuncDef, entry_point: dict):
        if n.decl.name == 'main':  # executing starts with function main
            if entry_point != self.scopes['__global']:
                print(f'Error at {n.coord}: function main could be occured only in global scope')
                self._error_flag = True
                return
            entry_point['main'] = {'0prev': self.scopes['__global'], '0self': n}
            self.visit_Compound(n.body, entry_point['main'], func_name='main', execute_flag=True)
        else:  # just preparing new scope for parameters
            entry_point[n.decl.name] = {'0prev': entry_point, '0self': n}  # 0prev-reference to parent scope
            self.visit_FuncDecl(n.decl.type, entry_point[n.decl.name])     # 0self-information about of current scope

    def visit_FuncDecl(self, n: tree.FuncDecl, entry_point: dict):  # adds parameters to new scope where function will be executed
        if n.args:
            for arg in n.args:
                if entry_point.get(arg.name) is not None:
                    print(f'Error at {n.coord}: two parameters with the same name')
                    self._error_flag = True
                    return
                entry_point[arg.name] = []

    def _print_scopes(self, d, separator=0):
        if type(d) != dict:
            print(d, end='')
            return
        for key, item in zip(d.keys(), d.values()):
            if key not in ('0prev', '0self'):
                print(separator*' ', f'{key}: ', end=' ')
                self._print_scopes(item, separator+2)
                print('')

    def visit_FileAST(self, n, entry_point: dict):

        for ext in n.ext:
            self.visit(ext, entry_point)


        self._print_scopes(self.scopes)
        #print(self.scopes)

    def visit_Compound(self, n: tree.Compound, entry_point: dict, func_name=None, execute_flag=False):

        for item in n.block_items:
            if not self._error_flag and execute_flag:
                self.visit(item, entry_point)

    def visit_EmptyStatement(self, n, entry_point: dict):
        return

    def visit_ParamList(self, n, entry_point: dict):
        return [].extend(self.visit(param) for param in n.params)

    def visit_Return(self, n, entry_point: dict):
        pass

    def visit_If(self, n, entry_point: dict, execute_flag=False):
        pass

    def visit_While(self, n, entry_point: dict):
        pass
