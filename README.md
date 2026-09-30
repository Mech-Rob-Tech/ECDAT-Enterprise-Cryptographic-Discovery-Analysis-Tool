# ECDAT

## Enterprise Cryptographic Discovery & Analysis Tool

**SIH Problem Statement:** SIH26-26164  
**Organization:** National Technical Research Organisation (NTRO)  
**Theme:** Blockchain & Cybersecurity

---

## Overview

ECDAT is an enterprise-oriented cryptographic discovery and analysis platform designed to help organizations identify cryptographic usage, understand its security and migration context, and make evidence-backed cryptographic migration decisions.

ECDAT is designed around a progression from **discovery to decision support**, rather than functioning only as a cryptographic inventory or CBOM viewer.

The current **v0.5.0** release establishes the Crypto Knowledge Layer that connects discovered cryptographic artifacts with structured knowledge about algorithms, standards, migration relationships, protocol applicability, compatibility, provenance, temporal validity, and migration candidates.

ECDAT is intended to answer questions such as:

1. **What cryptography exists?**
2. **Where is it being used?**
3. **What does that cryptographic usage mean in its context?**
4. **Which migration candidates are relevant?**
5. **Why was a particular candidate recommended?**
6. **What evidence and knowledge support that decision?**

---

# Current Release

## ECDAT v0.5.0 — Crypto Knowledge Layer

The v0.5.0 baseline introduces a structured cryptographic knowledge system that sits between discovery and analysis.

# Deployed version


Current capabilities include:

- Cryptographic source-code discovery
- Canonical artifact representation
- Cryptographic inventory generation
- Quantum-risk assessment
- Mosca-style migration-risk assessment
- Cryptographic knowledge schema
- Versioned knowledge registry
- Knowledge manifest and hashing
- Knowledge provenance
- Temporal validity
- Migration relationships
- Compatibility constraints
- Protocol applicability
- Hybrid classical/PQ cryptographic knowledge
- Context-aware candidate resolution
- Deterministic migration candidate scoring
- Deterministic candidate ranking
- Explainable candidate selection
- Knowledge regression and determinism testing
- Scan history
- Scan-state comparison
- Verification workflows
- Dashboard-ready structured results

The v0.5.0 release is the current frozen baseline for the next development phase.

---

# Product Direction

ECDAT is being developed around the following lifecycle:

```text
DISCOVER
   ↓
UNDERSTAND
   ↓
ASSESS
   ↓
DECIDE
   ↓
MIGRATE
   ↓
VERIFY
   ↓
ASSURE
````

The long-term architectural model is:

```text
Evidence Sources
       ↓
Canonical ECDAT Evidence / Artifact Model
       ↓
Crypto Knowledge
       ↓
Analytics
       ↓
Decision Support
       ↓
Migration Planning
       ↓
Expected State
       ↓
Rescan
       ↓
Semantic Diff
       ↓
Verification
       ↓
Continuous Assurance
```

Only the capabilities implemented in the current release should be considered production behavior. Future stages are intentionally developed incrementally.

---

# Problem Context

Modern organizations may use cryptography across many layers of their technology estate, including:

* Source-code repositories
* Applications
* Libraries and dependencies
* Protocol configurations
* Certificates
* Binaries
* Container images
* Hardware security modules
* Cloud services
* Internal infrastructure
* External infrastructure

Cryptographic technologies may include:

* RSA
* ECC
* ECDSA
* ECDH
* Diffie-Hellman
* AES
* DES / 3DES
* SHA-family algorithms
* MD5
* TLS
* OpenSSL
* Post-quantum algorithms
* Hybrid classical/PQ mechanisms

A meaningful post-quantum migration program requires more than identifying algorithm names.

Organizations need to understand:

* where cryptography is used,
* what purpose it serves,
* what protocol context it belongs to,
* how long protected data must remain confidential,
* how migration relationships apply,
* which alternatives are technically relevant,
* what standards or knowledge support those alternatives,
* and why a particular migration candidate was selected.

ECDAT is designed to progressively provide this context.

---

# Current Architecture

The current backend is organized into several logical layers.

```text
backend/
│
├── scanner/
│   └── Cryptographic discovery
│
├── model/
│   └── Canonical artifacts and scan state
│
├── mapping/
│   └── Context and artifact mapping
│
├── knowledge/
│   └── Cryptographic knowledge layer
│
├── analysis/
│   └── Risk, migration, scoring, diff and verification analysis
│
├── ingestion/
│   └── Business-context ingestion
│
├── storage/
│   └── Scan and verification history
│
└── tests/
    └── Knowledge and analytical regression tests
