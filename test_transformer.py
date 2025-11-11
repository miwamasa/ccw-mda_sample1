"""
Comprehensive test suite for Manufacturing to GHG transformation.

This module tests the rule-based data transformation from manufacturing
ontology to GHG emission report ontology.
"""

import unittest
import json
import os
from decimal import Decimal
from transformer import ManufacturingToGHGTransformer, EmissionFactors


class TestEmissionFactors(unittest.TestCase):
    """Test emission factor calculations and scope classification."""

    def test_get_factor_electricity(self):
        """Test emission factor for electricity."""
        factor = EmissionFactors.get_factor("electricity")
        self.assertEqual(factor, 0.500)

    def test_get_factor_natural_gas(self):
        """Test emission factor for natural gas."""
        factor = EmissionFactors.get_factor("natural_gas")
        self.assertEqual(factor, 2.03)

    def test_get_factor_case_insensitive(self):
        """Test that energy type names are case insensitive."""
        factor1 = EmissionFactors.get_factor("ELECTRICITY")
        factor2 = EmissionFactors.get_factor("Electricity")
        self.assertEqual(factor1, factor2)

    def test_get_factor_with_spaces(self):
        """Test energy type with spaces."""
        factor = EmissionFactors.get_factor("Natural Gas")
        self.assertEqual(factor, 2.03)

    def test_get_factor_unknown(self):
        """Test unknown energy type returns 0."""
        factor = EmissionFactors.get_factor("unknown_fuel")
        self.assertEqual(factor, 0.0)

    def test_scope_electricity(self):
        """Test that electricity is Scope 2."""
        scope = EmissionFactors.get_scope("electricity")
        self.assertEqual(scope, 2)

    def test_scope_natural_gas(self):
        """Test that natural gas is Scope 1."""
        scope = EmissionFactors.get_scope("natural_gas")
        self.assertEqual(scope, 1)

    def test_scope_diesel(self):
        """Test that diesel is Scope 1."""
        scope = EmissionFactors.get_scope("diesel")
        self.assertEqual(scope, 1)


