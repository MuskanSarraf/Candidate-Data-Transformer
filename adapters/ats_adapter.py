import json

from models.candidate import (
    Candidate,
    Location,
    Skill,
    Provenance,
)


def load_ats_data(file_path):
    """
    Reads ATS JSON and converts it into a list of Candidate objects.
    """

    with open(file_path, "r", encoding="utf-8") as file:
        ats_data = json.load(file)

    candidates = []

    for person in ats_data:

        candidate = Candidate(
            candidate_id=person.get("id"),
            full_name=person.get("candidateName"),
            emails=[person["primaryEmail"]] if person.get("primaryEmail") else [],
            phones=[person["mobileNumber"]] if person.get("mobileNumber") else [],
            headline=person.get("jobTitle"),

            location=Location(
                city=person.get("city"),
                country=person.get("countryCode")
            ),

            skills=[
                Skill(
                    name=skill,
                    confidence=1.0,
                    sources=["ATS"]
                )
                for skill in person.get("skills", [])
            ],

            provenance=[
                Provenance(
                    field="candidate",
                    source="ATS",
                    method="adapter_parse"
                )
            ],

            overall_confidence=0.90
        )

        candidates.append(candidate)

    return candidates