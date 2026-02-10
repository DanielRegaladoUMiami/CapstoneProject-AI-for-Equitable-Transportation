"""
Data loading and acquisition utilities.

Handles downloading and loading data from:
- US Census Bureau (ACS)
- GTFS feeds (Schedule & Real-Time)
- National Accessibility Evaluation Data
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
INTERIM_DIR = DATA_DIR / "interim"


def load_census_data(filepath=None):
    """Load US Census ACS demographic data."""
    # TODO: Implement in Sprint 1a
    pass


def load_gtfs_data(filepath=None):
    """Load GTFS schedule and real-time transit data."""
    # TODO: Implement in Sprint 1a
    pass


def load_accessibility_data(filepath=None):
    """Load National Accessibility Evaluation data."""
    # TODO: Implement in Sprint 1a
    pass


def load_merged_dataset(filepath=None):
    """Load the cleaned, merged analytical dataset."""
    path = filepath or PROCESSED_DIR / "merged_dataset.csv"
    return pd.read_csv(path)
