import re
from pathlib import Path

from analysis.quantum_risk import (
    assess_quantum_risk,
    assess_security_risk,
)
from analysis.recommendations import get_recommendation


CRYPTO_PATTERNS = {
    "RSA": [
        re.compile(
            r"\brsa\s*\.\s*(generate_private_key|generate_key|new|"
            r"privatekey|publickey)\s*\(",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bRSA(?:\.|_|\s|-)?(?:PRIVATE|PUBLIC)?KEY\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bRSA\s*(?:2048|3072|4096)\b",
            re.IGNORECASE,
        ),
    ],

    "ECDSA": [
        re.compile(
            r"\bec\s*\.\s*generate_private_key\s*\(",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bECDSA\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:ECDSA|ec)\b.*\b(?:sign|verify)\b",
            re.IGNORECASE,
        ),
    ],

    "ECDH": [
        re.compile(
            r"\bECDH\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\becdh\b.*\b(?:exchange|derive|shared)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bexchange\s*\(\s*ecdh\b",
            re.IGNORECASE,
        ),
    ],

    "Diffie-Hellman": [
        re.compile(
            r"\b(?:diffie[-_\s]?hellman|DH)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:dh|diffie_hellman)\b.*\b(?:exchange|derive|shared)\b",
            re.IGNORECASE,
        ),
    ],

    "AES": [
        re.compile(
            r"\bAES(?:GCM|CCM|CTR|CBC|ECB)?\s*\(",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bAES(?:[-_ ]?(?:128|192|256))?\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:encrypt|decrypt)\b.*\bAES\b",
            re.IGNORECASE,
        ),
    ],

    "DES": [
        re.compile(
            r"\b(?:DES|3DES|TripleDES|Triple-DES)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:DES|3DES|TripleDES|Triple-DES)\s*\(",
            re.IGNORECASE,
        ),
    ],

    "SHA-1": [
        re.compile(
            r"\b(?:sha1|sha-1)\s*\(",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bhashlib\s*\.\s*sha1\s*\(",
            re.IGNORECASE,
        ),
    ],

    "SHA-256": [
        re.compile(
            r"\b(?:sha256|sha-256)\s*\(",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bhashlib\s*\.\s*sha256\s*\(",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bSHA[-_ ]?256\b",
            re.IGNORECASE,
        ),
    ],

    "SHA-384": [
        re.compile(
            r"\b(?:sha384|sha-384)\s*\(",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bhashlib\s*\.\s*sha384\s*\(",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bSHA[-_ ]?384\b",
            re.IGNORECASE,
        ),
    ],

    "SHA-512": [
        re.compile(
            r"\b(?:sha512|sha-512)\s*\(",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bhashlib\s*\.\s*sha512\s*\(",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bSHA[-_ ]?512\b",
            re.IGNORECASE,
        ),
    ],

    "MD5": [
        re.compile(
            r"\b(?:md5|MD5)\s*\(",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bhashlib\s*\.\s*md5\s*\(",
            re.IGNORECASE,
        ),
    ],

    "TLS": [
        re.compile(
            r"\bssl\s*\.\s*SSLContext\s*\(",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bPROTOCOL_TLS(?:_CLIENT|_SERVER)?\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:minimum_version|maximum_version|"
            r"set_ciphers|verify_mode|check_hostname)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bTLS\s*1\.[0-3]\b",
            re.IGNORECASE,
        ),
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
    if algorithm in {
        "RSA",
        "ECDSA",
        "ECDH",
        "Diffie-Hellman",
    }:
        return "Asymmetric"

    if algorithm in {
        "AES",
        "DES",
    }:
        return "Symmetric"

    if algorithm in {
        "SHA-1",
        "SHA-256",
        "SHA-384",
        "SHA-512",
        "MD5",
    }:
        return "Hash"

    if algorithm == "TLS":
        return "Protocol"

    return "Unknown"


def get_detection_method(
    algorithm,
    line,
    pattern_index,
):
    stripped = line.strip()

    if algorithm == "TLS":
        return "protocol_configuration"

    if re.search(
        r"\b(?:rsa|ec|hashlib)\s*\.\s*\w+\s*\(",
        stripped,
        re.IGNORECASE,
    ):
        return "api_invocation"

    if re.search(
        r"\b(?:AESGCM|AESCCM|AES|DES|"
        r"TripleDES|SSLContext)\s*\(",
        stripped,
        re.IGNORECASE,
    ):
        return "api_invocation"

    if pattern_index == 0:
        return "api_invocation"

    if re.search(
        r"\b(?:cipher|minimum_version|maximum_version|"
        r"set_ciphers|verify_mode|check_hostname)\b",
        stripped,
        re.IGNORECASE,
    ):
        return "configuration"

    if re.search(
        r"\b(?:RSA|ECDSA|ECDH|Diffie[-_\s]?Hellman|"
        r"AES|DES|SHA[-_ ]?(?:1|256|384|512)|MD5)\b",
        stripped,
        re.IGNORECASE,
    ):
        return "algorithm_reference"

    return "pattern_match"


def get_detection_confidence(
    algorithm,
    line,
    detection_method,
):
    if detection_method in {
        "api_invocation",
        "protocol_configuration",
    }:
        return "high"

    if algorithm in {
        "RSA",
        "ECDSA",
        "ECDH",
        "Diffie-Hellman",
    }:
        if re.search(
            r"\b(?:generate_private_key|generate_key|"
            r"ECDSA|ECDH|Diffie[-_\s]?Hellman)\b",
            line,
            re.IGNORECASE,
        ):
            return "high"

    if detection_method in {
        "configuration",
        "algorithm_reference",
    }:
        return "medium"

    return "medium"


def get_purpose_confidence(purpose):
    if purpose in {
        "digital_signature",
        "encryption",
        "hashing",
        "protocol",
    }:
        return "high"

    if purpose == "key_establishment":
        return "medium"

    return "low"


def infer_crypto_purpose(
    algorithm,
    line,
    evidence_context,
):
    context_lines = []

    for entry in evidence_context:
        if isinstance(entry, dict):
            context_lines.append(
                str(entry.get("text", ""))
            )
        else:
            context_lines.append(str(entry))

    local_context = " ".join(
        [str(line)] + context_lines
    ).lower()

    if algorithm in {
        "SHA-1",
        "SHA-256",
        "SHA-384",
        "SHA-512",
        "MD5",
    }:
        return "hashing"

    if algorithm in {
        "AES",
        "DES",
    }:
        return "encryption"

    if algorithm == "ECDSA":
        if re.search(
            r"\b(?:sign|signature|signing|verify|"
            r"verification|signing_key)\b",
            local_context,
        ):
            return "digital_signature"

        return "unknown"

    if algorithm == "ECDH":
        if re.search(
            r"\b(?:exchange|shared_secret|shared_key|"
            r"derive|key_establishment|ecdh)\b",
            local_context,
        ):
            return "key_establishment"

        return "unknown"

    if algorithm == "Diffie-Hellman":
        if re.search(
            r"\b(?:exchange|shared_secret|shared_key|"
            r"derive|key_establishment|"
            r"diffie[-_\s]?hellman)\b",
            local_context,
        ):
            return "key_establishment"

        return "unknown"

    if algorithm == "RSA":
        if re.search(
            r"\b(?:sign|signature|signing|verify|"
            r"verification)\b",
            local_context,
        ):
            return "digital_signature"

        if re.search(
            r"\b(?:encrypt|encryption|decrypt|decryption|"
            r"ciphertext|plaintext|rsa_encrypt|rsa_decrypt)\b",
            local_context,
        ):
            return "encryption"

        if re.search(
            r"\b(?:key[_ -]?transport|key[_ -]?exchange|"
            r"key[_ -]?establishment|oaep|keywrap)\b",
            local_context,
        ):
            return "key_establishment"

        return "unknown"

    if algorithm == "TLS":
        return "protocol"

    return "unknown"


def build_evidence_context(
    lines,
    line_number,
    radius=2,
):
    index = line_number - 1

    start = max(
        0,
        index - radius,
    )

    end = min(
        len(lines),
        index + radius + 1,
    )

    context = []

    for position in range(start, end):
        context.append(
            {
                "line": position + 1,
                "text": lines[position].rstrip(),
            }
        )

    return context


def build_artifact_id(
    file_path,
    line_number,
    algorithm,
):
    return (
        f"{file_path}:{line_number}:{algorithm}"
    )


def detect_algorithm_details(
    algorithm,
    line,
):
    details = {}

    key_size_match = re.search(
        r"key_size\s*=\s*(\d+)",
        line,
        re.IGNORECASE,
    )

    if key_size_match:
        details["key_size"] = int(
            key_size_match.group(1)
        )

    curve_match = re.search(
        r"SECP\d+[RK]\d+|P-\d+",
        line,
        re.IGNORECASE,
    )

    if curve_match:
        details["curve"] = (
            curve_match.group(0).upper()
        )

    if algorithm == "AES":
        mode_match = re.search(
            r"\b(AESGCM|AESCCM|AESCTR|AESCBC|AEAD)\b",
            line,
            re.IGNORECASE,
        )

        if mode_match:
            details["mode"] = (
                mode_match.group(1).upper()
            )

        if re.search(
            r"\bAESGCM\b",
            line,
            re.IGNORECASE,
        ):
            details["mode"] = "GCM"

    if algorithm == "TLS":
        protocol_match = re.search(
            r"\b(PROTOCOL_TLS(?:_CLIENT|_SERVER)?)\b",
            line,
            re.IGNORECASE,
        )

        if protocol_match:
            details["protocol"] = (
                protocol_match.group(1).upper()
            )

        tls_version_match = re.search(
            r"\bTLS\s*([0-9](?:\.[0-9])?)\b",
            line,
            re.IGNORECASE,
        )

        if tls_version_match:
            details["version"] = (
                tls_version_match.group(1)
            )

    return details


def scan_file(file_path):
    findings = []

    try:
        text = Path(file_path).read_text(
            encoding="utf-8",
            errors="ignore",
        )
    except OSError:
        return findings

    lines = text.splitlines()

    for line_number, line in enumerate(
        lines,
        start=1,
    ):
        for algorithm, patterns in CRYPTO_PATTERNS.items():
            matched_pattern_index = None

            for pattern_index, pattern in enumerate(
                patterns
            ):
                if pattern.search(line):
                    matched_pattern_index = (
                        pattern_index
                    )
                    break

            if matched_pattern_index is None:
                continue

            evidence_context = (
                build_evidence_context(
                    lines,
                    line_number,
                    radius=2,
                )
            )

            detection_method = (
                get_detection_method(
                    algorithm,
                    line,
                    matched_pattern_index,
                )
            )

            confidence = (
                get_detection_confidence(
                    algorithm,
                    line,
                    detection_method,
                )
            )

            purpose = infer_crypto_purpose(
                algorithm,
                line,
                evidence_context,
            )

            purpose_confidence = (
                get_purpose_confidence(
                    purpose
                )
            )

            details = detect_algorithm_details(
                algorithm,
                line,
            )

            finding = {
                "artifact_id": build_artifact_id(
                    str(file_path),
                    line_number,
                    algorithm,
                ),
                "algorithm": algorithm,
                "type": get_crypto_type(
                    algorithm
                ),
                "file": str(file_path),
                "line": line_number,
                "evidence": line.strip(),
                "evidence_context": evidence_context,
                "detection_method": detection_method,
                "confidence": confidence,
                "purpose": purpose,
                "purpose_confidence": (
                    purpose_confidence
                ),
                "details": details,
            }

            findings.append(finding)

    return findings


def normalize_findings(findings):
    normalized = []

    for finding in findings:
        artifact = dict(finding)

        security_result = assess_security_risk(
            artifact
        )
        quantum_result = assess_quantum_risk(
            artifact
        )

        artifact["security_risk"] = (
            security_result.get(
                "security_risk",
                "MEDIUM",
            )
        )
        artifact["security_reason"] = (
            security_result.get(
                "risk_reason",
                "",
            )
        )

        if isinstance(quantum_result, dict):
            artifact["quantum_risk"] = (
                quantum_result.get(
                    "quantum_risk",
                    "MEDIUM",
                )
            )
            artifact["quantum_reason"] = (
                quantum_result.get(
                    "risk_reason",
                    "",
                )
            )
        else:
            artifact["quantum_risk"] = quantum_result
            artifact["quantum_reason"] = ""

        artifact["risk_reason"] = artifact["security_reason"]

        artifact["recommendation"] = (
            get_recommendation(artifact)
        )

        normalized.append(artifact)

    return deduplicate_findings(normalized)


def deduplicate_findings(findings):
    """
    Collapse duplicate/consecutive detections that represent the same
    logical configuration construct.

    Currently this is intentionally conservative and only handles TLS
    configuration lines that occur within the same source file and within
    a small line-distance window.

    Future canonical modeling will represent one logical artifact with
    multiple evidence occurrences.
    """
    result = []

    for finding in findings:
        if finding.get("algorithm") != "TLS":
            result.append(finding)
            continue

        duplicate = None

        for existing in reversed(result):
            if existing.get("algorithm") != "TLS":
                continue

            if existing.get("file") != finding.get("file"):
                continue

            existing_line = existing.get("line")
            current_line = finding.get("line")

            if (
                isinstance(existing_line, int)
                and isinstance(current_line, int)
                and current_line - existing_line <= 2
            ):
                duplicate = existing
                break

            if (
                isinstance(existing_line, int)
                and isinstance(current_line, int)
                and current_line < existing_line
            ):
                break

        if duplicate is None:
            result.append(finding)
            continue

        existing_context = duplicate.setdefault(
            "evidence_context",
            [],
        )

        current_context = finding.get(
            "evidence_context",
            [],
        )

        seen = {
            (
                entry.get("line"),
                entry.get("text"),
            )
            for entry in existing_context
            if isinstance(entry, dict)
        }

        for entry in current_context:
            if not isinstance(entry, dict):
                continue

            key = (
                entry.get("line"),
                entry.get("text"),
            )

            if key not in seen:
                existing_context.append(entry)
                seen.add(key)

        existing_evidence = duplicate.get(
            "evidence",
            "",
        )

        current_evidence = finding.get(
            "evidence",
            "",
        )

        if current_evidence and (
            current_evidence
            != existing_evidence
        ):
            duplicate["evidence"] = (
                existing_evidence
                + "\n"
                + current_evidence
            )

        existing_details = duplicate.setdefault(
            "details",
            {},
        )

        current_details = finding.get(
            "details",
            {},
        )

        for key, value in current_details.items():
            if value is not None:
                existing_details[key] = value

    return result

def build_risk_summary(artifacts):
    summary = {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
    }

    for artifact in artifacts:
        risk = artifact.get(
            "security_risk",
            artifact.get("quantum_risk", "MEDIUM"),
        )

        if isinstance(risk, dict):
            risk = risk.get(
                "security_risk",
                risk.get("quantum_risk", "MEDIUM"),
            )

        if risk in summary:
            summary[risk] += 1

    return summary


def scan_repository(root_path):
    root = Path(root_path)

    if not root.exists():
        return {
            "target": str(root),
            "total_files_scanned": 0,
            "total_artifacts": 0,
            "quantum_vulnerable_assets": 0,
            "risk_summary": {
                "CRITICAL": 0,
                "HIGH": 0,
                "MEDIUM": 0,
                "LOW": 0,
            },
            "artifacts": [],
        }

    all_findings = []
    files_scanned = 0

    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue

        if (
            file_path.suffix.lower()
            not in SUPPORTED_EXTENSIONS
        ):
            continue

        files_scanned += 1

        findings = scan_file(file_path)
        all_findings.extend(findings)

    artifacts = normalize_findings(
        all_findings
    )

    risk_summary = build_risk_summary(
        artifacts
    )

    quantum_vulnerable_assets = sum(
        1
        for artifact in artifacts
        if artifact.get("quantum_risk")
        in {"CRITICAL", "HIGH"}
    )

    return {
        "target": str(root),
        "total_files_scanned": files_scanned,
        "total_artifacts": len(artifacts),
        "quantum_vulnerable_assets": (
            quantum_vulnerable_assets
        ),
        "risk_summary": risk_summary,
        "artifacts": artifacts,
    }
