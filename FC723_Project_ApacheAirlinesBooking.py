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
import random
import sqlite3
import string
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

# The two permanent (non-booking) status codes stored in seat_map.
STATUS_FREE    = 'F'
STATUS_STORAGE = 'S'


# Path to the SQLite database file. Using a file (rather than :memory:)
# ensures bookings survive between program restarts.
DB_PATH = "bookings.db"

# Character pool for booking reference generation:
# 26 uppercase letters + 10 digits = 36 possible characters per position.
# With 8 positions the pool size is 36^8 = ~2.8 trillion unique references,
# making collisions negligible in practice.
REF_CHARS  = string.ascii_uppercase + string.digits
REF_LENGTH = 8

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
 
def get_db_connection():
    """
    Open and return a connection to the SQLite bookings database.

    The connection uses Row factory so columns can be accessed by name
    (e.g., row["first_name"]) as well as by index, which makes query
    results more readable throughout the codebase.

    Returns
    -------
    sqlite3.Connection
        An open connection to DB_PATH. The caller is responsible for
        closing it (ideally via a 'with' context manager).
    """
    # Connect to the database file. If the file does not exist yet,
    # sqlite3.connect() creates it automatically.
    conn = sqlite3.connect(DB_PATH)

    # Row factory makes each returned row behave like a dictionary so we
    # can write record["first_name"] instead of record[2], which is much
    # easier to read and less error-prone when columns change order.
    conn.row_factory = sqlite3.Row

    return conn

