# AI Rule Generator - Testing Instructions

## Improvements Made

The AI rule generator has been significantly enhanced with comprehensive JSON-LD mapping rules from `doc/RDF_JSON_LD_MAPPING.md`:

### Key Enhancements:

1. **Comprehensive Naming Convention Rules**
   - camelCase → snake_case conversion examples
   - Array property pluralization (hasEnergyConsumption → energy_consumptions)
   - Nested object simplification (energyTypeName → name)

2. **Complete Structure Patterns**
   - DatatypeProperty patterns
   - ObjectProperty (single and array) patterns
   - Nested object simplification examples
   - Complete source and target JSON-LD structure examples

3. **Concrete Examples**
   - Full manufacturing activity to GHG report transformation example
   - All field name conversions documented
   - Emission factors provided (electricity: 0.5, natural_gas: 2.03, diesel: 2.68)

4. **Substeps Requirement**
   - AI now required to generate substeps with field mappings
   - Cannot generate empty substeps
   - Must show complete mapping chain

## Testing Steps

### Step 1: Generate AI Rules

Run the enhanced AI rule generator:

```bash
# Set your API key
export ANTHROPIC_API_KEY="your-api-key-here"

# Generate rules with SSL verification disabled (for corporate environments)
python ai_rule_generator.py --no-verify-ssl \
    model/source/manufacturing-ontology.ttl \
    model/target/ghg-report-ontology.ttl \
    output/ai_generated_rules_v2.yaml
```

### Step 2: Transform Data

Use the generated rules to transform sample data:

```bash
python transformer.py \
    test_data/source/sample1_small_factory.json \
    output/ai_generated_rules_v2.yaml \
    output/ai_output_v2.json
```

### Step 3: Validate Output

Use the new validator to check if the output is correct:

```bash
python jsonld_validator.py \
    model/target/ghg-report-ontology.ttl \
    output/ai_output_v2.json
```

Expected validation results:
- ✅ **Errors: 0** - All field names should be snake_case
- ⚠️ **Warnings: few** - Minor naming suggestions acceptable
- ℹ️ **Info: few** - Optional fields not in ontology

### Step 4: Compare with Correct Output

Compare AI-generated output with the hand-crafted correct output:

```bash
python -c "
import json

with open('output/ai_output_v2.json') as f:
    ai_output = json.load(f)

with open('output/correct_output.json') as f:
    correct_output = json.load(f)

print('AI-generated total_emissions:', ai_output.get('total_emissions', 0))
print('Correct total_emissions:', correct_output.get('total_emissions', 0))
print('Number of emissions (AI):', len(ai_output.get('emissions', [])))
print('Number of emissions (correct):', len(correct_output.get('emissions', [])))
"
```

Expected results:
- Total emissions: ~12,175.5 kg-CO2
- Number of emissions: 3 records
- All emissions should have valid source_category, co2_amount, emission_factor

## What to Look For

### ✅ Good Signs:
1. **Non-zero emissions**: total_emissions > 0
2. **Correct field names**: snake_case (emission_source, co2_amount, source_category)
3. **Valid calculations**: co2_amount = amount × emission_factor
4. **Complete records**: All emissions have all required fields
5. **Validator passes**: 0 errors, minimal warnings

### ❌ Problem Indicators:
1. **Empty output**: total_emissions = 0 or emissions = []
2. **camelCase fields**: activityName instead of activity_name
3. **Missing substeps**: Generated YAML has empty substeps: []
4. **Wrong emission factors**: Not matching electricity: 0.5, natural_gas: 2.03, diesel: 2.68
5. **Validator errors**: Field naming violations or type mismatches

## Troubleshooting

### If AI-generated rules still have empty substeps:

Check the generated YAML file:
```bash
grep -A 5 "substeps:" output/ai_generated_rules_v2.yaml
```

If you see:
```yaml
substeps: []
```

This means the AI prompt needs further refinement. Report this as a bug.

### If output has zero emissions:

1. Check calculation_rules in generated YAML
2. Verify emission_factors in constants
3. Ensure transformation_steps have proper substeps with field_mappings

### If validator reports errors:

Read the validation report carefully:
```bash
python jsonld_validator.py \
    model/target/ghg-report-ontology.ttl \
    output/ai_output_v2.json \
    --report output/validation_report.txt

cat output/validation_report.txt
```

## Success Criteria

The AI rule generator improvements are successful if:

1. ✅ Generated rules file has NON-EMPTY substeps
2. ✅ All field names in generated rules use snake_case
3. ✅ Transformation produces total_emissions ≈ 12,175.5 kg-CO2
4. ✅ Validator reports 0 errors
5. ✅ Output matches structure of correct_output.json

## Next Steps

If testing is successful:
1. Commit the improved ai_rule_generator.py
2. Update documentation
3. Create examples showing before/after AI generation quality

If testing reveals issues:
1. Document specific problems found
2. Further refine the AI prompt based on issues
3. Iterate until success criteria are met
