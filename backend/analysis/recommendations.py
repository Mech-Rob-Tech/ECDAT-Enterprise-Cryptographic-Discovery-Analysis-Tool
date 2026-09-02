def get_recommendation(artifact):
    algorithm = artifact["algorithm"]

    if algorithm == "RSA":
        return (
            "Determine the cryptographic purpose. For key establishment "
            "or encryption workflows, evaluate migration toward ML-KEM "
            "or an appropriate hybrid mechanism. For digital signatures, "
            "evaluate ML-DSA, SLH-DSA, or an appropriate hybrid signature."
        )

    if algorithm == "ECDSA":
        return (
            "Evaluate migration toward ML-DSA, SLH-DSA, or an appropriate "
            "hybrid digital-signature mechanism."
        )

    if algorithm in {
        "ECDH",
        "Diffie-Hellman"
    }:
        return (
            "Evaluate ML-KEM or an appropriate hybrid key-establishment "
            "mechanism combining classical and post-quantum techniques."
        )

    if algorithm == "AES":
        return (
            "No urgent post-quantum replacement is required when using "
            "an appropriate key size such as AES-256. Continue monitoring "
            "cryptographic standards and implementation security."
        )

    if algorithm == "SHA-256":
        return (
            "No immediate post-quantum migration is required. Continue "
            "using an approved modern hash construction appropriate to "
            "the application's security requirements."
        )

    if algorithm in {
        "SHA-384",
        "SHA-512"
    }:
        return (
            "No immediate PQC replacement is required. Continue monitoring "
            "standards and ensure the hash function is used appropriately."
        )

    if algorithm == "SHA-1":
        return (
            "Replace SHA-1 with an approved modern hash algorithm such "
            "as SHA-256, SHA-384 or SHA-512 depending on the use case."
        )

    if algorithm == "MD5":
        return (
            "Replace MD5 immediately for security-sensitive applications "
            "with an approved modern hash algorithm appropriate to the "
            "specific use case."
        )

    if algorithm == "DES":
        return (
            "Replace DES or legacy 3DES usage with an approved modern "
            "symmetric cipher such as AES using an appropriate key size "
            "and authenticated mode."
        )

    if algorithm == "TLS":
        return (
            "Inspect the configured TLS version, cipher suites, "
            "authentication algorithm and key-exchange mechanism. "
            "Plan migration toward standards-approved PQC or hybrid TLS "
            "mechanisms where quantum-vulnerable public-key algorithms "
            "are currently used."
        )

    return (
        "Perform manual cryptographic review and determine an appropriate "
        "migration strategy based on the artifact's purpose and risk."
    )