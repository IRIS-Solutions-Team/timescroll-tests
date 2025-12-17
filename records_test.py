"""
Tests for timescroll.records module.
"""

import pytest
from collections import namedtuple, Counter

import sys
sys.path.insert(0, '../timescroll-package/src')

from timescroll.records import (
    build_record_class, 
    meta_fields_from_all_fields,
    _assemble_all_fields,
    _is_all_fields,
    _validate_unique_fields,
    META_DATA_TUPLE_NAME
)


class TestBuildRecordClass:
    """Test the build_record_class function."""

    def test_build_record_class_basic(self):
        """Test basic record class building."""
        meta_fields = ["country", "variable"]
        RecordClass = build_record_class(meta_fields=meta_fields)
        
        assert RecordClass.__name__ == "Record"
        assert RecordClass.meta_fields == meta_fields
        assert RecordClass.all_fields == ("country", "variable", "start_period", "observations")
        assert hasattr(RecordClass, "_meta_data_tuple_factory")

    def test_build_record_class_with_custom_name(self):
        """Test building record class with custom name."""
        meta_fields = ["region"]
        CustomRecord = build_record_class(meta_fields=meta_fields, class_name="CustomRecord")
        
        assert CustomRecord.__name__ == "CustomRecord"

    def test_build_record_class_empty_meta_fields(self):
        """Test building record class with empty meta fields."""
        RecordClass = build_record_class(meta_fields=[])
        
        assert RecordClass.meta_fields == []
        assert RecordClass.all_fields == ("start_period", "observations")

    def test_meta_data_tuple_factory_creation(self):
        """Test that meta data tuple factory is created correctly."""
        meta_fields = ["country", "variable"]
        RecordClass = build_record_class(meta_fields=meta_fields)
        
        factory = RecordClass._meta_data_tuple_factory
        assert factory.__name__ == META_DATA_TUPLE_NAME
        assert factory._fields == ("country", "variable")
        
        meta_data = factory(country="USA", variable="GDP")
        assert meta_data.country == "USA"
        assert meta_data.variable == "GDP"


