# ECDAT

## Enterprise Cryptographic Discovery & Analysis Tool

**SIH Problem Statement:** SIH26-26164  
**Organization:** National Technical Research Organisation (NTRO)  
**Theme:** Blockchain & Cybersecurity

---

## Overview

ECDAT is a software-based cryptographic discovery and post-quantum migration assessment tool designed to help organizations identify cryptographic assets across their applications and infrastructure.

The tool is intended to support organizations preparing for migration toward Post-Quantum Cryptography (PQC) by answering four primary questions:

1. What cryptographic algorithms and technologies are currently being used?
2. Where are these cryptographic assets located?
3. Which assets may be vulnerable to future quantum attacks or are already cryptographically insecure?
4. What migration path should be considered for each identified asset?

The current implementation represents an initial prototype focused primarily on source-code cryptographic discovery and quantum-risk assessment.

---

# Problem Context

Organizations may use cryptographic technologies across:

- Source-code repositories
- Applications
- Libraries and dependencies
- TLS configurations
- Certificates
- Binaries
- Container images
- Hardware security modules
- Cloud services
- Internal and external infrastructure

Examples of cryptographic algorithms and technologies include:

- RSA
- ECC
- ECDSA
- ECDH
- Diffie-Hellman
- AES
- DES / 3DES
- SHA family
- MD5
- TLS
- OpenSSL

The transition toward Post-Quantum Cryptography requires organizations to first understand where cryptography exists and which assets must be prioritized for migration.

ECDAT provides a structured mechanism for performing this discovery and assessment.

---

# Current Prototype Scope

The current prototype implements an initial end-to-end ECDAT workflow:

```text
Source Repository
        ↓
Cryptographic Discovery
        ↓
Artifact Normalization
        ↓
Cryptographic Classification
        ↓
Quantum Risk Assessment
        ↓
Mosca Migration Assessment
        ↓
PQC / Hybrid Recommendation
        ↓
Dashboard-Ready JSON Report
```

The current implementation focuses on scanning source-code repositories.

Future versions are intended to extend discovery to additional enterprise assets.

---

# Current Features

## Cryptographic Discovery

ECDAT recursively scans supported source-code and configuration files to detect cryptographic usage.

The current scanner can identify:

- RSA
- ECDSA / ECC
- ECDH
- Diffie-Hellman
- AES
- DES / 3DES
- SHA-1
- SHA-256
- SHA-384
- SHA-512
- MD5
- TLS

---

## Cryptographic Metadata Extraction

Where possible, ECDAT attempts to identify additional information including:

- RSA key size
- Elliptic-curve type
- ECC key size
- AES key size
- AES operating mode
- TLS context
- Source file
- Source line
- Evidence snippet

Example:

```text
Algorithm : RSA
Type      : Asymmetric
Key Size  : 2048
File      : security/key_manager.py
Line      : 42
Evidence  : rsa.generate_private_key(...)
```

---

# Cryptographic Bill of Materials

The discovered artifacts are normalized into a structured inventory similar to a Cryptographic Bill of Materials (CBOM).

The CBOM-style information includes:

- Algorithm
- Cryptographic type
- Key size
- Mode
- Curve
- Protocol version
- Source file
- Source line
- Evidence
- Quantum risk
- Risk explanation
- Mosca migration risk
- Migration recommendation

This structured representation allows the discovery layer to remain independent from the dashboard and reporting components.

---

# Quantum Risk Assessment

ECDAT performs a basic risk classification for detected cryptographic assets.

Current risk levels are:

```text
CRITICAL
HIGH
MEDIUM
LOW
```

Examples:

### RSA

RSA is classified as a high post-quantum migration concern because sufficiently capable cryptographically relevant quantum computers could use Shor's algorithm against the integer factorisation problem on which RSA relies.

### ECDSA / ECC

Elliptic-curve public-key cryptography is also considered highly relevant to post-quantum migration because the elliptic-curve discrete logarithm problem is vulnerable to sufficiently capable implementations of Shor's algorithm.

### AES-256