```

The frontend is implemented separately using Next.js and consumes structured ECDAT results through the backend/API layer.

---

# Cryptographic Discovery

ECDAT currently performs source-code-oriented cryptographic discovery.

The scanner recursively analyzes supported source-code and configuration files and attempts to identify cryptographic usage.

Current discovery coverage includes technologies such as:

* RSA
* ECDSA / ECC
* ECDH
* Diffie-Hellman
* AES
* DES / 3DES
* SHA-1
* SHA-256
* SHA-384
* SHA-512
* MD5
* TLS

Discovery results are converted into structured cryptographic artifacts rather than being passed directly to the dashboard.

---

# Canonical Cryptographic Artifacts

ECDAT normalizes discovered findings into a canonical representation.

Depending on the available evidence, artifacts may contain information such as:

* Algorithm
* Cryptographic type
* Purpose
* Key size
* Curve
* Mode
* Protocol
* Protocol version
* Source file
* Source line
* Evidence
* Risk information
* Migration information
* Business context
* Canonical identity

Example:

```text
Algorithm : RSA
Type      : Asymmetric
Key Size  : 2048
File      : security/key_manager.py
Line      : 42
Evidence  : rsa.generate_private_key(...)
```

The canonical model allows discovery, knowledge, analysis, reporting, and verification to remain separated.

---

# Cryptographic Knowledge Layer

The Crypto Knowledge Layer is the major architectural addition in v0.5.0.

Instead of treating a discovered algorithm name as sufficient information, ECDAT resolves discovered cryptographic usage against structured knowledge.

The knowledge layer provides information about:

* Algorithms
* Algorithm identifiers
* Cryptographic primitives
* Purposes
* Standards
* Migration relationships
* Compatibility
* Protocol applicability
* Hybrid mechanisms
* Provenance
* Effective dates
* Knowledge versions
* Confidence
* Recommendations

The current knowledge registry is stored under:

```text
backend/knowledge/data/registry.json
```

The registry is loaded and validated through the knowledge layer rather than being treated as an unstructured configuration file.

---

# Knowledge Provenance

Knowledge records can retain provenance information describing where the knowledge originated.

This allows ECDAT to distinguish between:

```text
Discovery Evidence
        +
Knowledge Evidence
        ↓
Explainable Analysis
```

The knowledge layer supports source identifiers, authority information, confidence, and temporal validity.

This is important because cryptographic recommendations should not be treated as unexplained outputs from a black box.

---

# Temporal Knowledge

Cryptographic guidance and protocol applicability can change over time.

ECDAT therefore supports temporal validity for knowledge records.

Knowledge entries can include concepts such as:

```text
effective_from
effective_until
```

This allows resolution to be performed against a particular point in time rather than assuming that today's knowledge was always valid.

The goal is to support historically meaningful analysis and prevent current knowledge from being incorrectly applied to past states.

---

# Migration Relationships

ECDAT represents migration relationships explicitly rather than embedding migration logic entirely inside recommendation code.

Relationships can describe concepts such as:

```text
replaces
supersedes
hybrid_with
alternative_to
compatible_with
related_to
```

For example:

```text
Legacy / Existing Algorithm
            ↓
     Migration Relationship
            ↓
    Candidate Algorithm
```

This provides a structured foundation for deterministic migration candidate resolution.

---

# Protocol Applicability

Migration candidates cannot be evaluated independently of their protocol context.

ECDAT v0.5.0 therefore includes protocol applicability knowledge.

The current knowledge layer includes TLS 1.3 applicability for hybrid post-quantum key-establishment mechanisms such as:

```text
X25519MLKEM768
SecP256r1MLKEM768
SecP384r1MLKEM1024
```

Protocol knowledge can describe:

* Protocol
* Protocol version
* Usage
* Status
* Recommendation state
* Constraints
* Effective dates
* Provenance
* Confidence

This allows candidate selection to consider both:

```text
Algorithm Context
+
Protocol Context
```

rather than recommending algorithms solely from a name match.

---

# Hybrid Post-Quantum Knowledge

ECDAT supports knowledge representation for hybrid classical/post-quantum mechanisms.

The current registry includes examples such as:

```text
X25519MLKEM768
SecP256r1MLKEM768
SecP384r1MLKEM1024
```

These mechanisms combine classical and post-quantum components for key establishment.

ECDAT does not treat all PQC candidates as interchangeable. Candidate selection considers the relationship, purpose, target algorithm, and protocol applicability represented in the knowledge layer.

---

# Context-Aware Candidate Resolution

When an artifact is resolved, ECDAT can use contextual information such as:

* Algorithm
* Purpose
* Protocol
* Protocol version
* Point-in-time validity

A simplified resolution flow is:

```text
Discovered Artifact
       ↓
