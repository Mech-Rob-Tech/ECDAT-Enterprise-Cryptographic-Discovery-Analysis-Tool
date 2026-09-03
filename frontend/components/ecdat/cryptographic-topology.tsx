"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Background,
  Controls,
  EdgeLabelRenderer,
  Handle,
  Position,
  ReactFlow,
  getSmoothStepPath,
  useEdgesState,
  useNodesState,
  type Edge,
  type EdgeProps,
  type Node,
  type NodeProps,
} from "@xyflow/react";

import "@xyflow/react/dist/style.css";

import type {
  CanonicalCryptoArtifact,
  Evidence,
  MigrationOption,
  MoscaAssessment,
  Recommendation,
  RiskAssessment,
  ScanResult,
  VerificationState,
} from "../../lib/types";

import {
  buildArtifactInvestigation,
  buildArtifactInventory,
  displayAlgorithm,
  displayPurpose,
  type TopologyNodeData,
  type TopologyNode,
  type TopologyEdge,
} from "../../lib/topology";

type EcdatNodeType =
  Node<TopologyNodeData>;

type EcdatEdgeType =
  Edge<{
    relationshipType?: string;
    active?: boolean;
  }>;

const KIND_LABEL: Record<
  TopologyNodeData["kind"],
  string
> = {
  application: "APPLICATION",
  component: "COMPONENT",
  artifact: "CRYPTO ARTIFACT",
  evidence: "SOURCE EVIDENCE",
  risk: "RISK",
  mosca: "MOSCA",
  recommendation: "RECOMMENDATION",
  migration: "MIGRATION",
  verification: "VERIFICATION",
};

const KIND_ACCENT: Record<
  TopologyNodeData["kind"],
  string
> = {
  application: "#64748b",
  component: "#64748b",
  artifact: "#d8a900",
  evidence: "#38bdf8",
  risk: "#ef4444",
  mosca: "#a78bfa",
  recommendation: "#f59e0b",
  migration: "#22c55e",
  verification: "#14b8a6",
};

const KIND_DOT: Record<
  TopologyNodeData["kind"],
  string
> = {
  application: "APP",
  component: "CMP",
  artifact: "CRY",
  evidence: "EVD",
  risk: "RSK",
  mosca: "MSC",
  recommendation: "REC",
  migration: "MIG",
  verification: "VRF",
};

function riskTone(
  value: string | undefined,
): string {
  switch (
    value?.toUpperCase()
  ) {
    case "CRITICAL":
      return "#ef4444";
    case "HIGH":
      return "#f97316";
    case "MEDIUM":
      return "#eab308";
    case "LOW":
      return "#22c55e";
    default:
      return "#64748b";
  }
}

function EcdatNode({
  data,
}: NodeProps<EcdatNodeType>) {
  const accent =
    KIND_ACCENT[data.kind];

  const riskValue =
    data.kind === "risk"
      ? data.risk?.level
      : data.kind === "artifact"
        ? String(
            data.riskLabel ?? "",
          )
        : data.kind === "mosca"
          ? data.mosca?.risk ??
            undefined
          : undefined;

  return (
    <div
      style={{
        width: 240,
        minHeight: 120,
        borderRadius: 14,
        border:
          "1px solid rgba(255,255,255,0.10)",
        background:
          "linear-gradient(180deg, rgba(22,27,36,0.98), rgba(12,16,23,0.98))",
        boxShadow:
          "0 14px 35px rgba(0,0,0,0.28)",
        color: "#e5e7eb",
        padding: "14px 16px",
        position: "relative",
        overflow: "hidden",
      }}
    >
      <Handle
        type="target"
        position={Position.Top}
        style={{
          opacity: 0,
          width: 8,
          height: 8,
        }}
      />

      <div
        style={{
          position: "absolute",
          inset: "0 auto 0 0",
          width: 3,
          background: accent,
        }}
      />

      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent:
            "space-between",
          gap: 10,
          marginBottom: 12,
        }}
      >
        <span
          style={{
            fontSize: 9,
            fontWeight: 700,
            letterSpacing:
              "0.13em",
            color: accent,
          }}
        >
          {KIND_LABEL[data.kind]}
        </span>

        <span
          style={{
            fontSize: 9,
            fontWeight: 700,
            letterSpacing:
              "0.08em",
            color: "#64748b",
          }}
        >
          {KIND_DOT[data.kind]}
        </span>
      </div>

      <div
        style={{
          fontSize: 15,
          fontWeight: 700,
          lineHeight: 1.25,
          color: "#f8fafc",
          overflowWrap:
            "anywhere",
        }}
      >
        {data.label}
      </div>

      {data.subtitle && (
        <div
          style={{
            marginTop: 6,
            fontSize: 11,
            color: "#94a3b8",
            lineHeight: 1.35,
            overflowWrap:
              "anywhere",
          }}
        >
          {data.subtitle}
        </div>
      )}

      {data.description && (
        <div
          style={{
            marginTop: 8,
            fontSize: 10,
            color: "#64748b",
            lineHeight: 1.4,
            display:
              "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient:
              "vertical",
            overflow: "hidden",
          }}
        >
          {data.description}
        </div>
      )}

      {riskValue && (
        <div
          style={{
            marginTop: 10,
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            fontSize: 9,
            fontWeight: 800,
            letterSpacing:
              "0.08em",
            color: riskTone(
              riskValue,
            ),
          }}
        >
          <span
            style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background:
                riskTone(riskValue),
              display: "inline-block",
            }}
          />
          {riskValue}
        </div>
      )}

      <Handle
        type="source"
        position={Position.Bottom}
        style={{
          opacity: 0,
          width: 8,
          height: 8,
        }}
      />
    </div>
  );
}

function RelationshipEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  label,
}: EdgeProps<EcdatEdgeType>) {
  const [
    edgePath,
    labelX,
    labelY,
  ] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
    borderRadius: 14,
  });

  return (
    <>
      <path
        id={id}
        d={edgePath}
        fill="none"
        stroke="#d8a900"
        strokeWidth={1.8}
        opacity={0.9}
	className="ecdat-flow-edge"
      />

      {label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position:
                "absolute",
              transform:
                `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
              pointerEvents:
                "none",
              padding:
                "5px 9px",
              borderRadius: 999,
              border:
                "1px solid rgba(216,169,0,0.28)",
              background:
                "rgba(10,13,18,0.94)",
              color: "#d8a900",
              fontSize: 8,
              fontWeight: 700,
              letterSpacing:
                "0.07em",
              whiteSpace:
                "nowrap",
              boxShadow:
                "0 5px 18px rgba(0,0,0,0.25)",
            }}
          >
            {label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}

const nodeTypes = {
  ecdat: EcdatNode,
};

const edgeTypes = {
  relationship:
    RelationshipEdge,
};

function toReactFlowNodes(
  nodes: TopologyNode[],
): EcdatNodeType[] {
  return nodes as EcdatNodeType[];
}

function toReactFlowEdges(
  edges: TopologyEdge[],
): EcdatEdgeType[] {
  return edges.map(
    (edge) =>
      ({
        ...edge,
        data: edge.data,
      }) as EcdatEdgeType,
  );
}

function ArtifactInspector({
  artifact,
}: {
  artifact: CanonicalCryptoArtifact;
}) {
  return (
    <div
      style={{
        padding: 18,
        borderBottom:
          "1px solid rgba(255,255,255,0.08)",
      }}
    >
      <div
        style={{
          fontSize: 9,
          fontWeight: 700,
          letterSpacing:
            "0.13em",
          color: "#d8a900",
          marginBottom: 8,
        }}
      >
        SELECTED ARTIFACT
      </div>

      <div
        style={{
          fontSize: 19,
          fontWeight: 800,
          color: "#f8fafc",
        }}
      >
	{displayAlgorithm(artifact)}
      </div>

      <div
        style={{
          marginTop: 5,
          fontSize: 11,
          color: "#94a3b8",
        }}
      >
	{displayPurpose(artifact)}
      </div>

      <div
        style={{
          marginTop: 14,
          fontSize: 10,
          color: "#64748b",
          lineHeight: 1.5,
          overflowWrap:
            "anywhere",
        }}
      >
        {artifact.artifact_id}
      </div>

      <div
        style={{
          marginTop: 12,
          display: "flex",
          gap: 8,
          flexWrap: "wrap",
        }}
      >
        <Badge>
          {artifact.artifact_type}
        </Badge>

        {artifact.key_size && (
          <Badge>
            {artifact.key_size} bit
          </Badge>
        )}

        <Badge>
          {artifact.detection?.method ??
            "detection"}
        </Badge>
      </div>
    </div>
  );
}

function EvidenceInspector({
  evidence,
  count,
}: {
  evidence?: Evidence;
  count?: number;
}) {
  if (!evidence) {
    return null;
  }

  return (
    <InspectorSection
      title="SOURCE EVIDENCE"
      accent="#38bdf8"
    >
      <div
        style={{
          fontSize: 11,
          color: "#cbd5e1",
          lineHeight: 1.5,
        }}
      >
        {evidence.file}:
        {evidence.line}
      </div>

      <div
        style={{
          marginTop: 8,
          padding: 10,
          borderRadius: 8,
          background:
            "rgba(56,189,248,0.06)",
          fontSize: 10,
          color: "#94a3b8",
          lineHeight: 1.5,
          fontFamily:
            "ui-monospace, SFMono-Regular, Menlo, monospace",
          overflowWrap:
            "anywhere",
        }}
      >
        {evidence.text}
      </div>

      {count &&
        count > 1 && (
          <div
            style={{
              marginTop: 8,
              fontSize: 9,
              color: "#64748b",
            }}
          >
            + {count - 1}{" "}
            additional evidence
            location
            {count - 1 === 1
              ? ""
              : "s"}
          </div>
        )}
    </InspectorSection>
  );
}

function RiskInspector({
  risk,
}: {
  risk?: RiskAssessment;
}) {
  if (!risk) {
    return null;
  }

  return (
    <InspectorSection
      title="RISK"
      accent={riskTone(risk.level)}
    >
      <div
        style={{
          fontSize: 18,
          fontWeight: 800,
          color: riskTone(
            risk.level,
          ),
        }}
      >
        {risk.level}
      </div>

      <div
        style={{
          marginTop: 8,
          fontSize: 10,
          color: "#94a3b8",
          lineHeight: 1.5,
        }}
      >
        {risk.reason}
      </div>
    </InspectorSection>
  );
}

function MoscaInspector({
  mosca,
}: {
  mosca?: MoscaAssessment;
}) {
  if (!mosca) {
    return null;
  }

  return (
    <InspectorSection
      title="MOSCA"
      accent="#a78bfa"
    >
      <div
        style={{
          display: "flex",
          gap: 8,
          alignItems: "center",
        }}
      >
        <span
          style={{
            fontSize: 16,
            fontWeight: 800,
            color: riskTone(
              mosca.risk ??
                undefined,
            ),
          }}
        >
          {mosca.risk ??
            "UNKNOWN"}
        </span>

        {mosca.status && (
          <Badge>
            {mosca.status}
          </Badge>
        )}
      </div>

      {mosca.explanation && (
        <div
          style={{
            marginTop: 8,
            fontSize: 10,
            color: "#94a3b8",
            lineHeight: 1.5,
          }}
        >
          {mosca.explanation}
        </div>
      )}
    </InspectorSection>
  );
}

function RecommendationInspector({
  recommendation,
}: {
  recommendation?: Recommendation;
}) {
  if (!recommendation) {
    return null;
  }

  return (
    <InspectorSection
      title="RECOMMENDATION"
      accent="#f59e0b"
    >
      <div
        style={{
          display: "flex",
          gap: 8,
          alignItems: "center",
          flexWrap: "wrap",
        }}
      >
        <Badge>
          {recommendation.category}
        </Badge>

        <Badge>
          {recommendation.priority}
        </Badge>
      </div>

      <div
        style={{
          marginTop: 10,
          fontSize: 11,
          color: "#cbd5e1",
          lineHeight: 1.5,
        }}
      >
        {recommendation.text}
      </div>

      <div
        style={{
          marginTop: 8,
          fontSize: 10,
          color: "#64748b",
          lineHeight: 1.5,
        }}
      >
        {recommendation.rationale}
      </div>
    </InspectorSection>
  );
}

function MigrationInspector({
  migration,
}: {
  migration?: MigrationOption;
}) {
  if (!migration) {
    return null;
  }

  return (
    <InspectorSection
      title="MIGRATION OPTION"
      accent="#22c55e"
    >
      <div
        style={{
          fontSize: 15,
          fontWeight: 800,
          color: "#f8fafc",
        }}
      >
        {migration.name}
      </div>

      {migration.compatibility && (
        <div
          style={{
            marginTop: 7,
            fontSize: 10,
            color: "#94a3b8",
          }}
        >
          Compatibility:{" "}
          {migration.compatibility}
        </div>
      )}

      {migration.effort && (
        <div
          style={{
            marginTop: 5,
            fontSize: 10,
            color: "#94a3b8",
          }}
        >
          Effort:{" "}
          {migration.effort}
        </div>
      )}

      {migration.rationale && (
        <div
          style={{
            marginTop: 9,
            fontSize: 10,
            color: "#64748b",
            lineHeight: 1.5,
          }}
        >
          {migration.rationale}
        </div>
      )}
    </InspectorSection>
  );
}

function VerificationInspector({
  verification,
}: {
  verification?: VerificationState;
}) {
  if (!verification) {
    return null;
  }

  return (
    <InspectorSection
      title="VERIFICATION"
      accent="#14b8a6"
    >
      <div
        style={{
          fontSize: 15,
          fontWeight: 800,
          color: "#f8fafc",
        }}
      >
        {verification.status}
      </div>

      {verification.notes && (
        <div
          style={{
            marginTop: 8,
            fontSize: 10,
            color: "#94a3b8",
            lineHeight: 1.5,
          }}
        >
          {verification.notes}
        </div>
      )}

      {verification.verified_at && (
        <div
          style={{
            marginTop: 8,
            fontSize: 9,
            color: "#64748b",
          }}
        >
          {verification.verified_at}
        </div>
      )}
    </InspectorSection>
  );
}

function InspectorSection({
  title,
  accent,
  children,
}: {
  title: string;
  accent: string;
  children: React.ReactNode;
}) {
  return (
    <div
      style={{
        padding:
          "15px 18px",
        borderBottom:
          "1px solid rgba(255,255,255,0.06)",
      }}
    >
      <div
        style={{
          fontSize: 8,
          fontWeight: 800,
          letterSpacing:
            "0.13em",
          color: accent,
          marginBottom: 9,
        }}
      >
        {title}
      </div>

      {children}
    </div>
  );
}

function Badge({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding:
          "4px 7px",
        borderRadius: 999,
        border:
          "1px solid rgba(255,255,255,0.10)",
        background:
          "rgba(255,255,255,0.035)",
        color: "#94a3b8",
        fontSize: 8,
        fontWeight: 700,
        letterSpacing:
          "0.05em",
      }}
    >
      {children}
    </span>
  );
}

export function CryptographicTopology({
  scan,
}: {
  scan: ScanResult;
}) {
  const [
    selectedArtifactId,
    setSelectedArtifactId,
  ] = useState<string | null>(
    null,
  );

  /*
   * These are pure derived values.
   * They NEVER enter a state-sync useEffect.
   */
  const inventoryNodes =
    useMemo(
      () =>
        buildArtifactInventory(
          scan,
        ),
      [scan],
    );

  const investigation =
    useMemo(() => {
      if (!selectedArtifactId) {
        return {
          nodes: [],
          edges: [],
        };
      }

      return buildArtifactInvestigation(
        scan,
        selectedArtifactId,
      );
    }, [
      scan,
      selectedArtifactId,
    ]);

  const activeNodes =
    selectedArtifactId
      ? investigation.nodes
      : inventoryNodes;

  const activeEdges =
    selectedArtifactId
      ? investigation.edges
      : [];

  const initialNodes =
    useMemo(
      () =>
        toReactFlowNodes(
          activeNodes,
        ),
      [activeNodes],
    );

  const initialEdges =
    useMemo(
      () =>
        toReactFlowEdges(
          activeEdges,
        ),
      [activeEdges],
    );

  const [
    nodes,
    setNodes,
    onNodesChange,
  ] =
    useNodesState<EcdatNodeType>(
      initialNodes,
    );

  const [
    edges,
    setEdges,
    onEdgesChange,
  ] =
    useEdgesState<EcdatEdgeType>(
      initialEdges,
    );

  /*
   * IMPORTANT:
   *
   * We only synchronize when the actual view key
   * changes. We do NOT depend on freshly created
   * arrays/objects.
   *
   * This prevents the maximum-update-depth loop.
   */
  const viewKey =
    selectedArtifactId ??
    "__inventory__";

  useEffect(() => {
    setNodes(
      toReactFlowNodes(
        selectedArtifactId
          ? investigation.nodes
          : inventoryNodes,
      ),
    );

    setEdges(
      toReactFlowEdges(
        selectedArtifactId
          ? investigation.edges
          : [],
      ),
    );
  }, [
    viewKey,
    setNodes,
    setEdges,
  ]);

  const selectedArtifact =
    useMemo(
      () =>
        (
          scan.canonical_artifacts ??
          []
        ).find(
          (artifact) =>
            artifact.artifact_id ===
            selectedArtifactId,
        ),
      [
        scan,
        selectedArtifactId,
      ],
    );

  const selectedData =
    selectedArtifactId
      ? investigation.nodes.map(
          (
            node: TopologyNode,
          ) => node.data,
        )
      : [];

  const evidenceData =
    selectedData.find(
      (data) =>
        data.kind ===
        "evidence",
    );

  const riskData =
    selectedData.find(
      (data) =>
        data.kind ===
        "risk",
    );

  const moscaData =
    selectedData.find(
      (data) =>
        data.kind ===
        "mosca",
    );

  const recommendationData =
    selectedData.find(
      (data) =>
        data.kind ===
        "recommendation",
    );

  const migrationData =
    selectedData.find(
      (data) =>
        data.kind ===
        "migration",
    );

  const verificationData =
    selectedData.find(
      (data) =>
        data.kind ===
        "verification",
    );

  const handleNodeClick =
    useCallback(
      (
        event: React.MouseEvent,
        node: Node,
      ) => {
        event.stopPropagation();

        if (
          node.type !==
          "ecdat"
        ) {
          return;
        }

        const data =
          node.data as TopologyNodeData;

        if (
          data.kind ===
            "artifact" &&
          data.artifact
        ) {
          setSelectedArtifactId(
            data.artifact
              .artifact_id,
          );
        }
      },
      [],
    );

  const handleBack =
    useCallback(() => {
      setSelectedArtifactId(
        null,
      );
    }, []);

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        minHeight: 680,
        display: "flex",
        background:
          "#080b10",
        color: "#e5e7eb",
        border:
          "1px solid rgba(255,255,255,0.07)",
        borderRadius: 16,
        overflow: "hidden",
      }}
    >
      <div
        style={{
          flex: 1,
          minWidth: 0,
          position: "relative",
        }}
      >
        <div
          style={{
            position: "absolute",
            zIndex: 10,
            top: 18,
            left: 20,
            right: 20,
            display: "flex",
            alignItems: "center",
            justifyContent:
              "space-between",
            pointerEvents:
              "none",
          }}
        >
          <div>
            <div
              style={{
                fontSize: 11,
                fontWeight: 800,
                letterSpacing:
                  "0.15em",
                color: "#d8a900",
              }}
            >
              CRYPTO EXPLORER
            </div>

            <div
              style={{
                marginTop: 4,
                fontSize: 12,
                color: "#64748b",
              }}
            >
              {selectedArtifactId
                ? "Artifact investigation"
                : `${
                    inventoryNodes.length
                  } cryptographic artifacts`}
            </div>
          </div>

          {selectedArtifactId && (
            <button
              type="button"
              onClick={
                handleBack
              }
              style={{
                pointerEvents:
                  "auto",
                border:
                  "1px solid rgba(216,169,0,0.30)",
                background:
                  "rgba(216,169,0,0.06)",
                color: "#d8a900",
                borderRadius: 8,
                padding:
                  "8px 12px",
                fontSize: 10,
                fontWeight: 800,
                cursor:
                  "pointer",
                letterSpacing:
                  "0.05em",
              }}
            >
              ← BACK TO INVENTORY
            </button>
          )}
        </div>

<style jsx global>{`
  .ecdat-reactflow-controls {
    background: rgba(11, 15, 21, 0.96) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 10px !important;
    overflow: hidden;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.28);
  }

  .ecdat-reactflow-controls button {
    width: 34px !important;
    height: 34px !important;
    background: rgba(255, 255, 255, 0.025) !important;
    color: #94a3b8 !important;
    border: 0 !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06) !important;
  }

  .ecdat-reactflow-controls button:last-child {
    border-bottom: 0 !important;
  }

  .ecdat-reactflow-controls button:hover {
    background: rgba(216, 169, 0, 0.08) !important;
    color: #d8a900 !important;
  }

  .ecdat-flow-edge {
    stroke-dasharray: 8 10;
    animation: ecdat-flow 1.8s linear infinite;
  }

  @keyframes ecdat-flow {
    to {
      stroke-dashoffset: -36;
    }
  }
