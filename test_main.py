import pytest
from datetime import time, datetime
from main import (
    get_end_hour_from_start_hour, 
    get_end_time_from_end_hour, 
    get_date_object_from_string, 
    get_time_object_from_string
)

def test_get_end_hour_from_start_hour():
    assert get_end_hour_from_start_hour(10) == 11
    assert get_end_hour_from_start_hour(23) == 0

def test_get_end_time_from_end_hour():
    assert get_end_time_from_end_hour(11) == "11:00"
    assert get_end_time_from_end_hour(0) == "00:00"

def test_get_date_object_from_string():
    assert get_date_object_from_string("2024-10-01") == datetime.strptime("2024-10-01", "%Y-%m-%d").date()

def test_get_time_object_from_string():
    assert get_time_object_from_string("13:45") == time(13, 45)

