import hashlib
from datasketch import MinHash


def generate_minhash(text: str, num_perm: int = 128) -> MinHash:
    m = MinHash(num_perm=num_perm)
    for token in text.lower().split():
        m.update(token.encode("utf-8"))
    return m


def jaccard_similarity(m1: MinHash, m2: MinHash) -> float:
    return m1.jaccard(m2)


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
