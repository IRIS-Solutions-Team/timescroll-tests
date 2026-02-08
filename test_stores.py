"""
Unit tests for timescroll.stores module
"""

import pytest
import tempfile
import os
from collections import namedtuple
from timescroll import Store, Record, Schema
from timescroll.metadata import build_metadata_class


def test_store_creation():
    """Test basic Store creation"""
    schema = Schema(country=None, frequency=None)
    store = Store(schema)
    
    assert store.schema == schema
    assert store.records == []
    assert store.num_records == 0
    assert store.metadata_fields == ('country', 'frequency')
    assert store.data_fields == ('start_period', 'observations')
    assert store.all_fields == ('country', 'frequency', 'start_period', 'observations')


def test_store_with_converters():
    """Test Store creation with converters"""
    schema = Schema(country=None)
    converters_after_reading = {'observations': float}
    converters_before_writing = {'start_period': str}
    
    store = Store(
        schema,
        converters_after_reading=converters_after_reading,
        converters_before_writing=converters_before_writing
    )
    
    assert store.converters_after_reading == converters_after_reading
    assert store.converters_before_writing == converters_before_writing


def test_store_clear_records():
    """Test clearing records from store"""
    schema = Schema(country=None)
    store = Store(schema)
    
    # Add some records
    record = store.build_record(country='US', start_period='2023M01', observations=[1, 2])
    store.records.append(record)
    
    assert store.num_records == 1
    
    store.clear_records()
    assert store.records == []
    assert store.num_records == 0


def test_store_build_record():
    """Test building a record from store"""
    schema = Schema(country=None, frequency=None)
    store = Store(schema)
    
    record = store.build_record(
        country='US',
        frequency='monthly',
        start_period='2023M01',
        observations=[1.5, 2.0, 3.5]
    )
    
    assert record.metadata.country == 'US'
    assert record.metadata.frequency == 'monthly'
    assert record.start_period == '2023M01'
    assert record.observations == (1.5, 2.0, 3.5)


def test_store_build_record_from_compliant_tuple():
    """Test building record from tuple"""
    schema = Schema(country=None, frequency=None)
    store = Store(schema)
    
    input_tuple = ('US', 'monthly', '2023M01', 1.5, 2.0, 3.5)
    record = store.build_record_from_compliant_tuple(input_tuple)
    
    assert record.metadata.country == 'US'
    assert record.metadata.frequency == 'monthly'
    assert record.start_period == '2023M01'
    assert record.observations == (1.5, 2.0, 3.5)


def test_store_append_record():
    """Test appending record to store"""
    schema = Schema(country=None)
    store = Store(schema)
    
    record = store.build_record(country='US', start_period='2023M01', observations=[1, 2])
    store._append_record(record)
    
    assert store.num_records == 1
    assert store.records[0] == record


def test_store_append_record_duplicate_metadata():
    """Test that appending record with duplicate metadata raises error"""
    schema = Schema(country=None)
    store = Store(schema)
    
    record1 = store.build_record(country='US', start_period='2023M01', observations=[1, 2])
    record2 = store.build_record(country='US', start_period='2023M02', observations=[3, 4])
    
    store._append_record(record1)
    
    with pytest.raises(ValueError, match="already exists"):
        store._append_record(record2)


def test_store_replace_record():
    """Test replacing record in store"""
    schema = Schema(country=None)
    store = Store(schema)
    
    record1 = store.build_record(country='US', start_period='2023M01', observations=[1, 2])
    record2 = store.build_record(country='US', start_period='2023M02', observations=[3, 4])
    
    store._append_record(record1)
    store._replace_record(0, record2)
    
    assert store.num_records == 1
    assert store.records[0] == record2


def test_store_submit_records_new():
    """Test submitting new records"""
    schema = Schema(country=None)
    store = Store(schema)
    
    records = [
        store.build_record(country='US', start_period='2023M01', observations=[1, 2]),
        store.build_record(country='UK', start_period='2023M01', observations=[3, 4])
    ]
    
    store.submit_records(records)
    
    assert store.num_records == 2
    assert store.records[0].metadata.country == 'US'
    assert store.records[1].metadata.country == 'UK'


def test_store_submit_records_replace():
    """Test submitting records that replace existing ones"""
    schema = Schema(country=None)
    store = Store(schema)
    
    # Add initial record
    record1 = store.build_record(country='US', start_period='2023M01', observations=[1, 2])
    store._append_record(record1)
    
    # Submit replacement record
    record2 = store.build_record(country='US', start_period='2023M02', observations=[3, 4])
    store.submit_records([record2])
    
    assert store.num_records == 1
    assert store.records[0] == record2


def test_store_request_records_all():
    """Test requesting all records"""
    schema = Schema(country=None)
    store = Store(schema)
    
    records = [
        store.build_record(country='US', start_period='2023M01', observations=[1]),
        store.build_record(country='UK', start_period='2023M01', observations=[2])
    ]
    store.submit_records(records)
    
    requested_records = store.request_records(None)
    assert len(requested_records) == 2


def test_store_request_records_specific():
    """Test requesting specific records by metadata"""
    schema = Schema(country=None, frequency=None)
    store = Store(schema)
    
    metadata_class = build_metadata_class(schema)
    
    records = [
        store.build_record(country='US', frequency='monthly', start_period='2023M01', observations=[1]),
        store.build_record(country='UK', frequency='monthly', start_period='2023M01', observations=[2]),
        store.build_record(country='US', frequency='quarterly', start_period='2023Q1', observations=[3])
    ]
    store.submit_records(records)
    
    # Request specific metadata
    target_metadata = [metadata_class('US', 'monthly')]
    requested_records = store.request_records(target_metadata)
    
    assert len(requested_records) == 1
    assert requested_records[0].metadata.country == 'US'
    assert requested_records[0].metadata.frequency == 'monthly'