Canonical Algorithm
       ↓
Migration Relationships
       ↓
Target Algorithms
       ↓
Purpose Filtering
       ↓
Temporal Filtering
       ↓
Protocol Applicability
       ↓
Contextual Candidates
```

If sufficient protocol context exists, contextual candidates can be preferred over generic migration relationships.

This prevents the recommendation engine from treating a generic migration relationship as automatically valid in every protocol environment.

---

# Deterministic Candidate Scoring

ECDAT v0.5.0 uses deterministic multi-factor scoring to rank migration candidates.

The scorer considers factors such as:

* Migration relationship
* Hybrid status
* Knowledge confidence
* Purpose compatibility
* Standard maturity
* Protocol applicability
* Protocol recommendation state
* Migration burden

The scoring process is deterministic.

The same:

```text
Input
+
Knowledge Snapshot
+
Policy
```

produces the same ranked candidate result.

This is intentional.

ECDAT currently does **not** use machine learning to dynamically modify recommendation weights.

The objective at this stage is to provide:

* reproducibility,
* predictable behavior,
* explainability,
* regression-testability,
* and auditable decision support.

---

# Explainable Recommendations

ECDAT recommendations include structured explanation information.

A recommendation can expose factors such as:

```text
Matched Algorithm
Purpose Filter
Protocol Filter
Protocol Version Filter
Temporal Context
Migration Candidates Found
Contextual Candidates Found
Conflicts Found
Candidate Score
Decision
```

The system therefore aims to answer not only:

> What should we migrate to?

but also:

> Why was this candidate selected?

This distinction is central to ECDAT's decision-support architecture.

---

# Quantum Risk Assessment

ECDAT performs cryptographic risk classification for discovered artifacts.

Current risk levels include:

```text
CRITICAL
HIGH
MEDIUM
LOW
```

Examples include:

### RSA

RSA is highly relevant to post-quantum migration because sufficiently capable quantum computers could use Shor's algorithm against the integer factorization problem underlying RSA.

### ECDSA / ECC / ECDH

Elliptic-curve public-key cryptography is highly relevant to post-quantum migration because Shor's algorithm applies to the underlying discrete-logarithm problem.

### AES-256

AES-256 generally has a lower post-quantum migration priority than RSA or ECC under known quantum attack models.

### SHA-256

SHA-256 is affected differently from public-key cryptography and generally has a lower post-quantum migration priority.

### MD5

MD5 is already cryptographically insecure independently of future quantum-computing threats.

Risk classifications are intended as decision-support information and should not be interpreted as universal security guarantees.

---

# Mosca-Style Migration Risk

ECDAT includes a Mosca-style migration-risk assessment.

The model uses:

```text
X = Required confidentiality lifetime

Y = Estimated migration time

Z = Assumed quantum-threat horizon
```

The primary condition is:

```text
X + Y > Z
```

Example:

```text
Data lifetime       = 12 years
Migration time      = 4 years
Quantum horizon     = 10 years

X + Y = 16 years

16 > 10

Result:
AT_RISK
```

The quantum horizon is treated as a planning assumption rather than a prediction of the exact arrival date of a cryptographically relevant quantum computer.

---

# Verification and Scan History

ECDAT contains infrastructure for retaining scan and verification state.

Current backend components include:

```text
storage/
├── scan_history.py
└── verification_history.py
```

The analysis layer also contains functionality for:

* scan-state construction,
* scan comparison,
* verification,
* risk analysis,
* migration analysis.

This provides the foundation for comparing cryptographic state across scans instead of treating each scan as an isolated report.

---

# Structured Results

ECDAT produces structured JSON results that can be consumed by the dashboard and other interfaces.

Example high-level flow:

```text
Repository
    ↓
Scanner
    ↓
Canonical Artifacts
    ↓
Knowledge Resolution
    ↓
Risk / Migration Analysis
    ↓
Structured Results
    ↓
