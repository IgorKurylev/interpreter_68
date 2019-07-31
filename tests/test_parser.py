from parser import *

import sys, os

my_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, my_path + '/../')


def run_test(text):
    parser = Parser(yacc_debug=True)
    return parser.parse(text, debuglevel=False)


def test_basic_actions():
    text = r"""
        function main() 
        do
             int a := 4
             b := a
             b[4] := a ^ b
             a := gg()
             a + #b
             a ^ look
        done
    """
    run_test(text)


def test_conditions():
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
    run_test(text)


def test_wrong_newline():
    text = r"""
        function main() 
        do
            if 3+2 do  
                f := 4
            done
        done
    """
    try:
        run_test(text)
    except ParseError:
        pass


def test_while():
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
    run_test(text)


def test_functions_in_functions():
    text = r"""
        function main() 
        do
            function ggg()
            do
                function hhh()
                do
                    if 5 ^ 1
                        print(a[5])
                done
            done
        done
    """
    run_test(text)



