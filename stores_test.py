"""
Tests for timescroll.stores module.
"""

import pytest
import tempfile
import os
import csv
from collections import namedtuple

import sys

from timescroll.stores import Store, _read_meta_fields_from_csv_file
from timescroll import records


class TestStore:
    """Test the Store class functionality."""

    def test_init_basic(self):
        """Test basic Store initialization."""
        meta_fields = ["country", "variable"]
        store = Store(meta_fields=meta_fields)
        
        assert store.meta_fields == meta_fields
        assert store.all_fields == ("country", "variable", "start_period", "observations")
        assert store.records == []
        assert store.num_records == 0
        assert store.record_class.__name__ == "Record"

    def test_init_with_custom_record_class_name(self):
        """Test Store initialization with custom record class name."""
        meta_fields = ["region", "indicator"]
        store = Store(meta_fields=meta_fields, record_class_name="CustomRecord")
        
        assert store.record_class.__name__ == "CustomRecord"

    def test_init_with_converters(self):
        """Test Store initialization with converters."""
        meta_fields = ["country"]
        converter_after = {"start_period": str}
        converter_before = {"start_period": int}
        
        store = Store(
            meta_fields=meta_fields,
            converter_after_reading=converter_after,
            converter_before_writing=converter_before
        )
        
        assert store.converter_after_reading == converter_after
        assert store.converter_before_writing == converter_before

    def test_clear_records(self):
        """Test clearing records from store."""
        store = Store(meta_fields=["country"])
        record = store.create_record(country="USA", start_period="2020", observations=[1, 2, 3])
        store.records.append(record)
        
        assert store.num_records == 1
        store.clear_records()
        assert store.num_records == 0
        assert store.records == []

    def test_create_meta_data(self):
        """Test creating metadata namedtuple."""
        store = Store(meta_fields=["country", "variable"])
        meta_data = store.create_meta_data(country="USA", variable="GDP")
        
        assert isinstance(meta_data, tuple)
        assert hasattr(meta_data, "country")
        assert hasattr(meta_data, "variable")
        assert meta_data.country == "USA"
        assert meta_data.variable == "GDP"

    def test_create_record(self):
        """Test creating a record."""
        store = Store(meta_fields=["country"])
        record = store.create_record(
            country="USA",
            start_period="2020",
            observations=[1.0, 2.0, 3.0]
        )
        
        assert record.meta_data.country == "USA"
        assert record.start_period == "2020"
        assert record.observations == (1.0, 2.0, 3.0)

    def test_append_record(self):
        """Test appending a record to the store."""
        store = Store(meta_fields=["country"])
        record = store.create_record(country="USA", start_period="2020", observations=[1, 2])
        
        store.append_record(record)
        assert store.num_records == 1
        assert store.records[0] == record

    def test_append_record_with_duplicate_meta_data_raises_error(self):
        """Test that appending record with duplicate metadata raises error."""
        store = Store(meta_fields=["country"])
        record1 = store.create_record(country="USA", start_period="2020", observations=[1, 2])
        record2 = store.create_record(country="USA", start_period="2021", observations=[3, 4])
        
        store.append_record(record1)
        with pytest.raises(ValueError, match="already exists in the store"):
            store.append_record(record2)

    def test_append_record_skip_uniqueness_check(self):
        """Test appending record while skipping uniqueness check."""
        store = Store(meta_fields=["country"])
        record1 = store.create_record(country="USA", start_period="2020", observations=[1, 2])
        record2 = store.create_record(country="USA", start_period="2021", observations=[3, 4])
        
        store.append_record(record1)
        store.append_record(record2, check_meta_data_uniqueness=False)
        assert store.num_records == 2

    def test_replace_record(self):
        """Test replacing a record in the store."""
        store = Store(meta_fields=["country"])
        record1 = store.create_record(country="USA", start_period="2020", observations=[1, 2])
        record2 = store.create_record(country="CAN", start_period="2021", observations=[3, 4])
        
        store.append_record(record1)
        store.replace_record(0, record2)
        
        assert store.num_records == 1
        assert store.records[0] == record2

    def test_find_indexes_by_matching(self):
        """Test finding record indexes by metadata matching."""
        store = Store(meta_fields=["country", "variable"])
        
        # Create and add records
        record1 = store.create_record(country="USA", variable="GDP", start_period="2020")
        record2 = store.create_record(country="CAN", variable="CPI", start_period="2020")
        record3 = store.create_record(country="USA", variable="CPI", start_period="2020")
        
        store.append_record(record1, check_meta_data_uniqueness=False)
        store.append_record(record2, check_meta_data_uniqueness=False)
        store.append_record(record3, check_meta_data_uniqueness=False)
        
        # Test finding matches
        targets = [
            store.create_meta_data(country="USA", variable="GDP"),
            store.create_meta_data(country="USA", variable="CPI"),
            store.create_meta_data(country="UK", variable="GDP")  # Non-existent
        ]
        
        matching_indexes, unmatched_targets = store.find_indexes_by_matching(targets)
        
        assert len(matching_indexes) == 2
        assert 0 in matching_indexes  # USA-GDP
        assert 2 in matching_indexes  # USA-CPI
        assert len(unmatched_targets) == 1
        assert unmatched_targets[0] == store.create_meta_data(country="UK", variable="GDP")

    def test_find_indexes_by_matching_empty_targets(self):
        """Test finding indexes with empty targets list."""
        store = Store(meta_fields=["country"])
        matching_indexes, unmatched_targets = store.find_indexes_by_matching([])
        
        assert matching_indexes == []
        assert unmatched_targets == []


