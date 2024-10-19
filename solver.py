from pysat.card import *
from pysat.solvers import Glucose42
import chess

class SolverBuilder():
    
    def __init__(self, size=8):
        self.solver = Solver(size)
        
        self.bishop_count = 0
        self.queen_count = 0
        self.knight_count = 0
        self.rook_count = 0

        self.pos_vars = []
        self.cover_vars = []

        self.obstacle_var = self.solver.create_grid_variables("O")
        self.piece_order = []

    def add_bishop(self, count):
        for i in range(count):
            self.bishop_count += 1
            name = f'B{self.bishop_count}'
            cname = f'CB{self.bishop_count}'

            pos_var = self.solver.create_grid_variables(name)
            cover_var = self.solver.create_grid_variables(cname)

            self.pos_vars.append(pos_var)
            self.cover_vars.append(cover_var)

            self.solver.add_unique_clause(pos_var)
            self.solver.add_bishop_constraints(name, cname)

            self.piece_order.append('B')

        return self

    def add_queen(self, count):
        for i in range(count):
            self.queen_count += 1
            name = f'Q{self.queen_count}'
            cname = f'CQ{self.queen_count}'

            pos_var = self.solver.create_grid_variables(name)
            cover_var = self.solver.create_grid_variables(cname)

            self.pos_vars.append(pos_var)
            self.cover_vars.append(cover_var)

            self.solver.add_unique_clause(pos_var)
            self.solver.add_queen_constraints(name, cname)

            self.piece_order.append('Q')

        return self

    def add_knight(self, count):
        for i in range(count):
            self.knight_count += 1
            name = f'N{self.knight_count}'
            cname = f'CN{self.knight_count}'

            pos_var = self.solver.create_grid_variables(name)
            cover_var = self.solver.create_grid_variables(cname)

            self.pos_vars.append(pos_var)
            self.cover_vars.append(cover_var)

            self.solver.add_unique_clause(pos_var)
            self.solver.add_knight_constraints(name, cname)

            self.piece_order.append('N')

        return self

    def add_rook(self, count):
        for i in range(count):
            self.rook_count += 1
            name = f'R{self.rook_count}'
            cname = f'CR{self.rook_count}'

            pos_var = self.solver.create_grid_variables(name)
            cover_var = self.solver.create_grid_variables(cname)

            self.pos_vars.append(pos_var)
            self.cover_vars.append(cover_var)

            self.solver.add_unique_clause(pos_var)
            self.solver.add_rook_constraints(name, cname)

            self.piece_order.append('R')

        return self
            
    def build(self):
        self.solver.add_board_completion_constraint(*self.cover_vars)
        self.solver.add_cells_constraint(*self.pos_vars)
        
        self.solver.add_merged_constraint(*([self.obstacle_var] + self.pos_vars))

        return (self.solver, self.piece_order)

    def get_result(self):
        self.build()
        
        g = Glucose42()
        
        for clause in self.solver.clauses:
            g.add_clause(clause)
        
        def get_name(num):
            for key, val in variables_dict.items():
                if val==num:
                    return key
        
        display = None
        
        if not g.solve():
            display = 'No solution'
        else:   
            pos = []
            for lit in g.get_model():
                if lit > 64 and (((lit - 1) // 64) % 2) == 1:
                    pos.append(lit % 64)
            
            piece_dict = {'Q': chess.QUEEN, 'B': chess.BISHOP, 'N': chess.KNIGHT, 'R': chess.ROOK}
            board = chess.Board(fen=None)
            for i in range(len(self.piece_order)):
                board.set_piece_at(pos[i] - 1, chess.Piece(piece_dict[self.piece_order[i]], chess.WHITE))
            display = board
                
        return display

class Solver():
    
    def __init__(self, size=8):
        # Size of the chessboard
        self.size = size
        # Variables involved in CNF model
        self.variables_dict = {} 
        # Variables counter (start at 1 because 0 has special meaning for some SAT solvers 
        self.var_count = 1
        self.clauses = []

    def create_grid_variables(self, name):
        variables = []
        for i in range(self.size):
            for j in range(self.size):
                var = f"{name}_({i},{j})"
                variables.append(var)
                self.variables_dict[var] = self.var_count
                self.var_count += 1
        
        return variables

    def add_board_completion_constraint(self, *grids):
        for t in zip(*grids):
            cl = []
            for e in t:
                cl.append(self.variables_dict[e])
            self.clauses.append(cl)
    
    def add_unique_clause(self, variables):
        places = [self.variables_dict[var] for var in variables]
        cnf = CardEnc.equals(lits=places, encoding=EncType.pairwise, top_id=self.var_count)
        
        self.clauses += cnf.clauses

    def add_atmost_clause(self, variables):
        places = [self.variables_dict[var] for var in variables]
        cnf = CardEnc.atmost(lits=places, encoding=EncType.pairwise, top_id=self.var_count)
        
        self.clauses += cnf.clauses

    def add_cells_constraint(self, *grids):
        for t in zip(*grids):        
            self.add_atmost_clause(t)

    def add_merged_constraint(self, *grids):
        for t in zip(*grids):
            o = t[0]
            cl=[-self.variables_dict[o]]
            for e in t[1:]:
                self.clauses.append([-self.variables_dict[e], self.variables_dict[o]])
                cl.append(self.variables_dict[e])
            self.clauses.append(cl)

    def _get_obstacles(self, x1, y1, x2, y2):
        dx = 1 if x2 > x1 else 0 if x2==x1 else -1
        dy = 1 if y2 > y1 else 0 if y2==y1 else -1
        d = max(abs(x2-x1), abs(y2-y1)) if dx*dy==0 else min(abs(x2-x1), abs(y2-y1))
    
        obstacles=[]
    
        for i in range(1, d + 1):
            x=x1+i*dx
            y=y1+i*dy
    
            obstacles.append(self.variables_dict[f'O_({x},{y})'])
    
        return obstacles

    def add_queen_constraints(self, name, cname):
        for i in range(self.size):
            for j in range(self.size):
                var_name = self.variables_dict[(f"{name}_({i},{j})")]
                
                under_pos = []
                
                for k in range(-min(i, j), min(self.size - i, self.size - j)):
                    under_pos.append(self.variables_dict[f"{cname}_({i+k},{j+k})"])
                    C_var = self.variables_dict[f"{cname}_({i+k},{j+k})"]
                    obstacles = self._get_obstacles(i, j, i+k, j+k)
                    cl = [-var_name, C_var]
                    for o in obstacles:
                        cl.append(o)
                        self.clauses.append([-var_name, -o, -C_var])
                    self.clauses.append(cl)
                    
                    
                for k in range(-min(i, self.size - j - 1), min(self.size - i, j + 1)):
                    under_pos.append(self.variables_dict[f"{cname}_({i+k},{j-k})"])
                    C_var = self.variables_dict[f"{cname}_({i+k},{j-k})"]
                    obstacles = self._get_obstacles(i, j, i+k, j-k)
                    cl = [-var_name, C_var]
                    for o in obstacles:
                        cl.append(o)
                        self.clauses.append([-var_name, -o, -C_var])
                    self.clauses.append(cl)
                
                for k in range(self.size):
                    C_var1 = self.variables_dict[f"{cname}_({k},{j})"]
                    C_var2 = self.variables_dict[f"{cname}_({i},{k})"]
                    under_pos.append(C_var1)
                    under_pos.append(C_var2)
                    obstacles1 = self._get_obstacles(i, j, k, j)
                    cl1 = [-var_name, C_var1]
                    for o in obstacles1:
                        cl1.append(o)
                        self.clauses.append([-var_name, -o, -C_var1])
                    
                    obstacles2 = self._get_obstacles(i, j, i, k)
                    cl2 = [-var_name, C_var2]
                    for o in obstacles2:
                        cl2.append(o)
                        self.clauses.append([-var_name, -o, -C_var2])
    
                    self.clauses.append(cl1)
                    self.clauses.append(cl2)
                    
                    
                for x in range(self.size):
                    for y in range(self.size):
                        current_var = self.variables_dict[f"{cname}_({x},{y})"]
                        if not current_var in under_pos:
                            self.clauses.append([-var_name, -current_var])

    def add_rook_constraints(self, name, cname):
        for i in range(self.size):
            for j in range(self.size):
                var_name = self.variables_dict[(f"{name}_({i},{j})")]
                
                under_pos = []
                
                for k in range(self.size):
                    C_var1 = self.variables_dict[f"{cname}_({k},{j})"]
                    C_var2 = self.variables_dict[f"{cname}_({i},{k})"]
                    under_pos.append(C_var1)
                    under_pos.append(C_var2)
                    obstacles1 = self._get_obstacles(i, j, k, j)
                    cl1 = [-var_name, C_var1]
                    for o in obstacles1:
                        cl1.append(o)
                        self.clauses.append([-var_name, -o, -C_var1])
                    
                    obstacles2 = self._get_obstacles(i, j, i, k)
                    cl2 = [-var_name, C_var2]
                    for o in obstacles2:
                        cl2.append(o)
                        self.clauses.append([-var_name, -o, -C_var2])
    
                    self.clauses.append(cl1)
                    self.clauses.append(cl2)
                    
                    
                for x in range(self.size):
                    for y in range(self.size):
                        current_var = self.variables_dict[f"{cname}_({x},{y})"]
                        if not current_var in under_pos:
                            self.clauses.append([-var_name, -current_var])


    def add_bishop_constraints(self, name, cname):
        for i in range(self.size):
            for j in range(self.size):
                var_name = self.variables_dict[(f"{name}_({i},{j})")]
    
                under_pos=[]
                
                for k in range(-min(i, j), min(self.size - i, self.size - j)):
                    under_pos.append(self.variables_dict[f"{cname}_({i+k},{j+k})"])
                    C_var = self.variables_dict[f"{cname}_({i+k},{j+k})"]
                    obstacles = self._get_obstacles(i, j, i+k, j+k)
                    cl = [-var_name, C_var]
                    for o in obstacles:
                        cl.append(o)
                        self.clauses.append([-var_name, -o, -C_var])
                    self.clauses.append(cl)
                    
                    
                for k in range(-min(i, self.size - j - 1), min(self.size - i, j + 1)):
                    under_pos.append(self.variables_dict[f"{cname}_({i+k},{j-k})"])
                    C_var = self.variables_dict[f"{cname}_({i+k},{j-k})"]
                    obstacles = self._get_obstacles(i, j, i+k, j-k)
                    cl = [-var_name, C_var]
                    for o in obstacles:
                        cl.append(o)
                        self.clauses.append([-var_name, -o, -C_var])
                    self.clauses.append(cl)
    
                for x in range(self.size):
                    for y in range(self.size):
                        current_var = self.variables_dict[f"{cname}_({x},{y})"]
                        if not current_var in under_pos:
                            self.clauses.append([-var_name, -current_var])

    def add_knight_constraints(self, name, cname):
        moves = [
            (1, 2),
            (1, -2),
            (-1, 2),
            (-1, -2),
            (2, 1),
            (-2, 1),
            (2, -1),
            (-2, -1),
        ]
        
        for i in range(self.size):
            for j in range(self.size):
                var_name = self.variables_dict[(f"{name}_({i},{j})")]
    
                under_pos=[self.variables_dict[(f"{cname}_({i},{j})")]]
    
                for dx,dy in moves:
                    x = i + dx
                    y = j + dy
                    
                    if x >= 0 and y >=0 and x < self.size and y < self.size:
                        under_pos.append(self.variables_dict[(f"{cname}_({x},{y})")])
                        
                
                for x in range(self.size):
                    for y in range(self.size):
                        current_var = self.variables_dict[f"{cname}_({x},{y})"]
                        self.clauses.append([-var_name, current_var if current_var in under_pos else -current_var])

    def get_clauses(self):
        return self.clauses

    

    