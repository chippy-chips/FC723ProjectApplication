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