class TestRecordTemplate:
    """Test the _RecordTemplate functionality through built record classes."""

    def setup_method(self):
        """Set up test fixtures."""
        self.meta_fields = ["country", "variable"]
        self.RecordClass = build_record_class(meta_fields=self.meta_fields)

    def test_record_init_basic(self):
        """Test basic record initialization."""
        record = self.RecordClass()
        
        assert record.meta_data is None
        assert record.start_period is None
        assert record.observations == ()

    def test_record_init_with_data(self):
        """Test record initialization with data."""
        meta_data = self.RecordClass._meta_data_tuple_factory(country="USA", variable="GDP")
        observations = [1.0, 2.0, 3.0]
        
        record = self.RecordClass(
            meta_data=meta_data,
            start_period="2020",
            observations=observations
        )
        
        assert record.meta_data == meta_data
        assert record.start_period == "2020"
        assert record.observations == (1.0, 2.0, 3.0)  # Should be converted to tuple

    def test_record_id_property(self):
        """Test record ID property."""
        # Record with no meta_data
        record1 = self.RecordClass()
        assert record1.id == 0
        
        # Record with meta_data
        meta_data = self.RecordClass._meta_data_tuple_factory(country="USA", variable="GDP")
        record2 = self.RecordClass(meta_data=meta_data)
        assert record2.id == hash(meta_data)

    def test_record_equality(self):
        """Test record equality comparison."""
        meta_data = self.RecordClass._meta_data_tuple_factory(country="USA", variable="GDP")
        
        record1 = self.RecordClass(meta_data=meta_data, start_period="2020", observations=[1, 2])
        record2 = self.RecordClass(meta_data=meta_data, start_period="2020", observations=[1, 2])
        record3 = self.RecordClass(meta_data=meta_data, start_period="2021", observations=[1, 2])
        
        assert record1 == record2
        assert record1 != record3
        assert record1 != "not a record"

    def test_equal_meta_data(self):
        """Test equal_meta_data method."""
        meta_data1 = self.RecordClass._meta_data_tuple_factory(country="USA", variable="GDP")
        meta_data2 = self.RecordClass._meta_data_tuple_factory(country="USA", variable="CPI")
        
        record1 = self.RecordClass(meta_data=meta_data1)
        record2 = self.RecordClass(meta_data=meta_data1)
        record3 = self.RecordClass(meta_data=meta_data2)
        
        assert record1.equal_meta_data(record2)
        assert not record1.equal_meta_data(record3)

    def test_from_fields(self):
        """Test creating record from individual fields."""
        record = self.RecordClass.from_fields(
            country="USA",
            variable="GDP",
            start_period="2020",
            observations=[1, 2, 3]
        )
        
        assert record.meta_data.country == "USA"
        assert record.meta_data.variable == "GDP"
        assert record.start_period == "2020"
        assert record.observations == (1, 2, 3)

    def test_from_tuple(self):
        """Test creating record from tuple."""
        tuple_data = ("USA", "GDP", "2020", "100", "101", "102")
        record = self.RecordClass.from_tuple(tuple_data)
        
        assert record.meta_data.country == "USA"
        assert record.meta_data.variable == "GDP"
        assert record.start_period == "2020"
        assert record.observations == ("100", "101", "102")

    def test_from_dict(self):
        """Test creating record from dictionary."""
        data_dict = {
            "country": "USA",
            "variable": "GDP",
            "start_period": "2020",
            "observations": [100, 101, 102]
        }
        record = self.RecordClass.from_dict(data_dict)
        
        assert record.meta_data.country == "USA"
        assert record.meta_data.variable == "GDP"
        assert record.start_period == "2020"
        assert record.observations == (100, 101, 102)

    def test_to_tuple(self):
        """Test converting record to tuple."""
        record = self.RecordClass.from_fields(
            country="USA",
            variable="GDP",
            start_period="2020",
            observations=[100, 101]
        )
        
        expected_tuple = ("USA", "GDP", "2020", 100, 101)
        assert record.to_tuple() == expected_tuple

    def test_to_dict(self):
        """Test converting record to dictionary."""
        record = self.RecordClass.from_fields(
            country="USA",
            variable="GDP",
            start_period="2020",
            observations=[100, 101]
        )
        
        expected_dict = {
            "country": "USA",
            "variable": "GDP",
            "start_period": "2020",
            "observations": (100, 101)
        }
        assert record.to_dict() == expected_dict

    def test_copy(self):
        """Test copying a record."""
        original = self.RecordClass.from_fields(
            country="USA",
            variable="GDP",
            start_period="2020",
            observations=[100, 101]
        )
        
        copy = original.copy()
        
        assert copy == original
        assert copy is not original
        assert copy.meta_data == original.meta_data
        assert copy.observations == original.observations

    def test_convert_fields_no_converters(self):
        """Test field conversion with no converters."""
        record = self.RecordClass.from_fields(
            country="USA",
            variable="GDP",
            start_period="2020",
            observations=["100", "101"]
        )
        
        original_data = record.to_dict()
        record.convert_fields(None)
        
        assert record.to_dict() == original_data

    def test_convert_fields_with_converters(self):
        """Test field conversion with converters."""
        record = self.RecordClass.from_fields(
            country="usa",
            variable="gdp",
            start_period="2020",
            observations=["100", "101"]
        )
        
        converters = {
            "country": str.upper,
            "variable": str.upper,
            "observations": lambda obs: tuple(float(x) for x in obs)
        }
        
        record.convert_fields(converters)
        
        assert record.meta_data.country == "USA"
        assert record.meta_data.variable == "GDP"
        assert record.observations == (100.0, 101.0)

    def test_by_converting_fields(self):
        """Test creating new record by converting fields."""
        original = self.RecordClass.from_fields(
            country="usa",
            variable="gdp",
            start_period="2020",
            observations=["100", "101"]
        )
        
        converters = {
            "country": str.upper,
            "observations": lambda obs: tuple(float(x) for x in obs)
        }
        
        converted = self.RecordClass.by_converting_fields(original, converters)
        
        # Original should be unchanged
        assert original.meta_data.country == "usa"
        assert original.observations == ("100", "101")
        
        # Converted should have new values
        assert converted.meta_data.country == "USA"
        assert converted.observations == (100.0, 101.0)


