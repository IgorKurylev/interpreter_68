
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

parser = Parser(yacc_debug=True)
# with open("fib.txt", "r") as f:
#      ast = parser.parse(f.read(), filename='test3.txt', debuglevel=False)
ast = parser.parse(text, filename='<none>', debuglevel=False)
ast.show(attrnames=True, showcoord=True)

exec = nodevisitor.NodeVisitor(parser._err_flag, parser.tokens)
exec.visit(ast, entry_point=exec.scopes['__global'])
