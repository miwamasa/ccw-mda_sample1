"""
Generic Rule-Based Transformation Engine

This module implements a generic MDA transformation engine that reads
declarative transformation rules and applies them to transform data from
source model to target model. The engine is model-agnostic and reusable.
"""

import yaml
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from copy import deepcopy
import re


class RuleEngine:
    """
    Generic rule-based transformation engine.
    Reads declarative rules and applies them to transform data.
    """

    def __init__(self, rules_file: str):
        """
        Initialize the rule engine with a rules file.

        Args:
            rules_file: Path to YAML file containing transformation rules
        """
        with open(rules_file, 'r', encoding='utf-8') as f:
            self.rules = yaml.safe_load(f)

        self.constants = self.rules.get('constants', {})
        self.metadata = self.rules.get('metadata', {})
        self.options = self.rules.get('options', {})

    def transform(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform source data to target format using loaded rules.

        Args:
            source_data: Source data dictionary

        Returns:
            Transformed target data dictionary
        """
        # Initialize target structure
        target_data = {
            "@context": self.rules['root_mapping'].get('target_context', {}),
            "@type": self.rules['root_mapping'].get('target_type')
        }

        # Apply field mappings
        target_data = self._apply_field_mappings(source_data, target_data)

        # Execute transformation steps
        for step in self.rules.get('transformation_steps', []):
            target_data = self._execute_step(source_data, target_data, step)

        return target_data

    def _apply_field_mappings(
        self,
        source_data: Dict[str, Any],
        target_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply simple field-to-field mappings."""
        for mapping in self.rules.get('field_mappings', []):
            source_path = mapping.get('source_path')
            target_path = mapping.get('target_path')
            fixed_value = mapping.get('fixed_value')
            default = mapping.get('default')

            if fixed_value:
                value = self._resolve_value(fixed_value)
            else:
                value = self._get_nested_value(source_data, source_path)
                if value is None and default:
                    value = self._resolve_value(default)

            if value is not None:
                self._set_nested_value(target_data, target_path, value)

        return target_data

    def _execute_step(
        self,
        source_data: Dict[str, Any],
        target_data: Dict[str, Any],
        step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a transformation step."""
        step_name = step.get('name')

        if step_name == "transform_activities_to_emissions":
            return self._transform_activities_to_emissions(source_data, target_data, step)
        elif step_name == "calculate_aggregations":
            return self._calculate_aggregations(target_data, step)
        elif step_name == "generate_report_metadata":
            return self._generate_report_metadata(source_data, target_data, step)
        else:
            # Generic step execution
            return self._execute_generic_step(source_data, target_data, step)

        return target_data

    def _transform_activities_to_emissions(
        self,
        source_data: Dict[str, Any],
        target_data: Dict[str, Any],
        step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transform manufacturing activities to emissions."""
        activities = self._get_nested_value(source_data, step.get('source'))
        if not activities:
            activities = []

        emissions = []

        for activity in activities:
            # Process each energy consumption in the activity
            for substep in step.get('substeps', []):
                energy_consumptions = self._get_nested_value(
                    activity,
                    substep.get('source', '').replace('$.', '')
                )

                if not energy_consumptions:
                    continue

                for consumption in energy_consumptions:
                    emission = self._build_emission_entry(
                        consumption,
                        activity,
                        substep.get('mapping', [])
                    )
                    emissions.append(emission)

        target_data['emissions'] = emissions
        return target_data

    def _build_emission_entry(
        self,
        consumption: Dict[str, Any],
        activity: Dict[str, Any],
        mappings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build a single emission entry from consumption and activity data."""
        emission = {}

        for mapping in mappings:
            target_field = mapping.get('target')
            source_field = mapping.get('source')
            calculation = mapping.get('calculation')
            fixed_value = mapping.get('fixed_value')
            lookup = mapping.get('lookup')
            context = mapping.get('context')
            format_str = mapping.get('format')
            transform = mapping.get('transform')
            nested_mapping = mapping.get('mapping')

            # Determine the data context (consumption or activity)
            data_context = activity if context == 'parent' else consumption

            if nested_mapping:
                # Handle nested object mapping
                nested_obj = {}
                for nested in nested_mapping:
                    nested_target = nested.get('target')
                    nested_source = nested.get('source')
                    nested_context = nested.get('context')

                    nested_data_context = activity if nested_context == 'parent' else consumption
                    nested_value = self._get_nested_value(nested_data_context, nested_source)

                    if nested_value is not None:
                        nested_obj[nested_target] = nested_value

                emission[target_field] = nested_obj

            elif calculation:
                # Execute calculation rule
                calc_rule = self._find_calculation_rule(calculation)
                if calc_rule:
                    value = self._execute_calculation(
                        calc_rule,
                        consumption,
                        activity
                    )
                    if format_str:
                        value = format_str.format(scope=value)
                    emission[target_field] = value

            elif lookup:
                # Perform lookup
                lookup_source = lookup.get('source')
                lookup_key_path = lookup.get('key')
                key_transform = lookup.get('key_transform')
                default = lookup.get('default')

                key_value = self._get_nested_value(data_context, lookup_key_path)
                if key_transform:
                    key_value = self._apply_transform(key_value, key_transform)

                value = self._get_constant_value(lookup_source, key_value)
                if value is None and default:
                    value = self._resolve_value(default)

                emission[target_field] = value

            elif fixed_value:
                emission[target_field] = self._resolve_value(fixed_value)

            elif source_field:
                value = self._get_nested_value(data_context, source_field)
                if transform:
                    value = self._apply_transform(value, transform)
                emission[target_field] = value

        return emission

    def _calculate_aggregations(
        self,
        target_data: Dict[str, Any],
        step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate aggregated values."""
        for agg in step.get('aggregations', []):
            source_field = agg.get('source')
            filter_config = agg.get('filter')
            aggregate_config = agg.get('aggregate')
            formula = agg.get('formula')
            target_field = agg.get('target')
            rounding = agg.get('rounding')

            if formula:
                # Execute formula
                value = self._execute_formula(formula, target_data)
            else:
                # Perform aggregation
                data = self._get_nested_value(target_data, source_field)
                if not data:
                    data = []

                # Apply filter
                if filter_config:
                    field = filter_config.get('field')
                    equals = filter_config.get('equals')
                    data = [item for item in data if self._get_nested_value(item, field) == equals]

                # Perform aggregation
                if aggregate_config:
                    func = aggregate_config.get('function')
                    field = aggregate_config.get('field')

                    if func == 'sum':
                        value = sum(self._get_nested_value(item, field) or 0 for item in data)
                    elif func == 'count':
                        value = len(data)
                    elif func == 'avg':
                        values = [self._get_nested_value(item, field) for item in data if self._get_nested_value(item, field) is not None]
                        value = sum(values) / len(values) if values else 0
                    else:
                        value = 0

            # Apply rounding
            if rounding is not None:
                value = round(value, rounding)

            target_data[target_field] = value

        return target_data

    def _generate_report_metadata(
        self,
        source_data: Dict[str, Any],
        target_data: Dict[str, Any],
        step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate report metadata fields."""
        for mapping in step.get('mappings', []):
            target_field = mapping.get('target')
            calculation = mapping.get('calculation')
            function = mapping.get('function')
            format_str = mapping.get('format')

            if calculation:
                calc_rule = self._find_calculation_rule(calculation)
                if calc_rule:
                    value = self._execute_calculation(
                        calc_rule,
                        source_data,
                        target_data
                    )
                    target_data[target_field] = value

            elif function:
                if function == 'current_date':
                    if format_str == 'YYYY-MM-DD':
                        value = datetime.now().strftime('%Y-%m-%d')
                    else:
                        value = datetime.now().isoformat()
                    target_data[target_field] = value

        return target_data

    def _execute_generic_step(
        self,
        source_data: Dict[str, Any],
        target_data: Dict[str, Any],
        step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a generic transformation step."""
        source_path = step.get('source')
        target_path = step.get('target')
        is_iteration = step.get('iteration', False)
        substeps = step.get('substeps', [])

        # Get source data
        source_items = self._get_nested_value(source_data, source_path)

        if source_items is None:
            return target_data

        # If iteration, process each item
        if is_iteration and isinstance(source_items, list):
            target_items = []

            for item in source_items:
                # Apply all substeps to this item
                transformed_item = {}

                for substep in substeps:
                    mappings = substep.get('mapping', [])
                    for mapping in mappings:
                        target_field = mapping.get('target')
                        source_field = mapping.get('source')
                        transform = mapping.get('transform')

                        # Get value from source item
                        value = self._get_nested_value(item, source_field)

                        # Apply transformation if specified
                        if value and transform:
                            value = self._apply_transform(value, transform)

                        # Set in transformed item
                        if value is not None:
                            transformed_item[target_field] = value

                target_items.append(transformed_item)

            # Set target items in target data
            if target_path and target_items:
                self._set_nested_value(target_data, target_path, target_items)

        else:
            # Non-iteration: direct mapping
            transformed = {}

            for substep in substeps:
                mappings = substep.get('mapping', [])
                for mapping in mappings:
                    target_field = mapping.get('target')
                    source_field = mapping.get('source')

                    value = self._get_nested_value(source_items, source_field)
                    if value is not None:
                        transformed[target_field] = value

            if target_path and transformed:
                self._set_nested_value(target_data, target_path, transformed)

        return target_data

    def _find_calculation_rule(self, rule_name: str) -> Optional[Dict[str, Any]]:
        """Find a calculation rule by name."""
        for rule in self.rules.get('calculation_rules', []):
            if rule.get('name') == rule_name:
                return rule
        return None

    def _execute_calculation(
        self,
        calc_rule: Dict[str, Any],
        *data_contexts
    ) -> Any:
        """Execute a calculation rule."""
        rule_name = calc_rule.get('name')

        if rule_name == 'calculate_co2_emission':
            return self._calc_co2_emission(calc_rule, *data_contexts)
        elif rule_name == 'determine_scope':
            return self._calc_determine_scope(calc_rule, *data_contexts)
        elif rule_name == 'generate_emission_source':
            return self._calc_generate_emission_source(calc_rule, *data_contexts)
        elif rule_name == 'generate_report_id':
            return self._calc_generate_report_id(calc_rule, *data_contexts)
        elif rule_name == 'determine_reporting_period':
            return self._calc_determine_reporting_period(calc_rule, *data_contexts)

        return None

    def _calc_co2_emission(self, rule: Dict[str, Any], *contexts) -> float:
        """Calculate CO2 emission."""
        consumption = contexts[0] if contexts else {}

        energy_amount = self._get_nested_value(consumption, 'amount') or 0
        energy_type = self._get_nested_value(consumption, 'energy_type.name') or 'unknown'

        # Get emission factor via lookup
        lookup = rule.get('lookup', {}).get('emission_factor', {})
        key_transform = lookup.get('key_transform')

        if key_transform:
            energy_type = self._apply_transform(energy_type, key_transform)

        emission_factor = self._get_constant_value(
            lookup.get('source'),
            energy_type
        )

        if emission_factor is None:
            emission_factor = 0.0

        result = energy_amount * emission_factor
        rounding = rule.get('rounding')
        if rounding is not None:
            result = round(result, rounding)

        return result

    def _calc_determine_scope(self, rule: Dict[str, Any], *contexts) -> int:
        """Determine emission scope."""
        consumption = contexts[0] if contexts else {}
        energy_type = self._get_nested_value(consumption, 'energy_type.name') or 'unknown'

        for logic in rule.get('logic', []):
            condition = logic.get('condition')
            if condition:
                key_transform = condition.get('key_transform')
                if key_transform:
                    energy_type_normalized = self._apply_transform(energy_type, key_transform)

                check = condition.get('check')
                if check:
                    # Parse check condition
                    if 'in constants.scope_classification.scope1' in check:
                        scope1_types = self._get_constant_value('scope_classification', 'scope1')
                        if energy_type_normalized in scope1_types:
                            return logic.get('output')
                    elif 'in constants.scope_classification.scope2' in check:
                        scope2_types = self._get_constant_value('scope_classification', 'scope2')
                        if energy_type_normalized in scope2_types:
                            return logic.get('output')
            elif 'default' in logic:
                return logic.get('default')

        return 1  # Default to Scope 1

    def _calc_generate_emission_source(self, rule: Dict[str, Any], *contexts) -> str:
        """Generate emission source description."""
        consumption = contexts[0] if contexts else {}
        activity = contexts[1] if len(contexts) > 1 else {}

        facility = self._get_nested_value(activity, 'facility') or self._get_constant_value('defaults', 'unknown_facility')
        activity_name = self._get_nested_value(activity, 'activity_name') or self._get_constant_value('defaults', 'unknown_activity')

        return f"{facility} - {activity_name}"

    def _calc_generate_report_id(self, rule: Dict[str, Any], *contexts) -> str:
        """Generate report ID."""
        source_data = contexts[0] if contexts else {}
        target_data = contexts[1] if len(contexts) > 1 else {}

        org_name = self._get_nested_value(source_data, 'organization.name') or 'ORG'
        reporting_period = target_data.get('reporting_period') or datetime.now().strftime('%Y-%m')

        # Create abbreviation from organization name
        org_abbr = ''.join(word[0].upper() for word in org_name.split()[:3])

        return f"GHG-{org_abbr}-{reporting_period}"

    def _calc_determine_reporting_period(self, rule: Dict[str, Any], *contexts) -> str:
        """Determine reporting period from activity dates."""
        source_data = contexts[0] if contexts else {}

        activities = self._get_nested_value(source_data, 'manufacturing_activities') or []

        dates = []
        for activity in activities:
            start_date = activity.get('start_date')
            end_date = activity.get('end_date')
            if start_date:
                dates.append(start_date)
            if end_date:
                dates.append(end_date)

        if dates:
            dates.sort()
            # Return YYYY-MM format
            return dates[0][:7] if len(dates[0]) >= 7 else dates[0]

        return datetime.now().strftime('%Y-%m')

    def _execute_formula(self, formula: str, context: Dict[str, Any]) -> Any:
        """Execute a formula expression."""
        # Simple formula evaluation (secure version)
        # Replace variable names with their values
        safe_context = {k: v for k, v in context.items() if isinstance(k, str) and k.isidentifier()}

        try:
            # Only allow basic arithmetic operations
            allowed_names = {**safe_context}
            result = eval(formula, {"__builtins__": {}}, allowed_names)
            return result
        except Exception:
            return 0

    def _apply_transform(self, value: Any, transform: str) -> Any:
        """Apply a transformation to a value."""
        if value is None:
            return value

        if transform == 'lowercase_underscore':
            if isinstance(value, str):
                return value.lower().replace(' ', '_')
        elif transform == 'uppercase':
            if isinstance(value, str):
                return value.upper()
        elif transform == 'lowercase':
            if isinstance(value, str):
                return value.lower()

        return value

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get a value from nested dictionary using dot notation."""
        if not path or data is None:
            return None

        keys = path.split('.')
        current = data

        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None

            if current is None:
                return None

        return current

    def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any) -> None:
        """Set a value in nested dictionary using dot notation."""
        keys = path.split('.')
        current = data

        for i, key in enumerate(keys[:-1]):
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def _get_constant_value(self, path: str, key: Optional[str] = None) -> Any:
        """Get a value from constants."""
        # Strip "constants." prefix if present
        if path and path.startswith('constants.'):
            path = path[10:]  # Remove "constants." prefix

        value = self._get_nested_value(self.constants, path)

        if key and isinstance(value, dict):
            return value.get(key)

        return value

    def _resolve_value(self, value_expr: str) -> Any:
        """Resolve a value expression (e.g., ${constants.defaults.unknown_organization})."""
        if isinstance(value_expr, str) and value_expr.startswith('${') and value_expr.endswith('}'):
            path = value_expr[2:-1]
            if path.startswith('constants.'):
                return self._get_nested_value(self.constants, path[10:])

        return value_expr


def transform_file(rules_file: str, input_file: str, output_file: str) -> None:
    """
    Transform a source JSON file to target JSON file using rules.

    Args:
        rules_file: Path to transformation rules YAML file
        input_file: Path to source JSON file
        output_file: Path to output JSON file
    """
    # Load rule engine
    engine = RuleEngine(rules_file)

    # Read source data
    with open(input_file, 'r', encoding='utf-8') as f:
        source_data = json.load(f)

    # Transform
    target_data = engine.transform(source_data)

    # Write target data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(target_data, f, indent=2, ensure_ascii=False)

    print(f"Transformation complete: {input_file} -> {output_file}")
    print(f"  Rule file: {rules_file}")
    print(f"  Total emissions: {target_data.get('total_emissions', 0)} kg-CO2")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("Usage: python rule_engine.py <rules_yaml> <input_json> <output_json>")
        sys.exit(1)

    transform_file(sys.argv[1], sys.argv[2], sys.argv[3])