AES-256 has a lower post-quantum migration priority compared with RSA or ECC. Quantum search techniques may reduce its effective security margin, but AES-256 retains substantial security under known quantum attack models.

### SHA-256

SHA-256 has a lower migration priority compared with public-key cryptography and is affected differently by known quantum algorithms.

### MD5

MD5 is already considered cryptographically insecure independently of future quantum-computing threats and should not be used for security-sensitive applications.

---

# Mosca Migration Risk Assessment

ECDAT includes a Mosca-style migration-risk calculator.

The model uses:

```text
X = Required confidentiality lifetime of protected data

Y = Estimated time required to migrate the system

Z = Assumed time horizon until a cryptographically relevant
    quantum-computing threat becomes available
```

The primary condition is:

```text
X + Y > Z
```

If the required confidentiality lifetime plus the migration time exceeds the assumed quantum-threat horizon, migration planning should be considered urgent.

Example:

```text
Data lifetime       = 12 years
Migration time      = 4 years
Quantum horizon     = 10 years

X + Y = 16 years

16 > 10

Result:
AT_RISK
Migration Risk:
CRITICAL
```

The quantum horizon is treated as a planning assumption and not as a prediction of the exact arrival date of a cryptographically relevant quantum computer.

---

# PQC Migration Recommendations

ECDAT provides basic migration guidance based on the type and purpose of the detected cryptographic artifact.

Examples include:

## Key Establishment

Algorithms such as:

- RSA
- ECDH
- Diffie-Hellman

may require evaluation of:

- ML-KEM
- Hybrid classical + post-quantum key-establishment mechanisms

---

## Digital Signatures

Algorithms such as:

- RSA signatures
- ECDSA

may require evaluation of:

- ML-DSA
- SLH-DSA
- Hybrid digital-signature mechanisms

---

## Symmetric Cryptography

Appropriate use of AES-256 generally has lower immediate post-quantum migration priority compared with RSA or ECC.

---

## Legacy Cryptography

Algorithms such as:

- MD5
- SHA-1
- DES

may already require migration regardless of the future quantum threat.

---

# Project Structure

```text
ECDAT/
│
├── analysis/
│   ├── __init__.py
│   ├── mosca.py
│   ├── quantum_risk.py
│   ├── recommendations.py
│   └── report_builder.py
│
├── scanner/
│   ├── __init__.py
│   └── crypto_scanner.py
│
├── demo_repo/
│   └── payment_service.py
│
├── examples/
│   └── sample_scan_results.json
│
├── output/
│   └── scan_results.json
│
├── export_scan.py
├── test_scan.py
├── test_mosca.py
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

# Installation

## 1. Clone the repository

```powershell
git clone <repository-url>
cd ECDAT
```

---

## 2. Create a virtual environment

```powershell
python -m venv .venv
```

If Python is available through the Python Launcher:

```powershell
py -m venv .venv
```

---

## 3. Activate the virtual environment

### PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell execution policy prevents activation, the following may be used for the current PowerShell session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## 4. Install dependencies

```powershell
pip install -r requirements.txt
```

---

# Running the Prototype

## Run Cryptographic Discovery Test

```powershell
python test_scan.py
```

The scanner will analyze the current demonstration repository:

```text
demo_repo/
```

and output discovered cryptographic artifacts.

Example output:

```text
Target                 : demo_repo
Files scanned          : 1
Cryptographic artefacts: 6

Risk Summary
------------------------------
CRITICAL  : 1
HIGH      : 2
MEDIUM    : 1
LOW       : 2
```

---

# Run Mosca Assessment Test

```powershell
python test_mosca.py
```

Example result:

```text
data_lifetime        : 12.0
migration_time       : 4.0
quantum_horizon      : 10.0
business_criticality : Critical

