from parser import *
from nodevisitor import *

import sys, os

my_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, my_path + '/../')

parser = Parser(yacc_debug=True)


def run_test(text):
    ast = parser.parse(text, debuglevel=False)
    exec = NodeVisitor(parser._err_flag, parser.tokens)
    return exec.visit(ast, entry_point=exec.scopes['__global'])


def test_references_1():
    text = r"""

        function main()
        do
            a := 5
            b := 1
            a[3] := b
            b[4] := 1000
            a[3][2] := -1
        done
    """

    table = run_test(text)
    assert table['__global']['main']['a'] == [5, 'undef', 'undef', [1, 'undef', -1, 'undef', 1000]]
    assert table['__global']['main']['b'] == [1, 'undef', -1, 'undef', 1000]


# def test_references_2():
#     text = r"""
#
#             function main()
#             do
#                 a := 5
#                 b := a
#                 b := 6
#             done
#         """
#     table = run_test(text)
#     assert table['__global']['main']['a'] == [6]
#     assert table['__global']['main']['b'] == [6]


def test_references_3():
    text = r"""

            function main()
            do
                a := 5
                b := a
                b[0] := 6
            done
        """
    table = run_test(text)
    assert table['__global']['main']['a'] == [6]
    assert table['__global']['main']['b'] == [6]


def test_fibonacci():
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

    table = run_test(text)
    assert table['__global']['main']['a'] == [1, 1, 2, 3, 5]


def test_factorial():
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
    table = run_test(text)
    assert table['__global']['main']['a'] == [1, 2, 6, 24, 120]


def test_nested_functions():
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
    table = run_test(text)
    assert table['__global']['main']['a'] == 5


def test_sharp_operator():
    text = r"""
        function main(a, b, c)
        do
            a := 5
            b := 1
            a[3] := b
            b[4] := 1000
            c := #a
        done
    """
    table = run_test(text)
    assert table['__global']['main']['c'] == [1006]


def test_while():
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
    table = run_test(text)
    assert table['__global']['main']['a'] == 10


def test_casts():
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
    table = run_test(text)
    assert table['__global']['main']['a'] == [True]
    assert table['__global']['main']['b'] == [1]
    assert table['__global']['main']['c'] == ['empty']
    assert table['__global']['main']['d'] == [True]
    assert table['__global']['main']['e'] == [0]


def test_casts_2():  # cast empty to 0
    text = r"""
        function main()
        do
            a := 1 + empty
            b := true ^ exit
        done
    """
    table = run_test(text)
    assert table['__global']['main']['a'] == [1]
    assert table['__global']['main'].get('b') is None  # will not create b because of undefined cast


def test_move_operators():  # forward empty/false <=> forward 0
    text = r"""
        function main()
        do
            right
            forward empty
            right
            load 1
            forward 1
            right
            load 1
            forward 1
            forward false
            forward 1
        done
    """
    table = run_test(text)
    assert table['__global']['_pos'] == [3, 0, 3]


def test_load_drop():
    text = r"""
        function main()
        do
            right
            right
            load 1
            forward 1
            right
            load 1
            forward 1
            left
            drop 1
            left
            drop 1
            left
            left
            drop 1
        done
    """
    table = run_test(text)
    assert table['__global']['_map'][3][0] == [0, 'inf', 1, 'inf', 'inf', 1]
    assert table['__global']['_pos'] == [3, 0, 5]


def test_operator_test():
    text = r"""
        function main()
        do
            a := test
            right
            a[1] := test
            right
            load 1
            a[2] := test
            right
            a[3] := test
            right
            a[4] := test
            right
            a[5] := test
        done
    """
    table = run_test(text)
    assert table['__global']['main']['a'] == ['undef', 'inf', 'inf', 'inf', 'undef', 'inf']


def test_operator_look():
    text = r"""
        function main()
        do
            a := look
            right
            right
            load 1
            a[1] := look
        done
    """
    table = run_test(text)
    assert table['__global']['main']['a'] == ['inf', 1]


def test_stack_1():
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
            stack_push(1)
            stack_push(2)
            stack_push(3)

            a := stack_pop()
            a[1] := stack_pop()
            a[2] := stack_pop()
        done

    """
    table = run_test(text)
    assert table['__global']['main']['a'] == [3, 2, 1]


def test_stack_2():
    # in this implementation stack is array: [size, el1, el2, ...]
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

        function main()
        do
            var st := 0

            st := push(st, 1)
            st := push(st, 2)
            st := push(st, 3)

            res := pop(st)
            st := res[1]
            a := res[0]

            res := pop(st)
            st := res[1]
            a[1] := res[0]

            res := pop(st)
            st := res[1]
            a[2] := res[0]
        done
    """
    table = run_test(text)
    assert table['__global']['main']['a'] == [3, 2, 1]
