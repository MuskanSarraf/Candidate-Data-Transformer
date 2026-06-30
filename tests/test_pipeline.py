import argparse
import json

from main import run_pipeline
from services.normalizer import normalize_phone, normalize_skill


def test_default_pipeline_merges_sources_and_tracks_provenance(tmp_path):
    output = tmp_path / "default.json"
    records = run_pipeline(
        argparse.Namespace(
            ats_json="data/ats_sample.json",
            csv="data/recruiter_export.csv",
            github_json="data/github_sample.json",
            notes="data/recruiter_notes.txt",
            config="config/default_config.json",
            output=str(output),
        )
    )

    by_email = {record["emails"][0]: record for record in records if record["emails"]}
    muskan = by_email["muskan@example.com"]

    assert output.exists()
    assert muskan["full_name"] == "Muskan Sarraf"
    assert muskan["phones"] == ["+919876543210"]
    assert "FastAPI" in [skill["name"] for skill in muskan["skills"]]
    assert muskan["overall_confidence"] >= 0.8
    assert any(item["source"] == "github" for item in muskan["provenance"])


def test_custom_projection_renames_fields(tmp_path):
    output = tmp_path / "custom.json"
    records = run_pipeline(
        argparse.Namespace(
            ats_json="data/ats_sample.json",
            csv="data/recruiter_export.csv",
            github_json="data/github_sample.json",
            notes="data/recruiter_notes.txt",
            config="config/custom_config.json",
            output=str(output),
        )
    )

    assert "candidate_name" in records[0]
    assert "primary_email" in records[0]
    assert "provenance" not in records[0]
    assert json.loads(output.read_text(encoding="utf-8")) == records


def test_normalizers_handle_garbage_without_inventing_values():
    assert normalize_phone("abc") is None
    assert normalize_phone("9876543210") == "+919876543210"
    assert normalize_skill("postgres") == "PostgreSQL"