class TestUtilityFunctions:
    """Test utility functions in records module."""

    def test_assemble_all_fields(self):
        """Test _assemble_all_fields function."""
        meta_fields = ["country", "variable"]
        all_fields = _assemble_all_fields(meta_fields)
        
        expected = ("country", "variable", "start_period", "observations")
        assert all_fields == expected

    def test_assemble_all_fields_empty_meta(self):
        """Test _assemble_all_fields with empty meta fields."""
        all_fields = _assemble_all_fields([])
        expected = ("start_period", "observations")
        assert all_fields == expected

    def test_is_all_fields_valid(self):
        """Test _is_all_fields with valid all_fields."""
        valid_fields = ["country", "variable", "start_period", "observations"]
        assert _is_all_fields(valid_fields)

    def test_is_all_fields_invalid(self):
        """Test _is_all_fields with invalid all_fields."""
        # Wrong last fields
        invalid1 = ["country", "start_period", "wrong"]
        assert not _is_all_fields(invalid1)
        
        # Too short
        invalid2 = ["start_period"]
        assert not _is_all_fields(invalid2)
        
        # Wrong order
        invalid3 = ["country", "observations", "start_period"]
        assert not _is_all_fields(invalid3)

    def test_meta_fields_from_all_fields_valid(self):
        """Test meta_fields_from_all_fields with valid input."""
        all_fields = ["country", "variable", "start_period", "observations"]
        meta_fields = meta_fields_from_all_fields(all_fields)
        
        expected = ("country", "variable")
        assert meta_fields == expected

    def test_meta_fields_from_all_fields_minimal(self):
        """Test meta_fields_from_all_fields with minimal valid input."""
        all_fields = ["start_period", "observations"]
        meta_fields = meta_fields_from_all_fields(all_fields)
        
        expected = ()
        assert meta_fields == expected

    def test_meta_fields_from_all_fields_invalid(self):
        """Test meta_fields_from_all_fields with invalid input."""
        invalid_fields = ["country", "wrong_field", "observations"]
        
        with pytest.raises(ValueError, match="last two fields.*must be"):
            meta_fields_from_all_fields(invalid_fields)

    def test_validate_unique_fields_valid(self):
        """Test _validate_unique_fields with unique fields."""
        fields = ("country", "variable", "start_period", "observations")
        result = _validate_unique_fields(fields)
        assert result == fields

    def test_validate_unique_fields_invalid(self):
        """Test _validate_unique_fields with duplicate fields."""
        fields = ("country", "variable", "country", "observations")
        
        with pytest.raises(ValueError, match="Non-unique field names"):
            _validate_unique_fields(fields)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_record_class_with_single_meta_field(self):
        """Test record class with single meta field."""
        RecordClass = build_record_class(meta_fields=["country"])
        
        record = RecordClass.from_fields(
            country="USA",
            start_period="2020",
            observations=[1, 2, 3]
        )
        
        assert record.meta_data.country == "USA"
        assert len(record.meta_data) == 1

    def test_record_with_complex_observations(self):
        """Test record with complex observation data."""
        RecordClass = build_record_class(meta_fields=["series"])
        
        complex_obs = [1.5, None, "text", {"key": "value"}, [1, 2, 3]]
        record = RecordClass.from_fields(
            series="complex",
            start_period="2020",
            observations=complex_obs
        )
        
        assert record.observations == tuple(complex_obs)

    def test_from_tuple_with_extra_data(self):
        """Test from_tuple with more data than expected."""
        RecordClass = build_record_class(meta_fields=["country"])
        
        tuple_data = ("USA", "2020", "100", "101", "102", "extra", "data")
        record = RecordClass.from_tuple(tuple_data)
        
        assert record.meta_data.country == "USA"
        assert record.start_period == "2020"
        assert record.observations == ("100", "101", "102", "extra", "data")

    def test_from_tuple_insufficient_data(self):
        """Test from_tuple with insufficient data."""
        RecordClass = build_record_class(meta_fields=["country", "variable"])
        
        # This should work but create empty observations
        tuple_data = ("USA", "GDP", "2020")
        record = RecordClass.from_tuple(tuple_data)
        
        assert record.meta_data.country == "USA"
        assert record.meta_data.variable == "GDP"
        assert record.start_period == "2020"
        assert record.observations == ()