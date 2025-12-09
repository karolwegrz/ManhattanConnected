from itertools import combinations

def build_bitmasks(points):
    """
    points              := list of N points represented by tuples (x, y)
    aligned_mask[i]     := set of j in [N] such that points[i] and points[j] are aligned
    valid_mask[i][j]    := set of k in [N] such that points[k] is in the rectangle span by points[i], points[j]
    (for i, j in [N])

    Complexity: O(N^3)
    """
    N = len(points)

    valid_mask = [[0] * N for _ in range(N)]
    aligned_mask = [0] * N

    for i in range (N):
        for j in range(i+1, N):
            ax, ay = points[i][0], points[i][1]             # Point a
            bx, by = points[j][0], points[j][1]             # Point b

            if (ax == bx) or (ay == by):                    # Points a and b are aligned -> no need to check for the rectangle
                aligned_mask[i] |= (1 << j)
                aligned_mask[j] |= (1 << i)
                continue

            for k in range(N):
                cx, cy = points[k][0], points[k][1]         # Point c (different from a and b)
                if k == i or k == j:
                    continue

                xmin, xmax = min(ax, bx), max(ax, bx)
                ymin, ymax = min(ay, by), max(ay, by)

                if (xmin <= cx <= xmax) and (ymin <= cy <= ymax):   # Point c is in the rectangle span by a and b --> makes the pair (a, b) valid
                    valid_mask[i][j] |= (1 << k)
                    valid_mask[j][i] |= (1 << k)

    return valid_mask, aligned_mask

def is_pair_valid(i, j, subset_mask, valid_mask, aligned_mask):
    """
    Complexity: O(1) (Python should have optimized that constant as it's bit operations)
    """
    # Check whether i and j are aligned
    if (aligned_mask[i] & (1 << j)): 
        return True
    
    # Check whether subset contains a point validating i and j
    return bool(subset_mask & valid_mask[i][j]) 

def is_valid(subset_mask, N, valid_mask, aligned_mask):
    """
    Checks if all pairs in the subset are valid.

    Complexity: O(N^2)
    """
    for i in range(N):
        if not (subset_mask & (1 << i)):
            continue            
        for j in range(i + 1, N):
            if not (subset_mask & (1 << j)):
                continue
            
            if not is_pair_valid(i, j, subset_mask, valid_mask, aligned_mask):
                return False
    return True

def find_solutions(input_points, candidate_points, only_one=True):
    """
    Finds the minimum size subset of candidates that validates all pairs in (input U subset).
    """
    all_points = input_points + candidate_points
    n = len(input_points)
    m = len(candidate_points)
    N = len(all_points)

    if N > 63:
        raise ValueError("N must be <= 63 for the 64-bit integer bitmask trick.")

    # PRECOMPUTATION: O(N^3)
    valid_mask, aligned_mask = build_bitmasks(all_points)

    # First n bits indicate the input points, bits n+1, ..., N are the candidate points
    INPUT_MASK = (1 << n) - 1 
    CANDIDATE_INDICES = range(n, N)

    # Sanity check
    # if is_valid(INPUT_MASK, N, valid_mask, aligned_mask):
    #     return True, []

    # Enumerate subsets of candidate in increasing size until found connected subset
    list_solutions = []
    for size in range(m + 1):
        found_solution = False
        
        for subset_indices in combinations(CANDIDATE_INDICES, size):
            
            # Build the bitmask of the current set of points: O(size)
            SUBSET_MASK = INPUT_MASK
            for i in subset_indices:
                SUBSET_MASK |= (1 << i)
            
            if is_valid(SUBSET_MASK, N, valid_mask, aligned_mask):
                found_solution = True        
                subset_points = [all_points[i] for i in subset_indices]
                list_solutions.append(subset_points)
                if only_one:
                    return True, list_solutions
        
        if found_solution:
            return True, list_solutions
            
    return False, []
    
# def find_solutions(input_points, candidate_points, only_one=True):
    input_points, candidate_points = list(input_points), list(candidate_points)
    all_points = input_points + candidate_points
    n = len(input_points)
    m = len(candidate_points)
    N = len(all_points)

    if N > 63:
        raise ValueError("N must be <= 63 for 64-bit integer bitmask implementation.")

    valid_mask, aligned_mask = build_bitmasks(all_points)
    INPUT_MASK = (1 << n) - 1                   # The first n bits correspond to the input points
    CANDIDATE_INDICES = list(range(n, N))       # The remaining bits correspond to the candidate points
    # ALL_POINTS_INDICES = list(range(N))       
    all_solution_masks = []                     # will be changed in place

    def branch_and_bound_search(
        k,                             # Target size for the candidate subset
        unresolved_pairs,              # Set of (i, j) tuples representing pairs NOT yet valid
        current_mask,                  # Current mask of points selected so far
        current_size,                  # Size of the current subset of candidates
        next_candidate_idx,                   # Index in candidate_indices to start searching from
    ):
        """
        Incremental subset of size k enumeration. By incrementing the subset, we can restrict the connectivity check to the unresolved pairs.
        """
        if only_one and all_solution_masks:
            return

        # If arrived at target size, check if is solution
        if current_size == k:
            if not unresolved_pairs:
                all_solution_masks.append(current_mask)
            return 
            
        # Sanity check: enough candidates remain to attain target size
        remaining = N - next_candidate_idx + 1
        if current_size + remaining < k:
            return
        
        # Recursively try to add the next candidate to the set (DFS-style)
        for c_idx in range(next_candidate_idx, N):
            c_bit = (1 << c_idx)
            
            # Add point c to the current subset
            new_mask = current_mask | c_bit
            new_unresolved_pairs = set(unresolved_pairs)
            
            # Remove pairs (a, b) resolved by adding the point c (in O(|unresolved_pairs|) time)
            pairs_to_remove = set()
            for a_idx, b_idx in unresolved_pairs:
                if valid_mask[a_idx][b_idx] & c_bit: 
                    pairs_to_remove.add((a_idx, b_idx))
            new_unresolved_pairs -= pairs_to_remove

            # Add new unresolved pairs (a, c) where a is from previous subset
            nb_pairs_to_add = 0 
            for a_idx in range(N):
                if current_mask & (1 << a_idx):
                    if not is_pair_valid(a_idx, c_idx, new_mask, valid_mask, aligned_mask):
                        new_unresolved_pairs.add(tuple(sorted((a_idx, c_idx))))
                        nb_pairs_to_add += 1

            # if pairs_to_remove and nb_pairs_to_add != current_size: 
            branch_and_bound_search(k, new_unresolved_pairs, new_mask, current_size + 1, c_idx + 1)

    unresolved_pairs = set()
    for i in range(n):
        for j in range(i + 1, n):
            if not is_pair_valid(i, j, INPUT_MASK, valid_mask, aligned_mask):
                unresolved_pairs.add(tuple(sorted((i, j))))

    if not unresolved_pairs:
        return True, [[]]

    # Enumerate all subsets of candidate in increasing size --> do this via smart branch and bound
    for k in range(1, m + 1):
        
        branch_and_bound_search(k, unresolved_pairs, INPUT_MASK, 0, n)
        
        if all_solution_masks:
            all_solutions = []
        
            for solution_mask in all_solution_masks:
                
                # convert solution_mask to set of points
                solution = []
                for i in range(n, N):
                    if solution_mask & (1 << i):
                        solution.append(all_points[i])
                
                # add solution to list of solutions
                all_solutions.append(solution)
                
            return True, all_solutions
            
    return False, []