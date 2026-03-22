# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 13:32:04 2026

 Description
 -----------
 This module implements a terminal-based seat booking system
 for the Apache Airlines Burak757 passenger jet fleet.
 
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

# Constants

# The six cabin rows of the Burak757 (A = first, F = sixth/last).
ROWS = ['A', 'B', 'C', 'D', 'E', 'F']
 
# Total number of seat columns (1-indexed: 1 through 80).
NUM_COLUMNS = 80

# Row D (the 4th row, index 3) spans the full-width aisle of the aircraft.
AISLE_ROW = 'D'

# Storage compartments occupy columns 77 and 78 in rows D, E and F.
STORAGE_COLUMNS = [77, 78]
STORAGE_ROWS    = ['D', 'E', 'F']

# Seat status codes as named constants 
STATUS_FREE     = 'F'   # Seat is available for booking.
STATUS_RESERVED = 'R'   # Seat has been reserved by a customer.
STATUS_AISLE    = 'X'   # Position is a cabin aisle; cannot be booked.
STATUS_STORAGE  = 'S'   # Position is a storage area; cannot be booked.

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

           # Rule 2 – Remaining positions in the aisle row are marked X.
           elif row == AISLE_ROW:
               seat_map[row][col] = STATUS_AISLE

           # Rule 3 – Everything else is a free, bookable seat.
           else:
               seat_map[row][col] = STATUS_FREE

    return seat_map


