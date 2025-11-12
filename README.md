# MDA-Based Data Transformation: Automatic Rule Generation from Ontologies

## Overview

This project implements a **complete Model-Driven Architecture (MDA)** solution that **automatically generates transformation rules from RDF ontologies**. The system features:

1. **Automatic Rule Generation**: Analyzes source and target ontologies to generate transformation rules
2. **Generic Rule Engine**: Applies generated rules to transform data
3. **Complete Automation**: From ontologies to transformed data with minimal manual intervention

This represents a **fully model-driven approach** where ontologies drive the entire transformation process.

## Key Features

- **🤖 AI-Powered Rule Generation**: Uses Claude AI to semantically analyze ontologies and generate intelligent transformation rules
- **🔍 Automatic Rule Generation**: Similarity-based approach using semantic matching algorithms
- **🧠 Semantic Understanding**: AI infers complex calculations, aggregations, and domain-specific logic
- **📋 Declarative Rules**: All transformation logic in external YAML files, not code
- **🔄 Generic Engine**: Reusable engine works with ANY ontology pair
- **🧪 Comprehensive Testing**: 64 tests covering all components (62 passing + 2 integration requiring API key)
- **📚 Multi-Domain Support**: Proven with manufacturing→GHG and vehicle fleet→emissions transformations

## Architecture

### Complete MDA Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│  1. Ontology Layer (RDF/Turtle)                             │
│     INPUT: Source + Target Ontologies                       │
│     - vehicle-fleet-ontology.ttl                            │
│     - fleet-emissions-ontology.ttl                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
           ╔════════════════════════════════════╗
           ║  AUTOMATIC RULE GENERATION         ║
           ║  rule_generator.py                 ║
           ║  - Analyzes ontologies             ║
           ║  - Infers semantic mappings        ║
           ║  - Generates transformation rules  ║
           ╚════════════════════════════════════╝
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2. Rule Layer (Auto-Generated YAML)                        │
│     OUTPUT: transformation_rules.yaml                       │
│     - Metadata & namespaces                                 │
│     - Constants & lookup tables                             │
│     - Field mappings                                        │
│     - Calculation rules                                     │
│     - Transformation steps                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3. Transformation Engine (Generic Python)                  │
│     rule_engine.py                                          │
│     - Reads generated rules                                 │
│     - Applies transformations                               │
│     - Validates output                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  4. Output (Transformed JSON-LD)                            │
│     - Compliant with target ontology                        │
│     - Ready for consumption                                 │
└─────────────────────────────────────────────────────────────┘
```

### Source Model
**Manufacturing Ontology** (`model/source/manufacturing-ontology.ttl`)
- Represents manufacturing activities, products, and energy consumption
- Key classes: `ManufacturingActivity`, `Product`, `EnergyConsumption`, `EnergyType`
- Captures operational data including energy usage by type

### Target Model
**GHG Report Ontology** (`model/target/ghg-report-ontology.ttl`)
- Represents GHG emission reports following the GHG Protocol
- Key classes: `EmissionReport`, `Scope1Emission`, `Scope2Emission`, `Organization`
- Captures carbon footprint data with scope classification

### Transformation Rules
**Declarative Rules** (`transformation_rules.yaml`)

The transformation rules are defined externally in YAML format and include:

1. **Constants**: Emission factors, scope classifications, default values
2. **Field Mappings**: Direct source-to-target field mappings
3. **Calculation Rules**: Formulas for derived values (e.g., CO2 = energy × factor)
4. **Aggregation Rules**: Sum, count, average operations
5. **Classification Logic**: Conditional logic for categorization

**Example Rule Structure:**
```yaml
calculation_rules:
  - name: "calculate_co2_emission"
    description: "Convert energy consumption to CO2 emissions"
    input:
      energy_amount: "$.amount"
      energy_type: "$.energy_type.name"
    formula: "energy_amount * emission_factor"
    lookup:
      emission_factor:
        source: "constants.emission_factors"
        key: "energy_type"
