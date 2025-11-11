# MDA-Based Data Transformation: Manufacturing to GHG Emission Report

## Overview

This project implements a **Model-Driven Architecture (MDA)** approach for transforming manufacturing activity data into GHG (Greenhouse Gas) emission reports. The transformation is rule-based and follows the ontology definitions specified in RDF/Turtle format.

## Architecture

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

The transformation engine (`transformer.py`) implements the following rules:

1. **Energy to Emissions Conversion**
   - Apply emission factors to convert energy consumption to CO2 equivalents
   - Standard emission factors (kg-CO2 per unit):
     - Electricity: 0.500 kg-CO2/kWh
     - Natural Gas: 2.03 kg-CO2/m³
     - Fuel Oil: 2.68 kg-CO2/liter
     - Diesel: 2.68 kg-CO2/liter
     - Gasoline: 2.31 kg-CO2/liter
     - LPG: 1.51 kg-CO2/kg
     - Coal: 2.42 kg-CO2/kg

2. **Scope Classification**
   - Scope 1 (Direct Emissions): Natural gas, fuel oil, diesel, gasoline, LPG, coal
   - Scope 2 (Indirect Emissions): Purchased electricity

3. **Aggregation**
   - Sum emissions by scope
   - Calculate total emissions across all activities
   - Group by reporting period

4. **Metadata Mapping**
   - Organization information mapping
   - Report ID generation
   - Reporting period determination from activity dates

## Project Structure

```
ccw-mda_sample1/
├── model/
│   ├── source/
│   │   └── manufacturing-ontology.ttl    # Source RDF ontology
│   └── target/
│       └── ghg-report-ontology.ttl       # Target RDF ontology
├── test_data/
│   ├── source/                           # Sample input JSON files
│   │   ├── sample1_small_factory.json
│   │   ├── sample2_multi_fuel.json
│   │   └── sample3_electronics.json
│   └── target/                           # Generated output files
├── transformer.py                        # Main transformation engine
├── test_transformer.py                   # Comprehensive test suite
├── instructions.md                       # Project instructions
└── README.md                             # This file
```

## Installation

### Prerequisites
- Python 3.7 or higher

### Setup
No external dependencies required for the core transformation. The implementation uses only Python standard library.

```bash
cd ccw-mda_sample1
```

## Usage

### Command Line Interface

Transform a single file:

```bash
python transformer.py <input_json> <output_json>
```

Example:
```bash
python transformer.py test_data/source/sample1_small_factory.json test_data/target/output1.json
```

### Python API

```python
from transformer import ManufacturingToGHGTransformer

# Create transformer instance
transformer = ManufacturingToGHGTransformer()

# Load source data
import json
with open('input.json', 'r') as f:
    source_data = json.load(f)

# Transform
result = transformer.transform(source_data)

# Save result
with open('output.json', 'w') as f:
    json.dump(result, f, indent=2)
```

## Testing

### Run All Tests

```bash
python test_transformer.py
```

### Test Coverage

The test suite includes:

1. **Unit Tests**
   - Emission factor lookups
   - Scope classification
   - Energy type normalization (case-insensitive, space handling)

2. **Transformation Tests**
   - Simple single-activity transformation
   - Multi-activity aggregation
   - Multiple energy types per activity
   - Scope 1 and Scope 2 classification

3. **Integration Tests**
   - Sample 1: Small factory with electricity and natural gas
   - Sample 2: Heavy industry with coal, electricity, natural gas, and diesel
   - Sample 3: Electronics manufacturing with electricity and LPG

4. **Validation Tests**
   - Missing organization data
   - Empty activities
   - Zero energy consumption
   - Activities without energy consumption

### Expected Test Results

All tests should pass with the following emission calculations:

**Sample 1 (Small Factory):**
- Scope 1: 1,725.5 kg-CO2
- Scope 2: 10,450.0 kg-CO2
- Total: 12,175.5 kg-CO2

**Sample 2 (Multi-Fuel Heavy Industry):**
- Scope 1: 450,055.0 kg-CO2
- Scope 2: 22,500.0 kg-CO2
- Total: 472,555.0 kg-CO2

**Sample 3 (Electronics):**
- Scope 1: 1,812.0 kg-CO2
- Scope 2: 17,400.0 kg-CO2
- Total: 19,212.0 kg-CO2

## Sample Data Format

### Input Format (Manufacturing Data)

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
      "produces": {
        "@type": "mfg:Product",
        "product_name": "Widget",
        "quantity": 1000,
        "unit": "pieces"
      },
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

### Output Format (GHG Report)

```json
{
  "@context": {
    "ghg": "http://example.org/ghg-report#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "@type": "ghg:EmissionReport",
  "report_id": "GHG-CN-2024-01",
  "reporting_period": "2024-01",
  "report_date": "2024-11-11",
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
        "energy_unit": "kWh",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31"
      }
    }
  ],
  "total_scope1": 0.0,
  "total_scope2": 2500.0,
  "total_emissions": 2500.0
}
```

## Design Decisions

### 1. Emission Factors
Standard emission factors are based on typical values from international GHG accounting standards. For production use, these should be updated with:
- Regional grid emission factors for electricity
- Supplier-specific emission factors
- Annually updated values from official sources

### 2. Scope Classification
The implementation follows the GHG Protocol Corporate Standard:
- **Scope 1**: Direct emissions from owned or controlled sources
- **Scope 2**: Indirect emissions from purchased electricity, heat, or steam
- **Scope 3**: Not implemented (all other indirect emissions)

### 3. Calculation Method
Uses activity-based calculation:
```
CO2 Emissions = Energy Consumption × Emission Factor
```

### 4. Data Validation
Basic validation is performed:
- Missing data defaults to safe values
- Unknown energy types result in zero emissions (should be logged)
- Empty activities are handled gracefully

## Extending the Transformation

### Adding New Energy Types

```python
# In transformer.py, update EmissionFactors.FACTORS
FACTORS = {
    # ... existing factors ...
    "new_fuel_type": 2.5,  # kg-CO2/unit
}

# Update scope classification if needed
SCOPE_1_TYPES = ["natural_gas", ..., "new_fuel_type"]
```

### Custom Emission Factors

```python
transformer = ManufacturingToGHGTransformer()
# Override default factors
transformer.emission_factors.FACTORS["electricity"] = 0.6  # Regional factor
```

### Adding Scope 3 Emissions

Extend the `Emission` class hierarchy and update transformation rules to handle:
- Transportation
- Waste disposal
- Business travel
- Employee commuting

## Compliance

This implementation provides a foundation for GHG reporting. For regulatory compliance:

1. **Verify Emission Factors**: Use region-specific and annually updated factors
2. **Audit Trail**: Maintain detailed records of all inputs and calculations
3. **Third-Party Verification**: Consider external verification for official reporting
4. **Scope 3**: Add Scope 3 calculations as required by your reporting framework

## Standards Referenced

- [GHG Protocol Corporate Standard](https://ghgprotocol.org/corporate-standard)
- [ISO 14064-1:2018](https://www.iso.org/standard/66453.html) - Greenhouse gases specification
- [W3C RDF 1.1 Turtle](https://www.w3.org/TR/turtle/) - Ontology format

## License

This is a sample implementation for educational and demonstration purposes.

## Contributing

This project demonstrates MDA principles. For production use, consider:
- Adding JSON Schema validation
- Implementing logging and error handling
- Adding database integration
- Creating web API endpoints
- Implementing audit trails
- Adding data visualization

## Contact

For questions about this implementation, please refer to the project documentation.