def test_store_request_records_with_missing():
    """Test requesting records with return_missing=True"""
    schema = Schema(country=None)
    store = Store(schema)
    metadata_class = build_metadata_class(schema)
    
    # Add one record
    record = store.build_record(country='US', start_period='2023M01', observations=[1])
    store.submit_records([record])
    
    # Request both existing and non-existing
    target_metadata = [
        metadata_class('US'),
        metadata_class('UK')  # This doesn't exist
    ]
    
    requested_records, missing = store.request_records(target_metadata, return_missing=True)
    
    assert len(requested_records) == 1
    assert requested_records[0].metadata.country == 'US'
    assert len(missing) == 1
    assert missing[0].country == 'UK'


def test_store_indexes_by_metadata():
    """Test finding indexes by metadata"""
    schema = Schema(country=None)
    store = Store(schema)
    metadata_class = build_metadata_class(schema)
    
    records = [
        store.build_record(country='US', start_period='2023M01', observations=[1]),
        store.build_record(country='UK', start_period='2023M01', observations=[2]),
        store.build_record(country='DE', start_period='2023M01', observations=[3])
    ]
    store.submit_records(records)
    
    target_metadata = [
        metadata_class('UK'),
        metadata_class('FR')  # Doesn't exist
    ]
    
    index_map = store.indexes_by_metadata(target_metadata)
    
    assert index_map[metadata_class('UK')] == 1
    assert index_map[metadata_class('FR')] is None


def test_store_check_metadata_compliance():
    """Test metadata compliance checking"""
    schema = Schema(country=('value', 'US'))
    store = Store(schema)
    
    # Valid record
    valid_record = store.build_record(country='US', start_period='2023M01', observations=[1])
    store.check_metadata_compliance(valid_record)  # Should not raise
    
    # Invalid record
    metadata_class = build_metadata_class(Schema(country=None))
    invalid_metadata = metadata_class('UK')  # Doesn't match schema
    invalid_record = Record(metadata=invalid_metadata)
    
    with pytest.raises(TypeError, match="does not match"):
        store.check_metadata_compliance(invalid_record)


def test_store_write_read_csv_roundtrip():
    """Test writing and reading CSV files"""
    schema = Schema(country=None, frequency=None)
    store = Store(schema)
    
    # Create test records
    records = [
        store.build_record(country='US', frequency='monthly', start_period='2023M01', observations=[1.5, 2.0]),
        store.build_record(country='UK', frequency='quarterly', start_period='2023Q1', observations=[3.5, 4.0])
    ]
    store.submit_records(records)
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_filename = f.name
    
    try:
        store.write_records_to_csv_file(temp_filename)
        
        # Create new store and read back
        store2 = Store(schema)
        store2.read_records_from_csv_file(temp_filename)
        
        assert store2.num_records == 2
        
        # Check first record
        record1 = store2.records[0]
        assert record1.metadata.country == 'US'
        assert record1.metadata.frequency == 'monthly'
        assert record1.start_period == '2023M01'
        assert record1.observations == (1.5, 2.0)
        
        # Check second record
        record2 = store2.records[1]
        assert record2.metadata.country == 'UK'
        assert record2.metadata.frequency == 'quarterly'
        assert record2.start_period == '2023Q1'
        assert record2.observations == (3.5, 4.0)
        
    finally:
        os.unlink(temp_filename)


def test_store_csv_with_converter():
    """Test CSV reading with converter"""
    schema = Schema(country=None)
    store = Store(schema)
    
    # Create test CSV content with string numbers and empty values
    csv_content = """country,start_period,observations
US,2023M01,1.5,2.0,
UK,2023M01,3.0,,4.5
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        temp_filename = f.name
    
    try:
        # Use default converter that handles empty strings
        store.read_records_from_csv_file(temp_filename)
        
        assert store.num_records == 2
        
        # Check converted observations
        record1 = store.records[0]
        assert record1.observations == (1.5, 2.0, None)  # Empty string -> None
        
        record2 = store.records[1]
        assert record2.observations == (3.0, None, 4.5)  # Empty string -> None
        
    finally:
        os.unlink(temp_filename)


def test_store_csv_header_compliance():
    """Test CSV header compliance checking"""
    schema = Schema(country=None)
    store = Store(schema)
    
    # Create CSV with wrong headers
    csv_content = """wrong_header,start_period,observations
US,2023M01,1.5
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        temp_filename = f.name
    
    try:
        with pytest.raises(ValueError, match="does not match"):
            store.read_records_from_csv_file(temp_filename)
    finally:
        os.unlink(temp_filename)


def test_store_csv_skip_when():
    """Test CSV reading with skip_when function"""
    schema = Schema(country=None)
    store = Store(schema)
    
    # Create CSV with empty lines
    csv_content = """country,start_period,observations
US,2023M01,1.5
,2023M02,2.0
UK,2023M01,3.0
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        temp_filename = f.name
    
    try:
        # Should skip rows where first field is empty/whitespace
        store.read_records_from_csv_file(temp_filename)
        
        assert store.num_records == 2  # Should skip the empty country row
        assert store.records[0].metadata.country == 'US'
        assert store.records[1].metadata.country == 'UK'
        
    finally:
        os.unlink(temp_filename)