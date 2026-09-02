import re
from pathlib import Path
from analysis.quantum_risk import assess_quantum_risk
from analysis.recommendations import get_recommendation


CRYPTO_PATTERNS = {
    "RSA": [
        r"\brsa\.generate_private_key\s*\(",
        r"\bRSA\.generate\s*\(",
        r"\bRSA_generate_key\b",
        r"\bRSA_new\b",
    ],

    "ECDSA": [
        r"\bec\.generate_private_key\s*\(",
        r"\bECDSA\b",
        r"\bSECP256R1\b",
        r"\bSECP384R1\b",
        r"\bSECP521R1\b",
    ],

    "ECDH": [
        r"\bECDH\b",
        r"\becdh\b",
        r"\.exchange\s*\(",
    ],

    "Diffie-Hellman": [
        r"\bDiffie[- ]Hellman\b",
        r"\bDH_generate_key\b",
        r"\bdh\.generate_parameters\s*\(",
    ],

    "AES": [
        r"\bAESGCM\s*\(",
        r"\bAESCCM\s*\(",
        r"\bAES\.new\s*\(",
        r"\bCipher\s*\(\s*algorithms\.AES",
    ],

    "DES": [
        r"\bDES\.new\s*\(",
        r"\bTripleDES\s*\(",
        r"\b3DES\b",
    ],

    "SHA-1": [
        r"\bhashlib\.sha1\s*\(",
        r"\bSHA1\s*\(",
    ],

    "SHA-256": [
        r"\bhashlib\.sha256\s*\(",
        r"\bSHA256\s*\(",
    ],

    "SHA-384": [
        r"\bhashlib\.sha384\s*\(",
        r"\bSHA384\s*\(",
    ],

    "SHA-512": [
        r"\bhashlib\.sha512\s*\(",
        r"\bSHA512\s*\(",
    ],

    "MD5": [
        r"\bhashlib\.md5\s*\(",
        r"\bMD5\s*\(",
    ],

    "TLS": [
        r"\bssl\.SSLContext\s*\(",
        r"\bPROTOCOL_TLS(?:_CLIENT|_SERVER)?\b",
        r"\bTLSv1(?:\.[0-3])?\b",
    ],
}


SUPPORTED_EXTENSIONS = {
    ".py",
    ".java",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".c",
    ".cpp",
    ".cc",
    ".h",
    ".hpp",
    ".cs",
    ".go",
    ".rs",
    ".php",
    ".rb",
    ".swift",
    ".kt",
    ".kts",
    ".xml",
    ".json",
    ".yaml",
    ".yml",
    ".conf",
    ".ini",
    ".properties",
}


def get_crypto_type(algorithm):
    crypto_types = {
        "RSA": "Asymmetric",
        "ECDSA": "Asymmetric",
        "ECDH": "Asymmetric",
        "Diffie-Hellman": "Asymmetric",

        "AES": "Symmetric",
        "DES": "Symmetric",

        "SHA-1": "Hash",
        "SHA-256": "Hash",
        "SHA-384": "Hash",
        "SHA-512": "Hash",
        "MD5": "Hash",

        "TLS": "Protocol",
    }

    return crypto_types.get(algorithm, "Unknown")


