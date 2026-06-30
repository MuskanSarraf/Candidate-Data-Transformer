import argparse
import json
from pathlib import Path

from adapters.ats_adapter import load_ats_data
from adapters.csv_adapter import load_recruiter_csv
from adapters.github_adapter import load_github_data
from adapters.notes_adapter import load_recruiter_notes
from services.merger import merge_candidates
from services.normalizer import normalize_source_candidate
from services.projector import project_candidates
from services.validator import validate_projected


def run_pipeline(args: argparse.Namespace) -> list[dict]:
    source_candidates = []
    source_candidates.extend(load_ats_data(args.ats_json))
    source_candidates.extend(load_recruiter_csv(args.csv))
    source_candidates.extend(load_github_data(args.github_json))
    source_candidates.extend(load_recruiter_notes(args.notes))

    normalized = [
        candidate
        for candidate in (normalize_source_candidate(candidate) for candidate in source_candidates)
        if candidate.full_name or candidate.emails or candidate.phones
    ]
    merged = merge_candidates(normalized)

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    projected = project_candidates(merged, config)
    validate_projected(projected, config)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(projected, indent=2), encoding="utf-8")
    return projected


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build canonical candidate profiles from messy recruiting sources.")
    parser.add_argument("--ats-json", default="data/ats_sample.json", help="Path to ATS JSON blob.")
    parser.add_argument("--csv", default="data/recruiter_export.csv", help="Path to recruiter CSV export.")
    parser.add_argument("--github-json", default="data/github_sample.json", help="Path to GitHub profile API snapshot.")
    parser.add_argument("--notes", default="data/recruiter_notes.txt", help="Path to free-text recruiter notes.")
    parser.add_argument("--config", default="config/default_config.json", help="Projection config JSON.")
    parser.add_argument("--output", default="output/result_default.json", help="Where to write projected JSON.")
    return parser.parse_args()


def main() -> None:
    records = run_pipeline(parse_args())
    print(f"Wrote {len(records)} canonical candidate profile(s).")


if __name__ == "__main__":
    main()
