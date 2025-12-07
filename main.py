import streamlit as st

# Configurable grid size
GRID_ROWS = 10
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
        border: 1px solid #bbb;
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

if "connected" not in st.session_state:
    st.session_state.connected = True  # empty grid is trivially connected

# Button appearance mapping using emoji squares
EMOJI_MAP = {
    0: "⬜",
    1: "⬛",
    2: "🟥"
}

def is_this_MHC(grid):
    # Only black points matter.
    points = [(i, j) for i, row in enumerate(grid) for j, v in enumerate(row) if v == 1]

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
            miny, maxy = (ay, by) if ay < ay else (by, ay)  # bug fix: compare ay with by
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

def cycle_cell(i, j):
    st.session_state.grid[i][j] = (st.session_state.grid[i][j] + 1) % 3
    # Update connectedness flag; render message after the grid
    st.session_state.connected = is_this_MHC(st.session_state.grid)

# Layout grid with minimal gaps
for i in range(GRID_ROWS):
    cols = st.columns(GRID_COLS)
    for j in range(GRID_COLS):
        symbol = EMOJI_MAP[st.session_state.grid[i][j]]
        cols[j].button(symbol, key=f"{i}-{j}", on_click=cycle_cell, args=(i, j))

# Status message at the bottom of the grid
if st.session_state.connected:
    st.success("Connected")
else:
    st.error("Not Connected")
