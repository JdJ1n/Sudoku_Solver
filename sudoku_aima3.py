from aima3.search import *
from sudoku import *


def heuristique_h0(noeud: Node):
    return 0


class Sudoku(Problem):
    def __init__(self, grid):
        super().__init__(parse_grid(grid))
        self.nb_etats_generes = 0

    def actions(self, state):
        action_possibles = []
        if state is False:
            return action_possibles
        else:
            n, s_choice = min((len(state[s]), s) for s in squares if len(state[s]) > 1)
            for val_choice in state[s_choice]:
                action_possibles.append((s_choice, val_choice))
            return action_possibles

    def result(self, state, action):
        square, value = action[0], action[1]
        new_state = assign(state.copy(), square, value)
        self.nb_etats_generes += 1
        return new_state

    def goal_test(self, state):
        if state is False:
            return False
        else:
            return all(len(state[s]) == 1 for s in squares)


if __name__ == "__main__":
    start_time = time.time()
    prob_sudoku = Sudoku(grid2)
    solution = search.recursive_best_first_search(prob_sudoku, heuristique_h0)
    print(time.time() - start_time)
