from setmask import build_masks, is_valid, find_solutions
import time 


def example_1():
    input_points = [(0,0), (1, 1)]
    candidate_points = [(1,0)]
    expected = (1, 1)

    all_points = input_points + candidate_points
    N = len(all_points)
    n = len(input_points)
    return all_points, n, N, expected 

def example_2():
    input_points = [(0,0), (1,1)]
    candidate_points = [(1,0), (0,1)]
    expected = (2, 1)

    all_points = input_points + candidate_points
    N = len(all_points)
    n = len(input_points)
    return all_points, n, N, expected 

def example_3():
    input_points = [(0,0), (1,1), (2, 2)]
    candidate_points = [(1,0), (0,1), (2,1), (1, 2)]
    expected = (4, 2)

    all_points = input_points + candidate_points
    N = len(all_points)
    n = len(input_points)
    return all_points, n, N, expected 


def example_4():
    input_points = [(1,1), (2, 2), (3, 3), (4, 4), (5, 5), (0, 6), (6, 0)]
    candidate_points = []
    expected = 0

    all_points = input_points + candidate_points
    N = len(all_points)
    n = len(input_points)
    return all_points, n, N, expected 

def example_5():
    input_points = [(1,1), (2, 2), (3, 3), (4, 4), (5, 5), (0, 6), (6, 0)]
    candidate_points = [(1, 2), (2, 1), (2, 3), (3, 2), (3, 4), (4, 3), (4, 5), (5, 4), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (1, 6), (2, 6), (3, 6), (4, 6), (5, 6)]
    expected = (2, 10)

    all_points = input_points + candidate_points
    N = len(all_points)
    n = len(input_points)
    return all_points, n, N, expected 


def example_6():
    input_points = [(i, i) for i in range(1, 10)] + [(0, 10), (10, 0)]
    candidate_points = [(1, 2), (2, 1), (2, 3), (3, 2), (3, 4), (4, 3), (4, 5), (5, 4), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (1, 6), (2, 6), (3, 6), (4, 6), (5, 6)]
    candidate_points = [(i, i+1) for i in range(1, 9)] + [(i+1, i) for i in range(1, 9)] + [(i, 10) for i in range(1, 10)] + [(10, i) for i in range(1, 10)]
    expected = (2, -1)

    all_points = input_points + candidate_points
    N = len(all_points)
    n = len(input_points)
    return all_points, n, N, expected 


def run_test(all_points, n, N, expected):
    INPUT_MASK = set(range(n))

    t1 = time.time()
    valid, aligned = build_masks(all_points)
    t2 = time.time()
    connected = is_valid(INPUT_MASK, N, valid, aligned)
    t3 = time.time()
    found, sols = find_solutions(all_points, n, 10)
    t4 = time.time()

    con_check, precomp, search = t3-t2, t2-t1, t4-t2


    print(f"input points: {all_points[:n]}")
    print(f"candidate points: {all_points[n:]}")

    print(f"Input is already connected = {connected} (checked in {con_check} sec)")
    print(f"PRECOMPUTATION in {precomp} sec:")
    # print(f"valid = {valid}")
    # print(f"aligned = {aligned}")
    print(f"Found solutions={found} (in {search} sec) ")
    if found and not connected:
        # print(sols)
        print(f"Found {len(sols)} solutions of size {len(sols[0])} (expected size {expected})")
        for s in sols:
            print("next solution")
            print(s)

    print()
    return 


# run all tests:

run_test(*example_1())
run_test(*example_2())
run_test(*example_3())
run_test(*example_4())
run_test(*example_5())
run_test(*example_6())