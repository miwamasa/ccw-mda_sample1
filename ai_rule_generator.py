"""
AI-Powered Transformation Rule Generator

Uses Claude AI to analyze ontologies and generate intelligent transformation rules
including mappings, aggregations, and calculations.
"""

import os
import yaml
import json
from typing import Dict, List, Any, Optional
from rule_generator import OntologyAnalyzer
import anthropic


class AIRuleGenerator:
    """
    AI-powered rule generator that uses Claude to understand ontologies
    and generate intelligent transformation rules.
    """

    def __init__(self, source_ontology: str, target_ontology: str, api_key: Optional[str] = None, verify_ssl: bool = True):
        """
        Initialize AI rule generator.

        Args:
            source_ontology: Path to source ontology TTL file
            target_ontology: Path to target ontology TTL file
            api_key: Anthropic API key (or use ANTHROPIC_API_KEY env var)
            verify_ssl: Whether to verify SSL certificates (default: True)
                       Set to False if you have SSL certificate issues in corporate environments
        """
        self.source_analyzer = OntologyAnalyzer(source_ontology)
        self.target_analyzer = OntologyAnalyzer(target_ontology)

        # Initialize Anthropic client
        api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable or api_key parameter required")

        # Configure httpx client with SSL settings
        import httpx
        http_client = httpx.Client(verify=verify_ssl)
        self.client = anthropic.Anthropic(api_key=api_key, http_client=http_client)

        self.ai_suggestions = None

    def _extract_ontology_structure(self, analyzer: OntologyAnalyzer, ontology_name: str) -> Dict[str, Any]:
        """Extract ontology structure for AI analysis."""
        structure = {
            "ontology_name": ontology_name,
            "namespace": analyzer.namespace,
            "classes": []
        }

        for cls in analyzer.classes:
            cls_info = {
                "name": analyzer.get_label(cls),
                "uri": str(cls),
                "properties": []
            }

            # Get properties for this class
            props = analyzer.get_class_properties(cls)
            for prop in props:
                prop_info = analyzer.properties.get(prop, {})
                cls_info["properties"].append({
                    "name": analyzer.get_label(prop),
                    "uri": str(prop),
                    "type": prop_info.get('type'),
                    "range": str(prop_info.get('range')) if prop_info.get('range') else None
                })

            structure["classes"].append(cls_info)

        return structure

    def analyze_with_ai(self) -> Dict[str, Any]:
        """
        Use Claude AI to analyze ontologies and suggest transformation rules.

        Returns:
            Dictionary containing AI suggestions for mappings, calculations, and aggregations
        """
        # Extract ontology structures
        source_structure = self._extract_ontology_structure(self.source_analyzer, "Source")
        target_structure = self._extract_ontology_structure(self.target_analyzer, "Target")

        # Create prompt for Claude
        prompt = self._create_analysis_prompt(source_structure, target_structure)

        print("\n" + "=" * 70)
        print("AI ANALYSIS IN PROGRESS")
        print("=" * 70)
        print("Analyzing ontologies with Claude AI...")
        print(f"Source: {source_structure['namespace']}")
        print(f"Target: {target_structure['namespace']}")

        # Call Claude API with error handling
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
        except anthropic.APIConnectionError as e:
            print("\n" + "=" * 70)
            print("❌ API CONNECTION ERROR")
            print("=" * 70)
            print("\nSSL証明書エラーが発生しました。")
            print("\n解決方法:")
            print("1. 企業プロキシ環境の場合、SSL検証を無効化:")
            print("   python ai_rule_generator.py --no-verify-ssl source.ttl target.ttl output.yaml")
            print("\n2. または、デモモードを使用:")
            print("   python demo_ai_rule_generator.py")
            print("\n3. または、Pythonコードで:")
            print("   generator = AIRuleGenerator(source, target, verify_ssl=False)")
            print("\n元のエラー:", str(e))
            print("=" * 70)
            raise
        except Exception as e:
            print("\n" + "=" * 70)
            print("❌ API ERROR")
            print("=" * 70)
            print(f"Error: {type(e).__name__}: {str(e)}")
            print("=" * 70)
            raise

        # Parse AI response
        response_text = message.content[0].text

        print("\n" + "=" * 70)
        print("AI ANALYSIS COMPLETE")
        print("=" * 70)

        # Parse the JSON response from AI
        try:
            # Extract JSON from response (might be wrapped in markdown code blocks)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text

            suggestions = json.loads(json_text)
            self.ai_suggestions = suggestions

            return suggestions

        except json.JSONDecodeError as e:
            print(f"Error parsing AI response: {e}")
            print(f"Response: {response_text[:500]}...")
            raise

    def _create_analysis_prompt(self, source_structure: Dict, target_structure: Dict) -> str:
        """Create prompt for AI analysis."""
        prompt = f"""You are an expert in ontology mapping and data transformation. Analyze these two ontologies and suggest transformation rules.

CRITICAL: JSON-LD Field Naming and Structure Rules
==================================================

1. NAMING CONVENTION CONVERSION:
   - Ontology properties: camelCase (e.g., hasEnergyConsumption, activityName)
   - JSON-LD instance fields: snake_case (e.g., energy_consumptions, activity_name)
   - ALWAYS convert camelCase → snake_case in your field mappings

2. ARRAY PROPERTY NAMING:
   - Ontology: has + Name → JSON-LD: pluralized array
   - hasEnergyConsumption → energy_consumptions
   - hasEmission → emissions
   - hasActivity → activities

3. NESTED OBJECT SIMPLIFICATION:
   - Inside nested objects, remove redundant prefixes
   - energyTypeName (in energy_type object) → name
   - organizationName (in organization object) → organization_name (at root) OR name (inside organization object)
   - Context makes the field clear, so simplify when nested

4. COMPLETE NAMING EXAMPLES:
   Ontology Property         →  JSON-LD Field
   ==========================================
   activityId               →  activity_id
   activityName             →  activity_name
   hasEnergyConsumption     →  energy_consumptions (array)
   energyTypeName           →  name (inside energy_type object)
   reportingOrganization    →  reporting_organization (object)
   organizationName         →  organization_name
   totalEmissions           →  total_emissions
   co2Amount                →  co2_amount
   emissionSource           →  emission_source
   calculationMethod        →  calculation_method

5. DATA STRUCTURE PATTERNS:

   Pattern A - DatatypeProperty:
   Ontology: mfg:activityId (xsd:string)
   JSON-LD:  "activity_id": "ACT-2024-001"

   Pattern B - ObjectProperty (single):
   Ontology: mfg:produces → mfg:Product
   JSON-LD:  "produces": {{"@type": "mfg:Product", "product_name": "Widget", "quantity": 5000}}

   Pattern C - ObjectProperty (array):
   Ontology: mfg:hasEnergyConsumption → mfg:EnergyConsumption
   JSON-LD:  "energy_consumptions": [{{"@type": "mfg:EnergyConsumption", ...}}, {{...}}]

   Pattern D - Nested object simplification:
   Ontology: mfg:energyType → mfg:EnergyType with mfg:energyTypeName
   JSON-LD:  "energy_type": {{"@type": "mfg:EnergyType", "name": "electricity"}}
             (Note: energyTypeName becomes just "name" inside energy_type object)

6. COMPLETE STRUCTURE EXAMPLE:

   Source JSON-LD (Manufacturing):
   {{
     "manufacturing_activities": [
       {{
         "@type": "mfg:ManufacturingActivity",
         "activity_id": "ACT-2024-001",
         "activity_name": "Widget Assembly",
         "energy_consumptions": [
           {{
             "@type": "mfg:EnergyConsumption",
             "energy_type": {{
               "@type": "mfg:EnergyType",
               "name": "electricity"
             }},
             "amount": 12500,
             "unit": "kWh"
           }}
         ]
       }}
     ]
   }}

   Target JSON-LD (GHG Report):
   {{
     "@type": "ghg:EmissionReport",
     "report_id": "GHG-2024-01",
     "emissions": [
       {{
         "@type": "ghg:Scope2Emission",
         "emission_source": "Widget Assembly",
         "source_category": "electricity",
         "co2_amount": 6250.0
       }}
     ],
     "total_emissions": 6250.0
   }}

SOURCE ONTOLOGY:
{json.dumps(source_structure, indent=2)}

TARGET ONTOLOGY:
{json.dumps(target_structure, indent=2)}

Your task:
1. Identify class mappings between source and target ontologies
2. For each class mapping, identify property mappings using snake_case field names
3. Identify nested array iterations (e.g., energy_consumptions within manufacturing_activities)
4. Identify calculations (e.g., amount × emission_factor = co2_amount)
5. Identify aggregations (e.g., sum of all co2_amount → total_emissions)
6. Provide emission factors as constants (electricity: 0.5, natural_gas: 2.03, diesel: 2.68 kg-CO2/unit)

CRITICAL REQUIREMENTS:
- Use snake_case for ALL field names in your response
- Use plural forms for array fields (activities, consumptions, emissions)
- Include substeps with actual field mappings in transformation_steps
- Do NOT leave substeps empty
- Specify which fields to iterate over (e.g., "$.energy_consumptions")

Respond with a JSON object in this format:
{{
  "class_mappings": [
    {{
      "source_class": "ClassName",
      "target_class": "TargetClassName",
      "confidence": 0.95,
      "reasoning": "explanation of why these classes map"
    }}
  ],
  "property_mappings": [
    {{
      "source_class": "ClassName",
      "target_class": "TargetClassName",
      "mappings": [
        {{
          "source_property": "propertyName",
          "target_property": "targetPropertyName",
          "mapping_type": "direct|calculation|aggregation",
          "confidence": 0.90,
          "reasoning": "explanation"
        }}
      ]
    }}
  ],
  "calculations": [
    {{
      "name": "calculation_name",
      "description": "what this calculates",
      "source_class": "ClassName",
      "target_property": "targetProperty",
      "formula": "description of calculation",
      "inputs": ["input1", "input2"],
      "reasoning": "why this calculation is needed"
    }}
  ],
  "aggregations": [
    {{
      "name": "aggregation_name",
      "description": "what to aggregate",
      "source_class": "ClassName",
      "source_property": "arrayProperty",
      "target_property": "targetTotal",
      "function": "sum|count|average",
      "field": "fieldToAggregate",
      "reasoning": "why this aggregation is needed"
    }}
  ],
  "constants": {{
    "lookup_tables": [
      {{
        "name": "table_name",
        "description": "what this table is for",
        "example_values": {{"key1": "value1"}}
      }}
    ]
  }},
  "transformation_steps": [
    {{
      "step": 1,
      "name": "transform_activities_to_emissions",
      "description": "Transform manufacturing activities to emissions",
      "source": "manufacturing_activities",
      "target": "emissions",
      "iteration": true,
      "substeps": [
        {{
          "name": "iterate_energy_consumptions",
          "description": "Iterate over energy_consumptions array",
          "source": "$.energy_consumptions",
          "iteration": true,
          "substeps": [
            {{
              "name": "map_fields",
              "field_mappings": [
                {{
                  "target": "emission_source",
                  "source": "$.activity_name"
                }},
                {{
                  "target": "source_category",
                  "source": "$.energy_type.name"
                }}
              ]
            }},
            {{
              "name": "calculate_emissions",
              "calculation": "calculate_co2",
              "inputs": {{
                "amount": "$.amount",
                "energy_type": "$.energy_type.name"
              }}
            }}
          ]
        }}
      ]
    }}
  ]
}}

CRITICAL: Every transformation_step MUST include substeps with actual field mappings or calculations.
DO NOT generate empty substeps arrays. Show the complete mapping chain from source to target.

Focus on practical, implementable transformations. Be specific about field names and calculations."""

        return prompt

    def display_suggestions(self):
        """Display AI suggestions in a readable format."""
        if not self.ai_suggestions:
            print("No AI suggestions available. Run analyze_with_ai() first.")
            return

        suggestions = self.ai_suggestions

        print("\n" + "=" * 70)
        print("AI TRANSFORMATION SUGGESTIONS")
        print("=" * 70)

        # Display class mappings
        print("\n📋 CLASS MAPPINGS:")
        for mapping in suggestions.get('class_mappings', []):
            print(f"  ✓ {mapping['source_class']} → {mapping['target_class']}")
            print(f"    Confidence: {mapping.get('confidence', 0):.0%}")
            print(f"    Reasoning: {mapping.get('reasoning', 'N/A')}")

        # Display property mappings
        print("\n📋 PROPERTY MAPPINGS:")
        current_class = None
        for prop_mapping in suggestions.get('property_mappings', []):
            class_pair = f"{prop_mapping['source_class']} → {prop_mapping['target_class']}"
            if class_pair != current_class:
                print(f"\n  For {class_pair}:")
                current_class = class_pair

            # Handle nested mappings structure
            for mapping in prop_mapping.get('mappings', []):
                mapping_type = mapping.get('mapping_type', 'direct')
                icon = "🔢" if mapping_type == 'calculation' else "📊" if mapping_type == 'aggregation' else "→"
                print(f"    {icon} {mapping['source_property']} → {mapping['target_property']} ({mapping_type})")
                if mapping.get('transformation') and mapping['transformation'] != 'none':
                    print(f"       Transformation: {mapping['transformation']}")
                if mapping.get('notes'):
                    print(f"       Notes: {mapping['notes']}")

        # Display calculations
        if suggestions.get('calculations'):
            print("\n🔢 CALCULATIONS:")
            for calc in suggestions['calculations']:
                print(f"  • {calc['name']}: {calc['description']}")
                print(f"    Formula: {calc.get('formula', 'N/A')}")
                print(f"    Inputs: {', '.join(calc.get('inputs', []))}")
                print(f"    Reasoning: {calc.get('reasoning', 'N/A')}")

        # Display aggregations
        if suggestions.get('aggregations'):
            print("\n📊 AGGREGATIONS:")
            for agg in suggestions['aggregations']:
                print(f"  • {agg['name']}: {agg.get('description', 'N/A')}")
                source_field = agg.get('source_field', 'N/A')
                print(f"    Function: {agg['function']}({source_field})")
                source_path = agg.get('source_path', 'N/A')
                print(f"    Source: {source_path}")
                print(f"    Target: {agg.get('target_field', 'N/A')}")
                if agg.get('reasoning'):
                    print(f"    Reasoning: {agg['reasoning']}")

        # Display constants
        if suggestions.get('constants', {}).get('lookup_tables'):
            print("\n📚 LOOKUP TABLES:")
            for table in suggestions['constants']['lookup_tables']:
                print(f"  • {table['name']}: {table['description']}")
                if table.get('example_values'):
                    print(f"    Examples: {table['example_values']}")

        # Display transformation steps
        if suggestions.get('transformation_steps'):
            print("\n🔄 TRANSFORMATION STEPS:")
            for idx, step in enumerate(suggestions['transformation_steps'], 1):
                order = step.get('order', idx)
                print(f"  {order}. {step['name']}")
                print(f"     {step.get('description', 'N/A')}")
                source = step.get('source', 'N/A')
                target = step.get('target', 'N/A')
                print(f"     {source} → {target}")
                if step.get('reasoning'):
                    print(f"     Reasoning: {step['reasoning']}")

        print("\n" + "=" * 70)

    def generate_rules(self) -> Dict[str, Any]:
        """
        Generate transformation rules based on AI suggestions.

        Returns:
            Dictionary containing transformation rules in YAML format
        """
        if not self.ai_suggestions:
            raise ValueError("No AI suggestions available. Run analyze_with_ai() first.")

        suggestions = self.ai_suggestions

        # Build rules structure
        rules = {
            'metadata': {
                'name': 'AI-Generated Transformation',
                'version': '1.0',
                'source_ontology': self.source_analyzer.namespace,
                'target_ontology': self.target_analyzer.namespace,
                'description': 'Transformation rules generated by Claude AI',
                'generated_by': 'AI',
                'ai_model': 'claude-sonnet-4'
            },
            'constants': self._generate_constants(suggestions),
            'root_mapping': self._generate_root_mapping(suggestions),
            'field_mappings': self._generate_field_mappings(suggestions),
            'calculation_rules': self._generate_calculation_rules(suggestions),
            'transformation_steps': self._generate_transformation_steps(suggestions),
            'options': {
                'preserve_source_context': True,
                'case_sensitive': False,
                'null_handling': 'use_defaults'
            }
        }

        return rules

    def _generate_constants(self, suggestions: Dict) -> Dict:
        """Generate constants section from AI suggestions."""
        constants = {
            'defaults': {
                'unknown_value': 'Unknown'
            }
        }

        # Handle constants provided directly (like fuel_emission_factors)
        ai_constants = suggestions.get('constants', {})
        for key, value in ai_constants.items():
            if key != 'description' and isinstance(value, dict):
                constants[key] = value

        # Add lookup tables if provided in nested structure
        for table in ai_constants.get('lookup_tables', []):
            table_name = table['name'].replace(' ', '_').lower()
            constants[table_name] = table.get('example_values', {})

        # Auto-add emission_factors if not present
        if 'emission_factors' not in constants:
            constants['emission_factors'] = {
                'electricity': 0.5,
                'natural_gas': 2.03,
                'diesel': 2.68,
                'gasoline': 2.31,
                'fuel_oil': 2.68,
                'lpg': 1.51,
                'coal': 2.42
            }

        # Auto-add scope_classification if not present
        if 'scope_classification' not in constants:
            constants['scope_classification'] = {
                'scope1': ['natural_gas', 'diesel', 'gasoline', 'fuel_oil', 'lpg', 'coal'],
                'scope2': ['electricity']
            }

        return constants

    def _generate_root_mapping(self, suggestions: Dict) -> Dict:
        """Generate root mapping from AI suggestions."""
        # Find the root target class (often EmissionsReport, Report, etc.)
        target_classes = [m['target_class'] for m in suggestions.get('class_mappings', [])]

        # Heuristic: root class often contains "Report" or is the first one
        root_class = target_classes[0] if target_classes else "EmissionReport"

        # Determine namespace prefix
        namespace = self.target_analyzer.namespace
        prefix = 'ghg' if 'ghg' in namespace else 'target'

        return {
            'target_type': f'{prefix}:{root_class.replace(" ", "")}',
            'target_context': {
                prefix: namespace,
                'xsd': 'http://www.w3.org/2001/XMLSchema#'
            }
        }

    def _generate_field_mappings(self, suggestions: Dict) -> List[Dict]:
        """Generate field mappings from AI suggestions."""
        mappings = []

        for prop_group in suggestions.get('property_mappings', []):
            # Handle nested mappings structure
            for prop_mapping in prop_group.get('mappings', []):
                # Only include direct mappings in field_mappings
                # Calculations and aggregations are handled separately
                if prop_mapping.get('mapping_type', 'direct') == 'direct':
                    source_prop = prop_mapping['source_property'].replace(' ', '_').lower()
                    target_prop = prop_mapping['target_property'].replace(' ', '_').lower()

                    mappings.append({
                        'source_path': source_prop,
                        'target_path': target_prop,
                        'default': '${constants.defaults.unknown_value}'
                    })

        return mappings

    def _generate_calculation_rules(self, suggestions: Dict) -> List[Dict]:
        """Generate calculation rules from AI suggestions."""
        calc_rules = []

        for calc in suggestions.get('calculations', []):
            rule = {
                'name': calc.get('name', '').replace(' ', '_').lower(),
                'description': calc.get('description', ''),
                'input': {},
                'formula': calc.get('formula', ''),
                'output': calc.get('output', calc.get('target_property', '')).replace(' ', '_').lower()
            }

            # Add inputs
            for i, input_name in enumerate(calc.get('inputs', [])):
                rule['input'][f'input{i+1}'] = f'$.{input_name.replace(" ", "_").lower()}'

            calc_rules.append(rule)

        # Auto-add essential calculation rules if not present
        calc_rule_names = {r['name'] for r in calc_rules}

        # Add CO2 emission calculation if not present
        if 'calculate_co2_emission' not in calc_rule_names and 'calculate_co2_emissions' not in calc_rule_names:
            calc_rules.append({
                'name': 'calculate_co2_emission',
                'description': 'Convert energy consumption to CO2 emissions',
                'input': {
                    'energy_amount': '$.amount',
                    'energy_type': '$.energy_type.name'
                },
                'formula': 'energy_amount * emission_factor',
                'lookup': {
                    'emission_factor': {
                        'source': 'constants.emission_factors',
                        'key': 'energy_type',
                        'key_transform': 'lowercase_underscore',
                        'default': 0.0
                    }
                },
                'output': 'co2_amount',
                'rounding': 2
            })

        # Add scope determination if not present
        if 'determine_scope' not in calc_rule_names:
            calc_rules.append({
                'name': 'determine_scope',
                'description': 'Classify emission into Scope 1 or Scope 2',
                'input': {
                    'energy_type': '$.energy_type.name'
                },
                'logic': [
                    {
                        'condition': {
                            'key_transform': 'lowercase_underscore',
                            'check': 'energy_type in constants.scope_classification.scope1'
                        },
                        'output': 1
                    },
                    {
                        'condition': {
                            'key_transform': 'lowercase_underscore',
                            'check': 'energy_type in constants.scope_classification.scope2'
                        },
                        'output': 2
                    },
                    {
                        'default': 1
                    }
                ],
                'output': 'scope'
            })

        return calc_rules

    def _auto_generate_substeps(self, step: Dict, suggestions: Dict) -> List[Dict]:
        """
        Auto-generate substeps for transformation steps when AI doesn't provide them.
        Uses domain knowledge about manufacturing → GHG transformation patterns.
        """
        substeps = []
        source = step.get('source', '')
        target = step.get('target', '')

        # Pattern 1: manufacturing_activities → emissions
        # Need to iterate over energy_consumptions within each activity
        if 'activit' in source and 'emission' in target:
            substeps.append({
                'name': 'iterate_energy_consumptions',
                'description': 'Process each energy consumption in the activity',
                'source': '$.energy_consumptions',
                'iteration': True,
                'mapping': [
                    {
                        'target': 'emission_source',
                        'source': '$.activity_name',
                        'context': 'parent'
                    },
                    {
                        'target': 'source_category',
                        'source': '$.energy_type.name'
                    },
                    {
                        'target': '@type',
                        'calculation': 'determine_scope',
                        'format': 'ghg:Scope{scope}Emission'
                    },
                    {
                        'target': 'co2_amount',
                        'calculation': 'calculate_co2_emission'
                    },
                    {
                        'target': 'calculation_method',
                        'fixed_value': 'Activity-based calculation using standard emission factors'
                    },
                    {
                        'target': 'emission_factor',
                        'lookup': {
                            'source': 'constants.emission_factors',
                            'key': '$.energy_type.name',
                            'key_transform': 'lowercase_underscore'
                        }
                    }
                ]
            })

        # Pattern 2: Extract organization info
        elif 'organization' in target:
            substeps.append({
                'name': 'map_organization_fields',
                'mapping': [
                    {
                        'target': 'organization_name',
                        'source': 'organization.name',
                        'default': 'Unknown Organization'
                    },
                    {
                        'target': '@type',
                        'fixed_value': 'ghg:Organization'
                    }
                ]
            })

        # Pattern 3: Generic field mapping fallback
        else:
            # Try to find property mappings for this step
            source_class = source.replace('_', ' ').title().rstrip('s')  # Remove plural
            mappings = []

            for prop_group in suggestions.get('property_mappings', []):
                if source_class.lower() in prop_group.get('source_class', '').lower():
                    for mapping in prop_group.get('mappings', []):
                        if mapping.get('mapping_type', 'direct') == 'direct':
                            mappings.append({
                                'target': mapping['target_property'].replace(' ', '_').lower(),
                                'source': mapping['source_property'].replace(' ', '_').lower()
                            })

            if mappings:
                substeps.append({
                    'name': f'map_{step["name"]}_fields',
                    'mapping': mappings
                })

        return substeps

    def _generate_transformation_steps(self, suggestions: Dict) -> List[Dict]:
        """Generate transformation steps from AI suggestions."""
        steps = []

        for step_info in suggestions.get('transformation_steps', []):
            step = {
                'name': step_info.get('name', '').replace(' ', '_').lower(),
                'description': step_info.get('description', ''),
                'source': step_info.get('source', '').replace(' ', '_').lower(),
                'target': step_info.get('target', '').replace(' ', '_').lower(),
                'iteration': step_info.get('iteration', True),
                'substeps': []
            }

            # Check for substeps in AI response first
            ai_substeps = step_info.get('substeps', [])
            if ai_substeps:
                # Use AI-provided substeps if available
                step['substeps'] = ai_substeps
            else:
                # Auto-generate substeps for known patterns
                step['substeps'] = self._auto_generate_substeps(step, suggestions)

            steps.append(step)

        # Add aggregation step if there are aggregations
        if suggestions.get('aggregations'):
            agg_step = {
                'name': 'calculate_aggregations',
                'description': 'Calculate aggregated values',
                'aggregations': []
            }

            for agg in suggestions['aggregations']:
                # Determine source for aggregation
                source_class = agg.get('source_class', '').replace(' ', '_').lower()
                if source_class:
                    source = source_class + 's' if not source_class.endswith('s') else source_class
                else:
                    # Default to 'emissions' for GHG reports
                    source = 'emissions'

                agg_step['aggregations'].append({
                    'name': agg['name'].replace(' ', '_').lower(),
                    'source': source,
                    'aggregate': {
                        'function': agg['function'],
                        'field': agg.get('field', '').replace(' ', '_').lower()
                    },
                    'rounding': 2,
                    'target': agg.get('target_property', '').replace(' ', '_').lower()
                })

            steps.append(agg_step)

        return steps

    def save_rules(self, output_file: str):
        """Save generated rules to YAML file."""
        rules = self.generate_rules()

        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(rules, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        print(f"\n✅ AI-generated rules saved to: {output_file}")


def generate_rules_with_ai(
    source_ontology: str,
    target_ontology: str,
    output_file: str,
    api_key: Optional[str] = None,
    verify_ssl: bool = True
):
    """
    Generate transformation rules using AI analysis.

    Args:
        source_ontology: Path to source ontology TTL file
        target_ontology: Path to target ontology TTL file
        output_file: Path to output YAML rules file
        api_key: Anthropic API key (optional, uses env var if not provided)
        verify_ssl: Whether to verify SSL certificates (default: True)
    """
    generator = AIRuleGenerator(source_ontology, target_ontology, api_key, verify_ssl=verify_ssl)

    # Analyze with AI
    generator.analyze_with_ai()

    # Display suggestions
    generator.display_suggestions()

    # Generate and save rules
    generator.save_rules(output_file)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="AI-powered transformation rule generator for RDF ontologies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (SSL verification enabled):
  python ai_rule_generator.py source.ttl target.ttl output.yaml

  # Disable SSL verification (for corporate proxy environments):
  python ai_rule_generator.py --no-verify-ssl source.ttl target.ttl output.yaml

  # With explicit API key:
  python ai_rule_generator.py source.ttl target.ttl output.yaml --api-key YOUR_KEY

  # If you have SSL issues, consider using the demo instead:
  python demo_ai_rule_generator.py
"""
    )

    parser.add_argument(
        "source_ontology",
        help="Path to source ontology TTL file"
    )
    parser.add_argument(
        "target_ontology",
        help="Path to target ontology TTL file"
    )
    parser.add_argument(
        "output_file",
        help="Path to output YAML rules file"
    )
    parser.add_argument(
        "--api-key",
        help="Anthropic API key (or use ANTHROPIC_API_KEY env var)",
        default=None
    )
    parser.add_argument(
        "--no-verify-ssl",
        action="store_true",
        help="Disable SSL certificate verification (use in corporate proxy environments)"
    )

    args = parser.parse_args()

    generate_rules_with_ai(
        args.source_ontology,
        args.target_ontology,
        args.output_file,
        api_key=args.api_key,
        verify_ssl=not args.no_verify_ssl
    )