def initialise_database():
    """
    Create the bookings table if it does not already exist.

    This function is safe to call on every program start. The
    CREATE TABLE IF NOT EXISTS guard means it is a no-op when the
    table is already present, preserving any existing booking data.

    Table columns
    -------------
    booking_ref     : Unique 8-character alphanumeric string (PRIMARY KEY).
    passport_number : Customer passport number. The same person may hold
                      more than one booking, so this column is not unique.
    first_name      : Customer first name.
    last_name       : Customer last name.
    seat_row        : Row letter of the booked seat (A-F).
    seat_col        : Column number of the booked seat (1-80).
    """
    # Open a connection and use it as a context manager so it closes cleanly.
    with get_db_connection() as conn:
        # IF NOT EXISTS means this is safe to run even when the table already
        # exists from a previous session - it will simply do nothing.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                booking_ref     TEXT    PRIMARY KEY,
                passport_number TEXT    NOT NULL,
                first_name      TEXT    NOT NULL,
                last_name       TEXT    NOT NULL,
                seat_row        TEXT    NOT NULL,
                seat_col        INTEGER NOT NULL
            )
        """)
        # Commit makes the table creation permanent on disk.
        conn.commit()
        
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
               
       with get_db_connection() as conn:
        for record in conn.execute(
            "SELECT booking_ref, seat_row, seat_col FROM bookings"
        ):
            row = record["seat_row"]
            col = record["seat_col"]
 
            # Safety check: only apply the booking if the position is a
            # recognised cell in our map. This guards against corrupt data.
            if row in seat_map and col in seat_map[row]:
                # Write the booking reference into the cell, which marks
                # it as reserved and links it back to the database record.
                seat_map[row][col] = record["booking_ref"]
 
    return seat_map

def is_reserved(cell_value):
    """
    Return True if a seat map cell value represents an active booking.
 
    A cell is reserved when its value is neither STATUS_FREE ("F") nor
    STATUS_STORAGE ("S"), meaning it holds an 8-character booking reference.
 
    Parameters
    ----------
    cell_value : str
        The current value stored in seat_map[row][col].
 
    Returns
    -------
    bool
    """
    # Any value that is not "F" (free) or "S" (storage) must be a booking
    return cell_value not in (STATUS_FREE, STATUS_STORAGE)
 

def generate_booking_reference(conn):
    """
    Generate a unique 8-character alphanumeric booking reference.
 
    Algorithm
    ---------
    The character pool is 26 uppercase ASCII letters (A-Z) combined with
    10 decimal digits (0-9), giving 36 possible characters per position.
    With 8 positions the total number of distinct references is 36^8,
    which is approximately 2.82 trillion. This makes the probability of a
    random collision negligibly small even for large numbers of bookings.
 
    Generation loop:
      1. Use random.choices() to independently sample REF_LENGTH (8)
         characters from REF_CHARS, allowing repetition within a single
         reference (e.g., "AA3BX92T" is valid).
         random.choices is used instead of random.sample because sample
         draws without replacement, which would prevent any character
         from appearing more than once per reference and would reduce the
         effective pool size unnecessarily.
 
      2. Join the sampled characters into a single string candidate.
 
      3. Query the database for a row with that booking_ref value.
         If no row is returned the candidate is unique and is returned
         immediately.
 
      4. If a row IS returned (collision), the loop repeats and a new
         candidate is generated. Given the pool size, in any realistic
         deployment this branch will never execute, but the loop provides
         a mathematically correct guarantee of uniqueness regardless.
 
    Parameters
    ----------
    conn : sqlite3.Connection
        An open database connection used to check for reference collisions.
        The same connection that is being used for the current booking
        transaction must be passed in so that references generated earlier
        in the same transaction are visible to the uniqueness check.
 
    Returns
    -------
    str
        A unique 8-character booking reference string (all uppercase).
    """
    while True:
        # Step 1: Pick REF_LENGTH characters at random from the pool.
        # random.choices samples WITH replacement, meaning the same character
        # can appear more than once in the same reference. This maximizes the
        # number of possible combinations (36^8 rather than 36 x 35 x ... x 29).
        candidate = ''.join(random.choices(REF_CHARS, k=REF_LENGTH))
        
        # Step 2: Ask the database whether this reference already exists.
       # "SELECT 1" is the lightest possible query - we only need to know
       # if a row exists, not what it contains.
       # fetchone() returns None when no matching row is found.
        existing = conn.execute(
           "SELECT 1 FROM bookings WHERE booking_ref = ?", (candidate,)
       ).fetchone()

       # Step 3: No row returned means the candidate is unique - use it.
        if existing is None:
           return candidate




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


    for ref in seat_refs:
        col, row = parse_seat_reference(ref)
 
        if col is None:
            # parse_seat_reference already printed an error; move to next.
            continue
        
        # Read the current value stored in the seat map for this position.
        value = seat_map[row][col]
 
        if value == STATUS_FREE:
            # "F" means the seat is empty and ready to be booked.
            print(f"  Seat {col}{row}  ->  [F] Free - available for booking")
 
        elif value == STATUS_STORAGE:
            # "S" means the position is a fixed storage compartment on the aircraft.
            print(f"  Seat {col}{row}  ->  [S] Storage area - cannot be booked")
        
        
        else:
            # Any other value is an 8-character booking reference, meaning this
            # seat is reserved. We look up the database to show the passenger's
            # name alongside the reference so staff can identify who booked it.
            with get_db_connection() as conn:
                record = conn.execute(
                    "SELECT first_name, last_name FROM bookings "
                    "WHERE booking_ref = ?",
                    (value,)
                ).fetchone()
 
            if record:
                # Display the reference and the passenger's full name.
                name = f"{record['first_name']} {record['last_name']}"
                print(f"  Seat {col}{row}  ->  [R] Reserved  |  "
                      f"Ref: {value}  |  {name}")
            else:
                # The reference exists in the map but not in the database.
                # This should not happen in normal use, but we handle it
                # gracefully rather than crashing.
                print(f"  Seat {col}{row}  ->  [R] Reserved  |  Ref: {value}")
 
 # Book a Seat  (REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007)
 
def book_seat(seat_map):
    """
    Reserve one or more seats for a single customer in one transaction.
 
    The function collects the customer's details once (passport number,
    first name, last name) and then asks which seats they want to book.
    A unique 8-character booking reference is generated for EACH seat,
    stored in the seat_map, and written to the database along with the
    customer's details.
 
    Validation rules applied per seat:
      - Reference must be a valid column+row string within the aircraft.
      - Seat must currently be free (STATUS_FREE). Reserved seats and
        storage positions are rejected with explanatory messages.
 
    A confirmation summary is printed listing successful bookings (with
    their assigned reference codes) and any rejected seats with reasons.
 
    Parameters
    ----------
    seat_map : dict
        The live seat map, updated in-place for each successful booking.
    """
    print("\n--- Book a Seat ---")
    passport = input("  Passport number    : ").strip().upper()
    if not passport:
        print("  [Error] Passport number cannot be empty.")
        return
 
    first_name = input("  First name         : ").strip().title()
    if not first_name:
        print("  [Error] First name cannot be empty.")
        return
 
    last_name = input("  Last name          : ").strip().title()
    if not last_name:
        print("  [Error] Last name cannot be empty.")
        return
 
    
    raw = input("  Enter seat reference(s) to book, e.g. 5B or 5B,6B: ").strip()
 
    seat_refs = [s.strip() for s in raw.split(',') if s.strip()]
 
  # Split the input into individual seat tokens using the helper function.
    seat_refs = split_seat_references(raw)
    if not seat_refs:
        print("  [Error] No seat references were entered.")
        return
 
    # These lists accumulate the results so we can print a full summary
    # after processing every requested seat.
    booked   = []   # (seat_label, booking_ref) for each successful booking.
    rejected = []   # (seat_label, reason) for each seat that could not be booked.
 
    # Open a single database connection for the whole transaction. Using one
    # connection means all the INSERT statements are committed together at the
    # end. If anything goes wrong before the commit, none of the inserts are
    # saved, which keeps the database consistent.
    with get_db_connection() as conn:
        for ref in seat_refs:
            col, row = parse_seat_reference(ref)
 
            # Skip tokens that did not pass the format/range check.
            if col is None:
                rejected.append(
                    (ref.upper(), "Invalid seat reference format or out-of-range")
                )
                continue
 
            # Read the current state of this seat from the in-memory map.
            value = seat_map[row][col]
 
            if value == STATUS_FREE:
                # The seat is available. Generate a unique reference for it.
                # We pass the open connection so the generator can check the
                # database for collisions, including references created earlier
                # in this same loop (before the final commit).
                booking_ref = generate_booking_reference(conn)
 
                # Write the booking to the database immediately. Doing this
                # before moving to the next seat ensures that generate_booking_
                # reference() will see this reference as "taken" if it somehow
                # generates the same string for a later seat in the same loop.
                conn.execute(
                    """INSERT INTO bookings
                       (booking_ref, passport_number, first_name,
                        last_name, seat_row, seat_col)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (booking_ref, passport, first_name, last_name, row, col)
                )
 
                # Update the in-memory seat map so the rest of the program
                # sees this seat as reserved straight away, without needing
                # to re-query the database.
                seat_map[row][col] = booking_ref
                booked.append((f"{col}{row}", booking_ref))
 
            elif value == STATUS_STORAGE:
                # The position is a storage compartment, not a seat.
                rejected.append(
                    (f"{col}{row}",
                     "Position is a storage area and cannot be booked")
                )
 
            else:
                # The cell already holds a booking reference, so the seat is
                # taken by someone else.
                rejected.append(
                    (f"{col}{row}",
                     "Seat is already reserved by another customer")
                )
 
        # Commit all inserts to disk in one atomic operation. Either all
        # successful bookings are saved or none of them are.
        conn.commit()
 
    # Print the full booking summary for the customer.
    print("\n  === Booking Confirmation ===")
    if booked:
        print(f"  Successfully reserved ({len(booked)} seat(s)) "
              f"for {first_name} {last_name} (Passport: {passport}):")
        for seat_label, booking_ref in booked:
            # Show each seat alongside its unique reference code so the
            # customer has a record they can use for check-in or cancellation.
            print(f"    [R] Seat {seat_label}  |  Booking Reference: {booking_ref}")
    else:
        print("  No seats were successfully booked.")
 
    if rejected:
        print(f"\n  Could not book ({len(rejected)} seat(s)):")
        for seat_label, reason in rejected:
            print(f"    [!] {seat_label} - {reason}")
            # Booking Confirmation Output (REQ-007)
            print("\n  === Booking Confirmation ===")
 
            