Frontend / Reports
```

A sample result is available in:

```text
sample_results.json
```

Backend examples are also available under:

```text
backend/examples/
```

---

# Frontend

The frontend is implemented using Next.js and provides views for different aspects of cryptographic analysis.

Current application areas include:

```text
/analysis
/artifacts
/import
/inventory
/migration
/mosca
/overview
/quantum
/reports
/topology
```

The frontend contains reusable ECDAT components for areas such as:

* Algorithm profiles
* Cryptographic topology
* Metrics
* Risk badges
* Quantum exposure
* Application layout

The frontend is designed to consume structured analysis results rather than embedding backend analysis logic into UI components.

---

# Project Structure

The current repository is organized approximately as follows:

```text
ECDAT/
│
├── backend/
│   ├── analysis/
│   │   ├── candidate_scoring.py
│   │   ├── mosca.py
│   │   ├── quantum_risk.py
│   │   ├── recommendations.py
│   │   ├── report_builder.py
│   │   ├── risk_landscape.py
│   │   ├── risk_matrix.py
│   │   ├── scan_diff.py
│   │   └── verification.py
│   │
│   ├── ingestion/
│   │   └── business_context_import.py
│   │
│   ├── knowledge/
│   │   ├── data/
│   │   │   └── registry.json
│   │   ├── compatibility.py
│   │   ├── conflicts.py
│   │   ├── freshness.py
│   │   ├── lifecycle.py
│   │   ├── migration.py
│   │   ├── provenance.py
│   │   ├── registry.py
│   │   ├── resolver.py
│   │   ├── schema.py
│   │   ├── serialization.py
│   │   ├── service.py
│   │   ├── temporal.py
│   │   └── validation.py
│   │
│   ├── mapping/
│   │   └── context_resolver.py
│   │
│   ├── model/
│   │   ├── business_context.py
│   │   ├── canonical.py
│   │   ├── identity.py
│   │   ├── relationships.py
│   │   ├── scan_diff.py
│   │   ├── scan_state.py
│   │   ├── scan_state_builder.py
│   │   ├── schema.py
│   │   └── validation.py
│   │
│   ├── scanner/
│   │   └── crypto_scanner.py
│   │
│   ├── storage/
│   │   ├── scan_history.py
│   │   └── verification_history.py
│   │
│   ├── tests/
│   │   └── knowledge and analytical regression tests
│   │
│   ├── demo_repo/
│   ├── examples/
│   ├── output/
│   ├── api.py
│   ├── export_scan.py
│   └── requirements.txt
│
├── dashboard/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── package.json
│
├── utils/
│
├── app.py
├── sample_results.json
├── SECURITY.md
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

Generated files such as Python bytecode, local caches, and development output are not part of the conceptual architecture.

---

# Installation

## Clone the Repository

```bash
git clone https://github.com/Mech-Rob-Tech/ECDAT-Enterprise-Cryptographic-Discovery-Analysis-Tool.git
cd ECDAT-Enterprise-Cryptographic-Discovery-Analysis-Tool
```

---

## Backend Setup

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Linux/macOS:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```bash
pip install -r backend/requirements.txt
```

---

## Frontend Setup

Move into the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Return to the repository root when required:

```bash
cd ..
```

---

# Running the Backend Tests

From the repository root:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

The project uses automated regression tests covering areas including:

* Cryptographic discovery
* Scan state
* Scan history
* Scan comparison
* Verification
* Knowledge schema
* Knowledge registry
* Knowledge provenance
* Knowledge compatibility
* Knowledge temporal validity
* Knowledge migration
* Knowledge resolution
* Hybrid mechanisms
* Candidate recommendations
* Deterministic candidate scoring

---

# Frontend Checks

From the frontend directory:

```bash
npm run lint
```

Build the frontend:

```bash
npm run build
```

These checks are also integrated into the repository CI workflow.

---

# Additional Validation

From the repository root:

```bash
python -m compileall -q .
```

and:

```bash
git diff --check
```

---

# Example Workflow

A simplified ECDAT analysis workflow is:

```text
1. Select a source repository
            ↓
2. Scan source code
            ↓
3. Discover cryptographic artifacts
            ↓
4. Normalize artifacts
            ↓
5. Resolve canonical identities
            ↓
6. Resolve applicable cryptographic knowledge
            ↓
7. Apply contextual constraints
            ↓
8. Assess quantum and migration risk
            ↓
9. Rank migration candidates
            ↓
10. Generate explainable results
            ↓
11. Present results through the frontend
```

---

# Current Limitations

The current v0.5.0 release is intentionally focused.

The following capabilities are **not yet part of the v0.5 implementation**:

