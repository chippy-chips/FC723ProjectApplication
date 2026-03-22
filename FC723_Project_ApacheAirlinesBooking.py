# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 13:32:04 2026

 Description
 -----------
 This module implements a terminal-based seat booking system
 for the Apache Airlines Burak757 passenger jet fleet.
 The "Show Booking Status" option opens a themed Tkinter (TTK)
 graphical window for a clear, color-coded seat map view.
 
 
 The Burak757 cabin layout:
   - Rows    : A, B, C, D, E, F  (6 rows)
   - Columns : 1 – 80            (80 columns)
   - Aisles  : Row D across all columns (status code "X")
   - Storage : Columns 77–78 in rows D, E and F (status code "S")
 
 Seat Status Codes
 -----------------
   "F" – Free     : seat is available for booking
   "R" – Reserved : seat has been successfully booked
   "X" – Aisle    : physical aisle position; not bookable
   "S" – Storage  : storage compartment area; not bookable

@author: chipp
"""

import tkinter as tk
import tkinter.ttk as ttk

# Constants

# The six cabin rows of the Burak757 (A = first, F = sixth/last).
ROWS = ['A', 'B', 'C', 'D', 'E', 'F']
 
# Total number of seat columns (1-indexed: 1 through 80).
NUM_COLUMNS = 80

# Sentinel used only in the display layer to insert the aisle visual row.
# It is never a key inside seat_map.
_AISLE_SENTINEL = '_AISLE_'


# Storage compartments occupy columns 77 and 78 in rows D, E and F.
STORAGE_COLUMNS = [77, 78]
STORAGE_ROWS    = ['D', 'E', 'F']

# Display-layer status code for aisle cells (visual only, not stored in seat_map).
STATUS_AISLE = 'X'

# Seat status codes as named constants 
STATUS_FREE     = 'F'   # Seat is available for booking.
STATUS_RESERVED = 'R'   # Seat has been reserved by a customer.
STATUS_STORAGE  = 'S'   # Position is a storage area; cannot be booked.

# Color palette used by the TTK seat map window (hex color codes).
# Keeping these in one place makes future re-theming straightforward.

COLOR_FREE_BG       = "#2ecc71"   # Green  – free seats
COLOR_FREE_FG       = "#ffffff"
COLOR_RESERVED_BG   = "#e74c3c"   # Red    – reserved seats
COLOR_RESERVED_FG   = "#ffffff"
COLOR_AISLE_BG      = "#f39c12"   # Amber  – aisle display row
COLOR_AISLE_FG      = "#ffffff"
COLOR_STORAGE_BG    = "#3498db"   # Blue   – storage areas
COLOR_STORAGE_FG    = "#ffffff"
COLOR_HEADER_FG     = "#ecf0f1"   # Light text for column/row headers
COLOR_WINDOW_BG     = "#1a252f"   # Near-black window background
COLOR_PANEL_BG      = "#2c3e50"   # Dark panel for legend and summary bars
COLOR_PANEL_FG      = "#ecf0f1"   # Light text on dark panels
 

# Seat Map initialization 

def initialize_seat_map():
    """
  Build and return the complete seat map for the Burak757 aircraft.

  The seat map is stored as a dictionary of dictionaries:
      seat_map[row_letter][column_number] -> status_code

  Initialization rules applied in priority order:
    1. Positions in the storage columns (77, 78) within rows D, E, F
       are assigned status "S" (storage takes precedence over aisle).
    2. All remaining positions in the aisle row (D) are assigned "X".
    3. All other positions are assigned "F" (free / available).

  Returns
  -------
  dict
      A fully populated seat map where every position in the 6×80 grid
      carries one of the four status codes: F, R, X, or S.
  """
    seat_map = {}

    for row in ROWS:
       seat_map[row] = {}  # Create a sub-dictionary for each row.

       for col in range(1, NUM_COLUMNS + 1):

           # Rule 1 – Storage areas take the highest priority.
           if row in STORAGE_ROWS and col in STORAGE_COLUMNS:
               seat_map[row][col] = STATUS_STORAGE
           # Rule 2 – Everything else is a free, bookable seat.
           else:
               seat_map[row][col] = STATUS_FREE

    return seat_map


# Input Parsing Helper

def split_seat_references(raw_input):
    """
    Split a raw user input string into individual seat reference tokens,
    accepting commas, spaces, or any mix of both as delimiters.
 
    All of the following produce the same three tokens:
        "5B,6B,7B"
        "5B 6B 7B"
        "5B, 6B, 7B"
        "5B , 6B , 7B"
 
    Parameters
    ----------
    raw_input : str
        The raw string entered by the user.
 
    Returns
    -------
    list of str
        A list of non-empty token strings ready for individual validation.
        Empty tokens (e.g., from trailing commas) are discarded.
    """
    # Replace every comma with a space, then split on any whitespace run.
    # This handles commas, spaces, and mixed separators in a single step.
    return raw_input.replace(',', ' ').split()
 

def parse_seat_reference(seat_ref):
    """
    Parse and validate a seat reference string entered by the user.
    
    Accepted formats (case-insensitive):
     "5B"  ->  column=5,  row='B'
     "22A" ->  column=22, row='A'
     "80F" ->  column=80, row='F'
     The seat reference must consist of a numeric column identifier
    followed by a single alphabetic row letter
    Parameters
    ----------
    seat_ref : str
        The raw input string provided by the user.
    Returns
    -------
    tuple (int, str) or (None, None)
        A (column, row) pair if the reference is valid; (None, None)
        together with a printed error message if it is invalid.

    """
    seat_ref = seat_ref.strip().upper()
    # A valid reference has at least two characters (digit(s) + letter).
    if len(seat_ref) < 2:
        print(f"  [Error] '{seat_ref}' is not a valid seat reference. "
              "Please use the format: column+row, e.g. 14C or 5B.")
        return None, None
    
    
    # The last character must be the row letter; everything before it is the column.
    row_char   = seat_ref[-1]
    column_str = seat_ref[:-1]
    
    
    # Validate the row character.
    if row_char not in ROWS:
       print(f"  [Error] Row '{row_char}' does not exist. "
             f"Valid rows are: {', '.join(ROWS)}.")
       return None, None
   
    
   # Validate the column number.
    if not column_str.isdigit():
       print(f"  [Error] Column '{column_str}' is not a valid number.")
       return None, None
    col = int(column_str)
    
    if col < 1 or col > NUM_COLUMNS:
        print(f"  [Error] Column {col} is out of range. "
              f"Valid columns are 1 to {NUM_COLUMNS}.")
        return None, None
 
    return col, row_char

# Check Seat Availability (REQ-003)

def check_availability(seat_map):
    """
    Allow the user to enquire about the current status of one or more seats.
 
    The user may enter a single seat reference (e.g. "14C") or a
    comma-separated list of references (e.g. "14C, 15C, 16C").
    For each valid reference the current status is displayed using the
    human-readable descriptions below.
 
    Parameters
    ----------
    seat_map : dict
        The live seat map returned by initialise_seat_map() and kept
        up-to-date by subsequent booking operations.
    """
    print("\n--- Check Seat Availability ---")
    raw = input("  Enter seat reference(s), e.g. 14C or 14C,15C: ").strip()
    # Support comma-separated multiple seat references in one query.
    seat_refs = [s.strip() for s in raw.split(',') if s.strip()]

    if not seat_refs:
       print("  [Error] No seat references were entered.")
       return

   # Human-readable descriptions for each status code.
    status_labels = {
        STATUS_FREE:     "Free - available for booking",
        STATUS_RESERVED: "Reserved - already booked",
        STATUS_STORAGE:  "Storage area - cannot be booked",
    }
    for ref in seat_refs:
        col, row = parse_seat_reference(ref)
 
        if col is None:
            # parse_seat_reference already printed an error; move to next.
            continue
 
        current_status = seat_map[row][col]
        label = status_labels.get(current_status, "Unknown status")
        print(f"  Seat {col}{row}  ->  [{current_status}] {label}")
        
        
 # Book a Seat  (REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007)
 
def book_seat(seat_map):
    """
    Allow the user to reserve one or more seats in a single interaction.
 
    The system validates each requested seat before confirming any booking:
      - The seat reference must be valid (parseable column+row).
      - The seat must currently have status "F" (free).
      - Aisle positions ("X") are rejected with an explanatory message.
      - Storage positions ("S") are rejected with an explanatory message.
 
    After processing the entire request, a confirmation summary is displayed
    listing successfully booked seats and any rejected references with reasons.
    The seat map is updated in-place for all successful bookings (REQ-006).
 
    Parameters
    ----------
    seat_map : dict
        The live seat map, modified in-place upon successful bookings.
    """
    print("\n--- Book a Seat ---")
    raw = input("  Enter seat reference(s) to book, e.g. 5B or 5B,6B: ").strip()
 
    seat_refs = [s.strip() for s in raw.split(',') if s.strip()]
 
    if not seat_refs:
        print("  [Error] No seat references were entered.")
        return
    
    # Accumulators for the confirmation summary (REQ-007).
    successfully_booked = []
    rejected_seats      = []   # List of (reference, reason) tuples.
 
    for ref in seat_refs:
        col, row = parse_seat_reference(ref)
 
        # Skip references that failed basic format/range validation.
        if col is None:
            rejected_seats.append(
                (ref.upper(), "Invalid seat reference format or out-of-range")
                )
            continue
        
        current_status = seat_map[row][col]
 
        if current_status == STATUS_FREE:
            # Valid free seat – update the status to Reserved (REQ-006).
            seat_map[row][col] = STATUS_RESERVED
            successfully_booked.append(f"{col}{row}")
 
        elif current_status == STATUS_RESERVED:
            # Seat is already taken; reject with a clear message (REQ-003).
            rejected_seats.append(
                (f"{col}{row}", "Seat is already reserved by another customer")
            )
 
        elif current_status == STATUS_STORAGE:
            # Storage compartment; not a passenger seat (REQ-005).
            rejected_seats.append(
                (f"{col}{row}", "Position is a storage area and cannot be booked")
            )
            # Booking Confirmation Output (REQ-007)
            print("\n  === Booking Confirmation ===")
 
    if successfully_booked:
        print(f"  Successfully reserved ({len(successfully_booked)} seat(s)):")
        for seat in successfully_booked:
            print(f"    [R] {seat} – Confirmed as Reserved")
    else:
        print("  No seats were successfully booked.")
 
    if rejected_seats:
        print(f"\n  Could not book ({len(rejected_seats)} seat(s)):")
        for seat_ref, reason in rejected_seats:
            print(f"    [!] {seat_ref} – {reason}")
            
# Free a Seat (Cancellation) 
def free_seat(seat_map):
    """
    Allow the user to cancel an existing reservation and return the seat
    to a free state.
 
    Only seats that currently carry status "R" (reserved) may be freed.
    Attempting to free a seat that is already free, an aisle, or a storage
    area will produce an explanatory error message without altering any data.
 
    Parameters
    ----------
    seat_map : dict
        The live seat map, modified in-place when a reservation is cancelled.
    """
    print("\n--- Free a Seat (Cancel Reservation) ---")
    raw = input(
        "  Enter seat reference(s) to free, e.g. 5B or 5B,6B: "
        ).strip()
 
    # Accept commas, spaces, or mixed delimiters between seat references.
    seat_refs = split_seat_references(raw)
 
    if not seat_refs:
        print("  [Error] No seat references were entered.")
        return
    
    freed_seats   = []
    rejected_seats = []
 
    for ref in seat_refs:
        col, row = parse_seat_reference(ref)
        
        if col is None:
            rejected_seats.append(
                (ref.upper(), "Invalid seat reference format or out-of-range")
                )
            continue
        
        current_status = seat_map[row][col]

    if current_status == STATUS_RESERVED:
        # Cancel the booking by restoring the seat to Free.
        seat_map[row][col] = STATUS_FREE
        freed_seats.append(f"{col}{row}")

    elif current_status == STATUS_FREE:
        rejected_seats.append(
            (f"{col}{row}", "Seat is already free; no reservation to cancel")
        )


    elif current_status == STATUS_STORAGE:
        rejected_seats.append(
            (f"{col}{row}", "Position is a storage area; it cannot hold a reservation")
        )

# Cancellation Confirmation Output
    print("\n  === Cancellation Confirmation ===")
 
    if freed_seats:
        print(f"  Successfully freed ({len(freed_seats)} seat(s)):")
        for seat in freed_seats:
            print(f"    [F] {seat} – Now available for booking")
    else:
        print("  No seats were freed.")
        
    if rejected_seats:
       print(f"\n  Could not free ({len(rejected_seats)} seat(s)):")
       for seat_ref, reason in rejected_seats:
           print(f"    [!] {seat_ref} – {reason}")

# Show Booking Status  (REQ-001, REQ-006)

def show_booking_status_gui(seat_map):
    """
    Open a TTK graphical window showing the live Burak757 seat map (REQ-001).
 
    Window sections
    ---------------
    Title area   : airline name, subtitle with live occupancy figures.
    Seat grid    : Canvas widget, 80 columns x 7 visual rows (A, B, C,
                   [aisle], D, E, F). The aisle row is amber, unlabeled,
                   and purely cosmetic - it has no corresponding seat_map data.
    Legend bar   : Color swatches and labels for F, R, X, S.
    Summary bar  : Free / Reserved / Occupied% / Storage / Total counts.
    Close button : Returns focus to the terminal menu.
 
    The window blocks the terminal menu loop via mainloop() until closed,
    preventing stale-data issues from concurrent bookings.
 
    Color coding
    ------------
    Green  (#2ecc71) - Free      [F]
    Red    (#e74c3c) - Reserved  [R]
    Amber  (#f39c12) - Aisle     [X]  (display only)
    Blue   (#3498db) - Storage   [S]
 
    Parameters
    ----------
    seat_map : dict
        Current live seat map; read-only inside this function.
    """
    # Cell sizing and spacing
    CELL_W = 18
    CELL_H = 20
    CELL_PAD = 2
    
    # Left Margin for row labels; Top Margin for Column number labels
 
    ROW_LABEL_W = 28
    COL_LABEL_H = 36
 
    # The display row sequence interleaves the visual aisle between C and D.
    # Each entry is either a real row letter (key in seat_map) or the sentinel.
    DISPLAY_ROWS = ['A', 'B', 'C', _AISLE_SENTINEL, 'D', 'E', 'F']
 
    CANVAS_W = ROW_LABEL_W + NUM_COLUMNS * (CELL_W + CELL_PAD) + CELL_PAD
    CANVAS_H = COL_LABEL_H + len(DISPLAY_ROWS) * (CELL_H + CELL_PAD) + CELL_PAD
 
    # Map each status code to its background and foreground colors.
    cell_bg = {
        STATUS_FREE:     COLOR_FREE_BG,
        STATUS_RESERVED: COLOR_RESERVED_BG,
        STATUS_AISLE:    COLOR_AISLE_BG,
        STATUS_STORAGE:  COLOR_STORAGE_BG,
    }
    cell_fg = {
        STATUS_FREE:     COLOR_FREE_FG,
        STATUS_RESERVED: COLOR_RESERVED_FG,
        STATUS_AISLE:    COLOR_AISLE_FG,
        STATUS_STORAGE:  COLOR_STORAGE_FG,
    }
 
    # Pre-compute occupancy counts for the summary bar.
    counts = {STATUS_FREE: 0, STATUS_RESERVED: 0, STATUS_STORAGE: 0}
    for row in ROWS:
        for col in range(1, NUM_COLUMNS + 1):
            counts[seat_map[row][col]] += 1
 
    total_bookable = counts[STATUS_FREE] + counts[STATUS_RESERVED]
    reserved_pct   = (counts[STATUS_RESERVED] / total_bookable * 100
                      if total_bookable > 0 else 0.0)
    # Build the window.
    root = tk.Tk()
    root.title("Apache Airlines - Burak757 Booking Status")
    root.configure(bg=COLOR_WINDOW_BG)
    root.resizable(False, False)
 
    style = ttk.Style(root)
    style.theme_use('clam')
 
    style.configure("Window.TFrame",  background=COLOR_WINDOW_BG)
    style.configure("Panel.TFrame",   background=COLOR_PANEL_BG)
 
    style.configure("Header.TLabel",
        background=COLOR_WINDOW_BG, foreground=COLOR_HEADER_FG,
        font=("Helvetica", 15, "bold"), padding=(0, 8, 0, 2))
 
    style.configure("SubHeader.TLabel",
        background=COLOR_WINDOW_BG, foreground="#95a5a6",
        font=("Helvetica", 9), padding=(0, 0, 0, 6))
 
    style.configure("Legend.TLabel",
        background=COLOR_PANEL_BG, foreground=COLOR_PANEL_FG,
        font=("Helvetica", 9), padding=(6, 5))
 
    style.configure("Summary.TLabel",
        background=COLOR_PANEL_BG, foreground=COLOR_PANEL_FG,
        font=("Helvetica", 10), padding=(10, 6))
 
    # Highlighted values in the summary bar use a yellow accent.
    style.configure("SummaryHL.TLabel",
        background=COLOR_PANEL_BG, foreground="#f1c40f",
        font=("Helvetica", 10, "bold"), padding=(2, 6))
 
    style.configure("Close.TButton",
        font=("Helvetica", 10, "bold"), padding=(14, 6))
 
    outer = ttk.Frame(root, style="Window.TFrame", padding=(16, 10, 16, 10))
    outer.pack(fill=tk.BOTH, expand=True)
 
    ttk.Label(outer, text="Burak757  -  Live Seat Map",
              style="Header.TLabel").pack(anchor="w")
 
    ttk.Label(outer,
        text=(f"Rows A-F  |  Columns 1-{NUM_COLUMNS}  |  "
              f"{counts[STATUS_RESERVED]} reserved  |  "
              f"{counts[STATUS_FREE]} available  |  "
              f"{reserved_pct:.1f}% occupied"),
        style="SubHeader.TLabel").pack(anchor="w")
 
    canvas = tk.Canvas(outer, width=CANVAS_W, height=CANVAS_H,
                       bg=COLOR_WINDOW_BG, highlightthickness=0)
    canvas.pack(pady=(0, 8))
 
    
 
    # Column number labels across the top, printed every 5 columns.
    for col in range(1, NUM_COLUMNS + 1):
        if col == 1 or col % 5 == 0:
            x = ROW_LABEL_W + (col - 1) * (CELL_W + CELL_PAD) + CELL_W // 2
            canvas.create_text(x, COL_LABEL_H // 2, text=str(col),
                                fill=COLOR_HEADER_FG, font=("Helvetica", 7),
                                anchor="center")
 
    # Subtle rule between column labels and the seat grid.
    canvas.create_line(0, COL_LABEL_H - 4, CANVAS_W, COL_LABEL_H - 4,
                       fill="#3d5166", width=1)
 
    # Render each display row, including the visual aisle sentinel.
    for r_idx, row_key in enumerate(DISPLAY_ROWS):
 
        y_center = COL_LABEL_H + r_idx * (CELL_H + CELL_PAD) + CELL_H // 2
 
        if row_key == _AISLE_SENTINEL:
            # Aisle row: draw amber X cells with no row label.
            for col in range(1, NUM_COLUMNS + 1):
                x0 = ROW_LABEL_W + (col - 1) * (CELL_W + CELL_PAD) + CELL_PAD
                y0 = COL_LABEL_H + r_idx * (CELL_H + CELL_PAD) + CELL_PAD
                x1 = x0 + CELL_W
                y1 = y0 + CELL_H
                canvas.create_rectangle(x0, y0, x1, y1,
                                        fill=COLOR_AISLE_BG, outline="")
                canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2,
                                   text=STATUS_AISLE, fill=COLOR_AISLE_FG,
                                   font=("Helvetica", 7, "bold"), anchor="center")
        else:
            # Normal bookable row: draw the row letter label then each seat cell.
            canvas.create_text(ROW_LABEL_W // 2, y_center, text=row_key,
                                fill=COLOR_HEADER_FG,
                                font=("Helvetica", 9, "bold"), anchor="center")
 
            for col in range(1, NUM_COLUMNS + 1):
                status = seat_map[row_key][col]
                bg = cell_bg.get(status, "#7f8c8d")
                fg = cell_fg.get(status, "#ffffff")
 
                x0 = ROW_LABEL_W + (col - 1) * (CELL_W + CELL_PAD) + CELL_PAD
                y0 = COL_LABEL_H + r_idx * (CELL_H + CELL_PAD) + CELL_PAD
                x1 = x0 + CELL_W
                y1 = y0 + CELL_H
 
                canvas.create_rectangle(x0, y0, x1, y1, fill=bg, outline="")
                canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2,
                                   text=status, fill=fg,
                                   font=("Helvetica", 7, "bold"), anchor="center")
 
    # Legend bar.
    legend_frame = ttk.Frame(outer, style="Panel.TFrame", padding=(4, 6))
    legend_frame.pack(fill=tk.X, pady=(0, 6))
    ttk.Label(legend_frame, text="Legend:", style="Legend.TLabel").pack(side=tk.LEFT)
 
    for bg_col, label_text in [
        (COLOR_FREE_BG,     "F  Free"),
        (COLOR_RESERVED_BG, "R  Reserved"),
        (COLOR_AISLE_BG,    "X  Aisle"),
        (COLOR_STORAGE_BG,  "S  Storage"),
    ]:
        swatch = tk.Canvas(legend_frame, width=14, height=14,
                           bg=COLOR_PANEL_BG, highlightthickness=0)
        swatch.create_rectangle(1, 1, 13, 13, fill=bg_col, outline="")
        swatch.pack(side=tk.LEFT, padx=(10, 2), pady=4)
        ttk.Label(legend_frame, text=label_text,
                  style="Legend.TLabel").pack(side=tk.LEFT, padx=(0, 4))
 
    # Summary bar.
    summary_frame = ttk.Frame(outer, style="Panel.TFrame", padding=(4, 4))
    summary_frame.pack(fill=tk.X, pady=(0, 10))
 
    def add_summary_item(parent, description, value, col_index):
        """
        Place a description/value pair in the summary bar at col_index.
 
        Parameters
        ----------
        parent      : ttk.Frame  The parent summary frame.
        description : str        Label text, e.g. "Free:".
        value       : str        The highlighted numeric or percentage value.
        col_index   : int        Logical column; each pair occupies 2 grid cols.
        """
        ttk.Label(parent, text=description, style="Summary.TLabel").grid(
            row=0, column=col_index * 2, sticky="e", padx=(10, 0))
        ttk.Label(parent, text=value, style="SummaryHL.TLabel").grid(
            row=0, column=col_index * 2 + 1, sticky="w")
 
    add_summary_item(summary_frame, "Free:",     str(counts[STATUS_FREE]),     0)
    add_summary_item(summary_frame, "Reserved:", str(counts[STATUS_RESERVED]), 1)
    add_summary_item(summary_frame, "Occupied:", f"{reserved_pct:.1f}%",       2)
    add_summary_item(summary_frame, "Storage:",  str(counts[STATUS_STORAGE]),  3)
    add_summary_item(summary_frame, "Total:",    str(sum(counts.values())),    4)
 
    ttk.Button(outer, text="Close", style="Close.TButton",
               command=root.destroy).pack(anchor="e")
 
    # Block the terminal menu until the window is closed to prevent stale data.
    root.mainloop()
 
    
 # Main Menu Loop
 
def display_menu():
    """
    Print the main menu to the terminal.
 
    The menu loops continuously until the user selects option 5 (Exit).
    """
    print("\n" + "=" * 52)
    print("   Apache Airlines - Burak757 Booking System")
    print("=" * 52)
    print("  1.  Check availability of seat")
    print("  2.  Book a seat")
    print("  3.  Free a seat")
    print("  4.  Show booking status")
    print("  5.  Exit program")
    print("=" * 52)
    
def main():
    """
    Entry point for the Burak757 Seat Booking System.
 
    Responsibilities
    ----------------
    1. Initialize the seat map on first run (REQ-001).
    2. Display the main menu in a continuous loop so that the user may
       perform multiple operations in a single session.
    3. Route each valid menu selection to its corresponding handler
       function.
    4. Accept only valid menu choices (1–5) and prompt again on invalid
       input, without crashing or terminating unexpectedly.
    5. Gracefully exit when the user selects option 5, or when an
       unexpected KeyboardInterrupt (Ctrl+C) is received.
    """
    print("\nInitialising Burak757 seat map …")
 
    # Build the seat map once at start-up; it persists for the entire session.
    seat_map = initialize_seat_map()
 
    print("Seat map ready.  All bookable seats initialised as [F] Free.")
 
        
    while True:
        display_menu()
 
        try:
            choice = input("  Enter your choice (1–5): ").strip()
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully without a traceback.
            print("\n\n  Session interrupted.  Goodbye!")
            break
 
        if choice == '1':
            check_availability(seat_map)
 
        elif choice == '2':
            book_seat(seat_map)
 
        elif choice == '3':
            free_seat(seat_map)
 
        elif choice == '4':
            show_booking_status_gui(seat_map)
 
        elif choice == '5':
            print("\n  Thank you for using the Apache Airlines Booking System.")
            print("  Goodbye!\n")
            break   # Exit the menu loop and terminate the program.
 
        else:
            # Inform the user of the invalid choice; do not exit the loop.
            print(f"\n  [Error] '{choice}' is not a valid menu option. "
                  "Please enter a number between 1 and 5.")
            
# Programme Entry Point

if __name__ == "__main__":
    main()