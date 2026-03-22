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