* Full dependency-level cryptographic intelligence
* Enterprise-wide dependency graph analysis
* Full binary cryptographic discovery
* Container-image cryptographic discovery
* Comprehensive certificate inventory
* Hardware Security Module discovery
* Cloud cryptographic service discovery
* Enterprise network-wide cryptographic discovery
* Full runtime cryptographic telemetry
* Automatic business-criticality inference
* Full business blast-radius analysis
* Automated migration execution
* Continuous cryptographic assurance
* Large-scale cloud-provider cryptographic inventory

These areas are deliberately kept outside the v0.5 baseline.

---

# Roadmap

ECDAT is being developed incrementally.

The planned progression is:

```text
v0.4  Temporal Verification
  ↓
v0.5  Crypto Knowledge Layer              ← Current
  ↓
v0.6  Dependency Intelligence
  ↓
v0.7  Business Impact + Blast Radius
  ↓
v0.8  Decision Engine
  ↓
v0.9  Migration State Machine
  ↓
v1.0  Expected State + Assurance
  ↓
v1.1  Contradiction Engine
  ↓
v1.2  Evidence Fabric
  ↓
v1.3  AST / Advanced Discovery
  ↓
v1.4  Runtime / Cloud / PKI Providers
  ↓
v1.5  AI Intelligence Layer
  ↓
v2.x  Continuous Crypto Assurance
```

The roadmap is subject to architectural and research validation as development progresses.

---

# Engineering Principles

ECDAT development follows several principles.

## Evidence over assumptions

Analysis should be grounded in discovered evidence and explicit knowledge rather than unexplained assumptions.

## Determinism where possible

Core analytical and recommendation behavior should be reproducible from the same inputs and knowledge snapshot.

## Explainability

Security-sensitive recommendations should expose the factors behind the result.

## Separation of concerns

Discovery, canonical modeling, knowledge, analysis, decision support, presentation, and verification should remain independently testable.

## Incremental architecture

Major capabilities should be introduced as separate stages rather than building an unnecessarily large system before the analytical model is validated.

## Security over cosmetic perfection

Security-sensitive and behaviorally important changes take priority over cosmetic cleanup.

---

# Security

ECDAT is security-oriented software, but it should not be assumed to be secure merely because it analyzes cryptography.

Please review:

```text
SECURITY.md
```

for the project's vulnerability-reporting process.

Do not disclose security vulnerabilities through public GitHub issues.

Potential security-sensitive areas include:

* Authentication and authorization
* Sensitive information exposure
* File handling
* Command execution
* Dependency vulnerabilities
* API security
* Cryptographic implementation
* Integrity of analysis results
* Integrity of knowledge data

---

# Responsible Use

ECDAT is intended to support cryptographic inventory, assessment, migration planning, and verification.

It does not:

* Break encryption
* Perform quantum computation
* Predict the exact arrival date of cryptographically relevant quantum computers
* Automatically replace cryptographic algorithms
* Guarantee that a migration candidate is appropriate for every deployment
* Replace expert cryptographic review

Final migration decisions should consider the actual operational environment, including:

* Security requirements
* Cryptographic purpose
* Protocol compatibility
* Business criticality
* Regulatory requirements
* Performance requirements
* Implementation constraints
* Interoperability
* Migration cost
* Current standards and guidance

---

# Contributing

Contributions are welcome.

Please read:

```text
CONTRIBUTING.md
```

before opening a pull request.

The expected workflow is:

```text
Fork
  ↓
Create branch
  ↓
Implement focused change
  ↓
Test
  ↓
Open Pull Request
  ↓
CI
  ↓
Review
  ↓
Merge
```

Do not commit directly to `main`.

---

# License

ECDAT is released under the **Apache License 2.0**.

See:

```text
LICENSE
```

for the complete license text.

---

# Project Status

**Current release:** `v0.5.0`

**Current focus:** Crypto Knowledge Layer

ECDAT is an actively developed research and engineering project. The current release establishes the foundation for context-aware cryptographic analysis and deterministic migration decision support.

The project is being developed incrementally toward a broader goal:

```text
Cryptographic Discovery
        ↓
Cryptographic Understanding
        ↓
Risk Assessment
        ↓
Migration Decision
        ↓
Migration Verification
        ↓
Continuous Cryptographic Assurance
```

---

# ECDAT

**Enterprise Cryptographic Discovery & Analysis Tool**

**SIH26-26164**
**National Technical Research Organisation (NTRO)**
**Blockchain & Cybersecurity**

```
