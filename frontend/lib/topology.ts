import type {
  CanonicalCryptoArtifact,
  Evidence,
  MigrationOption,
  MoscaAssessment,
  Recommendation,
  Relationship,
  RiskAssessment,
  ScanResult,
  VerificationState,
} from "./types";

export type TopologyNodeKind =
  | "application"
  | "component"
  | "artifact"
  | "evidence"
  | "risk"
  | "mosca"
  | "recommendation"
  | "migration"
  | "verification";

export interface TopologyNodeData {
  kind: TopologyNodeKind;
  label: string;
  subtitle?: string;
  description?: string;

  artifact?: CanonicalCryptoArtifact;
  evidence?: Evidence;
  risk?: RiskAssessment;
  mosca?: MoscaAssessment;
  recommendation?: Recommendation;
  migration?: MigrationOption;
  verification?: VerificationState;

  applicationId?: string | null;
  componentId?: string | null;

  stage?: string;
  active?: boolean;
  riskLabel?: string;

  evidenceCount?: number;
  evidenceRecords?: Evidence[];

  canonicalRelationshipIds?: string[];

  [key: string]: unknown;
}

export interface TopologyNode {
  id: string;
  type: "ecdat";
  position: {
    x: number;
    y: number;
  };
  data: TopologyNodeData;
}

export interface TopologyEdge {
  id: string;
  source: string;
  target: string;
  type: "relationship";
  label?: string;
  data?: {
    relationshipType: string;
    active?: boolean;
    canonicalRelationshipIds?: string[];
    derived?: boolean;
  };
  style?: {
    stroke?: string;
    strokeWidth?: number;
    opacity?: number;
  };
}

export const TOPOLOGY_GEOMETRY = {
  nodeWidth: 240,
  nodeHeight: 120,

  edgeLabelWidth: 120,
  edgeLabelHeight: 28,

  nodeGap: 48,
  labelClearance: 32,

  nodePitch: 288,

  minRowPitch: 212,
  rowPitch: 220,

  centerX: 0,

  artifactY: 80,
  analysisY: 300,
  recommendationY: 520,
  migrationY: 740,
  verificationY: 960,

  analysisOffsets: {
    evidence: -288,
    risk: 0,
    mosca: 288,
  },
} as const;

function stringValue(
  value: unknown,
  fallback = "Unknown",
): string {
  if (typeof value === "string") {
    return value;
  }

  if (
    value &&
    typeof value === "object"
  ) {
    const object =
      value as Record<
        string,
        unknown
      >;

    for (const key of [
      "name",
      "value",
      "label",
      "algorithm",
      "purpose",
      "type",
    ]) {
      if (
        typeof object[key] ===
        "string"
      ) {
        return object[key] as string;
      }
    }
  }

  return fallback;
}

export function displayAlgorithm(
  artifact: CanonicalCryptoArtifact,
): string {
  return stringValue(
    artifact.algorithm,
    "Unknown algorithm",
  );
}

export function displayPurpose(
  artifact: CanonicalCryptoArtifact,
): string {
  return stringValue(
    artifact.purpose,
    "Unknown purpose",
  );
}

function createNode(
  id: string,
  kind: TopologyNodeKind,
  position: {
    x: number;
    y: number;
  },
  data: Omit<TopologyNodeData, "kind">,
): TopologyNode {
  return {
    id,
    type: "ecdat",
    position,
    data: {
      ...data,
      kind,
    } as TopologyNodeData,
  };
}

function createVisualEdge(
  id: string,
  source: string,
  target: string,
  label: string,
  canonicalRelationshipIds: string[] = [],
): TopologyEdge {
  return {
    id,
    source,
    target,
    type: "relationship",
    label,
    data: {
      relationshipType: label,
      active: true,
      canonicalRelationshipIds,
      derived:
        canonicalRelationshipIds.length ===
        0,
    },
    style: {
      stroke: "#d8a900",
      strokeWidth: 1.8,
      opacity: 1,
    },
  };
}

function relatedRelationships(
  artifactId: string,
  relationships: Relationship[],
  relationshipTypes: string[],
): Relationship[] {
  const allowed =
    new Set(relationshipTypes);

  return relationships.filter(
    (relationship) =>
      relationship.source_id ===
        artifactId &&
      allowed.has(
        relationship.relationship_type,
      ),
  );
}