class TestStoreCSVOperations:
    """Test Store CSV file operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.csv_file = os.path.join(self.temp_dir, "test_data.csv")

    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.csv_file):
            os.remove(self.csv_file)
        os.rmdir(self.temp_dir)

    def test_from_csv_file_without_reading_records(self):
        """Test creating Store from CSV file without reading records."""
        # Create test CSV file
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["country", "variable", "start_period", "observations"])
            writer.writerow(["USA", "GDP", "2020", "100"])
            writer.writerow(["CAN", "CPI", "2021", "200"])
        
        store = Store.from_csv_file(self.csv_file, read_records=False)
        
        assert store.meta_fields == ("country", "variable")
        assert store.num_records == 0

    def test_from_csv_file_with_reading_records(self):
        """Test creating Store from CSV file and reading records."""
        # Create test CSV file
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["country", "variable", "start_period", "observations"])
            writer.writerow(["USA", "GDP", "2020", "100"])
            writer.writerow(["CAN", "CPI", "2021", "200"])
        
        store = Store.from_csv_file(self.csv_file, read_records=True)
        
        assert store.meta_fields == ("country", "variable")
        assert store.num_records == 2
        
        record1 = store.records[0]
        assert record1.meta_data.country == "USA"
        assert record1.meta_data.variable == "GDP"
        assert record1.start_period == "2020"
        assert record1.observations == ("100",)

    def test_read_records_from_csv_file(self):
        """Test reading records from CSV file into existing store."""
        # Create test CSV file
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["country", "start_period", "observations"])
            writer.writerow(["USA", "2020", "100"])
            writer.writerow(["CAN", "2021", "200"])
        
        store = Store(meta_fields=["country"])
        store.read_records_from_csv_file(self.csv_file)
        
        assert store.num_records == 2
        assert store.records[0].meta_data.country == "USA"
        assert store.records[1].meta_data.country == "CAN"

    def test_to_csv_file(self):
        """Test writing store records to CSV file."""
        store = Store(meta_fields=["country"])
        record1 = store.create_record(country="USA", start_period="2020", observations=["100", "101"])
        record2 = store.create_record(country="CAN", start_period="2021", observations=["200", "201"])
        
        store.append_record(record1, check_meta_data_uniqueness=False)
        store.append_record(record2, check_meta_data_uniqueness=False)
        
        store.to_csv_file(self.csv_file)
        
        # Verify the written file
        with open(self.csv_file, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == ["country", "start_period", "observations"]
            
            row1 = next(reader)
            assert row1 == ["USA", "2020", "100", "101"]
            
            row2 = next(reader)
            assert row2 == ["CAN", "2021", "200", "201"]

    def test_header_compliance_check_fails(self):
        """Test that header compliance check raises error for mismatched headers."""
        # Create CSV with wrong header
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["wrong_field", "start_period", "observations"])
            writer.writerow(["USA", "2020", "100"])
        
        store = Store(meta_fields=["country"])
        
        with pytest.raises(ValueError, match="CSV file header does not match"):
            store.read_records_from_csv_file(self.csv_file)


class TestUtilityFunctions:
    """Test utility functions in stores module."""

    def test_read_meta_fields_from_csv_file(self):
        """Test reading meta fields from CSV file."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        try:
            with temp_file as f:
                writer = csv.writer(f)
                writer.writerow(["country", "variable", "start_period", "observations"])
                writer.writerow(["USA", "GDP", "2020", "100"])
            
            meta_fields = _read_meta_fields_from_csv_file(temp_file.name)
            assert meta_fields == ("country", "variable")
        finally:
            os.unlink(temp_file.name)
