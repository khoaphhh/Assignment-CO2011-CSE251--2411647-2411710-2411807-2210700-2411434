import time
from pulp import LpProblem, LpVariable, LpMinimize, lpSum, LpBinary, LpStatus, PULP_CBC_CMD
from pyeda.inter import expr, expr2bdd
from copy import deepcopy


class DeadlockDetector:

    def __init__(self, petri_net, symbolic_solver):

        self.petri_net = petri_net
        self.bdd_solver = symbolic_solver
        self.transition_inputs = self.build_transition_input_map()

    def build_transition_input_map(self):
        input_map = {trans_id: set() for trans_id in self.petri_net.transitions}

        for source, target in self.petri_net.arcs:
            if source in self.petri_net.places and target in self.petri_net.transitions:
                input_map[target].add(source)

        return input_map

    def convert_marking_to_bdd(self, marking):

        if not marking:
            return expr2bdd(expr(1))

        boolean_clauses = []
        for place_id in sorted(self.petri_net.places.keys()):
            has_token = marking.get(place_id, 0)
            clause = f"x_{place_id}" if has_token == 1 else f"~x_{place_id}"
            boolean_clauses.append(clause)

        bdd_formula = " & ".join(boolean_clauses)
        return expr2bdd(expr(bdd_formula))

    def detect_deadlock(self, max_attempts=50):
        start_time = time.time()

        if not hasattr(self.bdd_solver, 'current_set'):
            try:
                current_states = self.bdd_solver.encode_initial_marking()
                transition_relation = self.bdd_solver.encode_transition_relation()
                state_variables = list(self.bdd_solver.place_to_curr_var.values())

                bdd_iteration = 0
                max_bdd_iterations = 100

                while bdd_iteration < max_bdd_iterations:
                    bdd_iteration += 1

                    state_transition_product = current_states & transition_relation

                    try:
                        if int(state_transition_product.satisfy_count()) == 0:
                            break
                    except:
                        break

                    next_states_encoded = state_transition_product.smoothing(state_variables)

                    try:
                        if int(next_states_encoded.satisfy_count()) == 0:
                            break
                    except:
                        break

                    next_states = expr2bdd(expr(0))
                    for assignment in next_states_encoded.satisfy_all():
                        variable_assignments = []
                        for place_id in self.petri_net.places.keys():
                            next_var = self.bdd_solver.place_to_next_var[place_id]
                            value = bool(assignment.get(next_var, False))
                            variable_assignments.append(f"x_{place_id}" if value else f"~x_{place_id}")

                        state_formula = " & ".join(variable_assignments)
                        try:
                            next_states = next_states | expr2bdd(expr(state_formula))
                        except:
                            continue

                    updated_states = current_states | next_states
                    if updated_states.equivalent(current_states):
                        break
                    current_states = updated_states

                self.bdd_solver.current_set = current_states

            except Exception as error:
                elapsed_time = time.time() - start_time
                return None, elapsed_time, f"BDD computation failed: {str(error)}"

        reachable_states_bdd = self.bdd_solver.current_set

        ilp_problem = LpProblem("FindDeadMarking", LpMinimize)

        marking_vars = {
            place_id: LpVariable(f"M_{place_id}", cat=LpBinary)
            for place_id in self.petri_net.places
        }

        for trans_id, input_places in self.transition_inputs.items():
            if input_places:
                ilp_problem += (
                    lpSum([marking_vars[p] for p in input_places]) <= len(input_places) - 1,
                    f"transition_disabled_{trans_id}"
                )
            else:
                ilp_problem += lpSum([1]) >= 2, f"no_input_{trans_id}"

        ilp_problem += (
            lpSum([marking_vars[p] for p in self.petri_net.places]) >= 1,
            "non_empty_marking"
        )

        ilp_problem += 0
        ilp_solver = PULP_CBC_CMD(msg=0)
        attempt_count = 0

        while attempt_count < max_attempts:
            attempt_count += 1

            ilp_problem.solve(ilp_solver)

            if LpStatus[ilp_problem.status] != "Optimal":
                elapsed_time = time.time() - start_time
                return None, elapsed_time, "No reachable deadlock found"

            candidate_marking = {
                place_id: int(round(marking_vars[place_id].varValue))
                for place_id in marking_vars
            }

            try:
                candidate_bdd = self.convert_marking_to_bdd(candidate_marking)
                intersection = reachable_states_bdd & candidate_bdd

                try:
                    reachable_count = int(intersection.satisfy_count())
                except:
                    reachable_count = 0

                if reachable_count > 0:
                    elapsed_time = time.time() - start_time
                    return candidate_marking, elapsed_time, "Deadlock FOUND"

            except:
                pass

            nogood_terms = []
            for place_id in marking_vars:
                if candidate_marking[place_id] == 0:
                    nogood_terms.append(marking_vars[place_id])
                else:
                    nogood_terms.append(1 - marking_vars[place_id])

            ilp_problem += (
                lpSum(nogood_terms) >= 1,
                f"exclude_solution_{attempt_count}"
            )
        elapsed_time = time.time() - start_time
        return None, elapsed_time, f"No deadlock found after {max_attempts} attempts"