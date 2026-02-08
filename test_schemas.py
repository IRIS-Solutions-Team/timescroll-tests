"""
Unit tests for timescroll.schemas module
"""

import pytest
from collections import namedtuple
from timescroll import Schema, EmptySchema


def test_empty_schema_creation():
    """Test creating an empty schema"""
    schema = Schema()
    assert schema.fields == ()
    assert schema.validate(namedtuple('Empty', [])())


def test_simple_schema_creation():
    """Test creating a simple schema with field names"""
    schema = Schema(country=None, frequency=None)
    assert schema.fields == ('country', 'frequency')


def test_free_form_validation():
    """Test free-form validation (None validator)"""
    schema = Schema(country=None, frequency=None)
    TestMetadata = namedtuple('TestMetadata', ['country', 'frequency'])
    
    # Should accept any values
    metadata = TestMetadata('US', 'monthly')
    assert schema.validate(metadata)
    
    metadata = TestMetadata(123, None)
    assert schema.validate(metadata)


def test_value_validation():
    """Test value validation (exact match)"""
    schema = Schema(country=('value', 'US'))
    TestMetadata = namedtuple('TestMetadata', ['country'])
    
    # Should accept exact match
    metadata = TestMetadata('US')
    assert schema.validate(metadata)
    
    # Should reject different value
    metadata = TestMetadata('UK')
    assert not schema.validate(metadata)


def test_enumeration_validation():
    """Test enumeration validation"""
    schema = Schema(frequency=('enumeration', ['monthly', 'quarterly', 'annual']))
    TestMetadata = namedtuple('TestMetadata', ['frequency'])
    
    # Should accept values in enumeration
    metadata = TestMetadata('monthly')
    assert schema.validate(metadata)
    
    metadata = TestMetadata('annual')
    assert schema.validate(metadata)
    
    # Should reject values not in enumeration
    metadata = TestMetadata('weekly')
    assert not schema.validate(metadata)


def test_test_validation():
    """Test function-based validation"""
    schema = Schema(year=('test', lambda x: isinstance(x, int) and x > 2000))
    TestMetadata = namedtuple('TestMetadata', ['year'])
    
    # Should accept valid values
    metadata = TestMetadata(2023)
    assert schema.validate(metadata)
    
    # Should reject invalid values
    metadata = TestMetadata(1999)
    assert not schema.validate(metadata)
    
    metadata = TestMetadata('2023')
    assert not schema.validate(metadata)


def test_mixed_validation_types():
    """Test schema with multiple validation types"""
    schema = Schema(
        country=('enumeration', ['US', 'UK', 'DE']),
        frequency=('value', 'quarterly'),
        year=('test', lambda x: isinstance(x, int) and 2000 <= x <= 2030),
        notes=None
    )
    TestMetadata = namedtuple('TestMetadata', ['country', 'frequency', 'year', 'notes'])
    
    # Valid metadata
    metadata = TestMetadata('US', 'quarterly', 2023, 'some notes')
    assert schema.validate(metadata)
    
    # Invalid country
    metadata = TestMetadata('FR', 'quarterly', 2023, 'some notes')
    assert not schema.validate(metadata)
    
    # Invalid frequency
    metadata = TestMetadata('US', 'monthly', 2023, 'some notes')
    assert not schema.validate(metadata)
    
    # Invalid year
    metadata = TestMetadata('US', 'quarterly', 1995, 'some notes')
    assert not schema.validate(metadata)


def test_validate_and_raise_success():
    """Test validate_and_raise with valid metadata"""
    schema = Schema(country=('value', 'US'))
    TestMetadata = namedtuple('TestMetadata', ['country'])
    
    metadata = TestMetadata('US')
    # Should not raise any exception
    schema.validate_and_raise(metadata)


def test_validate_and_raise_failure():
    """Test validate_and_raise with invalid metadata"""
    schema = Schema(
        country=('value', 'US'),
        year=('test', lambda x: isinstance(x, int) and x > 2000)
    )
    TestMetadata = namedtuple('TestMetadata', ['country', 'year'])
    
    metadata = TestMetadata('UK', 1999)
    with pytest.raises(ValueError, match="Invalid metadata fields"):
        schema.validate_and_raise(metadata)


def test_iterate_validator_results():
    """Test iterating through validator results"""
    schema = Schema(
        country=('value', 'US'),
        frequency=('enumeration', ['monthly', 'quarterly'])
    )
    TestMetadata = namedtuple('TestMetadata', ['country', 'frequency'])
    
    # All valid
    metadata = TestMetadata('US', 'monthly')
    results = list(schema.iteratate_validator_results(metadata))
    assert results == [True, True]
    
    # Mixed results
    metadata = TestMetadata('UK', 'monthly')
    results = list(schema.iteratate_validator_results(metadata))
    assert results == [False, True]


def test_empty_schema_instance():
    """Test that EmptySchema is properly initialized"""
    assert EmptySchema.fields == ()
    assert EmptySchema.validate(namedtuple('Empty', [])())


def test_validator_with_none_parameter():
    """Test validator creation with None parameter"""
    schema = Schema(field=('enumeration', []))
    assert 'field' in schema._validators


def test_validator_edge_cases():
    """Test validator edge cases"""
    # Test with empty enumeration
    schema = Schema(field=('enumeration', []))
    TestMetadata = namedtuple('TestMetadata', ['field'])
    
    metadata = TestMetadata('anything')
    assert not schema.validate(metadata)
    
    # Test with complex objects
    schema = Schema(obj=('value', {'key': 'value'}))
    TestMetadata = namedtuple('TestMetadata', ['obj'])
    
    metadata = TestMetadata({'key': 'value'})
    assert schema.validate(metadata)
    
    metadata = TestMetadata({'key': 'different'})
    assert not schema.validate(metadata)
