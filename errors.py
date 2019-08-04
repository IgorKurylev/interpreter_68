from parser import Parser
import nodevisitor

# invalid unary expression
text = r""" 

    function main()
    do
        a := 5
        a[3] := 1
        -a
        a := 6
    done
"""

# invalid binary expression
text = r"""

    function main()
    do
        a := 5
        a[3] := 1
        a + 10
        a := 6
    done
"""

# a is already defined
text = r"""

    function main()
    do
        bool a := 5
        cell a := exit
    done
"""

parser = Parser(yacc_debug=True)
ast = parser.parse(text, filename='<none>', debuglevel=False)
ast.show(attrnames=True, showcoord=True)

exec = nodevisitor.NodeVisitor(parser._err_flag, parser.tokens)
exec.visit(ast, entry_point=exec.scopes['__global'])