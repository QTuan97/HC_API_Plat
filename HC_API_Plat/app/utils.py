import re

def normalize_project_name(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r'\s+', '_', s)              # spaces → underscore
    s = re.sub(r'_+', '_', s)               # collapse multiple underscores
    s = re.sub(r'[^a-z0-9_.,]', '', s)      # allow only a–z, 0–9, _, . and ,
    return s.rstrip('_. ,')                 # remove trailing underscores, dots, commas
