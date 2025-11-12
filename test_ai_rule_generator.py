"""
Tests for AI-powered rule generator.

Note: These tests require ANTHROPIC_API_KEY to be set.
Run with: ANTHROPIC_API_KEY=your-key python -m pytest test_ai_rule_generator.py
"""

import unittest
import os
import json
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
from ai_rule_generator import AIRuleGenerator


class TestAIRuleGenerator(unittest.TestCase):
    """Test suite for AI-powered rule generator."""

    def setUp(self):
        """Set up test fixtures."""
        self.source_ontology = "model_examples/vehicle_fleet/vehicle-fleet-ontology.ttl"
        self.target_ontology = "model_examples/vehicle_fleet/fleet-emissions-ontology.ttl"

        # Mock API key for tests
        self.mock_api_key = "test-api-key-12345"

    def test_initialization(self):
        """Test AIRuleGenerator initialization."""
        generator = AIRuleGenerator(
            self.source_ontology,
            self.target_ontology,
            api_key=self.mock_api_key
        )

        self.assertIsNotNone(generator.source_analyzer)
        self.assertIsNotNone(generator.target_analyzer)
        self.assertIsNotNone(generator.client)

    def test_initialization_without_api_key(self):
        """Test that initialization fails without API key."""
        # Clear environment variable
        old_key = os.environ.get('ANTHROPIC_API_KEY')
        if old_key:
            del os.environ['ANTHROPIC_API_KEY']

        try:
            with self.assertRaises(ValueError) as context:
                AIRuleGenerator(self.source_ontology, self.target_ontology)

            self.assertIn("ANTHROPIC_API_KEY", str(context.exception))
        finally:
            # Restore environment variable
            if old_key:
                os.environ['ANTHROPIC_API_KEY'] = old_key

    def test_extract_ontology_structure(self):
        """Test ontology structure extraction."""
        generator = AIRuleGenerator(
            self.source_ontology,
            self.target_ontology,
            api_key=self.mock_api_key
        )

        source_structure = generator._extract_ontology_structure(
            generator.source_analyzer,
            "Source"
        )

        # Verify structure has expected keys
        self.assertIn("classes", source_structure)
        self.assertIn("namespace", source_structure)
        self.assertIn("ontology_name", source_structure)

        # Verify we found some classes
        self.assertGreater(len(source_structure["classes"]), 0)

        # Check for expected vehicle fleet classes
        class_names = [cls["name"] for cls in source_structure["classes"]]
        self.assertTrue(
            any("Vehicle" in name for name in class_names),
            f"Expected Vehicle class in {class_names}"
        )

        # Verify classes have properties
        for cls in source_structure["classes"]:
            self.assertIn("properties", cls)
            self.assertIsInstance(cls["properties"], list)

    def test_create_analysis_prompt(self):
        """Test AI analysis prompt creation."""
        generator = AIRuleGenerator(
            self.source_ontology,
            self.target_ontology,
            api_key=self.mock_api_key
        )

        source_structure = generator._extract_ontology_structure(
            generator.source_analyzer,
            "Source"
        )
        target_structure = generator._extract_ontology_structure(
            generator.target_analyzer,
            "Target"
        )

        prompt = generator._create_analysis_prompt(source_structure, target_structure)

        # Verify prompt contains key instructions
        self.assertTrue(
            "ontology" in prompt.lower() and ("transformation" in prompt.lower() or "mapping" in prompt.lower()),
            "Prompt should mention ontology transformation or mapping"
        )
        self.assertIn("class_mappings", prompt)
        self.assertIn("property_mappings", prompt)
        self.assertIn("calculations", prompt)
        self.assertIn("aggregations", prompt)
        self.assertTrue("JSON" in prompt or "json" in prompt.lower())

    @patch('anthropic.Anthropic')
    def test_analyze_with_ai_mock(self, mock_anthropic):
        """Test AI analysis with mocked API response."""
        # Create mock AI response
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps({
            "class_mappings": [
                {
                    "source_class": "Vehicle",
                    "target_class": "VehicleEmission",
                    "confidence": 0.95,
                    "reasoning": "Vehicle generates emissions"
                }
            ],
            "property_mappings": [
                {
                    "source_class": "Vehicle",
                    "target_class": "VehicleEmission",
                    "mappings": [
                        {
                            "source_property": "vehicleId",
                            "target_property": "vehicle_id",
                            "mapping_type": "direct",
                            "confidence": 1.0
                        }
                    ]
                }
            ],
            "calculations": [
                {
                    "name": "calculate_emissions",
                    "description": "Calculate CO2 emissions",
                    "formula": "fuel_amount * emission_factor",
                    "inputs": ["fuel_amount", "emission_factor"],
                    "output": "carbon_emissions"
                }
            ],
            "aggregations": [
                {
                    "name": "sum_fuel",
                    "function": "sum",
                    "source_field": "fuel_amount",
                    "target_field": "fuel_consumed"
                }
            ],
            "constants": {
                "fuel_emission_factors": {
                    "diesel": 2.68,
                    "gasoline": 2.31
                }
            },
            "transformation_steps": [
                {
                    "name": "transform_vehicles",
                    "description": "Transform vehicles to emissions",
                    "source": "vehicles",
                    "target": "vehicle_emissions",
                    "iteration": True
                }
            ]
        })

        # Configure mock client
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        # Run analysis
        generator = AIRuleGenerator(
            self.source_ontology,
            self.target_ontology,
            api_key=self.mock_api_key
        )
        suggestions = generator.analyze_with_ai()

        # Verify suggestions structure
        self.assertIn("class_mappings", suggestions)
        self.assertIn("property_mappings", suggestions)
        self.assertIn("calculations", suggestions)
        self.assertIn("aggregations", suggestions)
        self.assertIn("constants", suggestions)
        self.assertIn("transformation_steps", suggestions)

        # Verify content
        self.assertEqual(len(suggestions["class_mappings"]), 1)
        self.assertEqual(suggestions["class_mappings"][0]["source_class"], "Vehicle")
        self.assertEqual(len(suggestions["calculations"]), 1)
        self.assertEqual(suggestions["calculations"][0]["name"], "calculate_emissions")

    @patch('anthropic.Anthropic')
    def test_generate_rules_from_suggestions(self, mock_anthropic):
        """Test YAML rule generation from AI suggestions."""
        # Mock AI response
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps({
            "class_mappings": [
                {
                    "source_class": "Vehicle",
                    "target_class": "VehicleEmission",
                    "confidence": 0.95,
                    "reasoning": "Vehicle generates emissions"
                }
            ],
            "property_mappings": [
                {
                    "source_class": "Vehicle",
                    "target_class": "VehicleEmission",
                    "mappings": [
                        {
                            "source_property": "vehicleId",
                            "target_property": "vehicle_id",
                            "mapping_type": "direct",
                            "confidence": 1.0
                        }
                    ]
                }
            ],
            "calculations": [],
            "aggregations": [],
            "constants": {
                "fuel_emission_factors": {
                    "diesel": 2.68
                }
            },
            "transformation_steps": [
                {
                    "name": "transform_vehicles",
                    "description": "Transform vehicles to emissions",
                    "source": "vehicles",
                    "target": "vehicle_emissions",
                    "iteration": True
                }
            ]
        })

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        # Generate rules
        generator = AIRuleGenerator(
            self.source_ontology,
            self.target_ontology,
            api_key=self.mock_api_key
        )
        generator.analyze_with_ai()
        rules = generator.generate_rules()

        # Verify rules structure
        self.assertIn("metadata", rules)
        self.assertIn("constants", rules)
        self.assertIn("transformation_steps", rules)

        # Verify metadata
        self.assertIn("AI", rules["metadata"]["name"])
        self.assertIn("ai_model", rules["metadata"])

        # Verify constants
        self.assertIn("fuel_emission_factors", rules["constants"])
        self.assertEqual(rules["constants"]["fuel_emission_factors"]["diesel"], 2.68)

        # Verify transformation steps
        self.assertGreater(len(rules["transformation_steps"]), 0)
        self.assertEqual(rules["transformation_steps"][0]["name"], "transform_vehicles")

    @patch('anthropic.Anthropic')
    def test_save_rules(self, mock_anthropic):
        """Test saving generated rules to YAML file."""
        # Mock AI response with comprehensive data
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps({
            "class_mappings": [
                {
                    "source_class": "Vehicle",
                    "target_class": "VehicleEmission",
                    "confidence": 0.95,
                    "reasoning": "Test mapping"
                }
            ],
            "property_mappings": [
                {
                    "source_class": "Vehicle",
                    "target_class": "VehicleEmission",
                    "mappings": [
                        {
                            "source_property": "vehicleId",
                            "target_property": "vehicle_id",
                            "mapping_type": "direct",
                            "confidence": 1.0
                        }
                    ]
                }
            ],
            "calculations": [
                {
                    "name": "calc_test",
                    "description": "Test calculation",
                    "formula": "a * b",
                    "inputs": ["a", "b"],
                    "output": "result"
                }
            ],
            "aggregations": [
                {
                    "name": "sum_test",
                    "function": "sum",
                    "source_field": "value",
                    "target_field": "total"
                }
            ],
            "constants": {
                "test_constant": 1.0
            },
            "transformation_steps": [
                {
                    "name": "test_step",
                    "source": "source",
                    "target": "target",
                    "iteration": True
                }
            ]
        })

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        # Save rules
        output_file = "test_ai_output_rules.yaml"
        try:
            generator = AIRuleGenerator(
                self.source_ontology,
                self.target_ontology,
                api_key=self.mock_api_key
            )
            generator.analyze_with_ai()
            generator.save_rules(output_file)

            # Verify file was created
            self.assertTrue(Path(output_file).exists())

            # Verify file contents
            with open(output_file, 'r') as f:
                loaded_rules = yaml.safe_load(f)

            self.assertIn("metadata", loaded_rules)
            self.assertIn("constants", loaded_rules)
            self.assertIn("transformation_steps", loaded_rules)

        finally:
            # Cleanup
            if Path(output_file).exists():
                Path(output_file).unlink()

    def test_display_suggestions(self):
        """Test that display_suggestions runs without errors."""
        generator = AIRuleGenerator(
            self.source_ontology,
            self.target_ontology,
            api_key=self.mock_api_key
        )

        # Set mock suggestions
        generator.suggestions = {
            "class_mappings": [
                {
                    "source_class": "Vehicle",
                    "target_class": "VehicleEmission",
                    "confidence": 0.95,
                    "reasoning": "Test mapping"
                }
            ],
            "property_mappings": [],
            "calculations": [],
            "aggregations": [],
            "constants": {},
            "transformation_steps": []
        }

        # Should not raise any exceptions
        try:
            generator.display_suggestions()
        except Exception as e:
            self.fail(f"display_suggestions raised exception: {e}")


