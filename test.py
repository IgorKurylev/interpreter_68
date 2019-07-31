
from parser import Parser

# text = r"""
#     big main() begin
#         rr.
#         rr.
#         go.
#         rr.
#         rr.
#         go.
#         rl.
#         rl.
#         go.
#         go.
#         print(_x_pos, _y_pos, _rotation).
#         print(sonar).
#         print(sonar).
#         print(sonar).
#
#         field small tiny t << sonar.
#     end.
# """

#
# text = r"""
#
#
#     big tst << 0.
#     field small tiny t << {{1,2,3}, {1,2}}.
# """
#
#
# text = r"""
#     field small tiny t << {{{1,2,3}, {1,2}, {1,2,3,4}}, {{1,2,3}, {1}}}.
# """



# text = r"""
#     big main() begin
#         field small tiny f << 1.
#         f[] << 3.
#     end.
# """
#
# text = r"""
#     big main() begin
#         f << 3.
#     end.
# """
#
# text = r"""
#
# big main() begin
#     err().
# end.
#
# big err() begin
#
# end.
#
# """

# text = r"""
# big var << 0.
# big var << 3.
# """

# text = r"""
#     small var << 100000.
# """

# text = r"""
#     small var << {1,2,3,4,5,6,7}.
# """

# text = r"""
#     big main() begin
#         field small tiny f << 5.
#         print(f[0][1][5]).
#     end.
# """

# text = r"""
# big err() begin
#
# end.
#
# big main() begin
#     small t << 3.
#     err(t).
# end.
# """

# text = r"""
# big err(small t) begin
#
# end.
#
# big main() begin
#     err().
# end.
# """

# text = r"""
#     big main(small t) begin
#         big t << 4.
#     end.
# """

# text = r"""
#     big main() begin
#         field small tiny f << 5.
#
#         print(f[f]).
#     end.
# """

# text = r"""
#     big main() begin
#         field small tiny f << 5.
#
#         print(f[t()]).
#
#     end.
# """

# text = r"""
#         big main() begin
#         field small tiny f << 5.
#
#         print(f[t]).
#
#     end.
# """

# text = r"""
#
#     big main() begin
#       small t >> 10.
#     end.
# """
#
# text = r"""
#     big main() begin
#         until 1 do begin
#
#         end.
#     end.
# """

# text = r"""
#     big main() begin
#         small t << 0.
#         4.
#         t.
#     end.
# """


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

parser = Parser(yacc_debug=True)
# with open("fib.txt", "r") as f:
#      ast = parser.parse(f.read(), filename='test3.txt', debuglevel=False)
ast = parser.parse(text, filename='<none>', debuglevel=True)
ast.show(attrnames=True, showcoord=True)

# exec = nodevisitor.NodeVisitor(parser._err_flag, parser.func_dict)
# exec.visit(ast)
