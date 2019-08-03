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


def test_references_2():
    text = r"""

            function main()
            do
                a := 5
                b := a
                b := 6
            done
        """
    table = run_test(text)
    assert table['__global']['main']['a'] == [6]
    assert table['__global']['main']['b'] == [6]


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
    assert table['__global']['main']['a'] == [5]


def sharp_operator():
    text = r"""
        function main(a, b, c)
        do
            a := 5
            b := 1
            a[3] := b
            b[4] := 1000
            c := a
        done
    """
    table = run_test(text)
    assert table['__global']['main']['c'] == [1006]

