import os
import sys

from reachability_explicit import ReachabilityNet
from reachability_bdd import SymbolicReachabilityPyEDA
from ilp_deadlock import DeadlockDetector


def test_file(file_path):
    filename = os.path.basename(file_path)
    print(f"\n{'=' * 70}")
    print(f"Testing: {filename}")
    print(f"{'=' * 70}")

    net = ReachabilityNet()

    print(f"\n[Task 1] Parsing {filename}...")
    if not net.parse_pnml(file_path):
        print("Parsing failed. Skipping this file.")
        return

    print("Summary:")
    net.summary()

    print("\nChecking Consistency...")
    is_consistent = net.check_consistency()

    if not is_consistent:
        print("Network is invalid. Skipping Task 2 but continuing with Task 3.")
        explicit_count = 0
    else:
        print("Task 1 Passed: Network is valid.")

        print(f"\n[Task 2] Computing Reachability Graph (BFS)...")
        try:
            net.build_pre_post()
            reachable_markings = net.bfs()
            explicit_count = len(reachable_markings)

            print(f"Task 2 Completed.")
            print(f"   Total reachable states: {explicit_count}")

            if explicit_count <= 20:
                print("   Marking list:")
                for idx, m in enumerate(reachable_markings):
                    sorted_m = dict(sorted(m.items()))
                    print(f"    {idx + 1}. {sorted_m}")
            else:
                print("   (List too long, hidden)")

        except Exception as e:
            print(f"Task 2 Error: {e}")
            explicit_count = 0

    print(f"\n[Task 3] Symbolic Reachability (BDD)...")
    try:
        sym_net = SymbolicReachabilityPyEDA()

        sym_net.places = net.places
        sym_net.transitions = net.transitions
        sym_net.arcs = net.arcs

        bdd_count, bdd_time, formulas = sym_net.compute_reachable(return_formula=True)

        print(f"Completed.")
        print(f"   Total states (Symbolic): {bdd_count}")
        print(f"   Computation time: {bdd_time:.4f}s")
        print(f"   Symbolic formula:")
        print(f"      - Initial: {formulas['initial']}")
        print(f"      - Final: {formulas['final']}")
        print(f"      - Iterations: {formulas['iterations']}")

        if is_consistent and explicit_count > 0:
            print(f"\n[Validation]")
            if explicit_count == bdd_count:
                print(f"   RESULTS MATCH ({explicit_count})")
            else:
                print(f"   WARNING: MISMATCH!")
                print(f"      Explicit: {explicit_count}")
                print(f"      Symbolic: {bdd_count}")
        else:
            print(f"\n[Validation]")
            print(f"   Cannot compare: Network invalid or Task 2 failed")

    except Exception as e:
        print(f"Task 3 Error: {e}")
        return

    print(f"\n[Task 4] Deadlock Detection (ILP + BDD)...")

    try:
        detector = DeadlockDetector(net, sym_net)

        dead_marking, elapsed_time, status_message = detector.detect_deadlock(max_attempts=20)

        print(f"Completed.")

        if dead_marking is not None:
            readable_marking = {
                net.places.get(place_id, {}).get('name', place_id): token_count
                for place_id, token_count in dead_marking.items() if token_count > 0
            }
            print(f"   Result: DEADLOCK FOUND")
            print(f"   Deadlock marking: {dict(sorted(readable_marking.items())) if readable_marking else '(empty)'}")
        else:
            print(f"   Result: NO DEADLOCK")
            print(f"   Reason: {status_message}")

        print(f"   Time: {elapsed_time:.4f}s")

    except Exception as error:
        print(f"Task 4 Error: {error}")


def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    examples_dir = os.path.join(os.path.dirname(current_dir), "examples")

    print(f"Scanning directory: {examples_dir}\n")

    if not os.path.exists(examples_dir):
        print(f"Examples directory not found: {examples_dir}")
        return

    pnml_files = sorted([f for f in os.listdir(examples_dir) if f.endswith(".pnml")])

    if not pnml_files:
        print("No .pnml files found in examples directory")
        return

    print(f"Found {len(pnml_files)} PNML file(s).\n")

    for f in pnml_files:
        path = os.path.join(examples_dir, f)
        test_file(path)

    print(f"\n{'=' * 70}")
    print("All files processed.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()