def detect_algorithm_details(algorithm, lines, line_index):
    details = {}

    context_start = max(0, line_index - 1)
    context_end = min(len(lines), line_index + 5)

    context = "\n".join(
        lines[context_start:context_end]
    )

    if algorithm == "RSA":
        match = re.search(
            r"key_size\s*=\s*(\d{3,5})",
            context,
            re.IGNORECASE,
        )

        if match:
            details["key_size"] = int(match.group(1))

    elif algorithm == "ECDSA":
        curve_patterns = {
            "SECP256R1": 256,
            "SECP384R1": 384,
            "SECP521R1": 521,
        }

        for curve, key_size in curve_patterns.items():
            if curve in context:
                details["curve"] = curve
                details["key_size"] = key_size
                break

    elif algorithm == "AES":
        if "AESGCM" in context:
            details["mode"] = "GCM"
        elif "AESCCM" in context:
            details["mode"] = "CCM"
        elif re.search(r"MODE_GCM", context, re.IGNORECASE):
            details["mode"] = "GCM"
        elif re.search(r"MODE_CBC", context, re.IGNORECASE):
            details["mode"] = "CBC"
        elif re.search(r"MODE_CTR", context, re.IGNORECASE):
            details["mode"] = "CTR"
        elif re.search(r"MODE_ECB", context, re.IGNORECASE):
            details["mode"] = "ECB"

        key_match = re.search(
            r"""(?:b["'][^"']*["']\s*\*\s*)(\d+)""",
            context,
        )

        if key_match:
            byte_count = int(key_match.group(1))
            details["key_size"] = byte_count * 8

    elif algorithm == "TLS":
        version_match = re.search(
            r"TLSv1(?:\.[0-3])?",
            context,
            re.IGNORECASE,
        )

        if version_match:
            details["version"] = version_match.group(0)

        if "PROTOCOL_TLS_CLIENT" in context:
            details["context"] = "Client"

        elif "PROTOCOL_TLS_SERVER" in context:
            details["context"] = "Server"

    return details


def scan_file(file_path):
    findings = []

    try:
        content = file_path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    except Exception:
        return findings

    lines = content.splitlines()

    for index, line in enumerate(lines):
        stripped = line.strip()

        if not stripped:
            continue

        # Imports prove a dependency exists but not necessarily
        # an actual cryptographic operation.
        if stripped.startswith(("import ", "from ")):
            continue

        for algorithm, patterns in CRYPTO_PATTERNS.items():
            matched = False

            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    matched = True
                    break

            if not matched:
                continue

            details = detect_algorithm_details(
                algorithm,
                lines,
                index,
            )

            finding = {
                "algorithm": algorithm,
                "type": get_crypto_type(algorithm),
                "file": str(file_path),
                "line": index + 1,
                "evidence": stripped[:300],
                "details": details,
            }

            findings.append(finding)

    return findings


def normalize_findings(findings):
    normalized = []

    for finding in findings:

        duplicate = False

        for existing in normalized:

            same_algorithm = (
                existing["algorithm"]
                == finding["algorithm"]
            )

            same_file = (
                existing["file"]
                == finding["file"]
            )

            close_lines = abs(
                existing["line"]
                - finding["line"]
            ) <= 3

            if (
                same_algorithm
                and same_file
                and close_lines
            ):
                existing["details"].update(
                    finding["details"]
                )

                duplicate = True
                break

        if not duplicate:
            normalized.append(finding)

    return normalized


def scan_repository(repository_path):
    repository = Path(repository_path)

    if not repository.exists():
        raise FileNotFoundError(
            f"Repository does not exist: {repository}"
        )

    raw_findings = []
    files_scanned = 0

    for file_path in repository.rglob("*"):

        if not file_path.is_file():
            continue

        if (
            file_path.suffix.lower()
            not in SUPPORTED_EXTENSIONS
        ):
            continue

        files_scanned += 1

        raw_findings.extend(
            scan_file(file_path)
        )

    findings = normalize_findings(
        raw_findings
    )

    for artifact in findings:
        risk = assess_quantum_risk(artifact)

        artifact["quantum_risk"] = risk["quantum_risk"]
        artifact["risk_reason"] = risk["risk_reason"]

        artifact["recommendation"] = get_recommendation(
            artifact
        )

    risk_summary = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    for artifact in findings:
        risk_level = artifact[
            "quantum_risk"
        ].lower()

        if risk_level in risk_summary:
            risk_summary[risk_level] += 1

    return {
        "target": str(repository),
        "total_files_scanned": files_scanned,
        "total_artifacts": len(findings),
        "risk_summary": risk_summary,
        "artifacts": findings,
    }