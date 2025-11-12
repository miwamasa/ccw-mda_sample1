"""
Demonstration of AI Rule Generator with Mock AI Response

This script demonstrates what the AI rule generator produces without requiring
an actual API key. It uses a pre-defined mock response that simulates what
Claude AI would return when analyzing the vehicle fleet ontologies.

Usage:
    python demo_ai_rule_generator.py
"""

import json
import yaml
from pathlib import Path
from ai_rule_generator import AIRuleGenerator
from unittest.mock import patch, MagicMock


def create_mock_ai_response():
    """
    Create a realistic mock response that simulates what Claude AI would return
    when analyzing vehicle fleet → emissions ontologies.
    """
    return {
        "class_mappings": [
            {
                "source_class": "Vehicle",
                "target_class": "VehicleEmission",
                "confidence": 0.95,
                "reasoning": "A Vehicle in the source ontology represents a fleet vehicle that consumes fuel and travels distances. The VehicleEmission class in the target ontology captures the emissions data for individual vehicles. The mapping is semantically sound as each vehicle generates emissions that need to be reported."
            },
            {
                "source_class": "Organization",
                "target_class": "ReportingOrganization",
                "confidence": 0.90,
                "reasoning": "Both represent the organization that operates the vehicle fleet. The Organization class contains operator details while ReportingOrganization represents the entity responsible for the emissions report."
            },
            {
                "source_class": "Fleet",
                "target_class": "EmissionsReport",
                "confidence": 0.85,
                "reasoning": "The Fleet represents the collection of vehicles and operations data, while EmissionsReport is the transformed output containing aggregated emissions data for the entire fleet."
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
                        "confidence": 1.0,
                        "transformation": "none"
                    },
                    {
                        "source_property": "vehicleType",
                        "target_property": "vehicle_type",
                        "mapping_type": "direct",
                        "confidence": 1.0,
                        "transformation": "none"
                    },
                    {
                        "source_property": "licensePlate",
                        "target_property": "license_plate",
                        "mapping_type": "direct",
                        "confidence": 0.95,
                        "transformation": "none"
                    },
                    {
                        "source_property": "fuelConsumptions",
                        "target_property": "fuel_consumed",
                        "mapping_type": "aggregation",
                        "confidence": 0.90,
                        "transformation": "sum of fuel_amount from all consumption records",
                        "notes": "Array of fuel consumption records needs to be aggregated"
                    },
                    {
                        "source_property": "fuelConsumptions",
                        "target_property": "distance_traveled",
                        "mapping_type": "aggregation",
                        "confidence": 0.90,
                        "transformation": "sum of distance_traveled from all consumption records"
                    },
                    {
                        "source_property": "fuelConsumptions",
                        "target_property": "carbon_emissions",
                        "mapping_type": "calculation",
                        "confidence": 0.95,
                        "transformation": "calculated from fuel consumption and emission factors",
                        "notes": "Requires calculation: total_fuel * emission_factor"
                    },
                    {
                        "source_property": "fuelConsumptions[0].fuelType.fuelTypeName",
                        "target_property": "fuel_type",
                        "mapping_type": "extraction",
                        "confidence": 0.85,
                        "transformation": "extract fuel type from first consumption record",
                        "notes": "Assumes all consumptions for a vehicle use the same fuel type"
                    }
                ]
            },
            {
                "source_class": "Organization",
                "target_class": "ReportingOrganization",
                "mappings": [
                    {
                        "source_property": "organizationName",
                        "target_property": "organization_name",
                        "mapping_type": "direct",
                        "confidence": 1.0,
                        "transformation": "none"
                    },
                    {
                        "source_property": "contactEmail",
                        "target_property": "contact_email",
                        "mapping_type": "direct",
                        "confidence": 0.95,
                        "transformation": "none"
                    }
                ]
            },
            {
                "source_class": "Fleet",
                "target_class": "EmissionsReport",
                "mappings": [
                    {
                        "source_property": "fleetId",
                        "target_property": "report_id",
                        "mapping_type": "direct",
                        "confidence": 0.90,
                        "transformation": "can be used as report identifier"
                    }
                ]
            }
        ],
        "calculations": [
            {
                "name": "calculate_vehicle_emissions",
                "description": "Calculate total CO2 emissions for a vehicle based on fuel consumption and emission factors",
                "formula": "sum(fuel_amount * emission_factor for each fuel_consumption)",
                "inputs": [
                    "fuel_consumptions (array of consumption records)",
                    "emission_factors (lookup table by fuel type)"
                ],
                "output": "carbon_emissions",
                "reasoning": "CO2 emissions must be calculated by multiplying the amount of fuel consumed by the appropriate emission factor for that fuel type. Standard emission factors: diesel=2.68 kg-CO2/L, gasoline=2.31 kg-CO2/L, LPG=1.51 kg-CO2/L.",
                "dependencies": {
                    "fuel_amount": "aggregation of fuel_amount from fuel_consumptions",
                    "emission_factor": "lookup from constants using fuel_type"
                }
            },
            {
                "name": "calculate_emission_factor",
                "description": "Look up the emission factor for a given fuel type",
                "formula": "constants.fuel_emission_factors[fuel_type]",
                "inputs": ["fuel_type"],
                "output": "emission_factor",
                "reasoning": "Emission factors are standard constants that vary by fuel type"
            }
        ],
        "aggregations": [
            {
                "name": "sum_fuel_consumed",
                "function": "sum",
                "description": "Total fuel consumed by a vehicle across all consumption records",
                "source_path": "Vehicle.fuelConsumptions",
                "source_field": "fuel_amount",
                "target_field": "fuel_consumed",
                "reasoning": "Each vehicle has multiple fuel consumption records that need to be summed to get total fuel used"
            },
            {
                "name": "sum_distance_traveled",
                "function": "sum",
                "description": "Total distance traveled by a vehicle",
                "source_path": "Vehicle.fuelConsumptions",
                "source_field": "distance_traveled",
                "target_field": "distance_traveled",
                "reasoning": "Distance is recorded per fuel consumption event and needs aggregation"
            },
            {
                "name": "sum_total_emissions",
                "function": "sum",
                "description": "Fleet-wide total CO2 emissions",
                "source_path": "vehicle_emissions",
                "source_field": "carbon_emissions",
                "target_field": "total_emissions",
                "reasoning": "Report needs total emissions across all vehicles"
            },
            {
                "name": "sum_total_fuel",
                "function": "sum",
                "description": "Fleet-wide total fuel consumption",
                "source_path": "vehicle_emissions",
                "source_field": "fuel_consumed",
                "target_field": "total_fuel_consumed",
                "reasoning": "Report needs total fuel consumed across all vehicles"
            },
            {
                "name": "count_vehicles",
                "function": "count",
                "description": "Number of vehicles in the fleet",
                "source_path": "vehicle_emissions",
                "target_field": "vehicle_count",
                "reasoning": "Report should include the number of vehicles"
            }
        ],
        "constants": {
            "fuel_emission_factors": {
                "diesel": 2.68,
                "gasoline": 2.31,
                "lpg": 1.51,
                "electric": 0.0,
                "description": "CO2 emission factors in kg-CO2 per liter of fuel"
            },
            "defaults": {
                "unknown_value": "Unknown",
                "unknown_fuel_type": "gasoline"
            }
        },
        "transformation_steps": [
            {
                "name": "transform_vehicles_to_emissions",
                "description": "Transform each vehicle and its fuel consumption data into an emission record",
                "source": "vehicles",
                "target": "vehicle_emissions",
                "iteration": True,
                "order": 1,
                "reasoning": "Primary transformation that converts operational vehicle data into emissions data",
                "substeps": [
                    {
                        "name": "map_vehicle_fields",
                        "description": "Map basic vehicle identification fields",
                        "fields": [
                            {"source": "vehicle_id", "target": "vehicle_id"},
                            {"source": "vehicle_type", "target": "vehicle_type"},
                            {"source": "license_plate", "target": "license_plate"}
                        ]
                    },
                    {
                        "name": "extract_fuel_type",
                        "description": "Extract fuel type from consumption records",
                        "source": "fuel_consumptions[0].fuel_type.fuel_type_name",
                        "target": "fuel_type",
                        "transformation": "lowercase"
                    },
                    {
                        "name": "aggregate_fuel_consumed",
                        "description": "Sum all fuel consumption",
                        "aggregation": "sum_fuel_consumed"
                    },
                    {
                        "name": "aggregate_distance",
                        "description": "Sum all distance traveled",
                        "aggregation": "sum_distance_traveled"
                    },
                    {
                        "name": "calculate_emissions",
                        "description": "Calculate CO2 emissions",
                        "calculation": "calculate_vehicle_emissions"
                    }
                ]
            },
            {
                "name": "calculate_fleet_totals",
                "description": "Calculate fleet-wide aggregate values",
                "source": "vehicle_emissions",
                "target": "report_summary",
                "order": 2,
                "reasoning": "After processing individual vehicles, compute fleet-level totals",
                "aggregations": [
                    "sum_total_emissions",
                    "sum_total_fuel",
                    "count_vehicles"
                ]
            },
            {
                "name": "map_organization_info",
                "description": "Map organization information to reporting organization",
                "source": "fleet_info.operator",
                "target": "reporting_organization",
                "order": 3,
                "reasoning": "Map the fleet operator to the reporting organization"
            }
        ]
    }


