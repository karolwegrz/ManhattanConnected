from libc.stdint cimport uint64_t
from itertools import combinations
import numpy as np
from libc.stdio cimport printf


def convert_mask_to_points(mask, all_points):
    subset = []
    for i in range(len(all_points)):
        if (mask & (<uint64_t>1 << i)):
            subset.append(all_points[i])
    return subset

cpdef tuple build_bitmasks(list points):
    """
    points              := list of N points represented by tuples (x, y)
    aligned_mask[i]     := set of j in [N] such that points[i] and points[j] are aligned
    valid_mask[i][j]    := set of k in [N] such that points[k] is in the rectangle span by points[i], points[j]
    (for i, j in [N])

    Complexity: O(N^3)
    """
    cdef int N = len(points)
    
    if N > 64:
        raise ValueError("N must be <= 64 for the 64-bit integer bitmask trick.")

    # Raw C implementation would malloc and do manual indexing: valid_mask[i*N + j] |= (<uint64_t>1 << k)
    # cdef uint64_t *valid_mask = <uint64_t*> malloc(N*N*sizeof(uint64_t))
    # cdef uint64_t *aligned_mask = <uint64_t*> malloc(N*sizeof(uint64_t))

    # Let's do memoryviews for now (sort of numpy arrays from what I understand?)
    cdef uint64_t[:] valid_mask = np.zeros(N*N, dtype=np.uint64)
    cdef uint64_t[:] aligned_mask = np.zeros(N, dtype=np.uint64)

    cdef int i, j, k
    cdef int ax, ay, bx, by, cx, cy
    cdef int xmin, xmax, ymin, ymax
    for i in range (N):
        for j in range(i + 1, N):
            ax = points[i][0]             
            ay = points[i][1]             
            bx = points[j][0]
            by = points[j][1]
            
        
            # If points a and b are aligned -> no need to check for the rectangle
            if (ax == bx) or (ay == by):   
                aligned_mask[i] |= (<uint64_t>1 << j)
                aligned_mask[j] |= (<uint64_t>1 << i)
                continue

            # List all the points c (!= a, != b) in the rectangle span by points a and b
            for k in range(N):
                if k == i or k == j:
                    continue
                cx = points[k][0]         
                cy = points[k][1]         
               
                xmin = min(ax, bx)
                xmax = max(ax, bx)
                ymin = min(ay, by)
                ymax = max(ay, by)

                if (xmin <= cx <= xmax) and (ymin <= cy <= ymax):
                    valid_mask[i*N + j] |= (<uint64_t>1 << k)
                    valid_mask[j*N + i] |= (<uint64_t>1 << k)
            
            

    return valid_mask, aligned_mask


# bint: is the C type for boolean values
cpdef bint is_pair_valid(int i, int j, uint64_t subset_mask, int N, uint64_t[:] valid_mask, uint64_t[:] aligned_mask):
    """
    Complexity: O(1) (Python should have optimized that constant as it's bit operations)
    """
    # Check whether i and j are aligned
    if (aligned_mask[i] & (<uint64_t>1 << j)): 
        return True

    # Check whether subset contains a point validating i and j
    return bool(subset_mask & valid_mask[i*N + j])

cpdef bint is_valid(uint64_t subset_mask, int N, uint64_t[:] valid_mask, uint64_t[:] aligned_mask):
    """
    Checks if all pairs in the subset are valid.

    Complexity: O(N^2)
    """
    # Iterate over every pair of points in subset == iterate over every 1-bits of subset_mask
    cdef int i, j
    for i in range(N):
        if not (subset_mask & (<uint64_t>1 << i)):
            continue            
        for j in range(i + 1, N):
            if not (subset_mask & (<uint64_t>1 << j)):
                continue
        
            if not is_pair_valid(i, j, subset_mask, N, valid_mask, aligned_mask):
                return False

    return True

# Change in argument: all_points contains all the points and we simply indicate the index n of the first candidate point in the list
cpdef tuple find_solutions_mask(list all_points, int n, int max_nb_sol=10):
    """
    Finds the minimum size subset of candidates that validates all pairs in (input U subset).
    """
    cdef int N = len(all_points)
    cdef int m = N - n

    if N > 63:
        raise ValueError("N must be <= 63 for the 64-bit integer bitmask trick.")

    # PRECOMPUTATION: O(N^3)
    valid_mask, aligned_mask = build_bitmasks(all_points)

    # First n bits indicate the input points, bits n+1, ..., N are the candidate points
    cdef uint64_t INPUT_MASK = (<uint64_t>1 << n) - 1 
    cdef range CANDIDATE_INDICES = range(n, N)

    # Sanity check
    # if is_valid(INPUT_MASK, N, valid_mask, aligned_mask):
    #     return True, []

    cdef int size
    cdef tuple subset_indices
    cdef bint found_solution = 0
    # One solution is encoded as a uint64_t integer, we will store at most max_nb_sol solutions
    cdef uint64_t[:] solutions_mask = np.zeros(max_nb_sol, dtype=np.uint64) 
    cdef int count_solutions = 0
    cdef uint64_t SUBSET_MASK
    cdef uint64_t POINTS_MASK
    cdef int i

    # Enumerate subsets of candidate in increasing size until found connected subset
    for size in range(m + 1):
        for subset_indices in combinations(CANDIDATE_INDICES, size):
            # Build the bitmask of the current set of points: O(size)
            SUBSET_MASK = 0
            for i in subset_indices:
                SUBSET_MASK |= (<uint64_t>1 << i)
            POINTS_MASK = INPUT_MASK | SUBSET_MASK

            if is_valid(POINTS_MASK, N, valid_mask, aligned_mask):
                solutions_mask[count_solutions] = SUBSET_MASK
                count_solutions += 1
                found_solution = 1
                if count_solutions == max_nb_sol:
                    return True, solutions_mask
        
        if found_solution:
            return True, solutions_mask
            
    return False, []

