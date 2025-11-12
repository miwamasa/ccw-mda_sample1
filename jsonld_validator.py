"""
JSON-LD to RDF Ontology Validator

Validates JSON-LD instance data against RDF/Turtle ontology definitions.
Checks naming conventions, data types, structure, and completeness.

Based on: doc/RDF_JSON_LD_MAPPING.md
"""

import json
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from rdflib import Graph, Namespace, RDF, RDFS, OWL, XSD


@dataclass
class ValidationIssue:
    """Represents a validation issue found in JSON-LD data."""
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'naming', 'type', 'structure', 'missing', 'unknown'
    path: str      # JSONPath to the issue
    message: str
    expected: Optional[str] = None
    actual: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Results of validation."""
    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    statistics: Dict[str, int] = field(default_factory=dict)

    def add_error(self, category: str, path: str, message: str,
                  expected: str = None, actual: str = None, suggestion: str = None):
        """Add an error issue."""
        self.issues.append(ValidationIssue(
            severity='error',
            category=category,
            path=path,
            message=message,
            expected=expected,
            actual=actual,
            suggestion=suggestion
        ))
        self.valid = False

    def add_warning(self, category: str, path: str, message: str,
                    expected: str = None, actual: str = None, suggestion: str = None):
        """Add a warning issue."""
        self.issues.append(ValidationIssue(
            severity='warning',
            category=category,
            path=path,
            message=message,
            expected=expected,
            actual=actual,
            suggestion=suggestion
        ))

    def add_info(self, category: str, path: str, message: str):
        """Add an info issue."""
        self.issues.append(ValidationIssue(
            severity='info',
            category=category,
            path=path,
            message=message
        ))

    def get_summary(self) -> Dict[str, int]:
        """Get summary statistics."""
        summary = {'errors': 0, 'warnings': 0, 'infos': 0}
        for issue in self.issues:
            key = issue.severity + 's' if issue.severity != 'info' else 'infos'
            summary[key] += 1
        return summary


class OntologyValidator:
    """
    Validates JSON-LD data against RDF ontology definitions.
    """

    def __init__(self, ontology_file: str):
        """
        Initialize validator with an ontology file.

        Args:
            ontology_file: Path to RDF/Turtle ontology file
        """
        self.ontology_file = ontology_file
        self.graph = Graph()
        self.graph.parse(ontology_file, format='turtle')

        # Extract namespace from ontology
        self.namespace = self._extract_namespace()

        # Cache ontology structures
        self.classes = self._extract_classes()
        self.properties = self._extract_properties()
        self.datatype_properties = self._extract_datatype_properties()
        self.object_properties = self._extract_object_properties()

    def _extract_namespace(self) -> str:
        """Extract the main namespace from ontology."""
        # Find the ontology declaration
        for s in self.graph.subjects(RDF.type, OWL.Ontology):
            ns_str = str(s)
            # Extract base namespace
            if '#' in ns_str:
                return ns_str.rsplit('#', 1)[0] + '#'
            elif '/' in ns_str:
                return ns_str.rsplit('/', 1)[0] + '/'

        # Fallback: look for common patterns
        for ns_prefix, ns_uri in self.graph.namespaces():
            if ns_prefix not in ['rdf', 'rdfs', 'owl', 'xsd']:
                return str(ns_uri)

        return None

    def _extract_classes(self) -> Dict[str, Dict[str, Any]]:
        """Extract all classes from ontology."""
        classes = {}
        for cls in self.graph.subjects(RDF.type, OWL.Class):
            cls_name = self._get_local_name(str(cls))
            classes[cls_name] = {
                'uri': str(cls),
                'label': self._get_label(cls),
                'comment': self._get_comment(cls),
                'superclasses': self._get_superclasses(cls)
            }
        return classes

    def _extract_properties(self) -> Dict[str, Dict[str, Any]]:
        """Extract all properties from ontology."""
        properties = {}

        # DatatypeProperty
        for prop in self.graph.subjects(RDF.type, OWL.DatatypeProperty):
            prop_name = self._get_local_name(str(prop))
            properties[prop_name] = self._extract_property_info(prop, 'datatype')

        # ObjectProperty
        for prop in self.graph.subjects(RDF.type, OWL.ObjectProperty):
            prop_name = self._get_local_name(str(prop))
            properties[prop_name] = self._extract_property_info(prop, 'object')

        return properties

    def _extract_datatype_properties(self) -> Dict[str, Dict[str, Any]]:
        """Extract datatype properties."""
        props = {}
        for prop in self.graph.subjects(RDF.type, OWL.DatatypeProperty):
            prop_name = self._get_local_name(str(prop))
            props[prop_name] = self._extract_property_info(prop, 'datatype')
        return props

    def _extract_object_properties(self) -> Dict[str, Dict[str, Any]]:
        """Extract object properties."""
        props = {}
        for prop in self.graph.subjects(RDF.type, OWL.ObjectProperty):
            prop_name = self._get_local_name(str(prop))
            props[prop_name] = self._extract_property_info(prop, 'object')
        return props

    def _extract_property_info(self, prop, prop_type: str) -> Dict[str, Any]:
        """Extract information about a property."""
        info = {
            'uri': str(prop),
            'type': prop_type,
            'label': self._get_label(prop),
            'comment': self._get_comment(prop),
            'domain': [],
            'range': None
        }

        # Get domain
        for domain in self.graph.objects(prop, RDFS.domain):
            info['domain'].append(self._get_local_name(str(domain)))

        # Get range
        for range_val in self.graph.objects(prop, RDFS.range):
            info['range'] = str(range_val)

        return info

    def _get_local_name(self, uri: str) -> str:
        """Extract local name from URI."""
        if '#' in uri:
            return uri.split('#')[-1]
        elif '/' in uri:
            return uri.split('/')[-1]
        return uri

    def _get_label(self, subject) -> str:
        """Get rdfs:label for a subject."""
        for label in self.graph.objects(subject, RDFS.label):
            return str(label)
        return None

    def _get_comment(self, subject) -> str:
        """Get rdfs:comment for a subject."""
        for comment in self.graph.objects(subject, RDFS.comment):
            return str(comment)
        return None

    def _get_superclasses(self, cls) -> List[str]:
        """Get superclasses of a class."""
        superclasses = []
        for superclass in self.graph.objects(cls, RDFS.subClassOf):
            superclasses.append(self._get_local_name(str(superclass)))
        return superclasses

    def validate(self, json_file: str, strict: bool = False) -> ValidationResult:
        """
        Validate JSON-LD file against ontology.

        Args:
            json_file: Path to JSON-LD file
            strict: If True, treat warnings as errors

        Returns:
            ValidationResult with all issues found
        """
        result = ValidationResult(valid=True)

        # Load JSON-LD data
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            result.add_error('structure', '$', f'Failed to load JSON file: {e}')
            return result

        # Validate @context
        self._validate_context(data, result)

        # Validate structure
        self._validate_structure(data, result, path='$')

        # Update statistics
        result.statistics = result.get_summary()

        return result

    def _validate_context(self, data: Dict, result: ValidationResult):
        """Validate @context."""
        if '@context' not in data:
            result.add_warning('structure', '$',
                             '@context is missing',
                             suggestion='Add @context with namespace definitions')
            return

        context = data['@context']

        # Check if namespace is defined
        namespace_defined = False
        if isinstance(context, dict):
            for prefix, uri in context.items():
                if str(uri).rstrip('#/') in str(self.namespace).rstrip('#/'):
                    namespace_defined = True
                    break

        if not namespace_defined:
            result.add_warning('structure', '$.@context',
                             f'Ontology namespace not found in @context',
                             expected=self.namespace)

    def _validate_structure(self, data: Any, result: ValidationResult,
                          path: str, expected_class: str = None):
        """Recursively validate data structure."""
        if isinstance(data, dict):
            self._validate_object(data, result, path, expected_class)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._validate_structure(item, result, f'{path}[{i}]', expected_class)

    def _validate_object(self, obj: Dict, result: ValidationResult,
                        path: str, expected_class: str = None):
        """Validate a JSON object."""
        # Check @type
        if '@type' in obj:
            type_value = obj['@type']
            # Extract class name from @type (remove prefix)
            if ':' in type_value:
                class_name = type_value.split(':')[-1]
            else:
                class_name = type_value

            # Check if class exists in ontology
            if class_name not in self.classes:
                result.add_error('type', f'{path}.@type',
                               f'Class "{class_name}" not found in ontology',
                               actual=class_name,
                               suggestion=f'Available classes: {", ".join(list(self.classes.keys())[:5])}...')
            else:
                # Validate properties for this class
                self._validate_properties(obj, result, path, class_name)
        else:
            # Object without @type - check if it's a nested object
            if path != '$':
                self._validate_properties(obj, result, path, None)

        # Recursively validate nested structures
        for key, value in obj.items():
            if key in ['@context', '@type']:
                continue

            item_path = f'{path}.{key}'

            if isinstance(value, dict):
                # Check naming convention
                self._validate_naming(key, result, item_path)
                self._validate_structure(value, result, item_path)
            elif isinstance(value, list):
                self._validate_naming(key, result, item_path, is_array=True)
                for i, item in enumerate(value):
                    self._validate_structure(item, result, f'{item_path}[{i}]')
            else:
                # Validate field name
                self._validate_naming(key, result, item_path)

    def _validate_properties(self, obj: Dict, result: ValidationResult,
                           path: str, class_name: str):
        """Validate properties of an object."""
        for key, value in obj.items():
            if key in ['@context', '@type']:
                continue

            item_path = f'{path}.{key}'

            # Convert JSON-LD field name to ontology property name
            ontology_prop = self._json_to_ontology_name(key)

            # Check if property exists
            if ontology_prop not in self.properties:
                # Try common variations
                alternatives = self._find_similar_properties(ontology_prop)
                if alternatives:
                    result.add_warning('unknown', item_path,
                                     f'Property not found in ontology',
                                     actual=key,
                                     suggestion=f'Did you mean: {", ".join(alternatives[:3])}?')
                else:
                    result.add_info('unknown', item_path,
                                  f'Property "{key}" not defined in ontology (may be valid)')
            else:
                # Validate property type
                prop_info = self.properties[ontology_prop]
                self._validate_property_type(value, prop_info, result, item_path)

    def _validate_property_type(self, value: Any, prop_info: Dict,
                               result: ValidationResult, path: str):
        """Validate property value type."""
        if prop_info['type'] == 'datatype':
            # Check XSD type
            range_type = prop_info.get('range')
            if range_type:
                expected_json_type = self._xsd_to_json_type(range_type)
                actual_json_type = type(value).__name__

                if expected_json_type and actual_json_type != expected_json_type:
                    result.add_error('type', path,
                                   f'Type mismatch',
                                   expected=expected_json_type,
                                   actual=actual_json_type)

        elif prop_info['type'] == 'object':
            # Should be object or array
            if not isinstance(value, (dict, list)):
                result.add_error('type', path,
                               f'Expected object or array for ObjectProperty',
                               expected='object/array',
                               actual=type(value).__name__)

    def _validate_naming(self, field_name: str, result: ValidationResult,
                        path: str, is_array: bool = False):
        """Validate field naming convention."""
        # Check if it's snake_case
        if not self._is_snake_case(field_name):
            suggestion = self._to_snake_case(field_name)
            result.add_warning('naming', path,
                             f'Field name should be snake_case',
                             expected=suggestion,
                             actual=field_name)

        # Check if array fields are plural
        if is_array and not field_name.endswith('s'):
            result.add_warning('naming', path,
                             f'Array field should be plural',
                             actual=field_name,
                             suggestion=field_name + 's')

    def _is_snake_case(self, name: str) -> bool:
        """Check if name is in snake_case."""
        # Allow underscores and lowercase letters/numbers
        return re.match(r'^[a-z][a-z0-9_]*$', name) is not None

    def _to_snake_case(self, name: str) -> str:
        """Convert camelCase to snake_case."""
        # Insert underscore before uppercase letters
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _json_to_ontology_name(self, json_name: str) -> str:
        """Convert JSON-LD field name to ontology property name."""
        # Remove trailing 's' if plural
        if json_name.endswith('s') and len(json_name) > 1:
            singular = json_name[:-1]
            # Check if singular form exists
            camel = self._to_camel_case(singular)
            if f'has{camel.capitalize()}' in self.properties:
                return f'has{camel.capitalize()}'

        # Convert to camelCase
        return self._to_camel_case(json_name)

    def _to_camel_case(self, name: str) -> str:
        """Convert snake_case to camelCase."""
        components = name.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])

    def _find_similar_properties(self, prop_name: str) -> List[str]:
        """Find similar property names."""
        similar = []
        prop_lower = prop_name.lower()

        for ontology_prop in self.properties.keys():
            if prop_lower in ontology_prop.lower() or ontology_prop.lower() in prop_lower:
                # Convert to JSON-LD naming
                json_name = self._to_snake_case(ontology_prop)
                similar.append(json_name)

        return similar

    def _xsd_to_json_type(self, xsd_type: str) -> Optional[str]:
        """Convert XSD type to JSON type."""
        type_map = {
            str(XSD.string): 'str',
            str(XSD.decimal): 'int',  # JSON doesn't distinguish
            str(XSD.integer): 'int',
            str(XSD.float): 'float',
            str(XSD.double): 'float',
            str(XSD.boolean): 'bool',
            str(XSD.date): 'str',
            str(XSD.dateTime): 'str',
        }
        return type_map.get(xsd_type, None)


def generate_validation_report(result: ValidationResult, output_file: str = None) -> str:
    """
    Generate a human-readable validation report.

    Args:
        result: ValidationResult to report
        output_file: Optional file to write report to

    Returns:
        Report as string
    """
    lines = []
    lines.append("=" * 70)
    lines.append("JSON-LD VALIDATION REPORT")
    lines.append("=" * 70)
    lines.append("")

    # Summary
    summary = result.get_summary()
    status = "✅ VALID" if result.valid else "❌ INVALID"
    lines.append(f"Status: {status}")
    lines.append(f"Errors: {summary['errors']}")
    lines.append(f"Warnings: {summary['warnings']}")
    lines.append(f"Info: {summary['infos']}")
    lines.append("")

    if not result.issues:
        lines.append("✅ No issues found. JSON-LD data is valid!")
        lines.append("")
    else:
        # Group by severity
        errors = [i for i in result.issues if i.severity == 'error']
        warnings = [i for i in result.issues if i.severity == 'warning']
        infos = [i for i in result.issues if i.severity == 'info']

        if errors:
            lines.append("❌ ERRORS")
            lines.append("-" * 70)
            for issue in errors:
                lines.append(f"Path: {issue.path}")
                lines.append(f"Category: {issue.category}")
                lines.append(f"Message: {issue.message}")
                if issue.expected:
                    lines.append(f"Expected: {issue.expected}")
                if issue.actual:
                    lines.append(f"Actual: {issue.actual}")
                if issue.suggestion:
                    lines.append(f"Suggestion: {issue.suggestion}")
                lines.append("")

        if warnings:
            lines.append("⚠️  WARNINGS")
            lines.append("-" * 70)
            for issue in warnings:
                lines.append(f"Path: {issue.path}")
                lines.append(f"Category: {issue.category}")
                lines.append(f"Message: {issue.message}")
                if issue.expected:
                    lines.append(f"Expected: {issue.expected}")
                if issue.actual:
                    lines.append(f"Actual: {issue.actual}")
                if issue.suggestion:
                    lines.append(f"Suggestion: {issue.suggestion}")
                lines.append("")

        if infos:
            lines.append("ℹ️  INFORMATION")
            lines.append("-" * 70)
            for issue in infos:
                lines.append(f"Path: {issue.path}")
                lines.append(f"Message: {issue.message}")
                lines.append("")

    lines.append("=" * 70)

    report = "\n".join(lines)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

    return report


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python jsonld_validator.py <ontology.ttl> <data.json> [report.txt]")
        print("")
        print("Example:")
        print("  python jsonld_validator.py model/source/manufacturing-ontology.ttl \\")
        print("                            test_data/source/sample1_small_factory.json \\")
        print("                            validation_report.txt")
        sys.exit(1)

    ontology_file = sys.argv[1]
    json_file = sys.argv[2]
    report_file = sys.argv[3] if len(sys.argv) > 3 else None

    print(f"Validating: {json_file}")
    print(f"Against ontology: {ontology_file}")
    print("")

    # Create validator
    validator = OntologyValidator(ontology_file)

    # Validate
    result = validator.validate(json_file)

    # Generate report
    report = generate_validation_report(result, report_file)
    print(report)

    # Exit with appropriate code
    sys.exit(0 if result.valid else 1)
