#!/usr/bin/env python3
"""
Test script for improved rule generation logic.
This simulates AI suggestions and tests the improved substeps generation.
"""

import yaml
import json
from ai_rule_generator import AIRuleGenerator

# Mock AI suggestions based on typical response
mock_suggestions = {
    "class_mappings": [
        {
            "source_class": "ManufacturingActivity",
            "target_class": "EmissionReport",
            "confidence": 0.90
        }
    ],
    "property_mappings": [
        {
            "source_class": "ManufacturingActivity",
            "target_class": "Emission",
            "mappings": [
                {
                    "source_property": "activity_name",
                    "target_property": "emission_source",
                    "mapping_type": "direct"
                },
                {
                    "source_property": "energy_type_name",
                    "target_property": "source_category",
                    "mapping_type": "direct"
                }
            ]
        }
    ],
    "calculations": [],
    "aggregations": [
        {
            "name": "total_emissions",
            "function": "sum",
            "field": "co2_amount",
            "target_property": "total_emissions"
        }
    ],
    "constants": {
        "emission_factors": {
            "electricity": 0.5,
            "natural_gas": 2.03,
            "diesel": 2.68
        }
    },
    "transformation_steps": [
        {
            "name": "transform_activities_to_emissions",
            "description": "Transform manufacturing activities to emission records",
            "source": "manufacturing_activities",
            "target": "emissions",
            "iteration": True,
            "substeps": []  # Empty - will be auto-generated
        },
        {
            "name": "create_organization_info",
            "description": "Extract organization information",
            "source": "manufacturing_activities",
            "target": "reporting_organization",
            "iteration": False,
            "substeps": []  # Empty - will be auto-generated
        }
    ]
}

def test_improved_generation():
    """Test improved rule generation with auto-substeps."""
    print("=" * 70)
    print("TESTING IMPROVED RULE GENERATION")
    print("=" * 70)

    # Create generator instance with dummy API key (we won't call AI)
    import os
    os.environ['ANTHROPIC_API_KEY'] = 'test-key-not-used'
    generator = AIRuleGenerator(
        "model/source/manufacturing-ontology.ttl",
        "model/target/ghg-report-ontology.ttl",
        verify_ssl=False
    )

    # Set mock AI suggestions
    generator.ai_suggestions = mock_suggestions

    print("\n✓ Loaded mock AI suggestions")
    print(f"  - {len(mock_suggestions['transformation_steps'])} transformation steps")
    print(f"  - All substeps initially empty: {all(not step.get('substeps') for step in mock_suggestions['transformation_steps'])}")

    # Generate rules with improved logic
    print("\n🔧 Generating rules with improved logic...")
    rules = generator.generate_rules()

    # Check results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    # Check constants
    print("\n📋 Constants:")
    print(f"  ✓ emission_factors: {len(rules['constants'].get('emission_factors', {}))} entries")
    print(f"  ✓ scope_classification: {'scope1' in rules['constants'].get('scope_classification', {})}")

    # Check calculation_rules
    calc_rules = rules['calculation_rules']
    print(f"\n🔢 Calculation Rules: {len(calc_rules)}")
    for rule in calc_rules:
        print(f"  ✓ {rule['name']}: {rule.get('description', 'N/A')}")

    # Check transformation_steps
    steps = rules['transformation_steps']
    print(f"\n🔄 Transformation Steps: {len(steps)}")

    empty_substeps_count = 0
    non_empty_substeps_count = 0

    for step in steps:
        substeps = step.get('substeps', [])
        if substeps:
            non_empty_substeps_count += 1
            print(f"\n  ✅ {step['name']}:")
            print(f"     Source: {step.get('source', 'N/A')}")
            print(f"     Target: {step.get('target', 'N/A')}")
            print(f"     Substeps: {len(substeps)}")
            for substep in substeps:
                print(f"       - {substep.get('name', 'unnamed')}")
                if 'mapping' in substep:
                    print(f"         Mappings: {len(substep['mapping'])}")
        else:
            empty_substeps_count += 1
            print(f"\n  ❌ {step['name']}: EMPTY SUBSTEPS")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if empty_substeps_count == 0:
        print("✅ SUCCESS: All transformation steps have substeps!")
        print(f"   - {non_empty_substeps_count} steps with substeps")
        print(f"   - 0 steps with empty substeps")
    else:
        print(f"⚠️  WARNING: {empty_substeps_count} steps still have empty substeps")
        print(f"   - {non_empty_substeps_count} steps with substeps")
        print(f"   - {empty_substeps_count} steps with empty substeps")

    # Save improved rules
    output_file = "output/ai_generated_rules_v2_improved.yaml"
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(rules, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"\n💾 Saved improved rules to: {output_file}")

    return rules, empty_substeps_count == 0

if __name__ == "__main__":
    try:
        rules, success = test_improved_generation()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
