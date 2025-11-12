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

    def __init__(self, source_ontology: str, target_ontology: str, api_key: Optional[str] = None):
        """
        Initialize AI rule generator.

        Args:
            source_ontology: Path to source ontology TTL file
            target_ontology: Path to target ontology TTL file
            api_key: Anthropic API key (or use ANTHROPIC_API_KEY env var)
        """
        self.source_analyzer = OntologyAnalyzer(source_ontology)
        self.target_analyzer = OntologyAnalyzer(target_ontology)

        # Initialize Anthropic client
        api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable or api_key parameter required")

        self.client = anthropic.Anthropic(api_key=api_key)

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

        # Call Claude API
        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

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

SOURCE ONTOLOGY:
{json.dumps(source_structure, indent=2)}

TARGET ONTOLOGY:
{json.dumps(target_structure, indent=2)}

Your task:
1. Identify class mappings between source and target ontologies
2. For each class mapping, identify property mappings
3. Identify where aggregations are needed (e.g., summing values from arrays)
4. Identify where calculations are needed (e.g., multiplying values, applying factors)
5. Suggest any constant values or lookup tables that might be needed

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
      "source_property": "propertyName",
      "target_property": "targetPropertyName",
      "mapping_type": "direct|calculation|aggregation",
      "confidence": 0.90,
      "reasoning": "explanation"
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
      "name": "step_name",
      "description": "what this step does",
      "source": "source_collection",
      "target": "target_collection",
      "iteration": true
    }}
  ]
}}

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

        return constants

    def _generate_root_mapping(self, suggestions: Dict) -> Dict:
        """Generate root mapping from AI suggestions."""
        # Find the root target class (often EmissionsReport, Report, etc.)
        target_classes = [m['target_class'] for m in suggestions.get('class_mappings', [])]

        # Heuristic: root class often contains "Report" or is the first one
        root_class = target_classes[0] if target_classes else "TransformationResult"

        return {
            'target_type': f'target:{root_class.replace(" ", "")}',
            'target_context': {
                'target': self.target_analyzer.namespace,
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

        return calc_rules

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

            # Add property mappings for this step
            source_class = step_info.get('source', '').replace('_', ' ').title()

            substep = {
                'name': f'map_{step["name"]}_fields',
                'mapping': []
            }

            # Handle nested mappings structure
            for prop_group in suggestions.get('property_mappings', []):
                if prop_group['source_class'].lower() in source_class.lower():
                    for mapping in prop_group.get('mappings', []):
                        # Only add direct mappings to substeps
                        if mapping.get('mapping_type', 'direct') == 'direct':
                            substep['mapping'].append({
                                'target': mapping['target_property'].replace(' ', '_').lower(),
                                'source': mapping['source_property'].replace(' ', '_').lower()
                            })

            if substep['mapping']:
                step['substeps'].append(substep)

            steps.append(step)

        # Add aggregation step if there are aggregations
        if suggestions.get('aggregations'):
            agg_step = {
                'name': 'calculate_aggregations',
                'description': 'Calculate aggregated values',
                'aggregations': []
            }

            for agg in suggestions['aggregations']:
                agg_step['aggregations'].append({
                    'name': agg['name'].replace(' ', '_').lower(),
                    'source': agg.get('source_class', '').replace(' ', '_').lower() + 's',
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
    api_key: Optional[str] = None
):
    """
    Generate transformation rules using AI analysis.

    Args:
        source_ontology: Path to source ontology TTL file
        target_ontology: Path to target ontology TTL file
        output_file: Path to output YAML rules file
        api_key: Anthropic API key (optional, uses env var if not provided)
    """
    generator = AIRuleGenerator(source_ontology, target_ontology, api_key)

    # Analyze with AI
    generator.analyze_with_ai()

    # Display suggestions
    generator.display_suggestions()

    # Generate and save rules
    generator.save_rules(output_file)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print("Usage: python ai_rule_generator.py <source_ontology.ttl> <target_ontology.ttl> <output_rules.yaml> [api_key]")
        sys.exit(1)

    api_key = sys.argv[4] if len(sys.argv) > 4 else None

    generate_rules_with_ai(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        api_key
    )
