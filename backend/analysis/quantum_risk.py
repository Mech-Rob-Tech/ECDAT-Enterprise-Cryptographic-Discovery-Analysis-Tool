def assess_quantum_risk(artifact):
    algorithm = artifact["algorithm"]
    details = artifact.get("details", {})

    if algorithm == "RSA":
        return {
            "quantum_risk": "HIGH",
            "risk_reason": (
                "RSA relies on integer factorisation and is vulnerable "
                "to sufficiently capable cryptographically relevant "
                "quantum computers using Shor's algorithm."
            )
        }

    if algorithm in {
        "ECDSA",
        "ECDH",
        "Diffie-Hellman"
    }:
        return {
            "quantum_risk": "HIGH",
            "risk_reason": (
                f"{algorithm} relies on mathematical problems that "
                "can be efficiently attacked by sufficiently capable "
                "quantum computers using Shor's algorithm."
            )
        }

    if algorithm == "AES":
        key_size = details.get("key_size")

        if key_size and key_size < 256:
            return {
                "quantum_risk": "MEDIUM",
                "risk_reason": (
                    f"AES-{key_size} is not broken by Shor's algorithm, "
                    "but quantum search techniques such as Grover's "
                    "algorithm reduce its effective security margin."
                )
            }

        return {
            "quantum_risk": "LOW",
            "risk_reason": (
                "AES-256 is not affected by Shor's algorithm and "
                "retains substantial security against known quantum "
                "search advantages."
            )
        }

    if algorithm == "MD5":
        return {
            "quantum_risk": "CRITICAL",
            "risk_reason": (
                "MD5 is already cryptographically broken independently "
                "of quantum-computing threats and should not be used "
                "for security-sensitive purposes."
            )
        }

    if algorithm == "SHA-1":
        return {
            "quantum_risk": "CRITICAL",
            "risk_reason": (
                "SHA-1 is already considered cryptographically insecure "
                "for collision-sensitive security applications, "
                "independently of quantum threats."
            )
        }

    if algorithm in {
        "SHA-256",
        "SHA-384",
        "SHA-512"
    }:
        return {
            "quantum_risk": "LOW",
            "risk_reason": (
                f"{algorithm} is affected less dramatically by known "
                "quantum algorithms than RSA or elliptic-curve "
                "cryptography and does not require the same immediate "
                "PQC migration priority."
            )
        }

    if algorithm == "DES":
        return {
            "quantum_risk": "CRITICAL",
            "risk_reason": (
                "DES and legacy 3DES configurations provide inadequate "
                "security for modern applications and should be migrated "
                "regardless of future quantum threats."
            )
        }

    if algorithm == "TLS":
        return {
            "quantum_risk": "MEDIUM",
            "risk_reason": (
                "TLS quantum exposure depends on the configured "
                "authentication and key-establishment algorithms. "
                "RSA, ECDSA, ECDH or finite-field Diffie-Hellman "
                "within TLS may require PQC or hybrid migration."
            )
        }

    return {
        "quantum_risk": "MEDIUM",
        "risk_reason": (
            "The quantum-security properties of this cryptographic "
            "artifact require further assessment."
        )
    }