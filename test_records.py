"""
Unit tests for timescroll.records module
"""

import pytest
from collections import namedtuple
from timescroll import Record, Schema
from timescroll.metadata import build_metadata_class, EmptyMetadata


def test_record_creation_empty():
    """Test creating a record with default/empty values"""
    record = Record()
    assert record.metadata == EmptyMetadata()
    assert record.start_period is None
    assert record.observations == ()


def test_record_creation_with_values():
    """Test creating a record with specific values"""
    schema = Schema(country=None, frequency=None)
    metadata_class = build_metadata_class(schema)
    metadata = metadata_class('US', 'monthly')
    
    record = Record(
        metadata=metadata,
        start_period='2023M01',
        observations=[1.5, 2.0, 3.5]
    )
    
    assert record.metadata == metadata
    assert record.start_period == '2023M01'
    assert record.observations == (1.5, 2.0, 3.5)  # Should be tuple


def test_record_observations_tuple_conversion():
    """Test that observations are converted to tuple"""
    record = Record(observations=[1, 2, 3])
    assert record.observations == (1, 2, 3)
    assert isinstance(record.observations, tuple)
    
    record = Record(observations=(4, 5, 6))
    assert record.observations == (4, 5, 6)
    assert isinstance(record.observations, tuple)


def test_record_all_fields():
    """Test all_fields property"""
    schema = Schema(country=None, frequency=None)
    metadata_class = build_metadata_class(schema)
    metadata = metadata_class('US', 'monthly')
    
    record = Record(metadata=metadata)
    expected_fields = ('country', 'frequency', 'start_period', 'observations')
    assert record.all_fields == expected_fields


def test_record_equality():
    """Test record equality comparison"""
    schema = Schema(country=None)
    metadata_class = build_metadata_class(schema)
    metadata1 = metadata_class('US')
    metadata2 = metadata_class('US')
    metadata3 = metadata_class('UK')
    
    record1 = Record(metadata=metadata1, start_period='2023M01', observations=[1, 2])
    record2 = Record(metadata=metadata2, start_period='2023M01', observations=[1, 2])
    record3 = Record(metadata=metadata3, start_period='2023M01', observations=[1, 2])
    record4 = Record(metadata=metadata1, start_period='2023M02', observations=[1, 2])
    
    assert record1 == record2
    assert record1 != record3  # Different metadata
    assert record1 != record4  # Different start_period
    assert record1 != "not a record"  # Different type


def test_record_hash():
    """Test record hash based on metadata"""
    schema = Schema(country=None)
    metadata_class = build_metadata_class(schema)
    metadata1 = metadata_class('US')
    metadata2 = metadata_class('US')
    metadata3 = metadata_class('UK')

    record1 = Record(metadata=metadata1)
    record2 = Record(metadata=metadata2)
    record3 = Record(metadata=metadata3)

    assert record1.__hash__ == record2.__hash__
    assert record1.__hash__ != record3.__hash__


def test_record_equal_metadata():
    """Test equal_metadata method"""
    schema = Schema(country=None)
    metadata_class = build_metadata_class(schema)
    metadata1 = metadata_class('US')
    metadata2 = metadata_class('US')
    metadata3 = metadata_class('UK')
    
    record1 = Record(metadata=metadata1, start_period='2023M01')
    record2 = Record(metadata=metadata2, start_period='2023M02')  # Different start_period
    record3 = Record(metadata=metadata3, start_period='2023M01')
    
    assert record1.equal_metadata(record2)  # Same metadata, different data
    assert not record1.equal_metadata(record3)  # Different metadata


def test_record_to_tuple():
    """Test to_tuple method"""
    schema = Schema(country=None, frequency=None)
    metadata_class = build_metadata_class(schema)
    metadata = metadata_class('US', 'monthly')
    
    record = Record(
        metadata=metadata,
        start_period='2023M01',
        observations=[1.5, 2.0, 3.5]
    )
    
    expected_tuple = ('US', 'monthly', '2023M01', 1.5, 2.0, 3.5)
    assert record.to_tuple() == expected_tuple


def test_record_to_dict():
    """Test to_dict method"""
    schema = Schema(country=None, frequency=None)
    metadata_class = build_metadata_class(schema)
    metadata = metadata_class('US', 'monthly')
    
    record = Record(
        metadata=metadata,
        start_period='2023M01',
        observations=[1.5, 2.0]
    )
    
    expected_dict = {
        'country': 'US',
        'frequency': 'monthly',
        'start_period': '2023M01',
        'observations': (1.5, 2.0)
    }
    assert record.to_dict() == expected_dict


def test_record_copy():
    """Test copy method"""
    schema = Schema(country=None)
    metadata_class = build_metadata_class(schema)
    metadata = metadata_class('US')
    
    original = Record(
        metadata=metadata,
        start_period='2023M01',
        observations=[1, 2, 3]
    )
    
    copy = original.copy()
    
    assert copy == original
    assert copy is not original
    assert copy.metadata is original.metadata  # Metadata is immutable
    assert copy.observations is original.observations  # Same tuple because tuples are immutable


def test_record_apply_converter_none():
    """Test apply_converter with None converter"""
    record = Record(start_period='2023M01', observations=[1, 2, 3])
    original_start_period = record.start_period
    original_observations = record.observations
    
    record.apply_converter(None)
    
    assert record.start_period == original_start_period
    assert record.observations == original_observations


def test_record_apply_converter_observations():
    """Test apply_converter with observations converter"""
    record = Record(observations=['1.5', '2.0', ''])
    
    converter = {
        'observations': lambda x: float(x) if x != '' else None
    }
    
    record.apply_converter(converter)
    
    assert record.observations == (1.5, 2.0, None)


def test_record_apply_converter_start_period():
    """Test apply_converter with start_period converter"""
    record = Record(start_period='2023-01')
    
    converter = {
        'start_period': lambda x: x.replace('-', 'M')
    }
    
    record.apply_converter(converter)
    
    assert record.start_period == '2023M01'


def test_record_apply_converter_both():
    """Test apply_converter with both converters"""
    record = Record(
        start_period='2023-01',
        observations=['1.5', '', '3.0']
    )
    
    converter = {
        'start_period': lambda x: x.replace('-', 'M'),
        'observations': lambda x: float(x) if x != '' else None
    }
    
    record.apply_converter(converter)
    
    assert record.start_period == '2023M01'
    assert record.observations == (1.5, None, 3.0)


def test_record_apply_converter_missing_keys():
    """Test apply_converter with missing converter keys"""
    record = Record(
        start_period='2023M01',
        observations=[1, 2, 3]
    )
    
    converter = {
        'some_other_field': lambda x: x
    }
    
    record.apply_converter(converter)
    
    # Should not change anything
    assert record.start_period == '2023M01'
    assert record.observations == (1, 2, 3)


def test_record_data_fields():
    """Test that data_fields class attribute is correct"""
    assert Record.data_fields == ('start_period', 'observations')


def test_record_slots():
    """Test that __slots__ is properly defined"""
    expected_slots = ('metadata', 'start_period', 'observations')
    assert Record.__slots__ == expected_slots