def main():
    """Run the demonstration."""
    print("=" * 80)
    print("AI RULE GENERATOR DEMONSTRATION (Mock Mode)")
    print("=" * 80)
    print()
    print("This demonstrates what the AI rule generator produces when analyzing")
    print("vehicle fleet → emissions ontologies, using a pre-defined mock response")
    print("that simulates Claude AI's semantic analysis.")
    print()

    source_ontology = "model_examples/vehicle_fleet/vehicle-fleet-ontology.ttl"
    target_ontology = "model_examples/vehicle_fleet/fleet-emissions-ontology.ttl"

    # Create mock AI client
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_ai_response = create_mock_ai_response()
    mock_response.content[0].text = json.dumps(mock_ai_response)

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    # Patch the Anthropic client
    with patch('anthropic.Anthropic') as mock_anthropic:
        mock_anthropic.return_value = mock_client

        # Create generator with mock API key
        print("🤖 Initializing AI Rule Generator...")
        generator = AIRuleGenerator(
            source_ontology,
            target_ontology,
            api_key="demo-mock-key-12345"
        )

        print("✓ Loaded source ontology: vehicle-fleet-ontology.ttl")
        print("✓ Loaded target ontology: fleet-emissions-ontology.ttl")
        print()

        # Analyze with AI (using mock)
        print("🔍 Analyzing ontologies with AI (mock mode)...")
        suggestions = generator.analyze_with_ai()
        print("✓ Analysis complete")
        print()

        # Display suggestions
        print("=" * 80)
        print("AI TRANSFORMATION SUGGESTIONS")
        print("=" * 80)
        print()
        generator.display_suggestions()

        # Generate rules
        print("\n" + "=" * 80)
        print("GENERATING YAML RULES")
        print("=" * 80)
        print()
        rules = generator.generate_rules()

        # Save rules
        output_file = "demo_ai_generated_rules.yaml"
        generator.save_rules(output_file)
        print(f"\n✅ Rules saved to: {output_file}")

        # Show a preview of the rules
        print("\n" + "=" * 80)
        print("GENERATED RULES PREVIEW")
        print("=" * 80)
        print()
        print("First 50 lines of generated YAML:")
        print("-" * 80)

        with open(output_file, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:50], 1):
                print(f"{i:3d} | {line}", end='')

        if len(lines) > 50:
            print(f"... ({len(lines) - 50} more lines)")

        # Summary statistics
        print("\n" + "=" * 80)
        print("SUMMARY STATISTICS")
        print("=" * 80)
        print()
        print(f"📊 Class Mappings:      {len(suggestions['class_mappings'])} mappings")
        print(f"📊 Property Mappings:   {sum(len(pm['mappings']) for pm in suggestions['property_mappings'])} mappings")
        print(f"📊 Calculations:        {len(suggestions['calculations'])} calculation rules")
        print(f"📊 Aggregations:        {len(suggestions['aggregations'])} aggregation rules")
        print(f"📊 Constants Defined:   {len(suggestions['constants'])} constant groups")
        print(f"📊 Transform Steps:     {len(suggestions['transformation_steps'])} steps")
        print()

        # Comparison with simple generator
        print("=" * 80)
        print("COMPARISON: AI vs Simple Rule Generator")
        print("=" * 80)
        print()
        print("Key Differences:")
        print()
        print("┌─────────────────────────┬──────────────────┬──────────────────┐")
        print("│ Feature                 │ Simple Generator │ AI Generator     │")
        print("├─────────────────────────┼──────────────────┼──────────────────┤")
        print("│ Class Mapping           │ String matching  │ Semantic         │")
        print("│ Property Mapping        │ Name similarity  │ Semantic + type  │")
        print("│ Calculations            │ ❌ None          │ ✅ Auto-inferred │")
        print("│ Aggregations            │ ❌ None          │ ✅ Auto-inferred │")
        print("│ Constants/Lookups       │ ❌ None          │ ✅ Suggested     │")
        print("│ Confidence Scores       │ ❌ No            │ ✅ Yes           │")
        print("│ Reasoning               │ ❌ No            │ ✅ Provided      │")
        print("│ Complex Transformations │ ❌ Limited       │ ✅ Comprehensive │")
        print("└─────────────────────────┴──────────────────┴──────────────────┘")
        print()

        print("💡 The AI generator understands:")
        print("   • Vehicles → VehicleEmission (semantic relationship)")
        print("   • Fuel consumption needs aggregation (sum)")
        print("   • CO2 = fuel × emission_factor (domain knowledge)")
        print("   • Fleet totals need roll-up calculations")
        print()

        print("✨ Next Steps:")
        print(f"   1. Review generated rules: {output_file}")
        print("   2. Test with rule_engine.py:")
        print(f"      python rule_engine.py {output_file} \\")
        print("          model_examples/vehicle_fleet/sample_fleet_data.json \\")
        print("          demo_ai_output.json")
        print()
        print("   3. To use real AI analysis (requires API key):")
        print("      export ANTHROPIC_API_KEY='your-key'")
        print("      python ai_rule_generator.py \\")
        print("          model_examples/vehicle_fleet/vehicle-fleet-ontology.ttl \\")
        print("          model_examples/vehicle_fleet/fleet-emissions-ontology.ttl \\")
        print("          ai_rules.yaml")
        print()

        print("=" * 80)
        print("Demo complete! Check the generated files.")
        print("=" * 80)


if __name__ == '__main__':
    main()
