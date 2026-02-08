# Timescroll Tests

Unit tests for the timescroll package.

## Structure

- `test_schemas.py` - Tests for schema validation system
- `test_metadata.py` - Tests for metadata class generation  
- `test_records.py` - Tests for record data structures
- `test_stores.py` - Tests for store management and CSV I/O

## Running Tests

Make sure you have the timescroll package available in your Python path, then run:

```bash
# Run all tests
pytest

# Run specific test file
pytest test_schemas.py

# Run with verbose output
pytest -v

# Run specific test function
pytest test_schemas.py::test_empty_schema_creation
```

## Requirements

- pytest
- timescroll package (from ../timescroll-package)

## Test Coverage

The tests cover:
- Schema creation and validation with different validator types
- Metadata class generation and behavior
- Record creation, equality, serialization, and data conversion
- Store operations including record management and CSV file I/O
- Error handling and edge cases