# Input Parsing

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
    raw_input = input("  Enter seat reference(s), e.g. 14C or 14C,15C: ").strip()
    # Support comma-separated multiple seat references in one query.
    seat_refs = [s.strip() for s in raw_input.split(',') if s.strip()]

    if not seat_refs:
       print("  [Error] No seat references were entered.")
       return

   # Human-readable descriptions for each status code.
    status_labels = {
       STATUS_FREE:     "Free – available for booking",
       STATUS_RESERVED: "Reserved – already booked",
       STATUS_AISLE:    "Aisle – cannot be booked",
       STATUS_STORAGE:  "Storage area – cannot be booked"
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
    raw_input = input("  Enter seat reference(s) to book, e.g. 5B or 5B,6B: ").strip()
 
    seat_refs = [s.strip() for s in raw_input.split(',') if s.strip()]
 
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
            rejected_seats.append((ref.upper(), "Invalid seat reference format or out-of-range"))
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
 
        elif current_status == STATUS_AISLE:
            # Aisle position; cannot be assigned to a passenger (REQ-004).
            rejected_seats.append(
                (f"{col}{row}", "Position is a cabin aisle and cannot be booked")
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
    raw_input = input("  Enter seat reference(s) to free, e.g. 5B or 5B,6B: ").strip()
 
    seat_refs = [s.strip() for s in raw_input.split(',') if s.strip()]
 
    if not seat_refs:
        print("  [Error] No seat references were entered.")
        return
    
    freed_seats   = []
    rejected_seats = []
 
    for ref in seat_refs:
        col, row = parse_seat_reference(ref)
        
        if col is None:
            rejected_seats.append((ref.upper(), "Invalid seat reference format or out-of-range"))
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

    elif current_status == STATUS_AISLE:
        rejected_seats.append(
            (f"{col}{row}", "Position is a cabin aisle; it cannot hold a reservation")
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

def show_booking_status(seat_map):
    """
    Display the current status of the entire Burak757 seat map in a
    structured grid layout (REQ-001 / REQ-006).
 
    The grid is printed with column numbers along the top header and
    row letters along the left margin, matching the physical orientation
    of the aircraft cabin as seen from the front.
 
    Color-coded legends
    --------------------
    For readability in compatible terminals each status code is displayed
    in its assigned colour:
      [F] Green   – Free seat
      [R] Red     – Reserved seat
      [X] Yellow  – Aisle position
      [S] Blue    – Storage area
 
    A summary panel beneath the grid reports the total count of seats in
    each status category to give staff a quick overview of occupancy.
 
    Parameters
    ----------
    seat_map : dict
        The current live seat map.
    """
    print("\n--- Burak757 Seat Map ---")
 
    # ANSI escape sequences for terminal colour output.
    # Reset color back to terminal default after each cell.
    COLOR_RESET   = "\033[0m"
    COLOR_GREEN   = "\033[92m"   # Free seats
    COLOR_RED     = "\033[91m"   # Reserved seats
    COLOR_YELLOW  = "\033[93m"   # Aisle positions
    COLOR_BLUE    = "\033[94m"   # Storage areas
 
    status_colors = {
        STATUS_FREE:     COLOR_GREEN,
        STATUS_RESERVED: COLOR_RED,
        STATUS_AISLE:    COLOR_YELLOW,
        STATUS_STORAGE:  COLOR_BLUE,
    }
 
    # --- Header bar: column numbers ---
    # Print column numbers in groups of 10 for readability;
    # each cell occupies 3 characters to align with status tokens.
    print("     ", end="")   # Offset for row-label margin.
    for col in range(1, NUM_COLUMNS + 1):
        if col % 10 == 1:    # Print only every 10th label to avoid clutter.
            label = str(col)
            print(f"{label:<10}", end="")
    print()                  # Newline after header.
 
    # --- Secondary header: tick marks every 5 columns ---
    print("     ", end="")
    for col in range(1, NUM_COLUMNS + 1):
        if col % 5 == 0:
            print("|", end="  ")
        else:
            print(" ", end="  ")
    print()
 
    # Row data
    # Tallies for the summary panel below the map.
    counts = {STATUS_FREE: 0, STATUS_RESERVED: 0,
              STATUS_AISLE: 0, STATUS_STORAGE: 0}
 
    for row in ROWS:
        # Print the row letter as the left-hand margin label.
        print(f"  {row}  ", end="")
 
        for col in range(1, NUM_COLUMNS + 1):
            status = seat_map[row][col]
            color = status_colors.get(status, "")
            # Each cell: colored status character + two spaces for spacing.
            print(f"{color}{status}{COLOR_RESET}  ", end="")
            counts[status] += 1
 
        print()   # Newline at the end of each row.
 
    # Status Legend 
    print()
    print("  Legend:  "
          f"{COLOR_GREEN}[F] Free{COLOR_RESET}    "
          f"{COLOR_RED}[R] Reserved{COLOR_RESET}    "
          f"{COLOR_YELLOW}[X] Aisle{COLOR_RESET}    "
          f"{COLOR_BLUE}[S] Storage{COLOR_RESET}")
 
    # Occupancy Summary
    total_bookable = counts[STATUS_FREE] + counts[STATUS_RESERVED]
    reserved_pct   = (
        (counts[STATUS_RESERVED] / total_bookable * 100)
        if total_bookable > 0 else 0.0
    )
    print()
    print("  ── Occupancy Summary ──────────────────────────────")
    print(f"  Free seats      : {counts[STATUS_FREE]:>4}")
    print(f"  Reserved seats  : {counts[STATUS_RESERVED]:>4}  ({reserved_pct:.1f}% of bookable seats)")
    print(f"  Aisle positions : {counts[STATUS_AISLE]:>4}  (not bookable)")
    print(f"  Storage areas   : {counts[STATUS_STORAGE]:>4}  (not bookable)")
    print(f"  Total positions : {sum(counts.values()):>4}")
    print("  ───────────────────────────────────────────────────")
 
    
 # Main Menu Loop
 
def display_menu():
    """
    Print the main menu of the Apache Airlines Burak757 Booking System.
 
    The menu remains available after every operation and is only dismissed
    when the user selects option 5 (Exit program).
    """
    print("\n" + "=" * 52)
    print("   Apache Airlines – Burak757 Booking System")
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
            show_booking_status(seat_map)
 
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