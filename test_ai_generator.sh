#!/bin/bash
# Test script for improved AI rule generator
# Usage: ./test_ai_generator.sh

set -e  # Exit on error

echo "================================"
echo "AI Rule Generator Testing Script"
echo "================================"
echo ""

# Check if API key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ Error: ANTHROPIC_API_KEY environment variable is not set"
    echo ""
    echo "Please set your API key:"
    echo "  export ANTHROPIC_API_KEY='your-api-key-here'"
    echo ""
    exit 1
fi

echo "✓ API key is set"
echo ""

# Step 1: Generate AI rules
echo "Step 1: Generating AI rules with enhanced prompt..."
echo "-----------------------------------------------"
python ai_rule_generator.py --no-verify-ssl \
    model/source/manufacturing-ontology.ttl \
    model/target/ghg-report-ontology.ttl \
    output/ai_generated_rules_v2.yaml

if [ $? -ne 0 ]; then
    echo "❌ Failed to generate AI rules"
    exit 1
fi
echo ""
echo "✓ AI rules generated: output/ai_generated_rules_v2.yaml"
echo ""

# Check for empty substeps
echo "Checking for empty substeps..."
EMPTY_SUBSTEPS=$(grep -c "substeps: \[\]" output/ai_generated_rules_v2.yaml || true)
if [ "$EMPTY_SUBSTEPS" -gt 0 ]; then
    echo "⚠️  Warning: Found $EMPTY_SUBSTEPS empty substeps in generated rules"
    echo "   This may cause transformation to produce empty output"
else
    echo "✓ No empty substeps found"
fi
echo ""

# Step 2: Transform data
echo "Step 2: Transforming sample data..."
echo "-----------------------------------"
python rule_engine.py \
    output/ai_generated_rules_v2.yaml \
    test_data/source/sample1_small_factory.json \
    output/ai_output_v2.json

if [ $? -ne 0 ]; then
    echo "❌ Failed to transform data"
    exit 1
fi
echo ""
echo "✓ Data transformed: output/ai_output_v2.json"
echo ""

# Step 3: Validate output
echo "Step 3: Validating output with JSON-LD validator..."
echo "---------------------------------------------------"
python jsonld_validator.py \
    model/target/ghg-report-ontology.ttl \
    output/ai_output_v2.json

if [ $? -ne 0 ]; then
    echo "⚠️  Validation completed with issues (see above)"
else
    echo "✓ Validation passed"
fi
echo ""

# Step 4: Compare results
echo "Step 4: Comparing with correct output..."
echo "----------------------------------------"
python -c "
import json
import sys

try:
    with open('output/ai_output_v2.json') as f:
        ai_output = json.load(f)

    with open('output/correct_output.json') as f:
        correct_output = json.load(f)

    ai_total = ai_output.get('total_emissions', 0)
    correct_total = correct_output.get('total_emissions', 0)
    ai_emissions_count = len(ai_output.get('emissions', []))
    correct_emissions_count = len(correct_output.get('emissions', []))

    print(f'AI-generated total_emissions: {ai_total} kg-CO2')
    print(f'Correct total_emissions:      {correct_total} kg-CO2')
    print(f'')
    print(f'AI-generated emissions count: {ai_emissions_count}')
    print(f'Correct emissions count:      {correct_emissions_count}')
    print(f'')

    # Check if results are close
    if ai_total == 0:
        print('❌ FAIL: AI-generated output has zero emissions')
        print('   This indicates the transformation rules are incomplete')
        sys.exit(1)
    elif abs(ai_total - correct_total) < 0.1:
        print('✅ SUCCESS: Total emissions match!')
        sys.exit(0)
    elif abs(ai_total - correct_total) / correct_total < 0.05:
        print('⚠️  WARNING: Total emissions are close but not exact')
        print(f'   Difference: {abs(ai_total - correct_total):.2f} kg-CO2 ({abs(ai_total - correct_total) / correct_total * 100:.2f}%)')
        sys.exit(0)
    else:
        print('❌ FAIL: Total emissions are significantly different')
        print(f'   Difference: {abs(ai_total - correct_total):.2f} kg-CO2 ({abs(ai_total - correct_total) / correct_total * 100:.2f}%)')
        sys.exit(1)

except FileNotFoundError as e:
    print(f'❌ Error: File not found - {e}')
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f'❌ Error: Invalid JSON - {e}')
    sys.exit(1)
"

COMPARE_EXIT=$?
echo ""

# Final summary
echo "================================"
echo "Test Summary"
echo "================================"
if [ $COMPARE_EXIT -eq 0 ]; then
    echo "✅ All tests passed!"
    echo ""
    echo "The AI rule generator improvements are working correctly."
    echo "The generated rules produce accurate GHG emission reports."
else
    echo "❌ Tests failed"
    echo ""
    echo "The AI-generated rules need further improvement."
    echo "Please review the output above for details."
fi
echo ""
echo "Generated files:"
echo "  - output/ai_generated_rules_v2.yaml (transformation rules)"
echo "  - output/ai_output_v2.json (transformed data)"
echo ""

exit $COMPARE_EXIT