# Free a Seat (Cancellation) 
def free_seat(seat_map):
    """
    Cancel one or more reservations belonging to a single customer.
 
    Cancellation is customer-driven: the customer provides their passport
    number and the system retrieves all seats currently reserved under
    that passport. The customer then selects which of their seats to
    cancel, or types "all" to cancel every seat in one go. This design
    means a customer can only ever see and cancel their own bookings -
    they cannot accidentally (or intentionally) free someone else's seat.
 
    For each confirmed cancellation:
      - The booking row is deleted from the database.
      - The seat_map cell is restored to STATUS_FREE ("F").
 
    Parameters
    ----------
    seat_map : dict
        The live seat map, updated in-place for each successful cancellation.
    """
    print("\n--- Free a Seat (Cancel Reservation) ---")
    # Ask the customer to identify themselves by passport number.
   # This is the key that links them to their bookings in the database.
    passport = input(
       "  Enter your passport number to look up your bookings: "
    ).strip().upper()

    if not passport:
       print("  [Error] Passport number cannot be empty.")
       return

    # Query the database for every seat currently booked under this passport.
    # Results are sorted by row then column so the numbered list is easy to read.
    with get_db_connection() as conn:
       records = conn.execute(
           """SELECT booking_ref, first_name, last_name, seat_row, seat_col
              FROM bookings
              WHERE passport_number = ?
              ORDER BY seat_row, seat_col""",
           (passport,)
       ).fetchall()

    # If the passport number returns no rows, the customer either has no
    # bookings or typed the wrong passport number.
    if not records:
       print(f"  No active bookings found for passport number '{passport}'.")
       return

    # Show the customer a numbered list of all their current bookings so they
    # can choose which ones to cancel by entering the corresponding numbers.
    customer_name = f"{records[0]['first_name']} {records[0]['last_name']}"
    print(f"\n  Bookings for {customer_name} (Passport: {passport}):")
    for i, rec in enumerate(records, start=1):
       # Enumerate starts at 1 so the customer sees a natural 1-based list.
       print(f"    {i}. Seat {rec['seat_col']}{rec['seat_row']}  |  "
             f"Ref: {rec['booking_ref']}")

    # Ask the customer to select which seats they want to cancel.
    # They can enter a single number, multiple numbers, or the word "all".
    print("\n  Enter seat numbers from the list above to cancel "
         "(e.g.  1   or   1 3   or   all):")
    choice_raw = input("  Your choice: ").strip().lower()

    if not choice_raw:
       print("  [Error] No selection made. No changes were applied.")
       return

    # Work out which database records the customer wants to cancel.
    if choice_raw == 'all':
       # "all" selects every booking in the list at once.
       selected = list(records)
    else:
       # Parse the numbers entered by the customer and map each one back
       # to the corresponding record from the query results.
       selected       = []
       invalid_entries = []

       for token in choice_raw.replace(',', ' ').split():
           if token.isdigit():
               # Convert from the 1-based number shown on screen to the
               # 0-based index used by Python lists.
               idx = int(token) - 1

               if 0 <= idx < len(records):
                   selected.append(records[idx])
               else:
                   # The number is valid digits but outside the list range.
                   invalid_entries.append(token)
           else:
               # The token is not a number at all - warn the customer.
               invalid_entries.append(token)

       if invalid_entries:
           print(f"  [Warning] Unrecognized selection(s) ignored: "
                 f"{', '.join(invalid_entries)}")

    # If nothing valid was selected (e.g., the customer only typed garbage),
    # bail out without making any changes.
    if not selected:
       print("  No valid seats were selected. No changes were applied.")
       return

    # Process each selected cancellation.
    freed    = []   # Records successfully canceled.
    rejected = []   # Records that could not be canceled (with reasons).

    with get_db_connection() as conn:
       for rec in selected:
           row = rec["seat_row"]
           col = rec["seat_col"]
           ref = rec["booking_ref"]

           # Double-check that the in-memory seat map still holds this exact
           # booking reference before deleting the database row. This guards
           # against the rare case where the map and database have gotten out
           # of sync (for example if someone manually edited the database file).
           if seat_map[row][col] == ref:
               # Remove the booking record from the database.
               conn.execute(
                   "DELETE FROM bookings WHERE booking_ref = ?", (ref,)
               )

               # Restore the seat map cell to Free so it can be booked again.
               seat_map[row][col] = STATUS_FREE
               freed.append(f"{col}{row} (Ref: {ref})")
           else:
               # The seat map does not match the database for this seat.
               # Do not delete anything and report the problem instead.
               rejected.append(
                   (f"{col}{row}", "Seat state mismatch - no change made")
               )

       # Commit all deletions together so they either all succeed or all fail.
       conn.commit()

    # Print the full cancellation summary.
    print("\n  === Cancellation Confirmation ===")
    if freed:
       print(f"  Successfully canceled ({len(freed)} seat(s)):")
       for entry in freed:
           print(f"    [F] {entry} - Now available for booking")
    else:
       print("  No seats were canceled.")

    if rejected:
       print(f"\n  Issues encountered ({len(rejected)}):")
       for seat_label, reason in rejected:
           print(f"    [!] {seat_label} - {reason}")