```

## Project Structure

```
ccw-mda_sample1/
├── model/
│   ├── source/
│   │   └── manufacturing-ontology.ttl    # Source RDF ontology
│   └── target/
│       └── ghg-report-ontology.ttl       # Target RDF ontology
├── model_examples/
│   └── vehicle_fleet/                    # Example: Vehicle fleet domain
│       ├── vehicle-fleet-ontology.ttl    # Source: Fleet operations
│       ├── fleet-emissions-ontology.ttl  # Target: Emissions reporting
│       ├── generated_rules.yaml          # Auto-generated rules
│       └── sample_fleet_data.json        # Sample data
├── rule_generator.py                     # Automatic rule generator (similarity-based)
├── ai_rule_generator.py                  # **NEW** AI-powered rule generator
├── test_rule_generation.py               # Rule generation tests (17 tests)
├── test_ai_rule_generator.py             # **NEW** AI rule generator tests (10 tests)
├── demo_ai_rule_generator.py             # **NEW** Demo script for AI generator
├── AI_RULE_GENERATOR_README.md           # **NEW** AI generator documentation (Japanese)
├── transformation_rules.yaml             # Hand-crafted transformation rules
├── rule_engine.py                        # Generic transformation engine
├── test_rule_engine.py                   # Rule engine tests (16 tests)
├── transformer.py                        # Legacy transformer (for compatibility)
├── test_transformer.py                   # Legacy tests (21 tests)
├── test_data/
│   ├── source/                           # Sample input JSON files
│   │   ├── sample1_small_factory.json
│   │   ├── sample2_multi_fuel.json
│   │   └── sample3_electronics.json
│   └── target/                           # Generated output files
├── instructions.md                       # Project instructions
└── README.md                             # This file
```

## Installation

### Prerequisites
- Python 3.7 or higher
- PyYAML (for rule parsing)
- RDFLib (for ontology parsing)
- Anthropic SDK (for AI-powered rule generation - optional)

### Setup
```bash
cd ccw-mda_sample1

# Basic setup (for similarity-based rule generation)
pip install pyyaml rdflib

# Optional: For AI-powered rule generation
pip install anthropic
export ANTHROPIC_API_KEY='your-api-key'
```

## Usage

### 🎯 Complete MDA Workflow (Fully Automatic)

The complete workflow from ontologies to transformed data:

```bash
# Step 1: Generate transformation rules from ontologies
python rule_generator.py \
    model_examples/vehicle_fleet/vehicle-fleet-ontology.ttl \
    model_examples/vehicle_fleet/fleet-emissions-ontology.ttl \
    model_examples/vehicle_fleet/generated_rules.yaml

# Step 2: Apply generated rules to transform data
python rule_engine.py \
    model_examples/vehicle_fleet/generated_rules.yaml \
    model_examples/vehicle_fleet/sample_fleet_data.json \
    model_examples/vehicle_fleet/output.json
```

**Output from Step 1 (Rule Generation):**
```
Generated transformation rules saved to: model_examples/vehicle_fleet/generated_rules.yaml
  Source ontology: http://example.org/fleet#
  Target ontology: http://example.org/fleet-emissions#
  Class mappings: 2
  Property mappings: 3
```

**Output from Step 2 (Transformation):**
```
Transformation complete: ... -> output.json
  Rule file: generated_rules.yaml
  Total emissions: [calculated value] kg-CO2
```

### 🤖 AI-Powered Rule Generation (Recommended)

For more intelligent rule generation using Claude AI:

```bash
# Run AI-powered rule generator
python ai_rule_generator.py \
    model_examples/vehicle_fleet/vehicle-fleet-ontology.ttl \
    model_examples/vehicle_fleet/fleet-emissions-ontology.ttl \
    ai_generated_rules.yaml

# If you get SSL certificate errors (corporate proxy environments):
python ai_rule_generator.py --no-verify-ssl \
    model_examples/vehicle_fleet/vehicle-fleet-ontology.ttl \
    model_examples/vehicle_fleet/fleet-emissions-ontology.ttl \
    ai_generated_rules.yaml

# The AI will analyze ontologies and generate rules with:
# - Semantic class/property mappings
# - Automatic calculation inference (e.g., CO2 = fuel × emission_factor)
# - Aggregation rules (sum, count, average)
# - Lookup tables and constants
# - Transformation steps with reasoning
```

**AI Output Example:**
```
📋 CLASS MAPPINGS:
  ✓ Vehicle → VehicleEmission (95% confidence)
    Reasoning: Vehicle represents fleet vehicles that generate emissions

🔢 CALCULATIONS:
  • calculate_vehicle_emissions
    Formula: sum(fuel_amount * emission_factor)
    Reasoning: CO2 emissions from fuel consumption using standard factors

📊 AGGREGATIONS:
  • sum_fuel_consumed: Total fuel across all consumption records
  • count_vehicles: Number of vehicles in fleet