export function buildArtifactInventory(
  scan: ScanResult,
): TopologyNode[] {
  const artifacts =
    scan.canonical_artifacts ?? [];

  const columns = Math.min(
    3,
    Math.max(1, artifacts.length),
  );

  const inventoryColumnGap = 48;
  const inventoryRowGap = 48;

  const cardWidth =
    TOPOLOGY_GEOMETRY.nodeWidth;

  const cardHeight =
    TOPOLOGY_GEOMETRY.nodeHeight;

  const pitchX =
    cardWidth +
    inventoryColumnGap;

  const pitchY =
    cardHeight +
    inventoryRowGap;

  const totalWidth =
    (columns - 1) * pitchX;

  return artifacts.map(
    (
      artifact,
      index,
    ) => {
      const column =
        index % columns;

      const row =
        Math.floor(
          index / columns,
        );

      const x =
        -totalWidth / 2 +
        column * pitchX;

      const y =
        80 +
        row * pitchY;

      const riskRelationship =
        (
          scan.relationships ??
          []
        ).find(
          (relationship) =>
            relationship.source_id ===
              artifact.artifact_id &&
            relationship.relationship_type ===
              "has_risk",
        );

      const risk =
        riskRelationship
          ? (
              scan.risk_assessments ??
              []
            ).find(
              (assessment) =>
                assessment.assessment_id ===
                riskRelationship.target_id,
            )
          : undefined;

      return createNode(
        artifact.artifact_id,
        "artifact",
        {
          x,
          y,
        },
        {
          label:
            displayAlgorithm(
              artifact,
            ),
          subtitle:
            displayPurpose(
              artifact,
            ),
          description:
            artifact.artifact_id,
          artifact,
          applicationId:
            artifact.application_id,
          componentId:
            artifact.component_id,
          stage: "inventory",
          active: false,
          riskLabel:
            risk?.level ??
            "UNKNOWN",
        },
      );
    },
  );
}

