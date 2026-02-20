import streamlit as st
import time
import json
import glob
import os
# import logging
import logging.config
import sys
# from setmask import find_solutions
# from bitmask import find_solutions_mask
from bitmask_cy import find_solutions, find_solutions_reverse


# Default values
GRID_ROWS = 10
GRID_COLS = 8
DISPLAY = True
# For the search:
MAX_NB_SOLS = 3
MIN_SIZE = 8
MAX_SIZE = 15
DECREASING = True # if False, then in increasing order

# Button appearance mapping using emoji squares
EMOJI_MAP = {
    0: "⬜",
    1: "🟩",
    2: "🟥",
    3: "🟦"
}

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

# Initialize session states
if "grid_rows" not in st.session_state:
    st.session_state.grid_rows = GRID_ROWS
if "grid_cols" not in st.session_state:
    st.session_state.grid_cols = GRID_COLS
if "grid" not in st.session_state or \
   len(st.session_state.grid) != st.session_state.grid_rows or \
   any(len(row) != st.session_state.grid_cols for row in st.session_state.grid):
    st.session_state.grid = [[0 for _ in range(st.session_state.grid_cols)] for _ in range(st.session_state.grid_rows)]
if "input" not in st.session_state:
    st.session_state.input = []
if "candidates" not in st.session_state:
    st.session_state.candidates = []
if "solutions" not in st.session_state:
    st.session_state.solutions = []
if "connected" not in st.session_state:
    st.session_state.connected = True  # empty grid is trivially connected


# if "min_size" not in st.session_state:
#     st.session_state.min_size = MIN_SIZE
# if "max_size" not in st.session_state:
#     st.session_state.max_size = MAX_SIZE

#######################################
# Solving functions

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

def search(all_points, n, decr=True):
    t1 = time.time()
    if decr:
        print("DECREASING SEARCH")
        found, solutions = find_solutions_reverse(all_points, n, max_nb_sol=st.session_state.max_nb_sol, min_size=st.session_state.min_size, max_size=st.session_state.max_size)
    else:
        print("INCREASING SEARCH")
        found, solutions = find_solutions(all_points, n, max_nb_sol=st.session_state.max_nb_sol, min_size=st.session_state.min_size, max_size=st.session_state.max_size)       
    t2 = time.time()
    nb_sol = len(solutions)

    if found and nb_sol > 0:
        st.session_state.solutions = solutions
        sol_size = len(solutions[0])
        st.info(f'Found {nb_sol}/{st.session_state.max_nb_sol} solutions of size {sol_size} (in {t2-t1} sec) (min size={st.session_state.min_size}, max_size={st.session_state.max_size})', icon="👇")


    else:
        st.info(f'No solution found of size in [{st.session_state.min_size}, {st.session_state.max_size}] (in {t2-t1} sec)', icon="👇")

#######################################
# Interface functions

def input_points(grid):
    return [(i, j) for i, row in enumerate(grid) for j, v in enumerate(row) if v == 1]

def candidate_points(grid):
    return [(i, j) for i, row in enumerate(grid) for j, v in enumerate(row) if v == 2]

def display_solutions():
    for x, solution in enumerate(st.session_state.solutions):
        st.write(f"Solution {x+1}:")
        for i in range(st.session_state.grid_rows):
            cols = st.columns(st.session_state.grid_cols)
            for j in range(st.session_state.grid_cols):
                if (i, j) in st.session_state.input:
                    symbol = EMOJI_MAP[1]
                elif [i, j] in solution or (i, j) in solution:
                    symbol = EMOJI_MAP[3]
                elif (i, j) in st.session_state.candidates:
                    symbol = EMOJI_MAP[2]
                else:
                    symbol = EMOJI_MAP[0]
                cols[j].button(symbol, key=f"{i}-{j}_{x}", args=(i, j, x))
    if not st.session_state.solutions:
        st.write("No solution found")

