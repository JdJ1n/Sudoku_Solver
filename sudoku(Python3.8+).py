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


def cross(front, back):
    """Cross product of elements in A and elements in B."""
    return [a + b for a in front for b in back]


digits = '123456789'
rows = 'ABCDEFGHI'
cols = digits
squares = cross(rows, cols)
unitlist = ([cross(rows, c) for c in cols] +
            [cross(r, cols) for r in rows] +
            [cross(rs, cs) for rs in ('ABC', 'DEF', 'GHI') for cs in ('123', '456', '789')])
units = dict((s, [u for u in unitlist if s in u])
             for s in squares)
peers = dict((s, set(sum(units[s], [])) - {s})
             for s in squares)


# Unit Tests #

def test():
    """A set of tests that must pass."""
    assert len(squares) == 81
    assert len(unitlist) == 27
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
    """Convert grid to a dict of possible values, {square: digits}, or
    return False if a contradiction is detected."""
    # To start, every square can be any digit; then assign values from the grid.
    values = dict((s, digits) for s in squares)
    for s, d in grid_values(grid).items():
        if d in digits and not assign(values, s, d):
            return False  # (Fail if we can't assign d to square s.)
    return values


def grid_values(grid):
    """Convert grid into a dict of {square: char} with '0' or '.' for empties."""
    chars = [c for c in grid if c in digits or c in '0.']
    assert len(chars) == 81
    return dict(zip(squares, chars))


# Constraint Propagation #

def assign(values, s, d):
    """Eliminate all the other values (except d) from values[s] and propagate.
    Return values, except return False if a contradiction is detected."""
    other_values = values[s].replace(d, '')
    if all(eliminate(values, s, d2) for d2 in other_values):
        return values
    else:
        return False


def eliminate(values, s, d):
    """Eliminate d from values[s]; propagate when values or places <= 2.
    Return values, except return False if a contradiction is detected."""
    if d not in values[s]:
        return values  # Already eliminated
    values[s] = values[s].replace(d, '')
    # (1) If a square s is reduced to one value d2, then eliminate d2 from the peers.
    if len(values[s]) == 0:
        return False  # Contradiction: removed last value
    elif len(values[s]) == 1:
        d2 = values[s]
        if not all(eliminate(values, s2, d2) for s2 in peers[s]):
            return False
    # (2) If a unit u is reduced to only one place for a value d, then put it there.
    for u in units[s]:
        dplaces = [s for s in u if d in values[s]]
        if len(dplaces) == 0:
            return False  # Contradiction: no place for this value
        elif len(dplaces) == 1:
            # d can only be in one place in unit; assign it there
            if not assign(values, dplaces[0], d):
                return False
    return values


# Display as 2-D grid #

def display(values):
    """Display these values as a 2-D grid."""
    width = 1 + max(len(values[s]) for s in squares)
    line = '+'.join(['-' * (width * 3)] * 3)
    for r in rows:
        print(''.join(values[r + c].center(width) + ('|' if c in '36' else ''))
              for c in cols)
        if r in 'CF':
            print(line)


# Search #

def solve(grid: object) -> object: return hill_climbing(grid)


def search(values):
    """Using depth-first search and propagation, try all possible values."""
    if values is False:
        return False  # Failed earlier
    if all(len(values[s]) == 1 for s in squares):
        return values  # Solved!
    # Chose the unfilled square s with the fewest possibilities
    _, s = min((len(values[s]), s) for s in squares if len(values[s]) > 1)
    # values = find_hidden_singles(values, s)
    return some(search(assign(values.copy(), s, d))
                for d in values[s])


def randomsearch(values):
    """Using depth-first search and propagation, try all possible values."""
    if values is False:
        return False  # Failed earlier
    if all(len(values[s]) == 1 for s in squares):
        return values  # Solved!
    # Chose the unfilled square s randomly
    s = random.choice([s for s in squares if len(values[s]) > 1])
    values = find_hidden_singles(values, s)
    return some(randomsearch(assign(values.copy(), s, d))
                for d in values[s])


def find_hidden_singles(values, s):
    """Find hidden singles in the units of s."""
    for d in values[s]:
        for unit in units[s]:
            dplaces = [s for s in unit if d in values[s]]
            if len(dplaces) == 1:
                assign(values, dplaces[0], d)
    return values


def hill_climbing(grid):
    # Parse the grid and initialize values
    values = parse_grid(grid)
    current_conflicts = count_conflicts(values)

    while True:
        # Generate neighbors
        neighbors = generate_neighbors(values)

        # Evaluate neighbors
        best_neighbor = None
        best_conflicts = current_conflicts

        for neighbor in neighbors:
            neighbor_conflicts = count_conflicts(neighbor)
            if neighbor_conflicts < best_conflicts:
                best_neighbor = neighbor
                best_conflicts = neighbor_conflicts

        # If no better neighbor found, stop
        if best_neighbor is None or best_conflicts >= current_conflicts:
            break

        # Move to the best neighbor
        values = best_neighbor
        current_conflicts = best_conflicts

    return values

def generate_neighbors(values):
    neighbors = []
    for square in squares:
        # Randomly select two squares in the same 3x3 box
        neighbors_squares = [s for s in peers[square] if
                             len(values[s]) > 1 and len(peers[s].intersection(peers[square])) > 5]
        if len(neighbors_squares) < 2:
            continue
        square1, square2 = random.sample(neighbors_squares, 2)

        # Swap values
        new_values = values.copy()
        new_values[square1], new_values[square2] = new_values[square2], new_values[square1]
        neighbors.append(new_values)

    return neighbors



def count_conflicts(values):
    conflicts = 0
    for unit in unitlist:
        seen = {}
        for square in unit:
            for digit in values[square]:
                if digit in seen:
                    conflicts += 1
                seen[digit] = True
    return conflicts

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

def solve_all(grids, name='', showif=0.0):
    """Attempt to solve a sequence of grids. Report results.
    When showif is a number of seconds, display puzzles that take longer.
    When showif is None, don't display any puzzles."""

    def time_solve(grid):
        start = time.perf_counter()  # change to perf_counter() because time.clock() is moved in Python 3.8
        values = solve(grid)
        t = time.perf_counter() - start  # change to perf_counter() because time.clock() is moved in Python 3.8
        # Display puzzles that take long enough
        if showif is not None and t > showif:
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

    def unitsolved(unit): return set(values[s] for s in unit) == set(digits)

    return values is not False and all(unitsolved(unit) for unit in unitlist)


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
    # noinspection PyTypeChecker
    solve_all(from_file("1000sudoku.txt"), "95sudoku", None)
    # solve_all(from_file("easy50.txt", '========'), "easy", None)
    # solve_all(from_file("easy50.txt", '========'), "easy", None)
    # solve_all(from_file("top95.txt"), "hard", None)
    # solve_all(from_file("hardest.txt"), "hardest", None)
    # solve_all([random_puzzle() for _ in range(99)], "random", 100.0)

# References used:
# http://www.scanraid.com/BasicStrategies.htm
# http://www.sudokudragon.com/sudokustrategy.htm
# http://www.krazydad.com/blog/2005/09/29/an-index-of-sudoku-strategies/
# http://www2.warwick.ac.uk/fac/sci/moac/currentstudents/peter_cock/python/sudoku/
