# Solve Every Sudoku Puzzle
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
values_tried = []


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
    values_tried.append(values)
    return values


def grid_values(grid):
    """Convert grid into a dict of {square: char} with '0' or '.' for empties."""
    unfixed.clear()
    values_tried.clear()
    chars = [c for c in grid if c in digits or c in '0.']
    assert len(chars) == 81
    make_grid = dict(zip(squares, chars))
    unfixed.extend(s for s in squares if make_grid[s] in '0.')
    return make_grid


# Constraint Propagation #

def get_conflicts(values):
    """Calculate the number of conflicts in rows and cols only count non-fixed cells."""
    conflicts = []
    # Check rows
    for i in 'ABCDEFGHI':
        row = [values[i + j] for j in '123456789']
        for digit in '123456789':
            count = row.count(digit)
            if count > 1:
                for k in '123456789':
                    if values[i + k] == digit:
                        conflicts.append(i + k)
    # Check columns
    for j in '123456789':
        col = [values[i + j] for i in 'ABCDEFGHI']
        for digit in '123456789':
            count = col.count(digit)
            if count > 1:
                for k in 'ABCDEFGHI':
                    if values[k + j] == digit:
                        conflicts.append(k + j)
    final_conflicts = list(set(conflicts) & set(unfixed))
    return final_conflicts


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


def simulated_annealing(values, max_iteration=50000):
    """Using simulated annealing, try all possible values."""
    current = values.copy()
    current_conflicts = get_conflicts(current.copy())
    current_score = len(current_conflicts)
    t_initial = 3.0
    t = t_initial
    t_min = 1e-126
    alpha = 0.99
    iteration = 0
    restart = 0

    while t > t_min and iteration <= max_iteration:
        iteration += 1
        neighbor = generate_neighbor(current, unfixed)
        if (not neighbor) or (current_score == 0):
            return current.copy()
        values_tried.append(current)
        next_neighbor = neighbor
        next_conflicts = get_conflicts(next_neighbor)
        next_score = len(next_conflicts)
        delta = next_score - current_score
        if delta < 0 or random.uniform(0, 1) < math.exp(-delta / t):
            current, current_conflicts, current_score = next_neighbor, next_conflicts, next_score
            restart = 0
        else:
            restart += 1
        t = t * alpha
        if restart >= 1000:
            restart = 0
            values = reheat(values, unfixed)
            t = t_initial
    return current.copy()


def generate_neighbor(values, non_fixed):
    max_attempts = 500
    attempts = 0
    i = random.choice(squares)
    while i not in non_fixed and attempts < max_attempts:
        i = random.choice(squares)
        attempts += 1
    if attempts == max_attempts:
        return values
    j = random.choice(cube[i])
    while i not in non_fixed or i == j and attempts < max_attempts:
        j = random.choice(cube[i])
        attempts += 1
    if attempts == max_attempts:
        return values
    neighbor = values.copy()
    neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
    return neighbor


def reheat(values, non_fixed):
    restart = values.copy()
    for s in squares:
        if s in unfixed:
            filled_values = [values[i][0] for i in cube[s] if i not in non_fixed]
            possible_values = set(str(i) for i in range(1, 10)) - set(filled_values)
            if possible_values:
                restart[s] = random.choice(list(possible_values))
    return restart


# Utilities #


def from_file(filename, sep='\n'):
    """Parse a file into a list of strings, separated by sep."""
    return open(filename).read().strip().split(sep)


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


if __name__ == '__main__':
    test()
    solve_all(from_file("simple.txt"), "easy", 0.05)
    # noinspection PyTypeChecker
    solve_all(from_file("100sudoku.txt"), "easy", 0.05)
    # noinspection PyTypeChecker
    solve_all(from_file("1000sudoku.txt"), "easy", None)
    # noinspection PyTypeChecker
    solve_all(from_file("top95.txt"), "hard", None)
    # solve_all(from_file("hardest.txt"), "hardest", None)
    # solve_all([random_puzzle() for _ in range(99)], "random", 100.0)

# References used:
# http://www.scanraid.com/BasicStrategies.htm
# http://www.sudokudragon.com/sudokustrategy.htm
# http://www.krazydad.com/blog/2005/09/29/an-index-of-sudoku-strategies/
# http://www2.warwick.ac.uk/fac/sci/moac/currentstudents/peter_cock/python/sudoku/
