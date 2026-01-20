from libc.stdint cimport uint64_t
from itertools import combinations
import numpy as np
from libc.stdio cimport printf
from time import time
import logging
import sys

# Number of trailing zeroes
cdef extern from "builtins.h":
    int __builtin_ctzll(unsigned long long x)

#####################
# ENCODING SETS OF POINTS:
# We fix the given input and candidate points and identify them with their index in that list. We call N the total number of points, and the first n points are input points.
# Then a subset of points can be identified with a {0, 1}^N vector. Actually, we identify it to the integer that has it's i-th bit = 1 iff the i-th point is present in the set.
# By handling sets of points as integers (called mask), we can check for intersection in constant time --> constant that is highly optimized in C as it's only bit operations.
# 
# SEARCH ALGORITHM:
# Precomputation: 
#   - compute for every point i in [N] the set of points j in [N] on the same row or column as i --> store the set as a mask in aligned_mask[i]
#   - compute for every pair of points i, j in [N] the set of points k in [N] that lie in the rectangle span by i and j --> store the set as a mask in valid_mask[i, j]
# Search:
# For every subset of candidate points in increasing order of size, test if it renders (subset U input) connected. 
# The union is a bit operation. 
# The connectivity testing is simply checking for every pair of points (i, j) in (subset U input) whether they are aligned, or (subset U input) contains a point in valid_mask[i, j]. 
# So we spend O(|subset U input|) time to check connectivity, where the constant is supposedly highly optimized. 
#####################

def mask_to_point(mask, all_points):
    subset = []
    for i in range(len(all_points)):
        if (mask & (<uint64_t>1 << i)):
            subset.append(all_points[i])
    return subset

def masks_to_points(mask_list, all_points):
    sol_list = []
    for mask in mask_list:
        if mask:
            sol_list.append(mask_to_point(mask, all_points))
    return sol_list


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
    # Check whether i and j are aligned or whether subset contains a point validating i and j
    return (aligned_mask[i] & (<uint64_t>1 << j)) or (subset_mask & valid_mask[i*N + j])


cpdef bint is_valid(uint64_t subset_mask, int N, uint64_t[:] valid_mask, uint64_t[:] aligned_mask):
    """
    Checks if all pairs in the subset are valid.

    Complexity: O(N^2)
    """
    # Iterate over every pair of points in subset == iterate over every 1-bits of subset_mask
    # Naïve way: always O(N^2)
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
cpdef tuple find_solutions(list all_points, int n, int max_nb_sol=3, int min_size=0, int max_size=0):
    """
    Finds the minimum size subset of candidates that validates all pairs in (input U subset).
    """
    cdef int N = len(all_points)
    cdef int m = N - n

    if N > 64:
        raise ValueError(f"N must be <= 64 for the 64-bit integer bitmask trick (currently N={N}).")

    # PRECOMPUTATION: O(N^3)
    valid_mask, aligned_mask = build_bitmasks(all_points)

    # print(aligned_mask[7])

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
    cdef int t1
    cdef int t2

    # Enumerate subsets of candidate in increasing size until found connected subset
    for size in range(min_size, max_size + 1):
        print("Testing size", size)
        t1 = time()
        for subset_indices in combinations(CANDIDATE_INDICES, size):
            # Build the bitmask of the current set of points: O(size)
            SUBSET_MASK = 0
            for i in subset_indices:
                SUBSET_MASK |= (<uint64_t>1 << i)
            POINTS_MASK = INPUT_MASK | SUBSET_MASK

            # Test connectivity
            if is_valid(POINTS_MASK, N, valid_mask, aligned_mask):
                solutions_mask[count_solutions] = SUBSET_MASK
                count_solutions += 1
                found_solution = 1
                if count_solutions == max_nb_sol:
                    t2 = time()
                    print(f"Found {count_solutions} solutions ({t2-t1} sec)")
                    return True, masks_to_points(solutions_mask, all_points)
        
        if found_solution:
            t2 = time()
            print(f"Found {count_solutions} solutions ({t2-t1} sec)")
            return True, masks_to_points(solutions_mask, all_points)
        
        t2 = time()
        print(f"Not found ({t2-t1} sec)")
            
    return False, []


