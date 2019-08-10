import tree
import copy
from maze import _map


class NodeVisitor:
    MAX_WEIGHT = 10

    def __init__(self, error_flag, tokens):
        self._error_flag = error_flag
        self.tokens = tuple(token.lower() for token in tokens)

        self.scopes = {'__global': {'_map': _map,      # maze map
                                    '_pos': [0, 0, 0]  # robot coordinates and direction
                                    }                  # in format [y_pos, x_pos, rotation]
                       }
        self.scopes['__global']['0prev'] = self.scopes

        self.basic_types = { 'int'       : int,
                             'extra_int' : str,
                             'bool'      : bool,
                             'extra_bool': str,
                             'cell'      : str,
                           }

        self.operators = {'-'  : lambda x, y: x -  y,
                          '+'  : lambda x, y: x +  y,
                          '*'  : lambda x, y: x *  y,
                          '<'  : lambda x, y: x <  y,
                          '>'  : lambda x, y: x >  y,
                          '<=' : lambda x, y: x <= y,
                          '>=' : lambda x, y: x >= y,
                          '='  : lambda x, y: x == y,
                          '!=' : lambda x, y: x != y,
                          '^'  : lambda x, y: x ^  y,
                          }

        self.unary_operators = {'-': lambda x: -x if isinstance(x, (bool, int)) else '-' + x,
                                '#': self.sharp_operator,
                                }

        self.robot_operators = {'left' : self._left_op,
                                'right': self._right_op,
                                'test' : self._test_op,
                                'look' : self._look_op,
                                }
        self.operators_with_params = {'forward' : self._go_op,
                                      'backward': self._go_op,
                                      'load'    : self._load_drop,
                                      'drop'    : self._load_drop,
                                     }

        self._weight = 0
        self._max_weight = 10
        self.scopes['__global']['MAX_WEIGHT'] = self._max_weight
        self.scopes['__global']['WEIGHT'] = self._weight

    def _rotation_to_exit(self, x_pos, y_pos, rotation) -> list:  # gives an information about exit in each cell
        _map = self.scopes['__global']['_map']                    # returns list with 1st element is True/False if exit is reachable/unreachable
        assert _map[y_pos][x_pos]                                 # other elements in list are directions to exit or another cell

        exit_cells = ()
        if x_pos == 0 and y_pos % 2 == 0:
            if y_pos == 0:
                exit_cells = (0, 1, 4, 5)
            elif y_pos == len(_map) - 1:
                exit_cells = (2, 3, 4, 5)
            else:
                exit_cells = (4, 5)
        elif x_pos == len(_map[0]) - 1 and y_pos % 2 == 1:
            if y_pos == 1:
                exit_cells = (0, 1, 2)
            elif y_pos == len(_map) - 2:
                exit_cells = (1, 2, 3)
            else:
                exit_cells = (1, 2)
        elif y_pos == 0:
            exit_cells = (0, 1, 5)
        elif y_pos == 1:
            exit_cells = [0]
        elif y_pos == len(_map) - 1:
            exit_cells = (2, 3, 4)
        elif y_pos == len(_map) - 2:
            exit_cells = [3]

        res = [len(exit_cells) != 0 and rotation in exit_cells]  # first element is False if there is no direction to exit
        for item in exit_cells:
            if _map[y_pos][x_pos][item] in ('-inf', 0):  # if there is a wall, we will not return this direction
                res.append(item)
        return res

    def _next_cell(self, x_pos, y_pos, rotation, ignore_flag=False):  # returns coordinates if robot will make a step in current direction
        _map = self.scopes['__global']['_map']                        # in format [x_pos, y_pos]
        assert _map[y_pos][x_pos]

        exit_cells = self._rotation_to_exit(x_pos, y_pos, rotation)

        if rotation in exit_cells[1:]:
            return [-1, -1]      # returns [-1, -1] if robot will exit from the maze
        if not ignore_flag:
            if exit_cells[0]:        # returns current coordinates if there is a wall/box
                return [x_pos, y_pos]

        if rotation == 0:
            return [x_pos, y_pos - 2]
        if rotation == 3:
            return [x_pos, y_pos + 2]

        if y_pos % 2 == 0:
            if rotation == 1:
                return [x_pos, y_pos - 1]
            elif rotation == 2:
                return [x_pos, y_pos + 1]
            elif rotation == 4:
                return [x_pos - 1, y_pos + 1]
            else:
                return [x_pos - 1, y_pos - 1]

        if y_pos % 2 == 1:
            if rotation == 1:
                return [x_pos + 1, y_pos - 1]
            elif rotation == 2:
                return [x_pos + 1, y_pos + 1]
            elif rotation == 4:
                return [x_pos, y_pos + 1]
            else:
                return [x_pos, y_pos - 1]

    def _make_a_step(self, backward=False) -> int:
        _y_pos = self.scopes['__global']['_pos'][0]
        _x_pos = self.scopes['__global']['_pos'][1]
        _rotation = self.scopes['__global']['_pos'][2]
        if backward:
            _rotation = (_rotation + 3) % 6

        next = self._next_cell(_x_pos, _y_pos, _rotation)
        if next == [-1, -1]:  # go out from the maze
            self.scopes['__global']['_pos'] = [-1, -1, -1]
            return -1

        if next == [_x_pos, _y_pos]:  # wall case
            return 0

        if self.scopes['__global']['_map'][_y_pos][_x_pos][_rotation] == 0:  # make a step
            self.scopes['__global']['_pos'] = [next[1], next[0], _rotation]
            return 1
        return 0

    def _go_op(self, number, backward=False) -> bool:  # TODO add bad chance

        for _ in range(number):
            res = self._make_a_step(backward)
            if res == -1:
                return True
            if res == 0:
                return False
        return True

    def _left_op(self):
        if self._weight >= self._max_weight:
            return False
        rotation = self.scopes['__global']['_pos'][2]
        self.scopes['__global']['_pos'][2] = (rotation - 1) % 6
        return True

    def _right_op(self):
        if self._weight >= self._max_weight:
            return False
        rotation = self.scopes['__global']['_pos'][2]
        self.scopes['__global']['_pos'][2] = (rotation + 1) % 6
        return True

    def _load_drop(self, number, drop=False):
        assert number >= 0

        y_pos = self.scopes['__global']['_pos'][0]
        x_pos = self.scopes['__global']['_pos'][1]
        rotation = self.scopes['__global']['_pos'][2]
        _map = self.scopes['__global']['_map']

        x_next, y_next = self._next_cell(x_pos, y_pos, rotation, ignore_flag=True)
        if x_next == -1 and y_next == -1 or _map[y_next][x_next][rotation] == 0 and drop is False:
            return 'undef'
        if _map[y_pos][x_pos][rotation] == 'inf':                                      # wall case
            return False
        if _map[y_pos][x_pos][rotation] >= 0 and drop is True:
            _map[y_pos][x_pos][rotation] += number                                    # drop number of boxes to current cell
            _map[y_next][x_next][(rotation + 3) % 6] = _map[y_pos][x_pos][rotation]   # drop number of boxes from another side
            self._weight -= number
            self.scopes['__global']['WEIGHT'] = self._weight
            return True
        if _map[y_pos][x_pos][rotation] > 0 and drop is False:
            if self._weight == self._max_weight:
                return False
            for _ in range(number):
                if _map[y_pos][x_pos][rotation] == 0:
                    return True
                self.scopes['__global']['WEIGHT'] = self._weight
                self._weight += 1
                _map[y_pos][x_pos][rotation] -= 1                                        # remove one box from current cell
                _map[y_next][x_next][(rotation + 3) % 6] = _map[y_pos][x_pos][rotation]  # remove this box from another side
            return True

    def _test_op(self):
        y_pos = self.scopes['__global']['_pos'][0]
        x_pos = self.scopes['__global']['_pos'][1]
        rotation = self.scopes['__global']['_pos'][2]
        _map = self.scopes['__global']['_map']

        while _map[y_pos][x_pos][rotation] == 0 or _map[y_pos][x_pos][rotation] == '-inf':
            x_prev, y_prev = x_pos, y_pos
            x_pos, y_pos = self._next_cell(x_pos, y_pos, rotation)
            if x_pos == x_prev and y_pos == y_prev:
                return _map[y_pos][x_pos][rotation]  # returns 'inf' if wall and weight of box if box
            if x_pos == -1 and y_pos == -1:
                return 'undef'                       # no walls or boxes towards this direction
        else:
            return _map[y_pos][x_pos][rotation]      # if nearest obstacle is a next cell

    def _look_op(self):
        """
        :return: inf if exit towards current direction
                 or number of steps towards the nearest obstacle
        """
        y_pos = self.scopes['__global']['_pos'][0]
        x_pos = self.scopes['__global']['_pos'][1]
        rotation = self.scopes['__global']['_pos'][2]
        _map = self.scopes['__global']['_map']

        cnt = 0
        while _map[y_pos][x_pos][rotation] == 0 or _map[y_pos][x_pos][rotation] == '-inf':
            x_prev, y_prev = x_pos, y_pos
            x_pos, y_pos = self._next_cell(x_pos, y_pos, rotation)
            if x_pos == x_prev and y_pos == y_prev:
                return cnt
            if x_pos == -1 and y_pos == -1:
                return 'inf'                       # no walls or boxes towards this direction
            cnt += 1
        return cnt

    def visit(self, node, entry_point: dict, get_obj=False):
        """
        :param node: current ast node to visit
        :param entry_point: current scope
        :param get_obj: need only if node is tree.Id to call visit_ID with param get_obj=True
        :return: return value from visiting current node
        """
        method = 'visit_' + node.__class__.__name__
        if method == 'visit_ID' and get_obj:
            return self.visit_ID(node, entry_point, get_obj=True)
        return getattr(self, method, self.generic_visit)(node, entry_point)

    def generic_visit(self, node, entry_point: dict):

        if node is None or type(node) == str:
            return None
        else:
            return (self.visit(c, entry_point) for c_name, c in node.children())

    def visit_Constant(self, n, entry_point: dict):
        if n.value == 'false':
            return False
        return self.basic_types[n.type](n.value)  # cast value in proper way

    def visit_ID(self, n: tree.ID, entry_point: dict, get_obj=False, no_msg=False, get_scope=False):  # if get_obj is true we need a variable or a scope
        cur = entry_point                                                                            # else we need only to check if object exist
        while cur != self.scopes:  # we must check every parent scope                                # if get_scope is True we need a scope where object exist
            res = cur.get(n.name)
            if res is not None:
                if get_scope:
                    return cur, n.name
                return res if get_obj else n.name
            cur = cur['0prev']  # go to parent scope

        else:
            if no_msg is False:
                print(f'Error at {n.coord}: invalid ID {n.name}')
                self._error_flag = True
            return

    def visit_ArrayRef(self, n: tree.ArrayRef, entry_point: dict, get_reference=False):
        """
        :param get_reference: for assignment like a[5][3][1] := ... we need a reference
        (it's enough only to return an index before last)
        :return: none or element of array if get_reference=False
                 else return last subscript and reference
        """
        indices = []
        cur_node = n
        while type(cur_node) != tree.ID:
            index = self.visit(cur_node.subscript, entry_point, get_obj=True)
            if type(index) == list and len(index) == 1:
                index = index[0]
            indices.append(index)  # after a[1][2][3] indices will be [3, 2, 1]
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
                if get_reference and num == len(indices) - 1:
                    if type(array) != list:
                        print(f'Error at {n.coord}: invalid array reference')
                        self._error_flag = True
                        return
                    return index, array
                array = array[int(index)]

            return array
        except IndexError:
            return 'undef'
        except ValueError:
            return None

    def visit_FuncCall(self, n: tree.FuncCall, entry_point: dict):
        if n.name.name == 'print':
            arglist = self.visit(n.args, entry_point)
            if None in arglist:
                return  # Error is already occured
            print('PRINT CALL: ', ','.join(str(arg) for arg in arglist))
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
                new_scope['0prev'] = scope['0prev']  # we need a reference here
                new_scope['0self'] = scope['0self']  # only for optimization
                entry_point[new_name] = new_scope
                arglist = self.visit(n.args, entry_point)
                if arglist:
                    for arg, param in zip(arglist, new_scope['0self'].decl.type.args.params):  # copying arguments to scope
                        if arg is None:
                            return  # Error is already occured
                        new_scope[param.name] = arg
                res = self.visit_Compound(new_scope['0self'].body, new_scope)  # launching function
                del entry_point[new_name]
                return res
            except RecursionError:
                print(f'Error at {n.coord}: maximum recursion depth exceeded')
                self._error_flag = True

    def sharp_operator(self, x) -> int:  # sum of each element in array
        cnt = 0
        for item in x:
            if hasattr(item, '__iter__') and type(item) != str:
                cnt += self.sharp_operator(item)
            else:
                if item not in self.tokens:
                    cnt += int(item)
        return cnt

    def visit_UnaryOp(self, n: tree.UnaryOp, entry_point: dict, ):
        if n.op in self.robot_operators.keys():
            if not self._error_flag:
                return self.robot_operators[n.op]()
        elif n.op in self.operators_with_params.keys():
            number = self.visit(n.expr, entry_point, get_obj=True)
            if number is None:
                return
            try:
                if type(number) == list and len(number) == 1:
                    number = number[0]
                type_from = self._choose_type(number)
                number = self._cast_value(type_from=type_from, type_to=int, val=number)
                number = int(number)
                if number < 0:
                    raise ValueError
            except (ValueError, TypeError):
                print(f"Error at {n.coord}: invalid usage of forward/backward operator")
                self._error_flag = True
                return
            flag = n.op == 'backward' or n.op == 'drop'
            return self.operators_with_params[n.op](number, flag)
        else:
            val = self.visit(n.expr, entry_point, get_obj=True)
            if val is None:
                return
            try:
                return self.unary_operators[n.op](val)
            except TypeError:
                print(f'Error at {n.coord}: invalid unary expression')
                self._error_flag = True

    def visit_BinaryOp(self, n: tree.BinaryOp, entry_point: dict):
        left = self.visit(n.left, entry_point, get_obj=True)  # preparing left operand
        if type(left) == list and len(left) == 1:             # constant case
            left = left[0]

        right = self.visit(n.right, entry_point, get_obj=True)  # preparing right operand
        if type(right) == list and len(right) == 1:             # constant case
            right = right[0]

        if None in (left, right):
            return                                              # error is already occured

        type_left = self._choose_type(left)
        type_right = self._choose_type(right)
        if type_left in (int, 'int') and type_right != list:
            right = self._cast_value(type_from=type_right, type_to=type_left, val=right)
        if type_right in (int, 'int') and type_left != list:
            left = self._cast_value(type_from=type_left, type_to=type_right, val=left)
        try:
            return self.operators[n.op](left, right)
        except TypeError:
            print(f'Error at {n.coord}: invalid binary expression')
            self._error_flag = True

    def visit_Assignment(self, n: tree.Assignment, entry_point: dict):
        rvalue = self.visit(n.rvalue, entry_point, get_obj=True)  # preparing for right operand
        if rvalue is None:
            return

        if type(n.lvalue) == tree.ArrayRef:  # individual case for a[5] := ...
            res = self.visit_ArrayRef(n.lvalue, entry_point, get_reference=True)
            if res == 'undef':
                print(f'Error at {n.coord}: invalid assignment')
                self._error_flag = True
                return
            if res is None:
                return
            subscript, array = res[0], res[1]

            if type(array) in (int, bool, str):
                array = [array]
            try:
                if subscript > len(array) - 1:
                    array.extend('undef' for _ in range(subscript - len(array) + 1))  # this try/except block is only
            except TypeError:                                                         # for case when index b in a[b]
                print(f"Error at {n.coord}: invalid index in array reference {n}")    # is an array which length is > 1
                self._error_flag = True
                return
            try:
                array[subscript] = rvalue
            except IndexError:
                print(f'Error at {n.coord}: invalid assignment')
                self._error_flag = True
                return
        else:

            ref = self.visit_ID(n.lvalue, entry_point, get_obj=False, no_msg=True, get_scope=True)
            if ref is None:
                if type(rvalue) in self.basic_types.values():
                    rvalue = [rvalue]
                entry_point[n.lvalue.name] = rvalue
                return entry_point[n.lvalue.name]
            scope, name = ref[0], ref[1]
            # if len(scope[name]) == 1:
            #     if type(rvalue) == list and len(rvalue) == 1:
            #         rvalue = rvalue[0]
            #     scope[name][0] = rvalue
            # else:
            #     scope[name] = rvalue
            scope[name] = rvalue
            return rvalue

    def _cast_value(self, type_from, type_to, val):
        if type_from == type_to or type_from in ('int', int) and type_to in ('int', int):
            return val
        if type_from == 'cell':
            if type_to in (bool, 'bool'):
                if val in ('exit', 'empty'):
                    return True
                if val in ('box', 'wall'):
                    return False
                else:
                    return 'undef'
            if type_to in (int, 'int'):
                if val == 'empty':
                    return 0
                if val == 'wall':
                    return 'inf'
                if val == 'exit':
                    return '-inf'
                if val == 'box':
                    pass  # TODO cast box to it's weight
        elif type_from in (int, 'int'):
            if type_to == 'cell':
                if val == 0:
                    return 'empty'
                if val == 'inf':
                    return 'wall'
                if val == '-inf':
                    return 'exit'
                if val == 'nan':
                    return 'undef'
                else:
                    return 'box'
            if type_to in ('bool', bool):
                return bool(val)
        elif type_from in (bool, 'bool'):
            if type_to in ('int', int):
                return int(val)
        else:
            return None

    def _choose_type(self, ty):
        if type(ty) == str:
            if ty in ('wall', 'exit', 'empty', 'box'):
                return 'cell'
            if ty in ('inf', '-inf', 'nan'):
                return int
            if ty in ('true', 'false'):
                return bool
            else:
                return 'undef'
        else:
            return type(ty)

    def visit_Decl(self, n: tree.Decl, entry_point: dict):
        var = entry_point.get(n.name)
        if var is not None and type(var) != dict:
            print(f'Error at {n.coord}: variable {n.name} is already defined')
            self._error_flag = True
            return
        if n.init is None:
            entry_point[n.name] = ['undef']
        else:
            val = self.visit(n.init, entry_point, get_obj=True)
            if val is None:
                return
            if type(val) == list and len(val) == 1:
                val = val[0]
            if type(val) in self.basic_types.values() and n.type.name != 'var':
                try:
                    if n.type.name in ('extra_int', 'extra_bool', 'cell', 'int'):
                        if n.type.name[:5] == 'extra_':  # remove extra_
                            n.type.name = n.type.name[5:]
                        type_from = self._choose_type(val)
                        val = self._cast_value(type_from=type_from, type_to=n.type.name, val=val)
                        if val is None:
                            raise TypeError
                        entry_point[n.name] = [val]
                        return
                    entry_point[n.name] = [self.basic_types[n.type.name](val)]
                except TypeError:
                    print(f"Error at {n.coord}: cannot cast {val} to {n.type.name}")
                    self._error_flag = True
                    return
            else:
                entry_point[n.name] = [val]


    def visit_ExprList(self, n: tree.ExprList, entry_point: dict) -> list:
        visited_subexprs = []
        for expr in n.exprs:
            res = self.visit(expr, entry_point, get_obj=True)
            visited_subexprs.append(res)
        return visited_subexprs

    def visit_InitList(self, n: tree.InitList, entry_point: dict) -> list:
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
            self.visit_Compound(n.body, entry_point['main'], func_name='main')
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
                print(separator*' ', f'{key}: ', end='')
                self._print_scopes(item, separator+2)
            print('')

    def visit_FileAST(self, n, entry_point: dict):
        for ext in n.ext:
            self.visit(ext, entry_point)

        self._print_scopes(self.scopes)
        return self.scopes
        #print(self.scopes)

    def visit_Compound(self, n: tree.Compound, entry_point: dict, func_name=None):

        for item in n.block_items:
            if type(item) == tree.Return:
                return self.visit(item, entry_point)

            if not self._error_flag:
                res = self.visit(item, entry_point)
                if type(item) in (tree.If, tree.While) and res is not None:
                    return res

    def visit_EmptyStatement(self, n, entry_point: dict):
        return

    def visit_ParamList(self, n, entry_point: dict):
        return [].extend(self.visit(param) for param in n.params)

    def visit_Return(self, n: tree.Return, entry_point: dict):
        return self.visit(n.expr, entry_point, get_obj=True)

    def visit_If(self, n: tree.If, entry_point: dict, execute_flag=False):
        cond = self.visit(n.cond, entry_point, get_obj=True)
        if cond is None:
            return
        if bool(cond) and cond != 'undef':
            res = self.visit(n.iftrue, entry_point)
            if type(n.iftrue) == tree.Return or\
                    type(n.iftrue) in (tree.Compound, tree.While, tree.If) and res is not None:
                return res
        elif cond == 'undef' and n.ifundef is not None:
            res = self.visit(n.ifundef, entry_point)
            if type(n.ifundef) == tree.Return or\
                    type(n.ifundef) in (tree.Compound, tree.While, tree.If) and res is not None:
                return res

        elif not bool(cond) and n.iffalse is not None:
            res = self.visit(n.iffalse, entry_point)
            if type(n.iffalse) == tree.Return or\
                    type(n.iffalse) in (tree.Compound, tree.While, tree.If) and res is not None:
                return res
        else:
            return

    def visit_While(self, n: tree.While, entry_point: dict):
        cond = self.visit(n.cond, entry_point, get_obj=True)
        if cond is None:
            return
        if type(cond) == list and cond == [0] or cond == 'false':
            cond = False
        while bool(cond):
            if cond == 'undef':
                return
            res = self.visit(n.stmt, entry_point)
            if type(n.stmt) == tree.Return or type(n.stmt) in (tree.Compound, tree.If) and res is not None:
                return res
            cond = self.visit(n.cond, entry_point, get_obj=True)
            if type(cond) == list and cond == [0]:
                cond = False
        else:
            if n.finish is not None:
                res = self.visit(n.finish, entry_point)
                if type(n.finish) == tree.Return:
                    return res
