import unittest
from datetime import datetime, date
from typing import Any

# Import the functions to be tested
from backend.src.core.utils import (
    create_api_success_response,
    format_datetime_for_api,
    format_date_for_api, # Added as it's in utils.py
    normalize_symbol   # Added as it's in utils.py
)

class TestCoreUtils(unittest.TestCase):

    def test_create_api_success_response(self):
        # Test with only success=True (default message is not part of this version of function)
        response_minimal = create_api_success_response()
        self.assertEqual(response_minimal, {"success": True})

        # Test with data
        data_payload = {"user_id": 1, "name": "Test User"}
        response_with_data = create_api_success_response(data=data_payload)
        self.assertEqual(response_with_data, {"success": True, "data": data_payload})

        # Test with message
        message_payload = "Operation successful"
        response_with_message = create_api_success_response(message=message_payload)
        self.assertEqual(response_with_message, {"success": True, "message": message_payload})

        # Test with data and message
        response_full = create_api_success_response(data=data_payload, message=message_payload)
        self.assertEqual(response_full, {"success": True, "data": data_payload, "message": message_payload})

        # Test with extra fields
        response_extra = create_api_success_response(data=data_payload, message=message_payload, record_count=10, page=2)
        expected_response_extra = {
            "success": True,
            "data": data_payload,
            "message": message_payload,
            "record_count": 10,
            "page": 2
        }
        self.assertEqual(response_extra, expected_response_extra)

    def test_format_datetime_for_api(self):
        # Test with a valid datetime object
        dt_obj = datetime(2023, 1, 15, 10, 30, 45, 123456)
        expected_iso = "2023-01-15T10:30:45.123456"
        self.assertEqual(format_datetime_for_api(dt_obj), expected_iso)

        # Test with None input
        self.assertIsNone(format_datetime_for_api(None))

        # Test with a non-datetime object (e.g., a date object) - expects string conversion
        date_obj = date(2023, 1, 15)
        self.assertEqual(format_datetime_for_api(date_obj), str(date_obj))

        # Test with another non-datetime object (e.g., an int)
        self.assertEqual(format_datetime_for_api(12345), "12345")


    def test_format_date_for_api(self):
        # Test with a valid date object
        date_obj = date(2023, 1, 15)
        expected_iso_date = "2023-01-15"
        self.assertEqual(format_date_for_api(date_obj), expected_iso_date)

        # Test with None input
        self.assertIsNone(format_date_for_api(None))

        # Test with a datetime object (should format only the date part)
        # Current implementation of format_date_for_api will stringify it if it's not strictly a date
        # This test reflects the current behavior.
        dt_obj = datetime(2023, 1, 15, 10, 30, 45)
        self.assertEqual(format_date_for_api(dt_obj), str(dt_obj))
        # If it were to truncate, it would be: self.assertEqual(format_date_for_api(dt_obj), "2023-01-15")

        # Test with another non-date object
        self.assertEqual(format_date_for_api("not a date"), "not a date")

    def test_normalize_symbol(self):
        self.assertEqual(normalize_symbol(" nifty 50 "), "NIFTY 50")
        self.assertEqual(normalize_symbol("reliance"), "RELIANCE")
        self.assertEqual(normalize_symbol("BANKNIFTY"), "BANKNIFTY")
        self.assertEqual(normalize_symbol("  SBIN-EQ  "), "SBIN-EQ")

if __name__ == '__main__':
    unittest.main()
```
