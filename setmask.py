from itertools import combinations

def build_masks(points):
    """
    points              := list of N points represented by tuples (x, y)
    aligned_mask[i]     := set of j in [N] such that points[i] and points[j] are aligned
    valid_mask[i][j]    := set of k in [N] such that points[k] is in the rectangle span by points[i], points[j]
    (for i, j in [N])

    Complexity: O(n^3)
    """
    N = len(points)

    valid_mask = [[set() for _ in range(N)] for _ in range(N)]
    aligned_mask = [set() for _ in range(N)]

    for i in range (N):
        for j in range(i+1, N):
            ax, ay = points[i][0], points[i][1]             # Point a
            bx, by = points[j][0], points[j][1]             # Point b

            if (ax == bx) or (ay == by):                    # Points a and b are aligned -> no need to check for the rectangle
                aligned_mask[i].add(j)
                aligned_mask[j].add(i)
                continue

            for k in range(N):
                cx, cy = points[k][0], points[k][1]         # Point c (different from a and b)
                if k == i or k == j:
                    continue

                xmin, xmax = min(ax, bx), max(ax, bx)
                ymin, ymax = min(ay, by), max(ay, by)

                if (xmin <= cx <= xmax) and (ymin <= cy <= ymax):   # Point c is in the rectangle span by a and b --> makes the pair (a, b) valid
                    valid_mask[i][j].add(k)
                    valid_mask[j][i].add(k)

    return valid_mask, aligned_mask

def is_valid(subset_mask, M, aligned):
    """
    Whether the subset encoded in subset_mask is Manhattan Connected.

    subset_mask := subset of [N] --> corresponds to the encoding of a subset in points
    M, aligned : precomputed by build_mask(points)

    i, j in subset_mask are connected if either the corresponding points are aligned,
    or subset contains contains a point that makes (i, j), i.e. subset_mask contains k in M[i, j]
    """
    for (i, j) in combinations(subset_mask, 2):
        if not ((i in aligned[j]) or (subset_mask & M[i][j])):
            return False
    return True
    
def is_manhattan_connected(points):
    points = list(points)
    POINTS_MASK = set(range(len(points)))
    M, aligned = build_masks(points)
    return is_valid(POINTS_MASK, M, aligned)

def find_solutions(input, candidates, only_one=True):
    if is_manhattan_connected(input):
        return True, list()
    
    all_points = input + candidates

    n = len(input)
    m = len(candidates)
    N = n + m

    INPUT_MASK = set(range(n))
    CANDIDATE_MASK = range(n, N)

    # Precompute mask of valid points
    M, aligned = build_masks(all_points)

    # Iterate over every subset of size k of candidate points
    list_solutions = list()
    for size in range(1, m+1):
        found_solution = False
        for subset in combinations(CANDIDATE_MASK, size): 
            SUBSET_MASK = INPUT_MASK | set(subset)
            if is_valid(SUBSET_MASK, M, aligned):
                found_solution = True
                subset_points = [all_points[i] for i in subset]
                list_solutions.append(subset_points)

        if found_solution:
            return True, list_solutions
        
    return False, list()
