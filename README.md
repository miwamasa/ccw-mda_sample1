# MDA-Based Data Transformation: Manufacturing to GHG Emission Report

## Overview

This project implements a **Model-Driven Architecture (MDA)** approach for transforming manufacturing activity data into GHG (Greenhouse Gas) emission reports. The key feature is a **generic, reusable rule-based transformation engine** that reads declarative transformation rules from external configuration files, making it adaptable to different ontology pairs without code changes.

## Key Features

- **Declarative Rule Definition**: Transformation logic defined in external YAML files, not hardcoded
- **Generic Transformation Engine**: Reusable engine that can be applied to different model transformations
- **Model-Agnostic Design**: Change ontology mappings by updating rules, not code
- **Standards-Based**: Follows GHG Protocol Corporate Standard for emissions reporting
- **Comprehensive Testing**: 16+ tests covering engine functionality and transformation accuracy

## Architecture

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  1. Ontology Layer (RDF/Turtle)                             │
│     - Source: manufacturing-ontology.ttl                     │
│     - Target: ghg-report-ontology.ttl                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2. Rule Layer (Declarative YAML)                           │
│     - transformation_rules.yaml                             │
│     - Constants (emission factors, classifications)         │
│     - Field mappings                                        │
│     - Calculation rules                                     │
│     - Aggregation rules                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3. Engine Layer (Generic Python)                           │
│     - rule_engine.py (model-agnostic transformer)           │
│     - Reads and interprets rules                            │
│     - Applies transformations                               │
│     - Can be reused for ANY ontology pair                   │
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
├── transformation_rules.yaml             # Declarative transformation rules
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

### Setup
```bash
cd ccw-mda_sample1
pip install pyyaml
```

## Usage

### Rule-Based Transformation (Recommended)

Transform data using declarative rules:

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

### Reusing the Engine for Different Ontologies

The engine is completely generic! To transform different ontology pairs:

1. **Define your ontologies** (source and target in RDF/Turtle)
2. **Create a rules file** (YAML) defining mappings and calculations
3. **Run the same engine**: `python rule_engine.py your_rules.yaml input.json output.json`

**No code changes required!**

## Testing

### Run Rule Engine Tests

```bash
python test_rule_engine.py
```

**Expected output:** All 16 tests pass
- Engine initialization and rule loading
- Constant and metadata access
- Transformations and calculations
- Integration tests with all sample files

### Run Legacy Tests

```bash
python test_transformer.py
```

**Expected output:** All 21 tests pass (backward compatibility)

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

## Reusability Example

To create a transformation for a **different domain** (e.g., Supply Chain to Carbon Footprint):

1. **Create ontologies:**
   - `supply-chain-ontology.ttl`
   - `carbon-footprint-ontology.ttl`

2. **Create rules file:** `supply_chain_rules.yaml`
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

   # ... etc ...
   ```

3. **Use the same engine:**
   ```bash
   python rule_engine.py supply_chain_rules.yaml input.json output.json
   ```

**No changes to `rule_engine.py` required!**

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
