"""
Automatic Transformation Rule Generator

This module analyzes source and target RDF ontologies and automatically
generates declarative transformation rules in YAML format.

The generator creates a complete MDA transformation pipeline from ontology definitions.
"""

import yaml
from rdflib import Graph, Namespace, RDF, RDFS, OWL
from typing import Dict, List, Any, Set, Tuple, Optional
from collections import defaultdict
import re


class OntologyAnalyzer:
    """Analyzes an RDF ontology to extract structure and semantics."""

    def __init__(self, ontology_file: str):
        """Load and analyze an ontology file."""
        self.graph = Graph()
        self.graph.parse(ontology_file, format='turtle')

        self.classes = set()
        self.properties = {}  # property -> (domain, range, type)
        self.namespace = None

        self._analyze()

    def _analyze(self):
        """Analyze the ontology structure."""
        # Extract namespace
        self._extract_namespace()

        # Extract classes
        for cls in self.graph.subjects(RDF.type, OWL.Class):
            if not str(cls).startswith('http://www.w3.org'):
                self.classes.add(cls)

        # Extract properties
        for prop in self.graph.subjects(RDF.type, OWL.DatatypeProperty):
            domain = self._get_property_domain(prop)
            range_type = self._get_property_range(prop)
            self.properties[prop] = {
                'type': 'datatype',
                'domain': domain,
                'range': range_type
            }

        for prop in self.graph.subjects(RDF.type, OWL.ObjectProperty):
            domain = self._get_property_domain(prop)
            range_type = self._get_property_range(prop)
            self.properties[prop] = {
                'type': 'object',
                'domain': domain,
                'range': range_type
            }

    def _extract_namespace(self):
        """Extract the main namespace of the ontology."""
        for cls in self.graph.subjects(RDF.type, OWL.Class):
            cls_str = str(cls)
            if '#' in cls_str:
                self.namespace = cls_str.split('#')[0] + '#'
                break

    def _get_property_domain(self, prop):
        """Get the domain of a property."""
        for domain in self.graph.objects(prop, RDFS.domain):
            return domain
        return None

    def _get_property_range(self, prop):
        """Get the range of a property."""
        for range_type in self.graph.objects(prop, RDFS.range):
            return range_type
        return None

    def get_class_properties(self, cls) -> List[Any]:
        """Get all properties for a class."""
        props = []
        for prop, info in self.properties.items():
            if info['domain'] == cls:
                props.append(prop)
        return props

    def get_label(self, resource) -> str:
        """Get the label of a resource."""
        for label in self.graph.objects(resource, RDFS.label):
            label_str = str(label)
            if '@en' in label_str or '@' not in label_str:
                return label_str.split('@')[0].strip('"')
        return self._get_local_name(resource)

    def _get_local_name(self, resource) -> str:
        """Extract local name from URI."""
        uri = str(resource)
        if '#' in uri:
            return uri.split('#')[-1]
        elif '/' in uri:
            return uri.split('/')[-1]
        return uri

    def get_numeric_properties(self, cls) -> List[Any]:
        """Get numeric properties of a class."""
        numeric_types = [
            'http://www.w3.org/2001/XMLSchema#decimal',
            'http://www.w3.org/2001/XMLSchema#integer',
            'http://www.w3.org/2001/XMLSchema#float',
            'http://www.w3.org/2001/XMLSchema#double'
        ]

        numeric_props = []
        for prop in self.get_class_properties(cls):
            prop_range = self.properties[prop]['range']
            if prop_range and str(prop_range) in numeric_types:
                numeric_props.append(prop)

        return numeric_props


