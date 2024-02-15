# Solve Every Sudoku Puzzle
import itertools
# See http://norvig.com/sudoku.html

# Throughout this program we have:
#   r is a row,    e.g. 'A'
#   c is a column, e.g. '3'
#   s is a square, e.g. 'A3'
#   d is a digit,  e.g. '9'
#   u is a unit,   e.g. ['A1','B1','C1','D1','E1','F1','G1','H1','I1']
#   grid is a grid,e.g. 81 non-blank chars, e.g. starting with '.18...7...
#   values is a dict of possible values, e.g. {'A1':'12349', 'A2':'8', ...}
import time
import random
import math


def cross(front, back):
    """Cross product of elements in A and elements in B."""
    return [a + b for a in front for b in back]


digits = '123456789'
rows = 'ABCDEFGHI'
cols = digits
squares = cross(rows, cols)
unit_list = ([cross(rows, c) for c in cols] +
             [cross(r, cols) for r in rows] +
             [cross(rs, cs) for rs in ('ABC', 'DEF', 'GHI') for cs in ('123', '456', '789')])
cube = {s: [u for u in unit if u != s] for unit in unit_list for s in unit if len(unit) == 9}
units = dict((s, [u for u in unit_list if s in u])
             for s in squares)
peers = dict((s, set(sum(units[s], [])) - {s})
             for s in squares)
unfixed = []


# Unit Tests #