`}</style>

        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          onNodesChange={
            onNodesChange
          }
          onEdgesChange={
            onEdgesChange
          }
          onNodeClick={
            handleNodeClick
          }
          fitView
          fitViewOptions={{
            padding: 0.18,
            minZoom: 0.45,
            maxZoom: 1.2,
          }}
          nodesDraggable={
            Boolean(
              selectedArtifactId,
            )
          }
          nodesConnectable={
            false
          }
          elementsSelectable={
            true
          }
          proOptions={{
            hideAttribution:
              false,
          }}
          defaultEdgeOptions={{
            type: "relationship",
          }}
          style={{
            background:
              "#080b10",
          }}
        >
          <Background
            gap={28}
            size={1}
            color="rgba(255,255,255,0.035)"
          />

	<Controls
        className="ecdat-reactflow-controls"
        showInteractive={false}
	/>

        </ReactFlow>

        {!selectedArtifactId &&
          inventoryNodes.length ===
            0 && (
            <div
              style={{
                position:
                  "absolute",
                inset: 0,
                display: "flex",
                alignItems:
                  "center",
                justifyContent:
                  "center",
                pointerEvents:
                  "none",
              }}
            >
              <div
                style={{
                  textAlign:
                    "center",
                  color:
                    "#64748b",
                }}
              >
                <div
                  style={{
                    fontSize: 14,
                    fontWeight: 700,
                    color:
                      "#94a3b8",
                  }}
                >
                  No cryptographic
                  artifacts
                </div>

                <div
                  style={{
                    marginTop: 6,
                    fontSize: 11,
                  }}
                >
                  Run a scan to
                  populate the
                  explorer.
                </div>
              </div>
            </div>
          )}
      </div>

      <aside
        style={{
          width: 320,
          flexShrink: 0,
          borderLeft:
            "1px solid rgba(255,255,255,0.07)",
          background:
            "rgba(11,15,21,0.96)",
          overflowY: "auto",
        }}
      >
        {selectedArtifact ? (
          <>
            <ArtifactInspector
              artifact={
                selectedArtifact
              }
            />

            <EvidenceInspector
              evidence={
                evidenceData?.evidence
              }
              count={
                typeof evidenceData?.evidenceCount ===
                "number"
                  ? evidenceData.evidenceCount
                  : undefined
              }
            />

            <RiskInspector
              risk={
                riskData?.risk
              }
            />

            <MoscaInspector
              mosca={
                moscaData?.mosca
              }
            />

            <RecommendationInspector
              recommendation={
                recommendationData?.recommendation
              }
            />

            <MigrationInspector
              migration={
                migrationData?.migration
              }
            />

            <VerificationInspector
              verification={
                verificationData?.verification
              }
            />
          </>
        ) : (
          <div
            style={{
              padding: 20,
            }}
          >
            <div
              style={{
                fontSize: 9,
                fontWeight: 800,
                letterSpacing:
                  "0.13em",
                color: "#d8a900",
              }}
            >
              ARTIFACT INVENTORY
            </div>

            <div
              style={{
                marginTop: 10,
                fontSize: 13,
                color: "#cbd5e1",
                lineHeight: 1.5,
              }}
            >
              Select an artifact
              to inspect its
              evidence, risk,
              MOSCA assessment,
              recommendation and
              migration path.
            </div>

            <div
              style={{
                marginTop: 18,
                display: "grid",
                gap: 8,
              }}
            >
              {inventoryNodes.map(
                (
                  node: TopologyNode,
                ) => {
                  const artifact =
                    node.data
                      .artifact;

                  if (!artifact) {
                    return null;
                  }

                  return (
                    <button
                      key={
                        artifact.artifact_id
                      }
                      type="button"
                      onClick={() =>
                        setSelectedArtifactId(
                          artifact.artifact_id,
                        )
                      }
                      style={{
                        textAlign:
                          "left",
                        padding:
                          "11px 12px",
                        borderRadius:
                          9,
                        border:
                          "1px solid rgba(255,255,255,0.07)",
                        background:
                          "rgba(255,255,255,0.025)",
                        color:
                          "#cbd5e1",
                        cursor:
                          "pointer",
                      }}
                    >
                      <div
                        style={{
                          fontSize: 11,
                          fontWeight: 800,
                          color:
                            "#f8fafc",
                        }}
                      >
		{displayAlgorithm(artifact)}
                      </div>

                      <div
                        style={{
                          marginTop: 4,
                          fontSize: 9,
                          color:
                            "#64748b",
                        }}
                      >
                        {artifact.artifact_id}
                      </div>
                    </button>
                  );
                },
              )}
            </div>
          </div>
        )}
      </aside>
    </div>
  );
}

export default CryptographicTopology;