class RuleGenerator:
    """Generates transformation rules from source and target ontologies."""

    def __init__(self, source_ontology: str, target_ontology: str):
        """
        Initialize rule generator.

        Args:
            source_ontology: Path to source ontology TTL file
            target_ontology: Path to target ontology TTL file
        """
        self.source_analyzer = OntologyAnalyzer(source_ontology)
        self.target_analyzer = OntologyAnalyzer(target_ontology)

        self.class_mappings = {}
        self.property_mappings = {}

        self._infer_mappings()

    def _infer_mappings(self):
        """Infer class and property mappings based on semantic similarity."""
        # Simple name-based matching for classes
        for src_cls in self.source_analyzer.classes:
            src_name = self.source_analyzer.get_label(src_cls).lower()

            best_match = None
            best_score = 0

            for tgt_cls in self.target_analyzer.classes:
                tgt_name = self.target_analyzer.get_label(tgt_cls).lower()
                score = self._similarity_score(src_name, tgt_name)

                if score > best_score and score > 0.3:
                    best_score = score
                    best_match = tgt_cls

            if best_match:
                self.class_mappings[src_cls] = best_match

        # Infer property mappings
        for src_cls, tgt_cls in self.class_mappings.items():
            src_props = self.source_analyzer.get_class_properties(src_cls)
            tgt_props = self.target_analyzer.get_class_properties(tgt_cls)

            for src_prop in src_props:
                src_prop_name = self.source_analyzer.get_label(src_prop).lower()

                best_match = None
                best_score = 0

                for tgt_prop in tgt_props:
                    tgt_prop_name = self.target_analyzer.get_label(tgt_prop).lower()
                    score = self._similarity_score(src_prop_name, tgt_prop_name)

                    if score > best_score and score > 0.4:
                        best_score = score
                        best_match = tgt_prop

                if best_match:
                    if src_cls not in self.property_mappings:
                        self.property_mappings[src_cls] = {}
                    self.property_mappings[src_cls][src_prop] = best_match

    def _similarity_score(self, str1: str, str2: str) -> float:
        """Calculate semantic similarity between two strings."""
        # Simple word-based similarity
        words1 = set(re.findall(r'\w+', str1.lower()))
        words2 = set(re.findall(r'\w+', str2.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        # Jaccard similarity
        jaccard = len(intersection) / len(union)

        # Exact match bonus
        if str1 == str2:
            return 1.0

        # Substring match bonus
        if str1 in str2 or str2 in str1:
            return max(jaccard, 0.7)

        return jaccard

    def generate_rules(self,
                      transformation_name: str = "Auto-Generated Transformation",
                      include_calculations: bool = True) -> Dict[str, Any]:
        """
        Generate transformation rules.

        Args:
            transformation_name: Name of the transformation
            include_calculations: Whether to generate calculation rules

        Returns:
            Dictionary containing transformation rules
        """
        rules = {
            'metadata': {
                'name': transformation_name,
                'version': '1.0',
                'source_ontology': self.source_analyzer.namespace or 'unknown',
                'target_ontology': self.target_analyzer.namespace or 'unknown',
                'description': f'Auto-generated transformation rules',
                'generated': True
            },
            'constants': {
                'defaults': {
                    'unknown_value': 'Unknown'
                }
            },
            'root_mapping': {
                'target_type': self._get_root_class_name(),
                'target_context': {
                    'target': self.target_analyzer.namespace or 'http://example.org/target#',
                    'xsd': 'http://www.w3.org/2001/XMLSchema#'
                }
            },
            'field_mappings': self._generate_field_mappings(),
            'transformation_steps': self._generate_transformation_steps(),
            'options': {
                'preserve_source_context': True,
                'case_sensitive': False,
                'null_handling': 'use_defaults'
            }
        }

        if include_calculations:
            rules['calculation_rules'] = self._generate_calculation_rules()

        return rules

    def _get_root_class_name(self) -> str:
        """Get the root target class name."""
        # Find the most likely root class (one without being a range of others)
        root_classes = []

        for cls in self.target_analyzer.classes:
            is_root = True
            for prop_info in self.target_analyzer.properties.values():
                if prop_info['range'] == cls:
                    is_root = False
                    break

            if is_root:
                root_classes.append(cls)

        if root_classes:
            cls = root_classes[0]
            prefix = 'target'
            local_name = self.target_analyzer._get_local_name(cls)
            return f"{prefix}:{local_name}"

        return "target:TransformationResult"

    def _generate_field_mappings(self) -> List[Dict[str, Any]]:
        """Generate simple field-to-field mappings."""
        mappings = []

        for src_cls, tgt_cls in self.class_mappings.items():
            if src_cls not in self.property_mappings:
                continue

            for src_prop, tgt_prop in self.property_mappings[src_cls].items():
                src_prop_name = self.source_analyzer._get_local_name(src_prop)
                tgt_prop_name = self.target_analyzer._get_local_name(tgt_prop)

                # Convert to snake_case
                src_path = self._to_snake_case(src_prop_name)
                tgt_path = self._to_snake_case(tgt_prop_name)

                # Only add simple datatype properties to field mappings
                src_prop_info = self.source_analyzer.properties.get(src_prop, {})
                if src_prop_info.get('type') == 'datatype':
                    mappings.append({
                        'source_path': src_path,
                        'target_path': tgt_path,
                        'default': '${constants.defaults.unknown_value}'
                    })

        return mappings

    def _generate_transformation_steps(self) -> List[Dict[str, Any]]:
        """Generate transformation steps."""
        steps = []

        # Identify collection-to-collection transformations
        for src_cls, tgt_cls in self.class_mappings.items():
            src_local = self.source_analyzer._get_local_name(src_cls)
            tgt_local = self.target_analyzer._get_local_name(tgt_cls)

            # Create transformation step for collections
            step = {
                'name': f'transform_{self._to_snake_case(src_local)}',
                'description': f'Transform {src_local} to {tgt_local}',
                'source': self._to_snake_case(self._pluralize(src_local)),
                'target': self._to_snake_case(self._pluralize(tgt_local)),
                'iteration': True,
                'substeps': []
            }

            # Add property mappings as substep
            if src_cls in self.property_mappings:
                substep = {
                    'name': f'map_{self._to_snake_case(src_local)}_fields',
                    'mapping': []
                }

                for src_prop, tgt_prop in self.property_mappings[src_cls].items():
                    src_prop_name = self._to_snake_case(
                        self.source_analyzer._get_local_name(src_prop)
                    )
                    tgt_prop_name = self._to_snake_case(
                        self.target_analyzer._get_local_name(tgt_prop)
                    )

                    substep['mapping'].append({
                        'target': tgt_prop_name,
                        'source': src_prop_name
                    })

                step['substeps'].append(substep)

            steps.append(step)

        return steps

    def _generate_calculation_rules(self) -> List[Dict[str, Any]]:
        """Generate calculation rules for numeric properties."""
        calc_rules = []

        # Look for numeric properties that might need calculations
        for src_cls in self.source_analyzer.classes:
            numeric_props = self.source_analyzer.get_numeric_properties(src_cls)

            if len(numeric_props) >= 2:
                # Generate a sum calculation rule
                props_names = [
                    self._to_snake_case(self.source_analyzer._get_local_name(p))
                    for p in numeric_props[:2]
                ]

                calc_rules.append({
                    'name': f'calculate_total_{props_names[0]}',
                    'description': f'Calculate total from {props_names[0]}',
                    'input': {
                        'value': f'$.{props_names[0]}'
                    },
                    'formula': 'value',
                    'output': f'total_{props_names[0]}'
                })

        return calc_rules

    def _to_snake_case(self, name: str) -> str:
        """Convert camelCase or PascalCase to snake_case."""
        # Insert underscore before capitals
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        # Insert underscore before capitals preceded by lowercase
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        return s2.lower()

    def _pluralize(self, word: str) -> str:
        """Simple pluralization."""
        if word.endswith('y'):
            return word[:-1] + 'ies'
        elif word.endswith('s'):
            return word + 'es'
        else:
            return word + 's'

    def save_rules(self, output_file: str):
        """Save generated rules to YAML file."""
        rules = self.generate_rules()

        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(rules, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        print(f"Generated transformation rules saved to: {output_file}")
        print(f"  Source ontology: {self.source_analyzer.namespace}")
        print(f"  Target ontology: {self.target_analyzer.namespace}")
        print(f"  Class mappings: {len(self.class_mappings)}")
        print(f"  Property mappings: {sum(len(v) for v in self.property_mappings.values())}")


def generate_rules_from_ontologies(
    source_ontology: str,
    target_ontology: str,
    output_file: str,
    transformation_name: str = "Auto-Generated Transformation"
):
    """
    Generate transformation rules from ontologies.

    Args:
        source_ontology: Path to source ontology TTL file
        target_ontology: Path to target ontology TTL file
        output_file: Path to output YAML rules file
        transformation_name: Name of the transformation
    """
    generator = RuleGenerator(source_ontology, target_ontology)
    generator.save_rules(output_file)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("Usage: python rule_generator.py <source_ontology.ttl> <target_ontology.ttl> <output_rules.yaml>")
        sys.exit(1)

    generate_rules_from_ontologies(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        "Auto-Generated Transformation"
    )
