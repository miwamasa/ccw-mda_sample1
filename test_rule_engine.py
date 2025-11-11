"""
Test suite for the generic rule-based transformation engine.

Tests the rule engine's ability to read declarative rules and apply
transformations in a model-agnostic manner.
"""

import unittest
import json
import os
from rule_engine import RuleEngine


class TestRuleEngine(unittest.TestCase):
    """Test the rule engine with manufacturing to GHG transformation rules."""

    def setUp(self):
        """Set up test fixtures."""
        self.rules_file = "transformation_rules.yaml"
        self.engine = RuleEngine(self.rules_file)
        self.test_data_dir = "test_data/source"

    def test_engine_initialization(self):
        """Test that the engine loads rules correctly."""
        self.assertIsNotNone(self.engine.rules)
        self.assertIn('metadata', self.engine.rules)
        self.assertIn('constants', self.engine.rules)
        self.assertIn('transformation_steps', self.engine.rules)

    def test_metadata_loaded(self):
        """Test that metadata is loaded correctly."""
        metadata = self.engine.metadata
        self.assertEqual(metadata.get('name'), "Manufacturing to GHG Emission Report Transformation")
        self.assertEqual(metadata.get('version'), "1.0")

    def test_constants_loaded(self):
        """Test that constants are loaded correctly."""
        constants = self.engine.constants
        self.assertIn('emission_factors', constants)
        self.assertIn('scope_classification', constants)

        # Check emission factors
        emission_factors = constants['emission_factors']
        self.assertEqual(emission_factors['electricity'], 0.500)
        self.assertEqual(emission_factors['natural_gas'], 2.03)

        # Check scope classification
        scope_classification = constants['scope_classification']
        self.assertIn('electricity', scope_classification['scope2'])
        self.assertIn('natural_gas', scope_classification['scope1'])

    def test_get_nested_value(self):
        """Test nested value extraction."""
        data = {
            "organization": {
                "name": "Test Company"
            },
            "activities": [
                {"id": "A001"}
            ]
        }

        self.assertEqual(
            self.engine._get_nested_value(data, "organization.name"),
            "Test Company"
        )
        self.assertEqual(
            self.engine._get_nested_value(data, "activities"),
            [{"id": "A001"}]
        )
        self.assertIsNone(
            self.engine._get_nested_value(data, "nonexistent.path")
        )

    def test_get_constant_value(self):
        """Test constant value retrieval."""
        # Test with constants. prefix
        value = self.engine._get_constant_value("constants.emission_factors", "electricity")
        self.assertEqual(value, 0.500)

        # Test without constants. prefix
        value = self.engine._get_constant_value("emission_factors", "diesel")
        self.assertEqual(value, 2.68)

        # Test getting entire dictionary
        factors = self.engine._get_constant_value("emission_factors")
        self.assertIsInstance(factors, dict)
        self.assertIn('electricity', factors)

    def test_apply_transform(self):
        """Test value transformations."""
        # Lowercase underscore
        self.assertEqual(
            self.engine._apply_transform("Natural Gas", "lowercase_underscore"),
            "natural_gas"
        )
        self.assertEqual(
            self.engine._apply_transform("ELECTRICITY", "lowercase_underscore"),
            "electricity"
        )

        # Uppercase
        self.assertEqual(
            self.engine._apply_transform("test", "uppercase"),
            "TEST"
        )

        # Lowercase
        self.assertEqual(
            self.engine._apply_transform("TEST", "lowercase"),
            "test"
        )

    def test_simple_transformation(self):
        """Test basic transformation with minimal data."""
        source_data = {
            "organization": {"name": "Test Org"},
            "manufacturing_activities": [
                {
                    "activity_id": "A001",
                    "activity_name": "Test Activity",
                    "facility": "Test Facility",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "energy_consumptions": [
                        {
                            "energy_type": {"name": "electricity"},
                            "amount": 1000,
                            "unit": "kWh"
                        }
                    ]
                }
            ]
        }

        result = self.engine.transform(source_data)

        # Verify structure
        self.assertEqual(result["@type"], "ghg:EmissionReport")
        self.assertIn("emissions", result)
        self.assertIn("total_emissions", result)

        # Verify organization
        self.assertEqual(
            result["reporting_organization"]["organization_name"],
            "Test Org"
        )

        # Verify emissions calculation
        # 1000 kWh * 0.5 = 500 kg-CO2
        self.assertEqual(result["total_emissions"], 500.0)

    def load_sample(self, filename):
        """Load a sample JSON file."""
        filepath = os.path.join(self.test_data_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_sample1_transformation(self):
        """Test transformation of sample1_small_factory.json."""
        if not os.path.exists(os.path.join(self.test_data_dir, "sample1_small_factory.json")):
            self.skipTest("Sample file not found")

        source_data = self.load_sample("sample1_small_factory.json")
        result = self.engine.transform(source_data)

        # Verify totals
        self.assertAlmostEqual(result["total_scope1"], 1725.5, places=1)
        self.assertAlmostEqual(result["total_scope2"], 10450.0, places=1)
        self.assertAlmostEqual(result["total_emissions"], 12175.5, places=1)

        # Verify organization
        self.assertEqual(
            result["reporting_organization"]["organization_name"],
            "Acme Manufacturing Ltd"
        )

        # Verify reporting period
        self.assertEqual(result["reporting_period"], "2024-01")

    def test_sample2_transformation(self):
        """Test transformation of sample2_multi_fuel.json."""
        if not os.path.exists(os.path.join(self.test_data_dir, "sample2_multi_fuel.json")):
            self.skipTest("Sample file not found")

        source_data = self.load_sample("sample2_multi_fuel.json")
        result = self.engine.transform(source_data)

        # Verify totals
        self.assertAlmostEqual(result["total_scope1"], 450055.0, places=0)
        self.assertAlmostEqual(result["total_scope2"], 22500.0, places=0)
        self.assertAlmostEqual(result["total_emissions"], 472555.0, places=0)

        # Verify emissions count (should have 4 emissions: coal, electricity, natural gas, diesel)
        self.assertEqual(len(result["emissions"]), 4)

    def test_sample3_transformation(self):
        """Test transformation of sample3_electronics.json."""
        if not os.path.exists(os.path.join(self.test_data_dir, "sample3_electronics.json")):
            self.skipTest("Sample file not found")

        source_data = self.load_sample("sample3_electronics.json")
        result = self.engine.transform(source_data)

        # Verify totals
        self.assertAlmostEqual(result["total_scope1"], 1812.0, places=0)
        self.assertAlmostEqual(result["total_scope2"], 17400.0, places=0)
        self.assertAlmostEqual(result["total_emissions"], 19212.0, places=0)

        # Verify organization
        self.assertEqual(
            result["reporting_organization"]["organization_name"],
            "TechElectronics Japan"
        )

    def test_scope_classification(self):
        """Test that energy types are correctly classified into scopes."""
        source_data = {
            "organization": {"name": "Test"},
            "manufacturing_activities": [
                {
                    "activity_id": "A001",
                    "activity_name": "Test",
                    "facility": "Plant",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "energy_consumptions": [
                        {
                            "energy_type": {"name": "electricity"},
                            "amount": 100,
                            "unit": "kWh"
                        },
                        {
                            "energy_type": {"name": "natural_gas"},
                            "amount": 100,
                            "unit": "m³"
                        },
                        {
                            "energy_type": {"name": "diesel"},
                            "amount": 100,
                            "unit": "liters"
                        }
                    ]
                }
            ]
        }

        result = self.engine.transform(source_data)

        # Check scope classification
        scope1_emissions = [e for e in result["emissions"] if e["@type"] == "ghg:Scope1Emission"]
        scope2_emissions = [e for e in result["emissions"] if e["@type"] == "ghg:Scope2Emission"]

        self.assertEqual(len(scope1_emissions), 2)  # natural_gas and diesel
        self.assertEqual(len(scope2_emissions), 1)  # electricity

    def test_emission_calculations(self):
        """Test that emission calculations are correct."""
        source_data = {
            "organization": {"name": "Test"},
            "manufacturing_activities": [
                {
                    "activity_id": "A001",
                    "activity_name": "Test",
                    "facility": "Plant",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "energy_consumptions": [
                        {
                            "energy_type": {"name": "electricity"},
                            "amount": 2000,
                            "unit": "kWh"
                        },
                        {
                            "energy_type": {"name": "natural_gas"},
                            "amount": 500,
                            "unit": "m³"
                        }
                    ]
                }
            ]
        }

        result = self.engine.transform(source_data)

        # Find specific emissions
        electricity_emission = next(
            e for e in result["emissions"]
            if e["source_category"] == "electricity"
        )
        gas_emission = next(
            e for e in result["emissions"]
            if e["source_category"] == "natural_gas"
        )

        # Verify calculations
        # Electricity: 2000 * 0.5 = 1000
        self.assertEqual(electricity_emission["co2_amount"], 1000.0)
        self.assertEqual(electricity_emission["emission_factor"], 0.5)

        # Natural gas: 500 * 2.03 = 1015
        self.assertEqual(gas_emission["co2_amount"], 1015.0)
        self.assertEqual(gas_emission["emission_factor"], 2.03)

    def test_empty_activities(self):
        """Test handling of empty activities."""
        source_data = {
            "organization": {"name": "Empty Org"},
            "manufacturing_activities": []
        }

        result = self.engine.transform(source_data)

        self.assertEqual(result["total_emissions"], 0.0)
        self.assertEqual(len(result["emissions"]), 0)

    def test_activity_without_energy(self):
        """Test activity with no energy consumption."""
        source_data = {
            "organization": {"name": "Test"},
            "manufacturing_activities": [
                {
                    "activity_id": "A001",
                    "activity_name": "Manual Work",
                    "facility": "Plant",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "energy_consumptions": []
                }
            ]
        }

        result = self.engine.transform(source_data)

        self.assertEqual(result["total_emissions"], 0.0)
        self.assertEqual(len(result["emissions"]), 0)

    def test_case_insensitive_energy_types(self):
        """Test that energy type names are case-insensitive."""
        source_data = {
            "organization": {"name": "Test"},
            "manufacturing_activities": [
                {
                    "activity_id": "A001",
                    "activity_name": "Test",
                    "facility": "Plant",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "energy_consumptions": [
                        {
                            "energy_type": {"name": "ELECTRICITY"},
                            "amount": 100,
                            "unit": "kWh"
                        },
                        {
                            "energy_type": {"name": "Natural Gas"},
                            "amount": 100,
                            "unit": "m³"
                        }
                    ]
                }
            ]
        }

        result = self.engine.transform(source_data)

        # Should have 2 emissions
        self.assertEqual(len(result["emissions"]), 2)

        # Both should have proper emission factors
        for emission in result["emissions"]:
            self.assertGreater(emission["emission_factor"], 0)
            self.assertGreater(emission["co2_amount"], 0)

    def test_report_metadata(self):
        """Test report metadata generation."""
        source_data = {
            "organization": {"name": "Global Industries Corp"},
            "manufacturing_activities": [
                {
                    "activity_id": "A001",
                    "activity_name": "Test",
                    "facility": "Plant",
                    "start_date": "2024-02-15",
                    "end_date": "2024-02-28",
                    "energy_consumptions": []
                }
            ]
        }

        result = self.engine.transform(source_data)

        # Check report ID
        self.assertIn("GHG-", result["report_id"])
        self.assertIn("2024-02", result["report_id"])

        # Check reporting period
        self.assertEqual(result["reporting_period"], "2024-02")

        # Check report date format
        self.assertRegex(result["report_date"], r'\d{4}-\d{2}-\d{2}')


def run_all_tests():
    """Run all tests and generate a report."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestRuleEngine)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    return result


if __name__ == "__main__":
    run_all_tests()
