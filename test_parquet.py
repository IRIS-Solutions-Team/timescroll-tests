"""
Unit tests for timescroll Parquet functionality
"""

import pytest
import tempfile
import os
from collections import namedtuple
from timescroll import Store, Record, Schema
from timescroll.metadata import build_metadata_class


def test_store_write_read_parquet_roundtrip():
    """Test writing and reading Parquet files"""
    schema = Schema(country=None, frequency=None)
    store = Store(schema)
    
    # Create test records with variable-length observations
    records = [
        store.build_record(country="US", frequency="monthly", start_period="2023M01", observations=[1.5, 2.0]),
        store.build_record(country="UK", frequency="quarterly", start_period="2023Q1", observations=[3.5, 4.0, 5.5])
    ]
    store.submit_records(records)
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".parquet", delete=False) as f:
        temp_filename = f.name
    
    try:
        store.write_records_to_parquet_file(temp_filename)
        
        # Create new store and read back
        store2 = Store(schema)
        store2.read_records_from_parquet_file(temp_filename)
        
        assert store2.num_records == 2
        
        # Check first record
        record1 = store2.records[0]
        assert record1.metadata.country == "US"
        assert record1.metadata.frequency == "monthly"
        assert record1.start_period == "2023M01"
        assert record1.observations == (1.5, 2.0)
        
        # Check second record
        record2 = store2.records[1]
        assert record2.metadata.country == "UK"
        assert record2.metadata.frequency == "quarterly"
        assert record2.start_period == "2023Q1"
        assert record2.observations == (3.5, 4.0, 5.5)
        
    finally:
        os.unlink(temp_filename)


def test_store_parquet_variable_length_observations():
    """Test Parquet with records having different observation lengths"""
    schema = Schema(series=None)
    store = Store(schema)
    
    # Create records with very different observation lengths
    records = [
        store.build_record(series="short", start_period="2023M01", observations=[1.0]),
        store.build_record(series="medium", start_period="2023M01", observations=[2.0, 3.0, 4.0]),
        store.build_record(series="long", start_period="2023M01", observations=[5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    ]
    store.submit_records(records)
    
    # Write and read back
    with tempfile.NamedTemporaryFile(mode="w", suffix=".parquet", delete=False) as f:
        temp_filename = f.name
    
    try:
        store.write_records_to_parquet_file(temp_filename)
        
        store2 = Store(schema)
        store2.read_records_from_parquet_file(temp_filename)
        
        assert store2.num_records == 3
        assert len(store2.records[0].observations) == 1
        assert len(store2.records[1].observations) == 3
        assert len(store2.records[2].observations) == 6
        
        # Verify actual values
        assert store2.records[0].observations == (1.0,)
        assert store2.records[1].observations == (2.0, 3.0, 4.0)
        assert store2.records[2].observations == (5.0, 6.0, 7.0, 8.0, 9.0, 10.0)
        
    finally:
        os.unlink(temp_filename)


def test_store_parquet_with_converter():
    """Test Parquet reading with converter"""
    schema = Schema(country=None)
    store = Store(schema)
    
    # Create test record
    record = store.build_record(country="US", start_period="2023M01", observations=[1.5, 2.0])
    store.submit_records([record])
    
    # Write to parquet
    with tempfile.NamedTemporaryFile(mode="w", suffix=".parquet", delete=False) as f:
        temp_filename = f.name
    
    try:
        store.write_records_to_parquet_file(temp_filename)
        
        # Read back with converter
        store2 = Store(schema)
        converter = {
            "observations": lambda x: x * 2.0 if x is not None else None,  # Double all values
            "start_period": lambda x: x.replace("M", "-")  # Change format
        }
        store2.read_records_from_parquet_file(temp_filename, converter=converter)
        
        assert store2.num_records == 1
        record = store2.records[0]
        assert record.observations == (3.0, 4.0)  # Values doubled
        assert record.start_period == "2023-01"  # Format changed
        
    finally:
        os.unlink(temp_filename)


def test_store_parquet_compression_options():
    """Test different compression options for Parquet"""
    schema = Schema(country=None)
    store = Store(schema)
    
    record = store.build_record(country="US", start_period="2023M01", observations=[1.0, 2.0, 3.0])
    store.submit_records([record])
    
    compression_options = ["snappy", "gzip", "brotli"]
    
    for compression in compression_options:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".parquet", delete=False) as f:
            temp_filename = f.name
        
        try:
            # Write with specific compression
            store.write_records_to_parquet_file(temp_filename, compression=compression)
            
            # Read back and verify
            store2 = Store(schema)
            store2.read_records_from_parquet_file(temp_filename)
            
            assert store2.num_records == 1
            assert store2.records[0].observations == (1.0, 2.0, 3.0)
            
        finally:
            os.unlink(temp_filename)


def test_store_parquet_empty_store():
    """Test that writing empty store raises ValueError"""
    schema = Schema(country=None)
    store = Store(schema)
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".parquet", delete=False) as f:
        temp_filename = f.name
    
    try:
        with pytest.raises(ValueError, match="No records to write"):
            store.write_records_to_parquet_file(temp_filename)
    finally:
        # Clean up file if it was created
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)


def test_store_parquet_mixed_metadata_types():
    """Test Parquet with different metadata field types"""
    schema = Schema(country=None, year=None, active=None)
    store = Store(schema)
    
    # Create records with different metadata types
    records = [
        store.build_record(country="US", year=2023, active=True, start_period="2023M01", observations=[1.0]),
        store.build_record(country="UK", year=2024, active=False, start_period="2024M01", observations=[2.0, 3.0])
    ]
    store.submit_records(records)
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".parquet", delete=False) as f:
        temp_filename = f.name
    
    try:
        store.write_records_to_parquet_file(temp_filename)
        
        store2 = Store(schema)
        store2.read_records_from_parquet_file(temp_filename)
        
        assert store2.num_records == 2
        
        # Check metadata types are preserved
        record1 = store2.records[0]
        assert record1.metadata.country == "US"
        assert record1.metadata.year == 2023
        assert record1.metadata.active == True
        
        record2 = store2.records[1]
        assert record2.metadata.country == "UK"
        assert record2.metadata.year == 2024
        assert record2.metadata.active == False
        
    finally:
        os.unlink(temp_filename)