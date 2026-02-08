"""
Unit tests for timescroll.metadata module
"""

import pytest
from collections import namedtuple
from timescroll.metadata import build_metadata_class, EmptyMetadata
from timescroll import Schema, EmptySchema


def test_build_metadata_class_empty():
    """Test building metadata class with empty schema"""
    metadata_class = build_metadata_class(EmptySchema)
    assert metadata_class.__name__ == "Metadata"
    assert metadata_class._fields == ()
    
    # Should be able to instantiate
    instance = metadata_class()
    assert isinstance(instance, tuple)
    assert len(instance) == 0


def test_build_metadata_class_with_fields():
    """Test building metadata class with fields"""
    schema = Schema(country=None, frequency=None)
    metadata_class = build_metadata_class(schema)
    
    assert metadata_class.__name__ == "Metadata"
    assert metadata_class._fields == ('country', 'frequency')
    
    # Should be able to instantiate with values
    instance = metadata_class('US', 'monthly')
    assert instance.country == 'US'
    assert instance.frequency == 'monthly'


def test_build_metadata_class_with_complex_schema():
    """Test building metadata class with complex schema"""
    schema = Schema(
        country=('enumeration', ['US', 'UK']),
        frequency=('value', 'quarterly'),
        year=('test', lambda x: isinstance(x, int))
    )
    metadata_class = build_metadata_class(schema)
    
    assert metadata_class.__name__ == "Metadata"
    assert metadata_class._fields == ('country', 'frequency', 'year')
    
    # Should create namedtuple instances
    instance = metadata_class('US', 'quarterly', 2023)
    assert instance.country == 'US'
    assert instance.frequency == 'quarterly'
    assert instance.year == 2023
    
    # Should support namedtuple methods
    assert instance._asdict() == {
        'country': 'US', 
        'frequency': 'quarterly', 
        'year': 2023
    }


def test_empty_metadata_instance():
    """Test EmptyMetadata instance"""
    assert EmptyMetadata.__name__ == "Metadata"
    assert EmptyMetadata._fields == ()
    
    # Should be able to create instances
    instance = EmptyMetadata()
    assert isinstance(instance, tuple)
    assert len(instance) == 0


def test_metadata_class_equality():
    """Test equality of metadata class instances"""
    schema = Schema(country=None, year=None)
    metadata_class = build_metadata_class(schema)
    
    instance1 = metadata_class('US', 2023)
    instance2 = metadata_class('US', 2023)
    instance3 = metadata_class('UK', 2023)
    
    assert instance1 == instance2
    assert instance1 != instance3
    assert hash(instance1) == hash(instance2)
    assert hash(instance1) != hash(instance3)


def test_metadata_class_immutability():
    """Test that metadata instances are immutable (namedtuple behavior)"""
    schema = Schema(country=None, frequency=None)
    metadata_class = build_metadata_class(schema)
    
    instance = metadata_class('US', 'monthly')
    
    # Should not be able to modify fields
    with pytest.raises(AttributeError):
        instance.country = 'UK'


def test_multiple_metadata_classes():
    """Test creating multiple different metadata classes"""
    schema1 = Schema(country=None)
    schema2 = Schema(frequency=None, year=None)
    
    metadata_class1 = build_metadata_class(schema1)
    metadata_class2 = build_metadata_class(schema2)
    
    # Both should have same name but different fields
    assert metadata_class1.__name__ == "Metadata"
    assert metadata_class2.__name__ == "Metadata"
    assert metadata_class1._fields == ('country',)
    assert metadata_class2._fields == ('frequency', 'year')
    
    # Should be able to create distinct instances
    instance1 = metadata_class1('US')
    instance2 = metadata_class2('quarterly', 2023)
    
    assert instance1.country == 'US'
    assert instance2.frequency == 'quarterly'
    assert instance2.year == 2023


def test_metadata_class_string_representation():
    """Test string representation of metadata instances"""
    schema = Schema(country=None, frequency=None)
    metadata_class = build_metadata_class(schema)
    
    instance = metadata_class('US', 'monthly')
    
    # Should have proper string representation
    assert str(instance) == "Metadata(country='US', frequency='monthly')"
    assert repr(instance) == "Metadata(country='US', frequency='monthly')"