def cycle_cell(i, j):
    # updates the grid value when clicking
    st.session_state.grid[i][j] = (st.session_state.grid[i][j] + 1) % 3
    init_grid_pty()

def init_grid_pty():
    st.session_state.input = input_points(st.session_state.grid)
    st.session_state.candidates = candidate_points(st.session_state.grid)
    st.session_state.solutions = []

def init_grid():
    st.session_state.grid_rows = st.session_state.row_slider
    st.session_state.grid_cols = st.session_state.col_slider
    st.session_state.grid = [[0 for _ in range(st.session_state.grid_cols)] for _ in range(st.session_state.grid_rows)]
    init_grid_pty()

def load_instance(instance_name):
    with open(instance_name, 'r') as f:
        data_loaded = json.load(f)
        st.session_state.grid_rows = data_loaded['GRID_ROWS']
        st.session_state.grid_cols = data_loaded['GRID_COLS']

        st.session_state.grid = [[0 for _ in range(st.session_state.grid_cols)] for _ in range(st.session_state.grid_rows)]
        st.session_state.grid = data_loaded['grid']
        
        init_grid_pty()
        if 'solutions' in data_loaded:
            st.session_state.solutions = data_loaded['solutions']
    f.close()
    print(f"Loaded instance {instance_name}")

def load_latest():
    list_of_files = glob.glob('./json/*.json') 
    if len(list_of_files):
        # Load latest instance
        latest_file = max(list_of_files, key=os.path.getctime)
        load_instance(latest_file)
    else:
        st.write("No latest instance")

def load_file():
    load_instance(f'./json/{st.session_state.loaded_filename}.json')

def solver():

    print(f"\nInput size: {len(st.session_state.input)} + {len(st.session_state.candidates)} = {len(st.session_state.input) + len(st.session_state.candidates)}")
    
    t1 =  time.time()
    st.session_state.connected = is_manhattan_connected(st.session_state.input)
    t2 = time.time()

    # display_input(grid_rows, grid_cols, grid)
    if st.session_state.connected:
        st.success(f"Is already connected (in {t2-t1} sec)")
    else:
        all_points = st.session_state.input + st.session_state.candidates
        n = len(st.session_state.input)

        filename = time.strftime("%Y%m%d-%H%M%S")
        save(filename)
        search(all_points, n, DECREASING)
        save(filename)


def save(filename):
    instance = {
        'GRID_ROWS': st.session_state.grid_rows,
        'GRID_COLS': st.session_state.grid_cols,
        'grid': st.session_state.grid,
        'solutions': st.session_state.solutions
    }
    with open(f'./json/{filename}.json', 'w') as f:    
        json.dump(instance, f)
    f.close()  
    print(f"Saved in {filename}")



#### PAGE LAYOUT

st.title("Is this Mannhattan Connected?")

col1, col2, col3 = st.columns(3)
with col1:
    row_size = st.slider("Number of rows", 1, 20, GRID_ROWS, key="row_slider", on_change=init_grid)
    col_size = st.slider("Number of columns", 1, 20, GRID_COLS, key="col_slider", on_change=init_grid)
    st.button("Clear", type="primary", on_click=init_grid)
with col2:
    st.text_input("Instance to load:", "Enter json filename", key="loaded_filename", on_change=load_file)
    st.button("Load latest instance", type="primary", on_click=load_latest)
with col3:
    st.number_input("Min solution size", value=MIN_SIZE, key="min_size")
    st.number_input("Max solution size", value=MAX_SIZE, key="max_size")
    st.number_input("Max number solutions", value=MAX_NB_SOLS, key="max_nb_sol")
    submit = st.button("Solve", type="primary", on_click=solver, width='stretch')

for i in range(st.session_state.grid_rows):
    cols = st.columns(st.session_state.grid_cols)
    for j in range(st.session_state.grid_cols):
        symbol = EMOJI_MAP[st.session_state.grid[i][j]]
        cols[j].button(symbol, key=f"{i}-{j}", on_click=cycle_cell, args=(i, j))
if DISPLAY:
    display_solutions()