cpdef tuple find_solutions_reverse(list all_points, int n, int max_nb_sol=3, int min_size=0, int max_size=0):
    """
    Finds the minimum size subset of candidates that validates all pairs in (input U subset).
    """
    cdef int N = len(all_points)
    cdef int m = N - n
    min_size = max(0, min_size)
    max_size = min(m, max_size)

    if N > 64:
        raise ValueError(f"N must be <= 64 for the 64-bit integer bitmask trick (currently N={N}).")
    if min_size > max_size :
        raise ValueError(f"min_size={min_size} should be <= max_size={max_size}.")

    # PRECOMPUTATION: O(N^3)
    valid_mask, aligned_mask = build_bitmasks(all_points)

    # First n bits indicate the input points, bits n+1, ..., N are the candidate points
    cdef uint64_t INPUT_MASK = (<uint64_t>1 << n) - 1 
    cdef range CANDIDATE_INDICES = range(n, N)

    cdef int size
    cdef tuple subset_indices
    cdef bint found_solution
    # One solution is encoded as a uint64_t integer, we will store at most max_nb_sol solutions
    cdef uint64_t[:] solutions_mask = np.zeros(max_nb_sol, dtype=np.uint64) 
    cdef int count_solutions
    cdef int prev_count_solutions = 0
    cdef uint64_t SUBSET_MASK
    cdef uint64_t POINTS_MASK
    cdef int i
    cdef int t1
    cdef int t2


    # targets = logging.StreamHandler(sys.stdout), logging.FileHandler(f'./log/{filename}.log')
    # logging.basicConfig(format='%(message)s', level=logging.INFO, handlers=targets)


    # Enumerate subsets of candidate in decreasing size until found connected subset
    for size in range(max_size, min_size-1, -1):
        
        # (re)initialize number of solutions found for the current size
        found_solution = 0
        count_solutions = 0 
        
        # logging.info("Testing size", size)
        print("Testing size", size)
        t1 = time()
        for subset_indices in combinations(CANDIDATE_INDICES, size):
            # Build the bitmask of the current set of points: O(size)
            SUBSET_MASK = 0
            for i in subset_indices:
                SUBSET_MASK |= (<uint64_t>1 << i)
            POINTS_MASK = INPUT_MASK | SUBSET_MASK

            # Test connectivity
            if is_valid(POINTS_MASK, N, valid_mask, aligned_mask):
                
                # If this is the first solution found for current size: reinitialize everything
                if not found_solution:
                    found_solution = 1
                    solutions_mask = np.zeros(max_nb_sol, dtype=np.uint64)

                # Store solution
                solutions_mask[count_solutions] = SUBSET_MASK
                count_solutions += 1

                # If found max_nb_solution, move on to the next size 
                if count_solutions == max_nb_sol:
                    t2 = time()
                    # logging.info(f"Found {count_solutions} solutions ({t2-t1} sec)")
                    print(f"Found {count_solutions} solutions ({t2-t1} sec)")
                    prev_count_solutions = count_solutions
                    break


        # If didn't find solution in current size but in previous size, 
        # OR we the total number of solutions is < max_nb_sol
        # then stop the search and return stored solutions
        if not found_solution and prev_count_solutions > 0:
            t2 = time()
            # logging.info(f"Not found in {t2-t1} sec")
            print(f"Not found in {t2-t1} sec")
            return True, masks_to_points(solutions_mask, all_points)
        
        if found_solution and count_solutions < max_nb_sol:
            t2 = time()
            # logging.info(f"Found {count_solutions} in {t2-t1} sec")
            print(f"Found {count_solutions}/{max_nb_sol} in {t2-t1} sec")
            return True, masks_to_points(solutions_mask, all_points)

    t2 = time()
    # logging.info(f"found={found_solution} in {t2-t1} sec")
    print(f"found={found_solution} in {t2-t1} sec")
    return found_solution, masks_to_points(solutions_mask, all_points)

