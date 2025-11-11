"""
MDA-based Data Transformation: Manufacturing to GHG Emission Report

This module implements rule-based transformation from manufacturing ontology
to GHG emission report ontology following MDA principles.
"""

from typing import Dict, List, Any
from datetime import datetime
from decimal import Decimal
import json


class EmissionFactors:
    """
    Emission factors for converting energy consumption to CO2 emissions.
    Values are in kg-CO2 per unit of energy.
    """
    FACTORS = {
        "electricity": 0.500,      # kg-CO2/kWh (grid average)
        "natural_gas": 2.03,       # kg-CO2/m³
        "fuel_oil": 2.68,          # kg-CO2/liter
        "diesel": 2.68,            # kg-CO2/liter
        "gasoline": 2.31,          # kg-CO2/liter
        "lpg": 1.51,               # kg-CO2/kg
        "coal": 2.42,              # kg-CO2/kg
    }

    # Scope classification
    SCOPE_1_TYPES = ["natural_gas", "fuel_oil", "diesel", "gasoline", "lpg", "coal"]
    SCOPE_2_TYPES = ["electricity"]

    @classmethod
    def get_factor(cls, energy_type: str) -> float:
        """Get emission factor for given energy type."""
        energy_type_normalized = energy_type.lower().replace(" ", "_")
        return cls.FACTORS.get(energy_type_normalized, 0.0)

    @classmethod
    def get_scope(cls, energy_type: str) -> int:
        """Determine emission scope (1 or 2) for given energy type."""
        energy_type_normalized = energy_type.lower().replace(" ", "_")
        if energy_type_normalized in cls.SCOPE_1_TYPES:
            return 1
        elif energy_type_normalized in cls.SCOPE_2_TYPES:
            return 2
        return 1  # Default to Scope 1


class ManufacturingToGHGTransformer:
    """
    Transforms manufacturing activity data to GHG emission reports
    following the defined ontology mappings.
    """

    def __init__(self):
        self.emission_factors = EmissionFactors()

    def transform(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform source manufacturing data to target GHG report format.

        Args:
            source_data: JSON data compliant with manufacturing ontology

        Returns:
            JSON data compliant with GHG report ontology
        """
        # Extract manufacturing activities
        activities = source_data.get("manufacturing_activities", [])
        organization = source_data.get("organization", {})

        # Transform each activity to emissions
        emissions = []
        for activity in activities:
            activity_emissions = self._transform_activity(activity)
            emissions.extend(activity_emissions)

        # Aggregate emissions by scope
        scope1_emissions = [e for e in emissions if e.get("@type") == "ghg:Scope1Emission"]
        scope2_emissions = [e for e in emissions if e.get("@type") == "ghg:Scope2Emission"]

        total_scope1 = sum(e.get("co2_amount", 0) for e in scope1_emissions)
        total_scope2 = sum(e.get("co2_amount", 0) for e in scope2_emissions)
        total_emissions = total_scope1 + total_scope2

        # Determine reporting period from activities
        reporting_period = self._determine_reporting_period(activities)

        # Create emission report
        report = {
            "@context": {
                "ghg": "http://example.org/ghg-report#",
                "xsd": "http://www.w3.org/2001/XMLSchema#"
            },
            "@type": "ghg:EmissionReport",
            "report_id": self._generate_report_id(organization, reporting_period),
            "reporting_period": reporting_period,
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "reporting_organization": {
                "@type": "ghg:Organization",
                "organization_name": organization.get("name", "Unknown Organization")
            },
            "emissions": emissions,
            "total_scope1": round(total_scope1, 2),
            "total_scope2": round(total_scope2, 2),
            "total_emissions": round(total_emissions, 2)
        }

        return report

    def _transform_activity(self, activity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Transform a single manufacturing activity to emission entries.

        Args:
            activity: Manufacturing activity data

        Returns:
            List of emission entries
        """
        emissions = []
        energy_consumptions = activity.get("energy_consumptions", [])

        for consumption in energy_consumptions:
            energy_type = consumption.get("energy_type", {})
            energy_type_name = energy_type.get("name", "unknown")
            amount = consumption.get("amount", 0)
            unit = consumption.get("unit", "")

            # Calculate CO2 emissions
            emission_factor = self.emission_factors.get_factor(energy_type_name)
            co2_amount = amount * emission_factor

            # Determine scope
            scope = self.emission_factors.get_scope(energy_type_name)
            emission_type = f"ghg:Scope{scope}Emission"

            # Create emission entry
            emission = {
                "@type": emission_type,
                "emission_source": f"{activity.get('facility', 'Unknown')} - {activity.get('activity_name', 'Unknown Activity')}",
                "source_category": energy_type_name,
                "co2_amount": round(co2_amount, 2),
                "calculation_method": "Activity-based calculation using standard emission factors",
                "emission_factor": emission_factor,
                "activity_data": {
                    "activity_id": activity.get("activity_id"),
                    "energy_amount": amount,
                    "energy_unit": unit,
                    "start_date": activity.get("start_date"),
                    "end_date": activity.get("end_date")
                }
            }

            emissions.append(emission)

        return emissions

    def _determine_reporting_period(self, activities: List[Dict[str, Any]]) -> str:
        """
        Determine reporting period from activity dates.

        Args:
            activities: List of manufacturing activities

        Returns:
            Reporting period string (e.g., "2024-Q1", "2024-01")
        """
        if not activities:
            return datetime.now().strftime("%Y-%m")

        # Find earliest start and latest end dates
        dates = []
        for activity in activities:
            if activity.get("start_date"):
                dates.append(activity["start_date"])
            if activity.get("end_date"):
                dates.append(activity["end_date"])

        if dates:
            dates.sort()
            # Use year and month from earliest date
            return dates[0][:7]  # YYYY-MM format

        return datetime.now().strftime("%Y-%m")

    def _generate_report_id(self, organization: Dict[str, Any], period: str) -> str:
        """
        Generate unique report ID.

        Args:
            organization: Organization data
            period: Reporting period

        Returns:
            Report ID string
        """
        org_name = organization.get("name", "ORG")
        # Create simple ID from organization and period
        org_abbr = "".join(word[0].upper() for word in org_name.split()[:3])
        return f"GHG-{org_abbr}-{period}"


def transform_file(input_path: str, output_path: str) -> None:
    """
    Transform a source JSON file to target JSON file.

    Args:
        input_path: Path to source JSON file
        output_path: Path to output JSON file
    """
    transformer = ManufacturingToGHGTransformer()

    # Read source data
    with open(input_path, 'r', encoding='utf-8') as f:
        source_data = json.load(f)

    # Transform
    target_data = transformer.transform(source_data)

    # Write target data
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(target_data, f, indent=2, ensure_ascii=False)

    print(f"Transformation complete: {input_path} -> {output_path}")
    print(f"Total emissions: {target_data['total_emissions']} kg-CO2")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python transformer.py <input_json> <output_json>")
        sys.exit(1)

    transform_file(sys.argv[1], sys.argv[2])
