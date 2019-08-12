
from parser import Parser
import nodevisitor

text = r"""
     function main() 
     do
          int a := 4
          b := a
     done
"""

text = r"""
    function main() 
    do
        if 3+2
        do
            f := 4
            left
        done
        eldef 
            d := d + 2
        elund
        do
            4 - 2
        done
    done
"""

text = r"""
    function main() 
    do
        while 4+4
        do
            f + 5
            g := 5
        done
        finish
            f + 2
    done
"""

text = r"""
    function main() 
    do
        function ggg()
        do
            function hhh()
            do
                var a, b, c := undef
                if 5 ^ 1
                    print(a[5])
            done
        done
    done
"""
#
# text = r"""
#     function main(a, b, c)
#     do
#         var a
#         a[1][2] := 5
#     done
# """



text = r"""

    function main(a, b, c)
    do
        a := 3
        b := 4
        if 3 + 2
        do
            print(666)
        done
        eldef
        do
            
        done
            

    done
"""

text = r"""

    function main(a, b, c)
    do
        a := 3
        b := 4
        print(a+b)


    done
"""

text = r"""
    function fib(n)
    do
        if n = 0
            return n
        if n = 1
            return n
        return fib(n-2) + fib(n-1)
    done

    function main()
    do
        a := 0
        a[0] := fib(1)
        a[1] := fib(2)
        a[2] := fib(3)
        a[3] := fib(4)
        a[4] := fib(5) 
        
    done
"""

text = r"""
        function factorial(n)
        do
            if n = 0
                return n
            if n = 1
                return n
            return n * factorial(n-1)
        done

        function main()
        do
            a := 0
            a[0] := factorial(1)
            a[1] := factorial(2)
            a[2] := factorial(3)
            a[3] := factorial(4)
            a[4] := factorial(5) 
        done
"""

text = r"""
    function main() 
    do
        a := 0
        function ggg()
        do
            function hhh()
            do
                a := 5
            done
            hhh()
        done
        
        ggg()
    done
"""

text = r"""

    function main(a, b, c)
    do
        a := 5
        b := 1
        a[3] := b
        b[4] := 1000
        print(#a)
    done
"""

text = r"""

    function main(a, b, c)
    do
        a := 0
        while a != 5
        do
            a := a + 1
        done
        finish
            a := a + 5
    done
"""

text = r"""

    function main()
    do
        bool a := 5
        int b := a
        cell c := 0
        bool d := exit
        int e := empty
    done
"""

text = r"""
    function main()
    do
        a := look
        right
        right
        load 1
        a[1] := look
        
        FINISH := -1
        FINISH[1] := -1
        FINISH[2] := -1
    done
"""


text = r"""
    var _stack
    int _head := 0
    
    
    function stack_push(el)
    do
        _stack[_head] := el
        _head := _head + 1 
    done
    
    function stack_pop()
    do
        if _head = 0
            return undef
        _head := _head - 1
        return _stack[_head]
    done
    
    function main()
    do
        
    done
    
"""

# in this implementation stack is array: [size, el1, el2, ...]
# global variable WEIGHT is a current weight of loaded boxes
# it changes whenever we call load/drop operator, don't change it by yourself
# MAX_WEIGHT and WEIGHT are created in the nodevisitor __init__ method
# get_neighbours() function returns a stack with directions towards non-visited neighbours
# is_visited() function checks if the current cell is in the stack of visited cells
# TODO optimal arrangement of boxes + unsuccessful probability of robot operators execution
text = r"""
    function push(stack, el)
    do
        head := stack[0]
        stack[0] := head + 1
        stack[head + 1] := el
        return stack
    done
    
    function pop(stack)
    do
        head := stack[0]
        var res
        res[1] := stack
        if head = 0
            return res
        res[0] := stack[head]
        stack[0] := head - 1
        res[1] := stack
        return res
    done
    
    function _init(_y, _x, _dir)
    do
        _pos[0] := _y
        _pos[1] := _x
        _pos[2] := _dir
    done
    
    function is_visited(visited, coords)
    do
        cnt := visited[0]
        while cnt   
        do     
            if visited[cnt] = coords
                return true
            cnt := cnt - 1
        done
   
        return false
    done
    
    function rotate_180()
    do
        right
        right
        right
    done
    
    function load_box()
    do
        box_weight := test
        if look = 0 & box_weight > 0
            if WEIGHT + box_weight < MAX_WEIGHT - 1
                load box_weight       
    done
    
    function get_neighbours(visited)
    do
        res := 0
        cnt := 0
        while cnt != 6
        do
            if look = inf
            do
                while _pos != FINISH
                do
                    print(_pos, FINISH)
                    forward 1
                done
                return res
            done
            if test != inf
                load_box()
                
            if look > 0
            do
                forward 1
                b := is_visited(visited, get_coords())
                if b = false
                    res := push(res, _pos[2])
                backward 1
                rotate_180()
            done
            right
            cnt := cnt + 1
        done
        return res
    done
    
    function get_coords()
    do
        res := _pos[0]
        res[1] := _pos[1]
        return res
    done
    
    var FINISH
    
    function main()
    do
        FINISH[0] := -1
        FINISH[1] := -1
        FINISH[2] := -1
        
        _init(4, 1, 0)
        
        visited := 0
        visited := push(visited, get_coords())
        stack := 0
        
        cnt := 0
        coords := 0
        while _pos != FINISH
        do
            neighbours := get_neighbours(visited)
            if _pos = FINISH
                return 0
            
            if neighbours[0] > 0
            do
                stack := push(stack, _pos)
                res := pop(neighbours)
                next := res[0]
                neighbours := res[1]
                while _pos[2] != next
                    right
                forward 1
                visited := push(visited, get_coords())
            done
            eldef
            do
                if stack[0] = 0
                    return 1
                res := pop(stack)
                _pos := res[0]
                stack := res[1]
            done
            cnt := cnt + 1
            print(_pos)
        done
    done
"""

# text = r"""
#     function _init(_y, _x, _dir)
#     do
#         _pos[0] := _y
#         _pos[1] := _x
#         _pos[2] := _dir
#     done
#
#     function main()
#     do
#         _init(4, 1, 5)
#         print(look)
#     done
# """

# text = r"""
#     var FINISH
#
#     function main()
#     do
#         FINISH[0] := -1
#         FINISH[1] := -1
#         FINISH[2] := -1
#
#     done
# """

# text = r"""
#     function main()
#     do
#         a[1][2][3] := 3
#     done
# """


parser = Parser(yacc_debug=True)
ast = parser.parse(text, filename='<none>', debuglevel=False)
ast.show(attrnames=True, showcoord=True)

exec = nodevisitor.NodeVisitor(parser._err_flag, parser.tokens)
exec.visit(ast, entry_point=exec.scopes['__global'])