# Show Booking Status  (REQ-001, REQ-006)
def show_booking_status_gui(seat_map):
    """
    Open a TTK graphical window showing the live Burak757 seat map.
 
    The seat grid renders all 480 positions across 6 bookable rows plus
    one visual-only aisle row inserted between C and D. Each cell is
    color-coded by its current status:
 
      Green  (#2ecc71) - Free      [F]
      Red    (#e74c3c) - Reserved  (any 8-char booking reference)
      Amber  (#f39c12) - Aisle     [X]  (display only, not in seat_map)
      Blue   (#3498db) - Storage   [S]
 
    Reserved cells display the letter "R" in the GUI cell (the full
    8-character booking reference is too long to fit in a small cell
    but can be seen by using option 1 - Check Seat Availability).
 
    The window blocks the terminal menu loop via mainloop() until closed,
    preventing booking changes while the map is being viewed.
 
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
 
   # Count how many seats are in each category to populate the summary bar.
    # Any cell value that is not "F" or "S" is treated as a booking reference,
    # meaning that seat is reserved.
    reserved_count = 0
    free_count     = 0
    storage_count  = 0
    for row in ROWS:
        for col in range(1, NUM_COLUMNS + 1):
            v = seat_map[row][col]
            if v == STATUS_FREE:
                free_count += 1
            elif v == STATUS_STORAGE:
                storage_count += 1
            else:
                reserved_count += 1   # Booking reference found.
 
    # Calculate what percentage of bookable seats are currently occupied.
    total_bookable = free_count + reserved_count
    reserved_pct   = (reserved_count / total_bookable * 100
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
              f"{[reserved_count]} reserved  |  "
              f"{[free_count]} |  "
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
                value = seat_map[row_key][col]
        
 
                # Choose the cell color and the letter to display based on
                # the seat map value. Any value that is not "F" or "S" is
                # a booking reference, so we render it as red with "R".
                if value == STATUS_FREE:
                  bg, fg, label = COLOR_FREE_BG, COLOR_FREE_FG, "F"
                elif value == STATUS_STORAGE:
                  bg, fg, label = COLOR_STORAGE_BG, COLOR_STORAGE_FG, "S"
                else:
                  # Booking reference - display as reserved (red, "R").
                  bg, fg, label = COLOR_RESERVED_BG, COLOR_RESERVED_FG, "R"

                # Calculate pixel coordinates for this cell's top-left corner.
                x0 = ROW_LABEL_W + (col - 1) * (CELL_W + CELL_PAD) + CELL_PAD
                y0 = COL_LABEL_H + r_idx * (CELL_H + CELL_PAD) + CELL_PAD

                # Draw the colored background rectangle for the cell.
                canvas.create_rectangle(x0, y0, x0 + CELL_W, y0 + CELL_H,
                                      fill=bg, outline="")

                # Draw the status letter centered inside the rectangle.
                canvas.create_text(
                  (x0 + x0 + CELL_W) / 2, (y0 + y0 + CELL_H) / 2,
                  text=label, fill=fg,
                  font=("Helvetica", 7, "bold"), anchor="center"
              )
 
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
 
    # Populate the summary bar with the five key occupancy figures.
    add_summary_item(summary_frame, "Free:",     str(free_count),        0)
    add_summary_item(summary_frame, "Reserved:", str(reserved_count),    1)
    add_summary_item(summary_frame, "Occupied:", f"{reserved_pct:.1f}%", 2)
    add_summary_item(summary_frame, "Storage:",  str(storage_count),     3)
    add_summary_item(summary_frame, "Total:",
                    str(free_count + reserved_count + storage_count),   4)
 
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
    Program entry point for the Burak757 Seat Booking System.
 
    Runs three setup steps before entering the menu loop:
      1. initialise_database() - creates the bookings table if it does not
         exist yet (safe to call even when the table is already there).
      2. initialise_seat_map() - builds the in-memory grid and overlays any
         bookings stored in the database from previous sessions.
      3. Menu loop - displays the menu repeatedly until the user exits or
         presses Ctrl+C to interrupt the program.
    """
    print("\nInitializing Apache Airlines Booking System ...")
 
    # Set up the database table. This is a no-op if the table already exists.
    initialise_database()
 
    # Build the in-memory seat map and restore any previously saved bookings.
    seat_map = initialize_seat_map()
 
    print("System ready. Database connected. Seat map loaded.")
 
    # Keep showing the menu until the user chooses to exit.
    while True:
        display_menu()
 
        try:
            choice = input("  Enter your choice (1-5): ").strip()
        except KeyboardInterrupt:
            # Ctrl+C exits the program cleanly without a stack trace.
            print("\n\n  Session interrupted. Goodbye!")
            break
 
        if choice == '1':
            check_availability(seat_map)
        elif choice == '2':
            book_seat(seat_map)
        elif choice == '3':
            free_seat(seat_map)
        elif choice == '4':
            # Opens the TTK GUI window; menu resumes when the window is closed.
            show_booking_status_gui(seat_map)
        elif choice == '5':
            print("\n  Thank you for using the Apache Airlines Booking System.")
            print("  Goodbye!\n")
            break
        else:
            # Any input that is not 1-5 is rejected with an explanatory message.
            print(f"\n  [Error] '{choice}' is not a valid option. "
                  "Please enter a number between 1 and 5.")
 
 
# Programme Entry Point

if __name__ == "__main__":
    main()