```

**Demo Mode (No API Key Required):**
```bash
# Run demonstration with mock AI responses
python demo_ai_rule_generator.py
```

See [AI_RULE_GENERATOR_README.md](AI_RULE_GENERATOR_README.md) for detailed documentation (Japanese).

**Comparison:**

| Feature | rule_generator.py | ai_rule_generator.py |
|---------|-------------------|----------------------|
| Class Mapping | String similarity | Semantic understanding |
| Property Mapping | Name matching | Meaning + type analysis |
| Calculations | ❌ None | ✅ Auto-inferred |
| Aggregations | ❌ None | ✅ Auto-inferred |
| Constants/Lookups | ❌ None | ✅ Suggested |
| Reasoning | ❌ No | ✅ Provided |
| API Key Required | No | Yes (Anthropic) |

### Manual Rule-Based Transformation

If you have hand-crafted rules, transform data directly:

```bash
python rule_engine.py transformation_rules.yaml input.json output.json
```

**Example:**
```bash
python rule_engine.py transformation_rules.yaml \
    test_data/source/sample1_small_factory.json \
    test_data/target/output1.json
```

**Output:**
```
Transformation complete: test_data/source/sample1_small_factory.json -> test_data/target/output1.json
  Rule file: transformation_rules.yaml
  Total emissions: 12175.5 kg-CO2
```

### Python API

```python
from rule_engine import RuleEngine
import json

# Load rule engine with rules file
engine = RuleEngine('transformation_rules.yaml')

# Read source data
with open('input.json', 'r') as f:
    source_data = json.load(f)

# Transform
result = engine.transform(source_data)

# Save result
with open('output.json', 'w') as f:
    json.dump(result, f, indent=2)

print(f"Total emissions: {result['total_emissions']} kg-CO2")
```

### Reusing for Different Domains (NEW Automatic Approach!)

The system is completely domain-agnostic! To transform ANY ontology pair:

#### Option 1: Fully Automatic (Recommended)
1. **Define your ontologies** (source and target in RDF/Turtle)
2. **Generate rules automatically**: `python rule_generator.py source.ttl target.ttl rules.yaml`
3. **Apply generated rules**: `python rule_engine.py rules.yaml input.json output.json`

**Zero code changes! Works for any domain!**

#### Option 2: Manual Rules
1. Define your ontologies
2. Manually create rules file (YAML)
3. Run the same engine: `python rule_engine.py your_rules.yaml input.json output.json`

### Proven Domains

The system has been tested with multiple domains:

| Domain | Source Ontology | Target Ontology | Status |
|--------|----------------|-----------------|---------|
| Manufacturing | Manufacturing activities | GHG emissions | ✅ Working |
| Vehicle Fleet | Fleet operations | Fleet emissions | ✅ Working |
| Your Domain | Any ontology | Any ontology | 🚀 Ready |

## Testing

### Run Rule Generation Tests (NEW!)

```bash
python test_rule_generation.py
```

**Expected output:** All 17 tests pass
- Ontology parsing and analysis
- Automatic class mapping inference
- Automatic property mapping inference
- Rule generation quality
- Complete pipeline tests

### Run Rule Engine Tests

```bash
python test_rule_engine.py
```

**Expected output:** All 16 tests pass
- Engine initialization and rule loading
- Constant and metadata access
- Transformations and calculations
- Integration tests with all sample files

### Run Domain-Specific Tests

```bash
python test_transformer.py
```

**Expected output:** All 21 tests pass (manufacturing domain)

## Transformation Rule Structure

### Rule File Anatomy

```yaml
metadata:
  name: "Transformation Name"
  version: "1.0"
  source_ontology: "http://example.org/source#"
  target_ontology: "http://example.org/target#"

constants:
  # Lookup tables, factors, classifications
  emission_factors:
    electricity: 0.500
    natural_gas: 2.03

field_mappings:
  # Direct field-to-field mappings
  - source_path: "organization.name"
    target_path: "reporting_organization.organization_name"

calculation_rules:
  # Formulas and computations
  - name: "calculate_co2_emission"
    formula: "energy_amount * emission_factor"

transformation_steps:
  # Ordered sequence of transformations
  - name: "transform_activities"
    source: "manufacturing_activities"
    target: "emissions"
```

### Adding New Energy Types

Edit `transformation_rules.yaml` - **no code changes needed**:

```yaml
constants:
  emission_factors:
    electricity: 0.500
    natural_gas: 2.03
    hydrogen: 0.000      # Add new fuel type
    biomass: 1.80        # Add new fuel type

  scope_classification:
    scope1:
      - natural_gas
      - biomass          # Classify as Scope 1
    scope2:
      - electricity
      - hydrogen         # Classify as Scope 2