class TestTransformer(unittest.TestCase):
    """Test the main transformation logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.transformer = ManufacturingToGHGTransformer()

    def test_simple_transformation(self):
        """Test basic transformation with single activity."""
        source_data = {
            "organization": {"name": "Test Company"},
            "manufacturing_activities": [
                {
                    "activity_id": "A001",
                    "activity_name": "Production",
                    "facility": "Plant 1",
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

        result = self.transformer.transform(source_data)

        # Verify basic structure
        self.assertIn("@type", result)
        self.assertEqual(result["@type"], "ghg:EmissionReport")
        self.assertIn("report_id", result)
        self.assertIn("emissions", result)
        self.assertIn("total_emissions", result)

    def test_emission_calculation(self):
        """Test CO2 emission calculation."""
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
                            "amount": 2000,
                            "unit": "kWh"
                        }
                    ]
                }
            ]
        }

        result = self.transformer.transform(source_data)

        # Expected: 2000 kWh * 0.5 kg-CO2/kWh = 1000 kg-CO2
        self.assertEqual(result["total_scope2"], 1000.0)
        self.assertEqual(result["total_scope1"], 0.0)
        self.assertEqual(result["total_emissions"], 1000.0)

    def test_multi_energy_type(self):
        """Test transformation with multiple energy types."""
        source_data = {
            "organization": {"name": "Multi Energy Co"},
            "manufacturing_activities": [
                {
                    "activity_id": "A001",
                    "activity_name": "Production",
                    "facility": "Plant",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "energy_consumptions": [
                        {
                            "energy_type": {"name": "electricity"},
                            "amount": 1000,
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

        result = self.transformer.transform(source_data)

        # Expected Scope 1: 500 * 2.03 = 1015 kg-CO2
        # Expected Scope 2: 1000 * 0.5 = 500 kg-CO2
        self.assertEqual(result["total_scope1"], 1015.0)
        self.assertEqual(result["total_scope2"], 500.0)
        self.assertEqual(result["total_emissions"], 1515.0)

    def test_scope_classification(self):
        """Test that emissions are properly classified into scopes."""
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
                            "energy_type": {"name": "diesel"},
                            "amount": 100,
                            "unit": "liters"
                        }
                    ]
                }
            ]
        }

        result = self.transformer.transform(source_data)

        # Check that emissions are classified
        scope1_emissions = [e for e in result["emissions"] if e["@type"] == "ghg:Scope1Emission"]
        scope2_emissions = [e for e in result["emissions"] if e["@type"] == "ghg:Scope2Emission"]

        self.assertEqual(len(scope1_emissions), 1)
        self.assertEqual(len(scope2_emissions), 1)

    def test_organization_mapping(self):
        """Test that organization information is correctly mapped."""
        source_data = {
            "organization": {"name": "Acme Corporation"},
            "manufacturing_activities": []
        }

        result = self.transformer.transform(source_data)

        self.assertIn("reporting_organization", result)
        self.assertEqual(
            result["reporting_organization"]["organization_name"],
            "Acme Corporation"
        )

    def test_report_id_generation(self):
        """Test report ID generation."""
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

        result = self.transformer.transform(source_data)

        # Report ID should include organization abbreviation and period
        self.assertIn("GHG-", result["report_id"])
        self.assertIn("2024-02", result["report_id"])

    def test_empty_activities(self):
        """Test transformation with no activities."""
        source_data = {
            "organization": {"name": "Empty Org"},
            "manufacturing_activities": []
        }

        result = self.transformer.transform(source_data)

        self.assertEqual(result["total_emissions"], 0.0)
        self.assertEqual(len(result["emissions"]), 0)


class TestIntegrationWithSampleData(unittest.TestCase):
    """Integration tests using sample data files."""

    def setUp(self):
        """Set up test fixtures."""
        self.transformer = ManufacturingToGHGTransformer()
        self.test_data_dir = "test_data/source"

    def load_sample(self, filename):
        """Load a sample JSON file."""
        filepath = os.path.join(self.test_data_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_sample1_small_factory(self):
        """Test transformation of sample1_small_factory.json."""
        if not os.path.exists(os.path.join(self.test_data_dir, "sample1_small_factory.json")):
            self.skipTest("Sample file not found")

        source_data = self.load_sample("sample1_small_factory.json")
        result = self.transformer.transform(source_data)

        # Verify structure
        self.assertIn("@type", result)
        self.assertEqual(result["@type"], "ghg:EmissionReport")

        # Verify organization
        self.assertEqual(
            result["reporting_organization"]["organization_name"],
            "Acme Manufacturing Ltd"
        )

        # Verify emissions are calculated
        self.assertGreater(result["total_emissions"], 0)

        # Activity 1: 12500 kWh electricity = 6250 kg-CO2 (Scope 2)
        #           + 850 m³ natural gas = 1725.5 kg-CO2 (Scope 1)
        # Activity 2: 8400 kWh electricity = 4200 kg-CO2 (Scope 2)
        # Total Scope 1: 1725.5
        # Total Scope 2: 10450
        # Total: 12175.5
        self.assertAlmostEqual(result["total_scope1"], 1725.5, places=1)
        self.assertAlmostEqual(result["total_scope2"], 10450.0, places=1)
        self.assertAlmostEqual(result["total_emissions"], 12175.5, places=1)

    def test_sample2_multi_fuel(self):
        """Test transformation of sample2_multi_fuel.json."""
        if not os.path.exists(os.path.join(self.test_data_dir, "sample2_multi_fuel.json")):
            self.skipTest("Sample file not found")

        source_data = self.load_sample("sample2_multi_fuel.json")
        result = self.transformer.transform(source_data)

        # Verify organization
        self.assertEqual(
            result["reporting_organization"]["organization_name"],
            "Global Industries Corp"
        )

        # Should have multiple emission types
        self.assertGreater(len(result["emissions"]), 2)

        # Verify both scopes are present
        self.assertGreater(result["total_scope1"], 0)
        self.assertGreater(result["total_scope2"], 0)

        # Coal: 180000 kg * 2.42 = 435600 kg-CO2
        # Electricity: 45000 kWh * 0.5 = 22500 kg-CO2
        # Natural gas: 2500 m³ * 2.03 = 5075 kg-CO2
        # Diesel: 3500 liters * 2.68 = 9380 kg-CO2
        # Total Scope 1: 435600 + 5075 + 9380 = 450055
        # Total Scope 2: 22500
        self.assertAlmostEqual(result["total_scope1"], 450055.0, places=0)
        self.assertAlmostEqual(result["total_scope2"], 22500.0, places=0)

    def test_sample3_electronics(self):
        """Test transformation of sample3_electronics.json."""
        if not os.path.exists(os.path.join(self.test_data_dir, "sample3_electronics.json")):
            self.skipTest("Sample file not found")

        source_data = self.load_sample("sample3_electronics.json")
        result = self.transformer.transform(source_data)

        # Verify organization
        self.assertEqual(
            result["reporting_organization"]["organization_name"],
            "TechElectronics Japan"
        )

        # Verify reporting period
        self.assertEqual(result["reporting_period"], "2024-03")

        # Electricity: (28000 + 6800) kWh * 0.5 = 17400 kg-CO2 (Scope 2)
        # LPG: 1200 kg * 1.51 = 1812 kg-CO2 (Scope 1)
        self.assertAlmostEqual(result["total_scope1"], 1812.0, places=0)
        self.assertAlmostEqual(result["total_scope2"], 17400.0, places=0)
        self.assertAlmostEqual(result["total_emissions"], 19212.0, places=0)


class TestDataValidation(unittest.TestCase):
    """Test data validation and edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.transformer = ManufacturingToGHGTransformer()

    def test_missing_organization(self):
        """Test handling of missing organization data."""
        source_data = {
            "manufacturing_activities": []
        }

        result = self.transformer.transform(source_data)

        self.assertEqual(
            result["reporting_organization"]["organization_name"],
            "Unknown Organization"
        )

    def test_activity_without_energy_consumption(self):
        """Test activity with no energy consumption."""
        source_data = {
            "organization": {"name": "Test"},
            "manufacturing_activities": [
                {
                    "activity_id": "A001",
                    "activity_name": "Manual Assembly",
                    "facility": "Plant",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "energy_consumptions": []
                }
            ]
        }

        result = self.transformer.transform(source_data)

        self.assertEqual(result["total_emissions"], 0.0)
        self.assertEqual(len(result["emissions"]), 0)

    def test_zero_amount_consumption(self):
        """Test handling of zero energy consumption."""
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
                            "amount": 0,
                            "unit": "kWh"
                        }
                    ]
                }
            ]
        }

        result = self.transformer.transform(source_data)

        self.assertEqual(result["total_emissions"], 0.0)


def run_all_tests():
    """Run all tests and generate a report."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestEmissionFactors))
    suite.addTests(loader.loadTestsFromTestCase(TestTransformer))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationWithSampleData))
    suite.addTests(loader.loadTestsFromTestCase(TestDataValidation))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
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