def test():
    """A set of tests that must pass."""
    assert len(squares) == 81
    assert len(unit_list) == 27
    assert all(len(units[s]) == 3 for s in squares)
    assert all(len(peers[s]) == 20 for s in squares)
    assert units['C2'] == [['A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2'],
                           ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9'],
                           ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']]
    assert peers['C2'] == {'A2', 'B2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2', 'C1', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8',
                           'C9', 'A1', 'A3', 'B1', 'B3'}
    print('All tests pass.')


# Parse a Grid #

def parse_grid(grid):
    values = grid_values(grid)
    for s in squares:
        if values[s] in '0.':
            filled_values = [values[i][0] for i in cube[s] if values[i] not in '0.']
            possible_values = set(str(i) for i in range(1, 10)) - set(filled_values)
            if possible_values:
                values[s] = random.choice(list(possible_values))
    return values


def grid_values(grid):
    """Convert grid into a dict of {square: char} with '0' or '.' for empties."""
    unfixed.clear()
    chars = [c for c in grid if c in digits or c in '0.']
    assert len(chars) == 81
    make_grid = dict(zip(squares, chars))
    unfixed.extend(s for s in squares if make_grid[s] in '0.')
    return make_grid


# Constraint Propagation #

def count_conflicts(values, non_fixed):
    """Calculate the number of conflicts in rows and cols only count non-fixed cells."""
    conflicts = 0
    # Check rows
    for i in 'ABCDEFGHI':
        row = [values[i + j] for j in '123456789']
        for digit in '123456789':
            count = row.count(digit)
            if count > 1:
                unfixed_count = sum(1 for j in '123456789' if (i + j) in non_fixed and values[i + j] == digit)
                conflicts += 3 if unfixed_count == 3 else 2 if unfixed_count == 2 else 1
    # Check columns
    for j in '123456789':
        col = [values[i + j] for i in 'ABCDEFGHI']
        for digit in '123456789':
            count = col.count(digit)
            if count > 1:
                unfixed_count = sum(1 for i in 'ABCDEFGHI' if (i + j) in non_fixed and values[i + j] == digit)
                conflicts += 3 if unfixed_count == 3 else 2 if unfixed_count == 2 else 1
    return conflicts


def assign(values, s, d):
    for c in cube[s]:
        if d in values[c]:
            return False
    else:
        values[s] = d
        return values


# Display as 2-D grid #

def display(values):
    """Display these values as a 2-D grid."""
    width = 1 + max(len(values[s]) for s in squares)
    line = '+'.join(['-' * (width * 3)] * 3)
    for r in rows:
        print(''.join(values[r + c].center(width) + ('|' if c in '36' else '')
                      for c in cols))
        if r in 'CF':
            print(line)


# Search #

def solve(grid: object) -> object: return simulated_annealing(parse_grid(grid))


def simulated_annealing(values):
    """Using simulated annealing, try all possible values."""
    current = values
    current_score = count_conflicts(current, unfixed)
    t = 3.0
    t_min = 1e-26
    alpha = 0.99

    while t > t_min:
        neighbors = generate_neighbor(current, unfixed)
        if (not neighbors) or (current_score == 0):
            return current.copy()
        next_neighbor = random.choice(neighbors)
        next_score = count_conflicts(next_neighbor, unfixed)
        delta = next_score - current_score
        if delta < 0 or random.uniform(0, 1) < math.exp(-delta / t):
            current, current_score = next_neighbor, next_score
        t = t * alpha

    return current.copy()


def generate_neighbors(values, non_fixed):
    neighbors = []
    s_values = ['A1', 'A4', 'A7', 'D1', 'D4', 'D7', 'H1', 'H4', 'H7']
    for s in s_values:
        unfilled_squares = [sq for sq in cube[s] if sq in non_fixed]
        if len(unfilled_squares) < 2:
            continue
        combinations = list(itertools.combinations(unfilled_squares, 2))
        for c in combinations:
            square1, square2 = c
            new_values = values.copy()
            new_values[square1], new_values[square2] = new_values[square2], new_values[square1]
            neighbors.append(new_values)
    return neighbors


def generate_neighbor(values, non_fixed):
    neighbors = []
    s_values = ['A1', 'A4', 'A7', 'D1', 'D4', 'D7', 'H1', 'H4', 'H7']
    for s in s_values:
        unfilled_squares = [sq for sq in cube[s] if sq in non_fixed]
        if len(unfilled_squares) < 2:
            continue
        combination = random.choice(list(itertools.combinations(unfilled_squares, 2)))
        square1, square2 = combination
        new_values = values.copy()
        new_values[square1], new_values[square2] = new_values[square2], new_values[square1]
        neighbors.append(new_values)
    return neighbors


# Utilities #

def some(seq):
    """Return some element of seq that is true."""
    for e in seq:
        if e:
            return e
    return False


def from_file(filename, sep='\n'):
    """Parse a file into a list of strings, separated by sep."""
    return open(filename).read().strip().split(sep)


def shuffled(seq):
    """Return a randomly shuffled copy of the input sequence."""
    seq = list(seq)
    random.shuffle(seq)
    return seq


# System test #

def solve_all(grids, name='', show_if=0.0):
    """Attempt to solve a sequence of grids. Report results.
    When show_if is a number of seconds, display puzzles that take longer.
    When show_if is None, don't display any puzzles."""

    def time_solve(grid):
        start = time.perf_counter()
        values = solve(grid)
        t = time.perf_counter() - start
        # Display puzzles that take long enough
        if show_if is not None and t > show_if:
            display(grid_values(grid))
            if values:
                # noinspection PyTypeChecker
                display(values)
            print('(%.3f seconds)\n' % t)
        return t, solved(values)

    times, results = zip(*[time_solve(grid) for grid in grids])
    n = len(grids)
    if n > 1:
        print("Solved %d of %d %s puzzles (avg %.3f secs (%d Hz), max %.3f secs)." % (
            sum(results), n, name, sum(times) / n, n / sum(times), max(times)))


def solved(values):
    """A puzzle is solved if each unit is a permutation of the digits 1 to 9."""

    def unit_solved(unit): return set(values[s] for s in unit) == set(digits)

    return values is not False and all(unit_solved(unit) for unit in unit_list)


def random_puzzle(n=17):
    """Make a random puzzle with N or more assignments. Restart on contradictions.
    Note the resulting puzzle is not guaranteed to be solvable, but empirically
    about 99.8% of them are solvable. Some have multiple solutions."""
    values = dict((s, digits) for s in squares)
    for s in shuffled(squares):
        if not assign(values, s, random.choice(values[s])):
            break
        ds = [values[s] for s in squares if len(values[s]) == 1]
        if len(ds) >= n and len(set(ds)) >= 8:
            return ''.join(values[s] if len(values[s]) == 1 else '.' for s in squares)
    return random_puzzle(n)  # Give up and make a new puzzle


grid1 = '003020600900305001001806400008102900700000008006708200002609500800203009005010300'
grid2 = '4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......'
hard1 = '.....6....59.....82....8....45........3........6..3.54...325..6..................'

if __name__ == '__main__':
    test()
    solve_all(from_file("simple.txt"), "easy", 0.05)
    # noinspection PyTypeChecker
    solve_all(from_file("100sudoku.txt"), "easy", 0.05)
    # noinspection PyTypeChecker
    # solve_all(from_file("1000sudoku.txt"), "easy", None)
    # noinspection PyTypeChecker
    # solve_all(from_file("top95.txt"), "hard", None)
    # solve_all(from_file("hardest.txt"), "hardest", None)
    # solve_all([random_puzzle() for _ in range(99)], "random", 100.0)

# References used:
# http://www.scanraid.com/BasicStrategies.htm
# http://www.sudokudragon.com/sudokustrategy.htm
# http://www.krazydad.com/blog/2005/09/29/an-index-of-sudoku-strategies/
# http://www2.warwick.ac.uk/fac/sci/moac/currentstudents/peter_cock/python/sudoku/
