from models.candidate import Candidate

candidate = Candidate(
    full_name="Muskan Sarraf",
    emails=["muskan@gmail.com"]
)

print(candidate.model_dump())