```

### Customizing for Different Regions

Create region-specific rule files:

```bash
# US grid factors
python rule_engine.py rules_us.yaml input.json output.json

# EU grid factors
python rule_engine.py rules_eu.yaml input.json output.json

# Japan grid factors
python rule_engine.py rules_jp.yaml input.json output.json
```

## Sample Data and Results

### Sample 1: Small Factory
**Input:** 2 activities, electricity + natural gas
**Output:**
- Scope 1: 1,725.5 kg-CO2
- Scope 2: 10,450.0 kg-CO2
- **Total: 12,175.5 kg-CO2**

### Sample 2: Heavy Industry
**Input:** 2 activities, coal + electricity + natural gas + diesel
**Output:**
- Scope 1: 450,055.0 kg-CO2
- Scope 2: 22,500.0 kg-CO2
- **Total: 472,555.0 kg-CO2**

### Sample 3: Electronics Manufacturing
**Input:** 3 activities, electricity + LPG
**Output:**
- Scope 1: 1,812.0 kg-CO2
- Scope 2: 17,400.0 kg-CO2
- **Total: 19,212.0 kg-CO2**

## Data Format Specifications

### Input Format (Manufacturing Data - JSON-LD)

```json
{
  "@context": {
    "mfg": "http://example.org/manufacturing#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "organization": {
    "name": "Company Name"
  },
  "manufacturing_activities": [
    {
      "@type": "mfg:ManufacturingActivity",
      "activity_id": "ACT-2024-001",
      "activity_name": "Production Line A",
      "facility": "Factory Tokyo",
      "start_date": "2024-01-01",
      "end_date": "2024-01-31",
      "energy_consumptions": [
        {
          "@type": "mfg:EnergyConsumption",
          "energy_type": {
            "@type": "mfg:EnergyType",
            "name": "electricity"
          },
          "amount": 5000,
          "unit": "kWh"
        }
      ]
    }
  ]
}
```

### Output Format (GHG Report - JSON-LD)

```json
{
  "@context": {
    "ghg": "http://example.org/ghg-report#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "@type": "ghg:EmissionReport",
  "report_id": "GHG-CN-2024-01",
  "reporting_period": "2024-01",
  "report_date": "2025-11-11",
  "reporting_organization": {
    "@type": "ghg:Organization",
    "organization_name": "Company Name"
  },
  "emissions": [
    {
      "@type": "ghg:Scope2Emission",
      "emission_source": "Factory Tokyo - Production Line A",
      "source_category": "electricity",
      "co2_amount": 2500.0,
      "calculation_method": "Activity-based calculation using standard emission factors",
      "emission_factor": 0.5,
      "activity_data": {
        "activity_id": "ACT-2024-001",
        "energy_amount": 5000,
        "energy_unit": "kWh"
      }
    }
  ],
  "total_scope1": 0.0,
  "total_scope2": 2500.0,
  "total_emissions": 2500.0
}
```

## Design Decisions

### 1. Declarative Rules vs. Procedural Code
**Decision:** Use external YAML rules instead of hardcoded transformations

**Benefits:**
- Rules can be modified without changing code
- Same engine works for multiple ontology pairs
- Domain experts can modify rules without programming knowledge
- Version control for rules separate from code
- Easier testing and validation

### 2. Emission Factors
Standard emission factors are based on typical values from international GHG accounting standards. For production use:
- Use regional grid emission factors for electricity
- Update annually from official sources (EPA, IPCC, etc.)
- Consider supplier-specific factors when available

### 3. Scope Classification
Follows GHG Protocol Corporate Standard:
- **Scope 1**: Direct emissions from owned/controlled sources
- **Scope 2**: Indirect emissions from purchased electricity/heat/steam
- **Scope 3**: Not implemented (other indirect emissions)

### 4. Extensibility
The rule engine supports:
- Custom emission factors
- New energy types without code changes
- Complex calculation formulas
- Conditional logic and classifications
- Aggregations and rollups

## Automatic Rule Generation (How It Works)

The rule generator uses semantic analysis to automatically create transformation rules:

### Algorithm

1. **Parse Ontologies**: Load source and target ontologies using RDFLib
2. **Extract Structure**: Identify classes, properties, domains, ranges, and data types
3. **Infer Class Mappings**: Match classes using semantic similarity:
   - Exact name matches score 1.0
   - Substring matches score 0.7+
   - Word-based Jaccard similarity for related concepts
   - Threshold: 0.3 minimum similarity

4. **Infer Property Mappings**: Match properties within mapped classes:
   - Similar algorithm as class matching
   - Threshold: 0.4 minimum similarity
   - Considers property names and labels

5. **Generate Rules**: Create complete YAML rule set:
   - Field mappings for simple properties
   - Transformation steps for complex structures
   - Calculation rules for numeric properties
   - Constants and defaults

### Example: Vehicle Fleet → Emissions

**Input Ontologies:**
- Source: `fleet:Vehicle` with `fleet:vehicleId`, `fleet:vehicleType`
- Target: `femit:VehicleEmission` with `femit:vehicleId`, `femit:vehicleType`

**Generated Mappings:**
```
fleet:Vehicle → femit:VehicleEmission (0.85 similarity)
  fleet:vehicleId → femit:vehicleId (1.0 exact match)
  fleet:vehicleType → femit:vehicleType (1.0 exact match)

fleet:Organization → femit:ReportingOrganization (0.72 substring)
  fleet:organizationName → femit:organizationName (1.0 exact match)
```

**Result:** 2 class mappings, 3 property mappings → Complete transformation rules!

## Reusability Example (Manual Approach)

For complex transformations requiring custom logic:

1. **Create ontologies:**
   - `supply-chain-ontology.ttl`
   - `carbon-footprint-ontology.ttl`

2. **Either:** Generate rules automatically
   ```bash
   python rule_generator.py supply-chain-ontology.ttl carbon-footprint-ontology.ttl rules.yaml
   ```

3. **Or:** Create rules manually: `supply_chain_rules.yaml`
   ```yaml
   metadata:
     name: "Supply Chain to Carbon Footprint"
     source_ontology: "http://example.org/supply-chain#"
     target_ontology: "http://example.org/carbon-footprint#"

   constants:
     transport_factors:
       truck: 0.062  # kg-CO2/ton-km
       ship: 0.008
       airplane: 0.602

   calculation_rules:
     - name: "calculate_transport_emissions"
       formula: "distance * weight * transport_factor"
   ```

4. **Apply rules:**
   ```bash
   python rule_engine.py supply_chain_rules.yaml input.json output.json
   ```

**No changes to any Python code required!**

## Compliance

This implementation provides a foundation for GHG reporting. For regulatory compliance:

1. **Verify Emission Factors**: Use region-specific and annually updated factors
2. **Audit Trail**: Maintain detailed records of all inputs and calculations
3. **Third-Party Verification**: Consider external verification for official reporting
4. **Scope 3**: Add Scope 3 calculations as required by your reporting framework
5. **Rule Versioning**: Track rule file versions for audit purposes

## Standards Referenced

- [GHG Protocol Corporate Standard](https://ghgprotocol.org/corporate-standard) - Emissions calculation methodology
- [ISO 14064-1:2018](https://www.iso.org/standard/66453.html) - Greenhouse gases specification
- [W3C RDF 1.1 Turtle](https://www.w3.org/TR/turtle/) - Ontology format
- [W3C JSON-LD](https://www.w3.org/TR/json-ld/) - Instance data format

## Advantages of This MDA Approach

1. **Separation of Concerns**
   - Ontologies define structure
   - Rules define transformation logic
   - Engine provides execution

2. **Reusability**
   - Single engine for multiple transformations
   - Rules can be shared and versioned
   - Reduces development time for new transformations

3. **Maintainability**
   - Update emission factors without code changes
   - Easy to understand and modify rules
   - Clear traceability from ontology to output

4. **Testability**
   - Rule validation separate from engine testing
   - Easy to create test scenarios
   - Comprehensive test coverage

5. **Governance**
   - Rules can be reviewed by domain experts
   - Version control for rule changes
   - Audit trail for compliance

## Future Enhancements

- **Rule Validation**: Schema validation for rule files
- **Visual Rule Editor**: GUI for creating/editing rules
- **Rule Optimization**: Performance improvements for large datasets
- **Parallel Processing**: Multi-threaded transformation execution
- **Rule Composition**: Import and reuse rule fragments
- **Bidirectional Transformation**: Support reverse transformations

## License

This is a sample implementation for educational and demonstration purposes.

## Contributing

This project demonstrates MDA principles with a generic rule-based transformation engine. For production use, consider:
- Adding JSON Schema validation for rules
- Implementing comprehensive logging
- Adding database integration
- Creating REST API endpoints
- Implementing rule versioning system
- Adding data visualization dashboards

## Contact

For questions about this implementation, please refer to the project documentation or examine the rule files and engine code.
