# Candidate Data Transformer

Deterministic Python pipeline for turning messy candidate inputs into one canonical, trustworthy candidate profile per person.

The project follows the assignment flow:

```text
detect -> extract -> normalize -> deduplicate -> merge -> confidence -> project-to-output -> validate
```

## What It Handles

Structured sources:

- ATS JSON blob with non-canonical field names.
- Recruiter CSV export.

Unstructured sources:

- GitHub profile API snapshot.
- Free-text recruiter notes parsed with conservative regex extraction.

The sample data intentionally includes conflicts, duplicate people across sources, mixed phone formats, skill aliases, and malformed rows. Bad inputs are skipped or normalized to `null`; the pipeline does not invent missing facts.

## Canonical Output

The internal canonical record includes:

- `candidate_id`
- `full_name`
- `emails`
- `phones` in E.164-like format
- `location` with ISO country code
- `links`
- `headline`
- `years_experience`
- `skills` with confidence and sources
- `experience`
- `education`
- `provenance`
- `overall_confidence`

## Merge And Confidence Policy

Deduplication uses deterministic match keys:

- Email match first.
- Phone match second.
- Name match only when no stronger key exists.

When values conflict, higher-confidence sources win:

- ATS JSON: `0.90`
- Recruiter CSV: `0.85`
- GitHub: `0.70`
- Recruiter notes: `0.60`

Skills are merged by canonical skill name, and their source list is preserved. Overall confidence increases with source coverage, field coverage, and strong identity matches.

## Configurable Projection

The canonical record is separate from the output projection. Runtime config can:

- Select a subset of fields.
- Rename/remap fields with `from`.
- Apply normalizers such as `E164` and `canonical`.
- Toggle confidence and provenance.
- Choose missing-value behavior: `null`, `omit`, or `error`.

See:

- `config/default_config.json`
- `config/custom_config.json`

## Run Locally

Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Run the default schema:

```powershell
python main.py --config config/default_config.json --output output/result_default.json
```

Run the custom projection:

```powershell
python main.py --config config/custom_config.json --output output/result_custom.json
```

Run tests:

```powershell
python -m pytest -q
```

## Produced Outputs

Generated sample outputs are committed for review:

- `output/result_default.json`
- `output/result_custom.json`

The required one-page technical design PDF is included at:

- `output/pdf/MuskanSarraf_Eightfold_Design_Final_v3.pdf`

## Project Structure

```text
adapters/       source-specific extraction
config/         default and custom output configs
data/           sample inputs
models/         canonical Pydantic models
services/       normalize, merge, project, validate
tests/          regression tests
output/         generated JSON and PDF deliverables
```

## Assumptions And Scope

- GitHub input is a saved API-like JSON snapshot, not a live network call, to keep the demo deterministic.
- Recruiter notes are parsed conservatively. If a note block has no usable identity, it is ignored.
- Resume PDF/DOCX parsing is left out to keep the project focused and explainable under time pressure.
- The CLI is intentionally thin because correctness, traceability, and runtime projection are the core assignment criteria.
