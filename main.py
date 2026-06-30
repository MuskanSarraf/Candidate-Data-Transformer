from adapters.ats_adapter import load_ats_data


def main():
    candidates = load_ats_data("data/ats_sample.json")

    print("\n===== ATS Candidates =====\n")

    for i, candidate in enumerate(candidates, start=1):
        print(f"Candidate {i}")
        print(candidate.model_dump())
        print("-" * 60)


if __name__ == "__main__":
    main()