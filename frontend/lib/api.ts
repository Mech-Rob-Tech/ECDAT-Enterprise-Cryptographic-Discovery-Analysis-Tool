import type {
  RiskAssessment,
  RiskLevel,
  Application,
  CanonicalCryptoArtifact,
  Component,
  CryptoArtifact,
  Evidence,
  MigrationOption,
  MoscaAssessment,
  MoscaInputs,
  Recommendation,
  Relationship,
  ScanMetadata,
  ScanResult,
  ScanSummary,
  VerificationState,
} from "./types";

const STORAGE_KEY = "ecdat_scan_result";

type RawRecord = Record<string, unknown>;

function isRecord(
  value: unknown,
): value is RawRecord {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function stringValue(
  value: unknown,
  fallback = "",
): string {
  return typeof value === "string"
    ? value
    : fallback;
}

function numberValue(
  value: unknown,
  fallback = 0,
): number {
  return typeof value === "number"
    ? value
    : fallback;
}

function nullableNumber(
  value: unknown,
): number | null {
  return typeof value === "number"
    ? value
    : null;
}

function arrayValue<T>(
  value: unknown,
): T[] {
  return Array.isArray(value)
    ? (value as T[])
    : [];
}

function normalizeEvidence(
  value: unknown,
): Evidence[] {
  return arrayValue<RawRecord>(
    value,
  ).map((item) => ({
    evidence_id: stringValue(
      item.evidence_id,
    ),
    file: stringValue(
      item.file,
    ).replaceAll("\\", "/"),
    line: numberValue(
      item.line,
    ),
    text: stringValue(
      item.text,
    ),
    context:
      arrayValue<{
        line: number;
        text: string;
      }>(
        item.context,
      ),
  }));
}

function normalizeVerification(
  value: unknown,
): VerificationState | null {
  if (!isRecord(value)) {
    return null;
  }

  return {
    verification_id:
      stringValue(
        value.verification_id,
      ) || undefined,

    status: stringValue(
      value.status,
      "not_verified",
    ),

    verified_at:
      typeof value.verified_at ===
      "string"
        ? value.verified_at
        : null,

    notes: stringValue(
      value.notes,
      "Verification requires a subsequent scan after migration or remediation.",
    ),
  };
}

function normalizeCanonicalArtifact(
  rawArtifact: RawRecord,
  allEvidence: Evidence[],
  allRelationships: Relationship[],
  allMigrationOptions: MigrationOption[],
  allVerification: VerificationState[],
  allArtifacts: CryptoArtifact[],
): CanonicalCryptoArtifact {
  const artifactId =
    stringValue(
      rawArtifact.artifact_id,
    );

  const flatArtifact =
    allArtifacts.find(
      (artifact) =>
        artifact.artifact_id ===
        artifactId,
    );

  /*
   * ALGORITHM
   */
  const rawAlgorithm =
    rawArtifact.algorithm;

  const algorithm = isRecord(
    rawAlgorithm,
  )
    ? {
        name: stringValue(
          rawAlgorithm.name,
          flatArtifact?.algorithm ??
            "Unknown",
        ),
        family: stringValue(
          rawAlgorithm.family,
          "Unknown",
        ),
      }
    : {
        name: stringValue(
          rawAlgorithm,
          flatArtifact?.algorithm ??
            "Unknown",
        ),
        family: "Unknown",
      };

  /*
   * PURPOSE
   */
  const rawPurpose =
    rawArtifact.purpose;

  const purposeConfidence =
    isRecord(rawPurpose)
      ? stringValue(
          rawPurpose.confidence,
          "low",
        )
      : stringValue(
          flatArtifact?.purpose_confidence,
          "low",
        );

  const purpose = isRecord(
    rawPurpose,
  )
    ? {
        value: stringValue(
          rawPurpose.value,
          flatArtifact?.purpose ??
            "unknown",
        ),
        confidence:
          purposeConfidence as
            | "high"
            | "medium"
            | "low",
      }
    : {
        value: stringValue(
          rawPurpose,
          flatArtifact?.purpose ??
            "unknown",
        ),
        confidence:
          purposeConfidence as
            | "high"
            | "medium"
            | "low",
      };

  /*
   * DETECTION
   *
   * Always create the object.
   * This prevents the runtime crash we
   * saw in ArtifactInspector.
   */
  const rawDetection =
    rawArtifact.detection;

  const detection =
    isRecord(rawDetection)
      ? {
          method: stringValue(
            rawDetection.method,
            flatArtifact?.detection_method ??
              "Not available",
          ),
          confidence:
            stringValue(
              rawDetection.confidence,
              flatArtifact?.confidence ??
                "low",
            ) as
              | "high"
              | "medium"
              | "low",
        }
      : {
          method:
            flatArtifact?.detection_method ??
            "Not available",

          confidence:
            (flatArtifact?.confidence ??
              "low") as
              | "high"
              | "medium"
              | "low",
        };

  /*
   * EVIDENCE
   */
  let evidence =
    normalizeEvidence(
      rawArtifact.evidence,
    );

  if (
    evidence.length === 0 &&
    artifactId
  ) {
    const evidenceIds =
      allRelationships
        .filter(
          (relationship) =>
            relationship.source_id ===
              artifactId &&
            relationship.relationship_type ===
              "evidenced_by",
        )
        .map(
          (relationship) =>
            relationship.target_id,
        );

    evidence =
      allEvidence.filter(
        (item) =>
          evidenceIds.includes(
            item.evidence_id,
          ),
      );
  }

  /*
   * RISK
   */
  let risk:
    | CanonicalCryptoArtifact["risk"]
    | null = null;

  if (
    isRecord(rawArtifact.risk)
  ) {
    const security =
      isRecord(
        rawArtifact.risk.security,
      )
        ? rawArtifact.risk.security
        : {};

    const quantum =
      isRecord(
        rawArtifact.risk.quantum,
      )
        ? rawArtifact.risk.quantum
        : {};

    risk = {
      security: {
        assessment_id:
          stringValue(
            security.assessment_id,
          ),
        level:
          stringValue(
            security.level,
            "LOW",
          ) as
            | "CRITICAL"
            | "HIGH"
            | "MEDIUM"
            | "LOW",
        reason: stringValue(
          security.reason,
        ),
      },

      quantum: {
        level:
          stringValue(
            quantum.level,
            "LOW",
          ) as
            | "CRITICAL"
            | "HIGH"
            | "MEDIUM"
            | "LOW",
        reason: stringValue(
          quantum.reason,
        ),
      },
    };
  }

  /*
   * MOSCA
   */
  let mosca:
    | CanonicalCryptoArtifact["mosca"]
    | null = null;

  if (
    isRecord(rawArtifact.mosca)
  ) {
    mosca = {
      assessment_id:
        stringValue(
          rawArtifact.mosca
            .assessment_id,
        ),

     risk:
       (stringValue(
         rawArtifact.mosca.risk,
       ) || null) as RiskLevel | null,

      status:
        stringValue(
          rawArtifact.mosca.status,
        ) || null,

      explanation:
        stringValue(
          rawArtifact.mosca
            .explanation,
        ) || null,
    };
  }

  /*
   * MIGRATION OPTIONS
   */
  const migrationIds =
    arrayValue<string>(
      rawArtifact.migration_option_ids,
    );

  let migrationOptions =
    arrayValue<MigrationOption>(
      rawArtifact.migration_options,
    );

  if (
    migrationOptions.length === 0
  ) {
    migrationOptions =
      allMigrationOptions.filter(
        (option) =>
          migrationIds.includes(
            option.option_id,
          ),
      );
  }

  /*
   * VERIFICATION
   */
  const rawVerification =
    normalizeVerification(
      rawArtifact.verification,
    );

  const artifactVerification =
    rawVerification ??
    (
      stringValue(
        rawArtifact.verification_id,
      )
        ? allVerification.find(
            (state) =>
              state.verification_id ===
              stringValue(
                rawArtifact.verification_id,
              ),
          ) ?? null
        : null
    );

  /*
   * FINAL CANONICAL ARTIFACT
   */
  return {
    artifact_id:
      artifactId,

    algorithm,

    artifact_type:
      stringValue(
        rawArtifact.artifact_type,
        flatArtifact?.type ??
          "Unknown",
      ),

    purpose,

    detection,

    evidence,

    key_size:
      typeof rawArtifact.key_size ===
      "number"
        ? rawArtifact.key_size
        : flatArtifact?.key_size ??
          null,

    mode:
      typeof rawArtifact.mode ===
      "string"
        ? rawArtifact.mode
        : flatArtifact?.mode ??
          null,

    curve:
      typeof rawArtifact.curve ===
      "string"
        ? rawArtifact.curve
        : flatArtifact?.curve ??
          null,

    version:
      typeof rawArtifact.version ===
      "string"
        ? rawArtifact.version
        : flatArtifact?.version ??
          null,

    risk,

    mosca,

    recommendation_ids:
      arrayValue<string>(
        rawArtifact.recommendation_ids,
      ),

    migration_options:
      migrationOptions,

    verification:
      artifactVerification,

    application_id:
      typeof rawArtifact.application_id ===
      "string"
        ? rawArtifact.application_id
        : null,

    component_id:
      typeof rawArtifact.component_id ===
      "string"
        ? rawArtifact.component_id
        : null,

    details:
      isRecord(rawArtifact.details)
        ? rawArtifact.details
        : {},
  };
}

function normalizeFlatArtifacts(
  value: unknown,
): CryptoArtifact[] {
  return arrayValue<RawRecord>(
    value,
  ).map((artifact) => ({
    artifact_id: stringValue(
      artifact.artifact_id,
    ),

    algorithm: stringValue(
      artifact.algorithm,
      "Unknown",
    ),

    type: stringValue(
      artifact.type,
      "Unknown",
    ),

    key_size:
      nullableNumber(
        artifact.key_size,
      ),

    mode:
      typeof artifact.mode ===
      "string"
        ? artifact.mode
        : null,

    curve:
      typeof artifact.curve ===
      "string"
        ? artifact.curve
        : null,

    version:
      typeof artifact.version ===
      "string"
        ? artifact.version
        : null,

    file: stringValue(
      artifact.file,
    ).replaceAll("\\", "/"),

    line: numberValue(
      artifact.line,
    ),

    evidence: stringValue(
      artifact.evidence,
    ),

    evidence_context:
      arrayValue<{
        line: number;
        text: string;
      }>(
        artifact.evidence_context,
      ),

    detection_method:
      stringValue(
        artifact.detection_method,
        "pattern_match",
      ),

    confidence:
      stringValue(
        artifact.confidence,
        "low",
      ) as
        | "high"
        | "medium"
        | "low",

    purpose:
      stringValue(
        artifact.purpose,
        "unknown",
      ),

    purpose_confidence:
      stringValue(
        artifact.purpose_confidence,
        "low",
      ) as
        | "high"
        | "medium"
        | "low",

    quantum_risk:
      stringValue(
        artifact.quantum_risk,
        "LOW",
      ) as
        | "CRITICAL"
        | "HIGH"
        | "MEDIUM"
        | "LOW",

    risk_reason:
      stringValue(
        artifact.risk_reason,
      ),

   mosca_risk:
     (stringValue(
       artifact.mosca_risk,
     ) || null) as RiskLevel | null,

    mosca_status:
      stringValue(
        artifact.mosca_status,
      ) || null,

    mosca_explanation:
      stringValue(
        artifact.mosca_explanation,
      ) || null,

    recommendation:
      stringValue(
        artifact.recommendation,
      ),
  }));
}

function normalizeMetadata(
  raw: RawRecord,
): ScanMetadata {
  const metadata =
    isRecord(raw.metadata)
      ? raw.metadata
      : {};

  return {
    target: stringValue(
      metadata.target,
      stringValue(raw.target),
    ),

    generated_at:
      stringValue(
        metadata.generated_at,
        stringValue(
          raw.generated_at,
        ),
      ),

    prototype_scope:
      stringValue(
        metadata.prototype_scope,
        stringValue(
          raw.prototype_scope,
        ),
      ),
  };
}

function normalizeSummary(
  raw: RawRecord,
): ScanSummary {
  const summary =
    isRecord(raw.summary)
      ? raw.summary
      : {};

  const riskSummary =
    isRecord(
      summary.security_risk_summary,
    )
      ? summary.security_risk_summary
      : isRecord(
            raw.risk_summary,
          )
        ? raw.risk_summary
        : {};

  return {
    total_files_scanned:
      numberValue(
        summary.total_files_scanned,
        numberValue(
          raw.total_files_scanned,
        ),
      ),

    total_artifacts:
      numberValue(
        summary.total_artifacts,
        numberValue(
          raw.total_artifacts,
        ),
      ),

    security_risk_summary: {
      CRITICAL:
        numberValue(
          riskSummary.CRITICAL,
          isRecord(
            raw.risk_summary,
          )
            ? numberValue(
                raw.risk_summary
                  .critical,
              )
            : 0,
        ),

      HIGH:
        numberValue(
          riskSummary.HIGH,
          isRecord(
            raw.risk_summary,
          )
            ? numberValue(
                raw.risk_summary.high,
              )
            : 0,
        ),

      MEDIUM:
        numberValue(
          riskSummary.MEDIUM,
          isRecord(
            raw.risk_summary,
          )
            ? numberValue(
                raw.risk_summary
                  .medium,
              )
            : 0,
        ),

      LOW:
        numberValue(
          riskSummary.LOW,
          isRecord(
            raw.risk_summary,
          )
            ? numberValue(
                raw.risk_summary.low,
              )
            : 0,
        ),
    },

    quantum_relevant_assets:
      numberValue(
        summary.quantum_relevant_assets,
        numberValue(
          raw.quantum_vulnerable_assets,
        ),
      ),
  };
}

function normalizeMoscaInputs(
  value: unknown,
): MoscaInputs {
  const raw =
    isRecord(value)
      ? value
      : {};

  return {
    data_lifetime:
      numberValue(
        raw.data_lifetime,
      ),

    migration_time:
      numberValue(
        raw.migration_time,
      ),

    quantum_horizon:
      numberValue(
        raw.quantum_horizon,
      ),

    business_criticality:
      stringValue(
        raw.business_criticality,
        "unknown",
      ),
  };
}

function normalizeScanResult(
  raw: RawRecord,
): ScanResult {
  const evidence =
    normalizeEvidence(
      raw.evidence,
    );

  const relationships =
    arrayValue<Relationship>(
      raw.relationships,
    );

  const artifacts =
    normalizeFlatArtifacts(
      raw.artifacts,
    );

  const migrationOptions =
    arrayValue<MigrationOption>(
      raw.migration_options,
    );

  const verification =
    arrayValue<RawRecord>(
      raw.verification,
    ).map(
      normalizeVerification,
    ).filter(
      (
        value,
      ): value is VerificationState =>
        value !== null,
    );

  const rawVerification =
    !Array.isArray(
      raw.verification,
    )
      ? normalizeVerification(
          raw.verification,
        )
      : null;

  if (
    rawVerification &&
    verification.length === 0
  ) {
    verification.push(
      rawVerification,
    );
  }

  const rawCanonicalArtifacts =
    arrayValue<RawRecord>(
      raw.canonical_artifacts,
    );

  const canonical_artifacts =
    rawCanonicalArtifacts.map(
      (artifact) =>
        normalizeCanonicalArtifact(
          artifact,
          evidence,
          relationships,
          migrationOptions,
          verification,
          artifacts,
        ),
    );

  const applications =
    arrayValue<Application>(
      raw.applications,
    );

  const components =
    arrayValue<Component>(
      raw.components,
    );

  const riskAssessments =
    arrayValue<RiskAssessment>(
      raw.risk_assessments,
    );

  const moscaAssessments =
    arrayValue<MoscaAssessment>(
      raw.mosca_assessments,
    );

  const recommendations =
    arrayValue<Recommendation>(
      raw.recommendations,
    );

  const metadata =
    normalizeMetadata(raw);

  const summary =
    normalizeSummary(raw);

  return {
    metadata,

    summary,

    applications,

    components,

    canonical_artifacts,

    evidence,

    relationships,

    risk_assessments:
      riskAssessments,

    mosca_assessments:
      moscaAssessments,

    recommendations,

    migration_options:
      migrationOptions,

    verification,

    target:
      stringValue(
        raw.target,
        metadata.target,
      ),

    generated_at:
      stringValue(
        raw.generated_at,
        metadata.generated_at,
      ),

    prototype_scope:
      stringValue(
        raw.prototype_scope,
        metadata.prototype_scope,
      ),

    total_files_scanned:
      numberValue(
        raw.total_files_scanned,
        summary.total_files_scanned,
      ),

    total_artifacts:
      numberValue(
        raw.total_artifacts,
        summary.total_artifacts,
      ),

    quantum_vulnerable_assets:
      numberValue(
        raw.quantum_vulnerable_assets,
        summary.quantum_relevant_assets,
      ),

    risk_summary: {
      critical:
        summary.security_risk_summary
          .CRITICAL,

      high:
        summary.security_risk_summary
          .HIGH,

      medium:
        summary.security_risk_summary
          .MEDIUM,

      low:
        summary.security_risk_summary
          .LOW,
    },

    mosca_inputs:
      normalizeMoscaInputs(
        raw.mosca_inputs,
      ),

    artifacts,

    repository:
      stringValue(
        raw.target,
        metadata.target,
      ),
  };
}

export function getScanResult(): Promise<ScanResult> {
  return new Promise(
    (resolve, reject) => {
      if (
        typeof window ===
        "undefined"
      ) {
        reject(
          new Error(
            "Scan results are only available in the browser.",
          ),
        );
        return;
      }

      const stored =
        sessionStorage.getItem(
          STORAGE_KEY,
        );

      if (!stored) {
        reject(
          new Error(
            "No scan result available. Import and scan a repository first.",
          ),
        );
        return;
      }

      try {
        const parsed: unknown =
          JSON.parse(stored);

        if (
          !isRecord(parsed) ||
          !stringValue(
            parsed.target,
          ) ||
          !Array.isArray(
            parsed.artifacts,
          )
        ) {
          throw new Error(
            "Stored scan result is invalid.",
          );
        }

        const normalized =
          normalizeScanResult(
            parsed,
          );

        resolve(normalized);
      } catch (error) {
        console.error(
          "ECDAT scan result normalization failed:",
          error,
        );

        reject(
          new Error(
            "The stored scan result is invalid. Run a new repository scan.",
          ),
        );
      }
    },
  );
}