class TestAIRuleGeneratorIntegration(unittest.TestCase):
    """Integration tests requiring actual API key."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')
        self.source_ontology = "model_examples/vehicle_fleet/vehicle-fleet-ontology.ttl"
        self.target_ontology = "model_examples/vehicle_fleet/fleet-emissions-ontology.ttl"

    @unittest.skipUnless(
        os.environ.get('ANTHROPIC_API_KEY'),
        "ANTHROPIC_API_KEY not set - skipping integration test"
    )
    def test_real_ai_analysis(self):
        """Test real AI analysis with actual API (requires API key)."""
        generator = AIRuleGenerator(
            self.source_ontology,
            self.target_ontology
        )

        # Run actual AI analysis
        suggestions = generator.analyze_with_ai()

        # Verify we got reasonable suggestions
        self.assertIn("class_mappings", suggestions)
        self.assertIn("property_mappings", suggestions)

        # Should have found at least one class mapping
        self.assertGreater(len(suggestions["class_mappings"]), 0)

        # Display for visual verification
        print("\n" + "=" * 70)
        print("REAL AI ANALYSIS RESULTS")
        print("=" * 70)
        generator.display_suggestions()

    @unittest.skipUnless(
        os.environ.get('ANTHROPIC_API_KEY'),
        "ANTHROPIC_API_KEY not set - skipping integration test"
    )
    def test_full_pipeline_with_real_ai(self):
        """Test complete pipeline: AI analysis → rule generation → transformation."""
        from rule_engine import RuleBasedTransformer

        # Step 1: Generate rules with AI
        print("\n" + "=" * 70)
        print("STEP 1: AI RULE GENERATION")
        print("=" * 70)

        generator = AIRuleGenerator(
            self.source_ontology,
            self.target_ontology
        )
        suggestions = generator.analyze_with_ai()
        generator.display_suggestions()

        # Save AI-generated rules
        ai_rules_file = "test_ai_full_pipeline_rules.yaml"
        generator.save_rules(ai_rules_file)

        try:
            # Step 2: Transform data using AI-generated rules
            print("\n" + "=" * 70)
            print("STEP 2: TRANSFORMATION WITH AI-GENERATED RULES")
            print("=" * 70)

            transformer = RuleBasedTransformer(ai_rules_file)

            # Load sample data
            sample_data_file = "model_examples/vehicle_fleet/sample_fleet_data.json"
            with open(sample_data_file, 'r') as f:
                sample_data = json.load(f)

            # Transform
            result = transformer.transform(sample_data)

            # Verify transformation produced some output
            self.assertIsNotNone(result)
            self.assertIsInstance(result, dict)

            # Display result
            print("\nTransformation result:")
            print(json.dumps(result, indent=2))

            # Save result
            result_file = "test_ai_full_pipeline_output.json"
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\nSaved to: {result_file}")

        finally:
            # Cleanup
            for file in [ai_rules_file, "test_ai_full_pipeline_output.json"]:
                if Path(file).exists():
                    Path(file).unlink()


def run_comparison_test():
    """
    Compare results between simple rule generator and AI rule generator.
    Requires ANTHROPIC_API_KEY to be set.
    """
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print("❌ ANTHROPIC_API_KEY not set. Cannot run comparison.")
        print("   Set it with: export ANTHROPIC_API_KEY='your-key'")
        return

    from rule_generator import RuleGenerator
    from rule_engine import RuleBasedTransformer

    source_ont = "model_examples/vehicle_fleet/vehicle-fleet-ontology.ttl"
    target_ont = "model_examples/vehicle_fleet/fleet-emissions-ontology.ttl"
    sample_data = "model_examples/vehicle_fleet/sample_fleet_data.json"

    print("=" * 70)
    print("COMPARISON: Simple vs AI Rule Generator")
    print("=" * 70)

    # 1. Simple rule generator
    print("\n📋 SIMPLE RULE GENERATOR (Similarity-based)")
    print("-" * 70)
    simple_gen = RuleGenerator(source_ont, target_ont)
    simple_rules_file = "comparison_simple_rules.yaml"
    simple_gen.save_rules(simple_rules_file)

    # Transform with simple rules
    transformer = RuleBasedTransformer(simple_rules_file)
    with open(sample_data, 'r') as f:
        data = json.load(f)
    simple_result = transformer.transform(data)

    print("\nSimple rules result:")
    print(json.dumps(simple_result, indent=2)[:500] + "...")

    # 2. AI rule generator
    print("\n\n🤖 AI RULE GENERATOR (Semantic understanding)")
    print("-" * 70)
    ai_gen = AIRuleGenerator(source_ont, target_ont)
    ai_gen.analyze_with_ai()
    ai_gen.display_suggestions()

    ai_rules_file = "comparison_ai_rules.yaml"
    ai_gen.save_rules(ai_rules_file)

    # Transform with AI rules
    transformer = RuleBasedTransformer(ai_rules_file)
    ai_result = transformer.transform(data)

    print("\n\nAI rules result:")
    print(json.dumps(ai_result, indent=2)[:500] + "...")

    # Comparison
    print("\n\n📊 COMPARISON SUMMARY")
    print("=" * 70)

    # Load rules for comparison
    with open(simple_rules_file, 'r') as f:
        simple_rules = yaml.safe_load(f)
    with open(ai_rules_file, 'r') as f:
        ai_rules = yaml.safe_load(f)

    print(f"\nField mappings:")
    print(f"  Simple: {len(simple_rules.get('field_mappings', []))} mappings")
    print(f"  AI:     {len(ai_rules.get('field_mappings', []))} mappings")

    print(f"\nCalculation rules:")
    print(f"  Simple: {len(simple_rules.get('calculation_rules', []))} calculations")
    print(f"  AI:     {len(ai_rules.get('calculation_rules', []))} calculations")

    print(f"\nTransformation steps:")
    print(f"  Simple: {len(simple_rules.get('transformation_steps', []))} steps")
    print(f"  AI:     {len(ai_rules.get('transformation_steps', []))} steps")

    # Cleanup
    for file in [simple_rules_file, ai_rules_file]:
        if Path(file).exists():
            Path(file).unlink()

    print("\n" + "=" * 70)


if __name__ == '__main__':
    import sys

    if '--comparison' in sys.argv:
        run_comparison_test()
    else:
        unittest.main()
