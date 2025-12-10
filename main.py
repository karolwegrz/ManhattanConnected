import streamlit as st
import time
# from setmask import find_solutions
# from bitmask import find_solutions_mask
from bitmask_cy import find_solutions_mask

def find_solutions(all_points, n, max_nb_sol):
    found, mask_list = find_solutions_mask(all_points, n, max_nb_sol)
    solutions = convert_masks_to_points(mask_list, all_points)
    return found, solutions


# Configurable grid size
GRID_ROWS = 15
GRID_COLS = 10

# Tighten spacing, style buttons, and remove max-width/padding
st.markdown(
    """
    <style>
    .stButton>button {
        width: 100%;
        aspect-ratio: 1 / 1;
        padding: 0;
        margin: 0;
        border: 0;
        border-radius: 2px;
        background: transparent;
        line-height: 1;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Is this Mannhattan Connected?")

# Initialize session state for grid and connected flag
if "grid" not in st.session_state or \
   len(st.session_state.grid) != GRID_ROWS or \
   any(len(row) != GRID_COLS for row in st.session_state.grid):
    st.session_state.grid = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

if "input" not in st.session_state:
    st.session_state.input = list() 
if "candidates" not in st.session_state:
    st.session_state.candidates = list()  

if "connected" not in st.session_state:
    st.session_state.connected = True  # empty grid is trivially connected
if "solvable" not in st.session_state:
    st.session_state.solvable = True
if "solutions" not in st.session_state:
    st.session_state.solutions = set()

# Button appearance mapping using emoji squares
EMOJI_MAP = {
    0: "⬜",
    1: "⬛",
    2: "🟥",
    3: "🟦"
}

def input_points(grid):
    return [(i, j) for i, row in enumerate(grid) for j, v in enumerate(row) if v == 1]

def candidate_points(grid):
    return [(i, j) for i, row in enumerate(grid) for j, v in enumerate(row) if v == 2]

# Karol's n^3 solution
def is_manhattan_connected(points):
    """
    Karol's vibecode solution (we use it only once for the first check on input points)

    Complexity: O(n^3)
    """
    if len(points) <= 1:
        return True

    # For every pair of points a, b
    for idx_a in range(len(points)):
        ax, ay = points[idx_a]
        for idx_b in range(idx_a + 1, len(points)):
            bx, by = points[idx_b]

            # Pairs on the same row or column are MHC by definition
            if ax == bx or ay == by:
                continue

            # Check if there exists a point inside the axis-aligned rectangle
            minx, maxx = (ax, bx) if ax < bx else (bx, ax)
            miny, maxy = (ay, by) if ay < by else (by, ay)

            found_inside = False
            for cx, cy in points:
                if (cx,cy) == (ax,ay) or (cx,cy) == (bx,by):
                    continue
                if minx <= cx <= maxx and miny <= cy <= maxy:
                    found_inside = True
                    break
            if not found_inside:
                return False
    return True

def display_solutions(input, candidate, solutions):
    for x, solution in enumerate(solutions):
        st.write(f"Solution {x+1}:")
        for i in range(GRID_ROWS):
            cols = st.columns(GRID_COLS)
            for j in range(GRID_COLS):
                if (i, j) in input:
                    symbol = EMOJI_MAP[1]
                elif (i, j) in solution:
                    symbol = EMOJI_MAP[3]
                elif (i, j) in candidate:
                    symbol = EMOJI_MAP[2]
                else:
                    symbol = EMOJI_MAP[0]
                cols[j].button(symbol, key=f"{i}-{j}_{x}", args=(i, j, x))


def convert_masks_to_points(mask_list, all_points):
    sol_list = []
    for mask in mask_list:
        # print(mask)
        if mask:
            subset = []
            for i in range(N):
                if (mask & (1 << i)):
                    subset.append(all_points[i])
            # print(subset)
            sol_list.append(subset)
    return sol_list


def cycle_cell(i, j):
    st.session_state.grid[i][j] = (st.session_state.grid[i][j] + 1) % 3
    
    st.session_state.input = input_points(st.session_state.grid)
    st.session_state.candidates = candidate_points(st.session_state.grid)

    st.info(f"Input size: {len(st.session_state.input)}, Total size: {len(st.session_state.input) + len(st.session_state.candidates)}")

#######################################

# Layout grid with minimal gaps
for i in range(GRID_ROWS):
    cols = st.columns(GRID_COLS)
    for j in range(GRID_COLS):
        symbol = EMOJI_MAP[st.session_state.grid[i][j]]
        cols[j].button(symbol, key=f"{i}-{j}", on_click=cycle_cell, args=(i, j))

# Status message at the bottom of the grid
if st.button("Submit", type="primary"):

    t1 =  time.time()
    st.session_state.connected = is_manhattan_connected(st.session_state.input)
    t2 = time.time()

    if st.session_state.connected:
        st.success(f"Connected (in {t2-t1} sec)")
    else:
        st.error(f"Not Connected (in {t2-t1} sec)")

        all_points = st.session_state.input + st.session_state.candidates
        N = len(all_points)
        n = len(st.session_state.input)

        t3 = time.time()
        found, solutions = find_solutions(all_points, n, max_nb_sol=10)        
        t4 = time.time()

        nb_sol = len(solutions)
        if found and nb_sol > 0:
            sol_size = len(solutions[0])
            st.info(f'Found {nb_sol} solutions of size {sol_size} (in {t4-t3} sec)', icon="ℹ️")
            display_solutions(st.session_state.input, st.session_state.candidates, solutions)
        else:
            st.info(f'No solution found (in {t2-t1} sec)', icon="ℹ️")

