# Chess problem solving using SAT solver

I tried to solve this problem using SAT solver after reading this : https://blog.mathieuacher.com/ProgrammingChessPuzzles/

## Goal

The goal is to place 4 queens and 1 bishop on a 8x8 chess board so that all cells are covered.

## Running this notebook

To run this notebook you need : 

- [Jupyter](https://jupyter.org/)
- [PySat](https://pysathq.github.io/docs/html/index.html)
- [python-chess](https://python-chess.readthedocs.io/en/latest/)

`pip install jupyter python-sat python-chess`

## Limitations

I had to force the position of the Bishop to a corner, this way, it is not necessary to encode constraint related to obstruction between pieces.

Another solution would be to compute a new solution with the SAT solver until it is effectively valid (not tested, maybe it's too long).

It is theorically possible to model such thing in SAT but it was too complicated and require a lot of clauses.