from collections import defaultdict

from models.candidate import Candidate, Provenance, Skill


SOURCE_PRIORITY = {
    "ats_json": 0.9,
    "recruiter_csv": 0.85,
    "github": 0.7,
    "recruiter_notes": 0.6,
}


def merge_candidates(candidates: list[Candidate]) -> list[Candidate]:
    groups = _group_candidates(candidates)
    return [_merge_group(group) for group in groups]


def _group_candidates(candidates: list[Candidate]) -> list[list[Candidate]]:
    parent = list(range(len(candidates)))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left, right):
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    key_owner = {}
    for index, candidate in enumerate(candidates):
        keys = [f"email:{email}" for email in candidate.emails]
        keys.extend(f"phone:{phone}" for phone in candidate.phones)
        if not keys and candidate.full_name:
            keys.append(f"name:{candidate.full_name.lower()}")
        for key in keys:
            if key in key_owner:
                union(index, key_owner[key])
            else:
                key_owner[key] = index

    grouped = defaultdict(list)
    for index, candidate in enumerate(candidates):
        grouped[find(index)].append(candidate)
    return list(grouped.values())


def _merge_group(group: list[Candidate]) -> Candidate:
    ranked = sorted(group, key=_candidate_rank, reverse=True)
    best = ranked[0]
    merged = Candidate(
        candidate_id=best.candidate_id,
        full_name=_pick_scalar(ranked, "full_name"),
        emails=_unique(value for candidate in ranked for value in candidate.emails),
        phones=_unique(value for candidate in ranked for value in candidate.phones),
        location=_pick_location(ranked),
        links=_merge_links(ranked),
        headline=_pick_scalar(ranked, "headline"),
        years_experience=_pick_scalar(ranked, "years_experience"),
        skills=_merge_skills(ranked),
        experience=[item for candidate in ranked for item in candidate.experience],
        education=[item for candidate in ranked for item in candidate.education],
        provenance=[item for candidate in ranked for item in candidate.provenance],
    )
    merged.overall_confidence = _confidence(merged, group)
    merged.provenance.append(
        Provenance(field="overall_confidence", source="merge_engine", method="weighted_source_coverage", confidence=merged.overall_confidence)
    )
    return merged


def _candidate_rank(candidate: Candidate) -> float:
    return max((item.confidence for item in candidate.provenance), default=candidate.overall_confidence)


def _pick_scalar(candidates: list[Candidate], field: str):
    for candidate in candidates:
        value = getattr(candidate, field)
        if value not in (None, "", []):
            return value
    return None


def _pick_location(candidates: list[Candidate]):
    location = candidates[0].location.model_copy()
    for candidate in candidates[1:]:
        if not location.city and candidate.location.city:
            location.city = candidate.location.city
        if not location.region and candidate.location.region:
            location.region = candidate.location.region
        if not location.country and candidate.location.country:
            location.country = candidate.location.country
    return location


def _merge_links(candidates: list[Candidate]):
    links = candidates[0].links.model_copy(deep=True)
    for candidate in candidates[1:]:
        links.github = links.github or candidate.links.github
        links.linkedin = links.linkedin or candidate.links.linkedin
        links.portfolio = links.portfolio or candidate.links.portfolio
        links.other = _unique([*links.other, *candidate.links.other])
    return links


def _merge_skills(candidates: list[Candidate]) -> list[Skill]:
    skill_map = {}
    for candidate in candidates:
        for skill in candidate.skills:
            key = skill.name.lower()
            if key not in skill_map:
                skill_map[key] = Skill(name=skill.name, confidence=skill.confidence, sources=list(skill.sources))
            else:
                existing = skill_map[key]
                existing.confidence = round(max(existing.confidence, skill.confidence), 2)
                existing.sources = _unique([*existing.sources, *skill.sources])
    return sorted(skill_map.values(), key=lambda skill: skill.name.lower())


def _confidence(candidate: Candidate, group: list[Candidate]) -> float:
    source_count = len({source for item in candidate.provenance for source in [item.source] if source in SOURCE_PRIORITY})
    filled_fields = sum(
        1
        for value in [
            candidate.full_name,
            candidate.emails,
            candidate.phones,
            candidate.headline,
            candidate.skills,
            candidate.location.country,
        ]
        if value
    )
    score = 0.35 + min(source_count, 3) * 0.15 + min(filled_fields, 6) * 0.035
    if len(group) > 1 and candidate.emails:
        score += 0.1
    return round(min(score, 0.99), 2)


def _unique(values):
    seen = set()
    output = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            output.append(value)
    return output
