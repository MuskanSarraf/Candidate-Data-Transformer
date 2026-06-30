from typing import List, Optional
from pydantic import BaseModel


class Location(BaseModel):
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None


class Links(BaseModel):
    github: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None
    other: List[str] = []


class Skill(BaseModel):
    name: str
    confidence: float
    sources: List[str]


class Experience(BaseModel):
    company: str
    title: str
    start: Optional[str] = None
    end: Optional[str] = None
    summary: Optional[str] = None


class Education(BaseModel):
    institution: str
    degree: Optional[str] = None
    field: Optional[str] = None
    end_year: Optional[int] = None


class Provenance(BaseModel):
    field: str
    source: str
    method: str


class Candidate(BaseModel):
    candidate_id: Optional[str] = None
    full_name: Optional[str] = None

    emails: List[str] = []
    phones: List[str] = []

    location: Location = Location()
    links: Links = Links()

    headline: Optional[str] = None
    years_experience: Optional[float] = None

    skills: List[Skill] = []
    experience: List[Experience] = []
    education: List[Education] = []

    provenance: List[Provenance] = []

    overall_confidence: float = 0.0