x_plus_y             : 16.0
margin               : -6.0
mosca_status          : AT_RISK
mosca_risk            : CRITICAL
```

---

# Generate Dashboard-Ready JSON

Run:

```powershell
python export_scan.py
```

The complete ECDAT pipeline will:

1. Scan the target repository.
2. Discover cryptographic artifacts.
3. Normalize detected artifacts.
4. Classify cryptographic technologies.
5. Perform quantum-risk analysis.
6. Generate migration recommendations.
7. Perform Mosca assessment where applicable.
8. Generate a structured JSON report.

The generated report is written to:

```text
output/scan_results.json
```

---

# Sample Output

A committed example of the report structure is available at:

```text
examples/sample_scan_results.json
```

Example structure:

```json
{
  "target": "demo_repo",
  "total_files_scanned": 1,
  "total_artifacts": 6,
  "quantum_vulnerable_assets": 2,
  "risk_summary": {
    "critical": 1,
    "high": 2,
    "medium": 1,
    "low": 2
  },
  "artifacts": [
    {
      "algorithm": "RSA",
      "type": "Asymmetric",
      "key_size": 2048,
      "file": "demo_repo/payment_service.py",
      "line": 8,
      "quantum_risk": "HIGH",
      "mosca_risk": "CRITICAL",
      "recommendation": "Evaluate suitable PQC or hybrid migration mechanisms."
    }
  ]
}
```

---

# Dashboard Integration

The dashboard is designed to consume the structured scan-result JSON rather than relying directly on scanner internals.

This allows the backend discovery system and frontend dashboard to be developed independently.

Current integration model:

```text
ECDAT Scanner
      ↓
Analysis Engine
      ↓
scan_results.json
      ↓
ECDAT Dashboard
```

The frontend can therefore initially operate using:

```text
examples/sample_scan_results.json
```

and later directly consume:

```text
output/scan_results.json
```

---

# Current Prototype Status

The current screening prototype includes:

- Source-code cryptographic discovery
- Cryptographic artifact classification
- Basic CBOM generation
- Quantum-risk assessment
- Risk explanation
- Mosca-style migration analysis
- PQC / hybrid migration recommendations
- Dashboard-ready JSON generation

---

# Current Limitations

The prototype currently focuses on source-code analysis.

The following capabilities are not yet implemented:

- Binary cryptographic discovery
- Docker/container-image scanning
- Certificate discovery
- Dependency-level cryptographic inventory
- Hardware Security Module discovery
- Cloud cryptographic service discovery
- Enterprise-wide network discovery
- Automatic business-criticality identification
- Advanced migration-cost analysis
- Advanced latency/performance comparison of PQC alternatives
- Full semantic data-flow analysis

---

# Roadmap

Future ECDAT development is planned to include:

## Phase 1 — Current Prototype

- Source-code discovery
- CBOM generation
- Quantum-risk analysis
- Mosca assessment
- PQC recommendations
- Dashboard integration

## Phase 2

- Certificate scanning
- Cryptographic library/dependency discovery
- Configuration analysis
- Expanded language support

## Phase 3

- Binary analysis
- Container-image scanning
- Package inventory
- Advanced artifact correlation

## Phase 4

- Hardware cryptographic module discovery
- Cloud cryptographic service discovery
- Enterprise-wide CBOM generation

## Phase 5

- Business-criticality integration
- Cost-aware migration recommendations
- Latency-aware migration recommendations
- Advanced PQC/hybrid migration planning
- Large-scale enterprise reporting

---

# Security Considerations

ECDAT is intended to support cryptographic inventory and migration planning.

The tool does not:

- Break encryption
- Perform quantum computation
- Predict the exact arrival date of cryptographically relevant quantum computers
- Automatically replace cryptographic algorithms
- Guarantee that recommended algorithms are appropriate for every environment

Final cryptographic migration decisions must consider:

- Cryptographic purpose
- Security requirements
- Business criticality
- Regulatory requirements
- Performance requirements
- Compatibility
- Cost
- Implementation constraints
- Current standards and guidance

---

# Disclaimer

The current ECDAT implementation is an early SIH prototype intended to demonstrate the architecture and core cryptographic discovery and analysis workflow.

Risk classifications and migration recommendations are intended as decision-support information and should not replace expert cryptographic or cybersecurity review.

---

## ECDAT

**Enterprise Cryptographic Discovery & Analysis Tool**

Developed as a prototype for:

**SIH26-26164**  
**National Technical Research Organisation (NTRO)**  
**Blockchain & Cybersecurity**