export function buildArtifactInvestigation(
  scan: ScanResult,
  artifactId: string,
): {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
} {
  const artifact =
    (
      scan.canonical_artifacts ??
      []
    ).find(
      (item) =>
        item.artifact_id ===
        artifactId,
    );

  if (!artifact) {
    return {
      nodes: [],
      edges: [],
    };
  }

  const nodes: TopologyNode[] = [];
  const edges: TopologyEdge[] = [];

  const relationships =
    scan.relationships ?? [];

  const evidenceById =
    new Map<string, Evidence>();

  for (const evidence of
    scan.evidence ?? []) {
    evidenceById.set(
      evidence.evidence_id,
      evidence,
    );
  }

  const riskById =
    new Map<string, RiskAssessment>();

  for (const risk of
    scan.risk_assessments ?? []) {
    riskById.set(
      risk.assessment_id,
      risk,
    );
  }

  const moscaById =
    new Map<string, MoscaAssessment>();

  for (const mosca of
    scan.mosca_assessments ?? []) {
    moscaById.set(
      mosca.assessment_id,
      mosca,
    );
  }

  const recommendationById =
    new Map<
      string,
      Recommendation
    >();

  for (const recommendation of
    scan.recommendations ?? []) {
    recommendationById.set(
      recommendation.recommendation_id,
      recommendation,
    );
  }

  const migrationById =
    new Map<
      string,
      MigrationOption
    >();

  for (const migration of
    scan.migration_options ?? []) {
    migrationById.set(
      migration.option_id,
      migration,
    );
  }

  const verificationById =
    new Map<
      string,
      VerificationState
    >();

  if (
    Array.isArray(
      scan.verification,
    )
  ) {
    for (const verification of
      scan.verification) {
      if (
        verification.verification_id
      ) {
        verificationById.set(
          verification.verification_id,
          verification,
        );
      }
    }
  } else if (
    scan.verification
  ) {
    if (
      scan.verification
        .verification_id
    ) {
      verificationById.set(
        scan.verification
          .verification_id,
        scan.verification,
      );
    }
  }

  /*
   * ==================================================
   * ARTIFACT
   * ==================================================
   */

  nodes.push(
    createNode(
      artifact.artifact_id,
      "artifact",
      {
        x: 0,
        y:
          TOPOLOGY_GEOMETRY
            .artifactY,
      },
      {
        label:
          displayAlgorithm(
            artifact,
          ),
        subtitle:
          "Crypto Artifact",
        description:
          displayPurpose(
            artifact,
          ),
        artifact,
        applicationId:
          artifact.application_id,
        componentId:
          artifact.component_id,
        stage: "artifact",
        active: true,
      },
    ),
  );

  /*
   * ==================================================
   * EVIDENCE
   * ==================================================
   */

  const evidenceRelationships =
    relatedRelationships(
      artifactId,
      relationships,
      ["evidenced_by"],
    );

  const evidenceRecords =
    evidenceRelationships
      .map(
        (relationship) =>
          evidenceById.get(
            relationship.target_id,
          ),
      )
      .filter(
        (
          evidence,
        ): evidence is Evidence =>
          Boolean(evidence),
      );

  if (
    evidenceRecords.length > 0
  ) {
    const primaryEvidence =
      evidenceRecords[0];

    const evidenceNodeId =
      `evidence:${artifactId}`;

    nodes.push(
      createNode(
        evidenceNodeId,
        "evidence",
        {
          x:
            TOPOLOGY_GEOMETRY
              .analysisOffsets
              .evidence,
          y:
            TOPOLOGY_GEOMETRY
              .analysisY,
        },
        {
          label:
            "Source Evidence",
          subtitle:
            `${evidenceRecords.length} ${
              evidenceRecords.length ===
              1
                ? "location"
                : "locations"
            }`,
          description:
            primaryEvidence.text,
          evidence:
            primaryEvidence,
          stage: "analysis",
          active: true,
          evidenceCount:
            evidenceRecords.length,
          evidenceRecords,
          canonicalRelationshipIds:
            evidenceRelationships.map(
              (item) =>
                item.relationship_id,
            ),
        },
      ),
    );

    edges.push(
      createVisualEdge(
        `edge:${artifactId}:evidence`,
        artifactId,
        evidenceNodeId,
        "evidenced_by",
        evidenceRelationships.map(
          (item) =>
            item.relationship_id,
        ),
      ),
    );
  }

  /*
   * ==================================================
   * RISK
   * ==================================================
   */

  const riskRelationships =
    relatedRelationships(
      artifactId,
      relationships,
      ["has_risk"],
    );

  const riskRecords =
    riskRelationships
      .map(
        (relationship) =>
          riskById.get(
            relationship.target_id,
          ),
      )
      .filter(
        (
          risk,
        ): risk is RiskAssessment =>
          Boolean(risk),
      );

  const risk =
    riskRecords[0];

  const riskNodeId =
    `risk:${artifactId}`;

  if (risk) {
    nodes.push(
      createNode(
        riskNodeId,
        "risk",
        {
          x: 0,
          y:
            TOPOLOGY_GEOMETRY
              .analysisY,
        },
        {
          label:
            risk.level,
          subtitle:
            "Risk Assessment",
          description:
            risk.reason,
          risk,
          stage: "analysis",
          active: true,
        },
      ),
    );

    edges.push(
      createVisualEdge(
        `edge:${artifactId}:risk`,
        artifactId,
        riskNodeId,
        "has_risk",
        riskRelationships.map(
          (item) =>
            item.relationship_id,
        ),
      ),
    );
  }

  /*
   * ==================================================
   * MOSCA
   * ==================================================
   */

  const moscaRelationships =
    relatedRelationships(
      artifactId,
      relationships,
      ["evaluated_by"],
    );

  const moscaRecords =
    moscaRelationships
      .map(
        (relationship) =>
          moscaById.get(
            relationship.target_id,
          ),
      )
      .filter(
        (
          mosca,
        ): mosca is MoscaAssessment =>
          Boolean(mosca),
      );

  const mosca =
    moscaRecords[0];

  const moscaNodeId =
    `mosca:${artifactId}`;

  if (mosca) {
    nodes.push(
      createNode(
        moscaNodeId,
        "mosca",
        {
          x:
            TOPOLOGY_GEOMETRY
              .analysisOffsets
              .mosca,
          y:
            TOPOLOGY_GEOMETRY
              .analysisY,
        },
        {
          label:
            mosca.risk ??
            "UNKNOWN",
          subtitle:
            mosca.status ??
            "MOSCA Assessment",
          description:
            mosca.explanation ??
            "",
          mosca,
          stage: "analysis",
          active: true,
        },
      ),
    );

    edges.push(
      createVisualEdge(
        `edge:${artifactId}:mosca`,
        artifactId,
        moscaNodeId,
        "evaluated_by",
        moscaRelationships.map(
          (item) =>
            item.relationship_id,
        ),
      ),
    );
  }

  /*
   * ==================================================
   * RECOMMENDATION
   * ==================================================
   */

  const recommendationRelationships =
    relatedRelationships(
      artifactId,
      relationships,
      ["has_recommendation"],
    );

  const recommendation =
    recommendationRelationships
      .map(
        (relationship) =>
          recommendationById.get(
            relationship.target_id,
          ),
      )
      .find(
        (
          item,
        ): item is Recommendation =>
          Boolean(item),
      );

  const recommendationNodeId =
    `recommendation:${artifactId}`;

  if (recommendation) {
    nodes.push(
      createNode(
        recommendationNodeId,
        "recommendation",
        {
          x: 0,
          y:
            TOPOLOGY_GEOMETRY
              .recommendationY,
        },
        {
          label:
            recommendation.category,
          subtitle:
            recommendation.priority,
          description:
            recommendation.text,
          recommendation,
          stage: "recommendation",
          active: true,
        },
      ),
    );

    /*
     * IMPORTANT:
     *
     * If Risk exists, visually continue:
     *
     * Artifact -> Risk -> Recommendation
     *
     * instead of:
     *
     * Artifact -----------------> Recommendation
     *              ^
     *              |
     *            Risk
     *
     * The canonical has_recommendation relationship
     * remains attached to the derived visual edge.
     */
    if (risk) {
      edges.push(
        createVisualEdge(
          `edge:${artifactId}:risk-to-recommendation`,
          riskNodeId,
          recommendationNodeId,
          "informs",
          recommendationRelationships.map(
            (item) =>
              item.relationship_id,
          ),
        ),
      );
    } else {
      edges.push(
        createVisualEdge(
          `edge:${artifactId}:recommendation`,
          artifactId,
          recommendationNodeId,
          "has_recommendation",
          recommendationRelationships.map(
            (item) =>
              item.relationship_id,
          ),
        ),
      );
    }

    /*
     * ==================================================
     * MIGRATION
     * ==================================================
     */

    const migrationRelationships =
      relationships.filter(
        (relationship) =>
          relationship.source_id ===
            artifactId &&
          relationship.relationship_type ===
            "candidate_for",
      );

    const migrationRecords =
      migrationRelationships
        .map(
          (relationship) =>
            migrationById.get(
              relationship.target_id,
            ),
        )
        .filter(
          (
            migration,
          ): migration is MigrationOption =>
            Boolean(migration),
        );

    migrationRecords.forEach(
      (
        migration,
        index,
      ) => {
        const count =
          migrationRecords.length;

        const x =
          count === 1
            ? 0
            : (
                index -
                (count - 1) / 2
              ) *
              TOPOLOGY_GEOMETRY
                .nodePitch;

        nodes.push(
          createNode(
            migration.option_id,
            "migration",
            {
              x,
              y:
                TOPOLOGY_GEOMETRY
                  .migrationY,
            },
            {
              label:
                migration.name,
              subtitle:
                migration.effort ??
                "Migration Option",
              description:
                migration.rationale ??
                "",
              migration,
              stage: "migration",
              active: true,
            },
          ),
        );
      },
    );

    /*
     * Recommendation -> Migration
     *
     * The visual path continues downward
     * without crossing another node.
     */
    migrationRecords.forEach(
      (
        migration,
        index,
      ) => {
        const relationship =
          migrationRelationships.find(
            (item) =>
              item.target_id ===
              migration.option_id,
          );

        edges.push(
          createVisualEdge(
            `edge:${artifactId}:migration:${index}`,
            recommendationNodeId,
            migration.option_id,
            "candidate_for",
            relationship
              ? [
                  relationship.relationship_id,
                ]
              : [],
          ),
        );
      },
    );

    /*
     * ==================================================
     * VERIFICATION
     * ==================================================
     */

    const verificationRelationships =
      relationships.filter(
        (relationship) =>
          relationship.source_id ===
            artifactId &&
          relationship.relationship_type ===
            "verified_by",
      );

    const verification =
      verificationRelationships
        .map(
          (relationship) =>
            verificationById.get(
              relationship.target_id,
            ),
        )
        .find(
          (
            item,
          ): item is VerificationState =>
            Boolean(item),
        );

    if (verification) {
      const verificationNodeId =
        verification.verification_id ??
        `verification:${artifactId}`;

      nodes.push(
        createNode(
          verificationNodeId,
          "verification",
          {
            x: 0,
            y:
              TOPOLOGY_GEOMETRY
                .verificationY,
          },
          {
            label:
              verification.status,
            subtitle:
              "Verification",
            description:
              verification.notes ??
              "",
            verification,
            stage: "verification",
            active: true,
          },
        ),
      );

      if (
        migrationRecords.length > 0
      ) {
        migrationRecords.forEach(
          (
            migration,
            index,
          ) => {
            edges.push(
              createVisualEdge(
                `edge:${artifactId}:verification:${index}`,
                migration.option_id,
                verificationNodeId,
                "verified_by",
                verificationRelationships.map(
                  (item) =>
                    item.relationship_id,
                ),
              ),
            );
          },
        );
      } else {
        edges.push(
          createVisualEdge(
            `edge:${artifactId}:verification`,
            recommendationNodeId,
            verificationNodeId,
            "verified_by",
            verificationRelationships.map(
              (item) =>
                item.relationship_id,
            ),
          ),
        );
      }
    }
  }

  return {
    nodes,
    edges,
  };
}

export function buildTopologyGraph(
  scan: ScanResult,
): {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
} {
  return {
    nodes:
      buildArtifactInventory(scan),
    edges: [],
  };
}
