def assess_security_risk(artifact):
    """
    Cryptographic security severity for the current finding.

    This is independent of post-quantum migration relevance.
    Broken classical algorithms can be CRITICAL here even when they
    are not quantum-vulnerable.
    """
    algorithm = artifact["algorithm"]
    details = artifact.get("details", {})

    if algorithm in {"MD5", "SHA-1", "DES"}:
        return {
            "security_risk": "CRITICAL",
            "risk_reason": (
                f"{algorithm} is cryptographically inadequate for "
                "security-sensitive use and should be replaced. "
                "This severity is driven by classical cryptographic "
                "weakness, not by a quantum-computing claim."
            ),
        }

    if algorithm in {"RSA", "ECDSA", "ECDH", "Diffie-Hellman"}:
        return {
            "security_risk": "HIGH",
            "risk_reason": (
                f"{algorithm} remains in use as public-key cryptography "
                "that requires migration planning because of known "
                "quantum cryptanalysis against the underlying problem."
            ),
        }

    if algorithm == "AES":
        key_size = details.get("key_size") or artifact.get("key_size")

        if key_size and key_size < 256:
            return {
                "security_risk": "MEDIUM",
                "risk_reason": (
                    f"AES-{key_size} is currently usable but has a "
                    "reduced security margin under Grover-style search."
                ),
            }

        return {
            "security_risk": "LOW",
            "risk_reason": (
                "AES with a 256-bit key remains an approved modern "
                "symmetric construction for the current assessment."
            ),
        }

    if algorithm in {"SHA-256", "SHA-384", "SHA-512"}:
        return {
            "security_risk": "LOW",
            "risk_reason": (
                f"{algorithm} is an approved modern hash construction "
                "for the current assessment."
            ),
        }

    if algorithm == "TLS":
        return {
            "security_risk": "MEDIUM",
            "risk_reason": (
                "TLS security depends on the configured authentication "
                "and key-establishment algorithms and requires inspection."
            ),
        }

    return {
        "security_risk": "MEDIUM",
        "risk_reason": (
            "Further cryptographic security assessment is required."
        ),
    }


def assess_quantum_risk(artifact):
    """
    Quantum-migration relevance for the current finding.

    Do not classify classically broken algorithms as quantum-critical.
    """
    algorithm = artifact["algorithm"]
    details = artifact.get("details", {})

    if algorithm == "RSA":
        return {
            "quantum_risk": "HIGH",
            "risk_reason": (
                "RSA relies on integer factorisation and is vulnerable "
                "to sufficiently capable cryptographically relevant "
                "quantum computers using Shor's algorithm."
            ),
        }

    if algorithm in {"ECDSA", "ECDH", "Diffie-Hellman"}:
        return {
            "quantum_risk": "HIGH",
            "risk_reason": (
                f"{algorithm} relies on mathematical problems that "
                "can be efficiently attacked by sufficiently capable "
                "quantum computers using Shor's algorithm."
            ),
        }

    if algorithm == "AES":
        key_size = details.get("key_size") or artifact.get("key_size")

        if key_size and key_size < 256:
            return {
                "quantum_risk": "MEDIUM",
                "risk_reason": (
                    f"AES-{key_size} is not broken by Shor's algorithm, "
                    "but quantum search techniques such as Grover's "
                    "algorithm reduce its effective security margin."
                ),
            }

        return {
            "quantum_risk": "LOW",
            "risk_reason": (
                "AES-256 is not affected by Shor's algorithm and "
                "retains substantial security against known quantum "
                "search advantages."
            ),
        }

    if algorithm == "MD5":
        return {
            "quantum_risk": "LOW",
            "risk_reason": (
                "MD5 is classically broken and must be replaced, but "
                "that urgency is not caused by quantum computing. "
                "It is not a post-quantum public-key migration case."
            ),
        }

    if algorithm == "SHA-1":
        return {
            "quantum_risk": "LOW",
            "risk_reason": (
                "SHA-1 is classically insecure for collision-sensitive "
                "use. That finding is independent of quantum threats "
                "and is not a Shor-algorithm public-key exposure."
            ),
        }

    if algorithm in {"SHA-256", "SHA-384", "SHA-512"}:
        return {
            "quantum_risk": "LOW",
            "risk_reason": (
                f"{algorithm} is affected less dramatically by known "
                "quantum algorithms than RSA or elliptic-curve "
                "cryptography and does not require the same immediate "
                "PQC migration priority."
            ),
        }

    if algorithm == "DES":
        return {
            "quantum_risk": "LOW",
            "risk_reason": (
                "DES and legacy 3DES are inadequate for modern security "
                "independently of future quantum threats. Replacement "
                "is required, but not because of Shor-algorithm exposure."
            ),
        }

    if algorithm == "TLS":
        return {
            "quantum_risk": "MEDIUM",
            "risk_reason": (
                "TLS quantum exposure depends on the configured "
                "authentication and key-establishment algorithms. "
                "RSA, ECDSA, ECDH or finite-field Diffie-Hellman "
                "within TLS may require PQC or hybrid migration."
            ),
        }

    return {
        "quantum_risk": "MEDIUM",
        "risk_reason": (
            "The quantum-security properties of this cryptographic "
            "artifact require further assessment."
        ),
    }
