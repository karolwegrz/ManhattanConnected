import numpy as np
from bitmask_cy import build_bitmasks, is_valid, find_solutions_mask

def find_solutions(all_points, n, max_nb_sol):
    found, mask_list = find_solutions_mask(all_points, n, max_nb_sol)
    solutions = convert_masks_to_points(mask_list, all_points)
    return found, solutions

def convert_mask_to_points(mask, all_points):
    subset = []
    for i in range(len(all_points)):
        if (mask & (1 << i)):
            subset.append(all_points[i])
    return subset

def convert_masks_to_points(mask_list, all_points):
    sol_list = []
    for mask in mask_list:
        # print(mask)
        if mask:
            sol_list.append(convert_mask_to_points(mask, all_points))
    return sol_list

input_points = [(0, 8), (2, 2), (1, 1), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 0)]
candidate_points = [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (1, 2), (2, 1), (2, 3), (3, 2), (3, 4), (4, 3), (4, 5), (5, 4), (5, 6), (6, 5), (6, 7), (7, 6), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 6), (8, 7)]

# Base Example
# input_points = [(0,0), (1,1), (2, 2)]
# candidate_points = [(1,0), (0,1), (2,1), (1, 2)]
all_points = input_points + candidate_points
N = len(all_points)
n = len(input_points)

found, sols = find_solutions(all_points, n, max_nb_sol=10)
print("found:", found)
print(sols)

valid_mask, aligned_mask = build_bitmasks(all_points)
INPUT_MASK = (1 << n) - 1
print("inputs valid:", is_valid(INPUT_MASK, N, valid_mask, aligned_mask))

# valid_mask_array= np.asarray(valid_mask)

idx_81 = all_points.index((8, 1))
idx_77 = all_points.index((7, 7))
idx_22 = all_points.index((2, 2))
i, j = idx_81, idx_77
# print(f"(8, 1) has index {i} and (7, 7) has index {j} and (2, 2) has index {idx_22}")

# print("aligned to (8, 1)", convert_mask_to_points(aligned_mask[idx_81], all_points))
# print("aligned to (7, 7)", convert_mask_to_points(aligned_mask[idx_77], all_points), aligned_mask[idx_77])
# print(convert_mask_to_points(valid_mask[idx_77*N + idx_81], all_points))



ax = all_points[i][0]             
ay = all_points[i][1]             
bx = all_points[j][0]
by = all_points[j][1]
# print(ax, ay, bx, by)
# print((ax == bx) or (ay == by))