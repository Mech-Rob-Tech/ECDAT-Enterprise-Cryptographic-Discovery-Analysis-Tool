from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from model.dependency import Dependency


@dataclass(frozen=True)
class DependencyPath:
    """A deterministic path from a root node to a reachable dependency."""

    node_ids: Tuple[str, ...]
    dependency_ids: Tuple[str, ...]
    directness: str


@dataclass(frozen=True)
class DependencyClosure:
    """Dependency closure for one root node."""

    root_node_id: str
    direct_dependencies: Tuple[str, ...]
    indirect_dependencies: Tuple[str, ...]
    external_dependencies: Tuple[str, ...]
    affected_protocols: Tuple[str, ...]
    closure_depth: int
    path_count: int
    evidence_coverage: float


class DependencyEngine:
    """Deterministic dependency graph and traversal engine.

    The engine stores only observed dependency facts. Reachability, paths,
    closure depth and migration precedence are derived at query time.
    """

    def __init__(self, dependencies: Iterable[Dependency] = ()) -> None:
        self.dependencies = tuple(
            sorted(
                dependencies,
                key=lambda item: (
                    item.source_node_id,
                    item.target_node_id,
                    item.relationship_type,
                    item.dependency_id,
                ),
            )
        )
        self._outgoing: Dict[str, List[Dependency]] = defaultdict(list)
        self._incoming: Dict[str, List[Dependency]] = defaultdict(list)

        for dependency in self.dependencies:
            self._outgoing[dependency.source_node_id].append(dependency)
            self._incoming[dependency.target_node_id].append(dependency)

        for values in self._outgoing.values():
            values.sort(key=self._edge_sort_key)
        for values in self._incoming.values():
            values.sort(key=self._edge_sort_key)

    @staticmethod
    def _edge_sort_key(dependency: Dependency) -> Tuple[str, str, str, str]:
        return (
            dependency.target_node_id,
            dependency.relationship_type,
            dependency.confidence,
            dependency.dependency_id,
        )

    def direct_dependencies(self, node_id: str) -> Tuple[Dependency, ...]:
        return tuple(self._outgoing.get(node_id, ()))

    def paths(
        self,
        root_node_id: str,
        max_depth: Optional[int] = None,
    ) -> Tuple[DependencyPath, ...]:
        """Return deterministic simple paths from root to reachable nodes."""
        if max_depth is not None and max_depth < 1:
            return ()

        results: List[DependencyPath] = []
        queue = deque(
            [(root_node_id, (root_node_id,), (), frozenset({root_node_id}))]
        )

        while queue:
            node_id, node_path, edge_path, visited = queue.popleft()
            depth = len(edge_path)

            if depth > 0:
                results.append(
                    DependencyPath(
                        node_ids=node_path,
                        dependency_ids=edge_path,
                        directness="direct" if depth == 1 else "indirect",
                    )
                )

            if max_depth is not None and depth >= max_depth:
                continue

            for dependency in self._outgoing.get(node_id, ()):
                target = dependency.target_node_id
                if target in visited:
                    continue
                queue.append(
                    (
                        target,
                        node_path + (target,),
                        edge_path + (dependency.dependency_id,),
                        visited | {target},
                    )
                )

        return tuple(
            sorted(
                results,
                key=lambda item: (
                    len(item.dependency_ids),
                    item.node_ids,
                    item.dependency_ids,
                ),
            )
        )

    def closure(
        self,
        root_node_id: str,
        external_node_ids: Iterable[str] = (),
    ) -> DependencyClosure:
        """Compute direct/indirect dependency closure without inventing edges."""
        external = set(external_node_ids)
        root_paths = self.paths(root_node_id)

        direct = sorted(
            {
                path.node_ids[1]
                for path in root_paths
                if len(path.node_ids) == 2
            }
        )
        indirect = sorted(
            {
                path.node_ids[-1]
                for path in root_paths
                if len(path.node_ids) > 2
            }
            - set(direct)
        )

        protocols = sorted(
            {
                dependency.protocol
                for dependency in self.dependencies
                if dependency.protocol
                and dependency.source_node_id in {root_node_id, *direct, *indirect}
            }
        )

        reachable = set(direct) | set(indirect)
        external_dependencies = sorted(reachable & external)
        depth = max((len(path.dependency_ids) for path in root_paths), default=0)

        evidence_paths = [
            path
            for path in root_paths
            if all(
                dependency.evidence_ids
                for dependency in self._dependencies_for_path(path)
            )
        ]
        evidence_coverage = (
            len(evidence_paths) / len(root_paths)
            if root_paths
            else 1.0
        )

        return DependencyClosure(
            root_node_id=root_node_id,
            direct_dependencies=tuple(direct),
            indirect_dependencies=tuple(indirect),
            external_dependencies=tuple(external_dependencies),
            affected_protocols=tuple(protocols),
            closure_depth=depth,
            path_count=len(root_paths),
            evidence_coverage=round(evidence_coverage, 4),
        )

    def _dependencies_for_path(
        self,
        path: DependencyPath,
    ) -> Tuple[Dependency, ...]:
        by_id = {item.dependency_id: item for item in self.dependencies}
        return tuple(by_id[item] for item in path.dependency_ids)

    def migration_precedence(
        self,
        root_node_id: str,
    ) -> Tuple[Tuple[str, ...], ...]:
        """Return migration layers where dependencies precede dependants.

        For an observed A -> B dependency, B is placed before A. Cycles are
        emitted as a deterministic final layer because no safe topological
        ordering exists inside a cycle.
        """
        reachable = {root_node_id}
        queue = deque([root_node_id])
        while queue:
            node_id = queue.popleft()
            for dependency in self._outgoing.get(node_id, ()):
                if dependency.target_node_id not in reachable:
                    reachable.add(dependency.target_node_id)
                    queue.append(dependency.target_node_id)

        # Restrict the precedence graph to the reachable subgraph and reverse
        # dependency direction: target must migrate before source.
        prerequisites: Dict[str, set[str]] = {
            node_id: set() for node_id in reachable
        }
        dependants: Dict[str, set[str]] = {
            node_id: set() for node_id in reachable
        }

        for dependency in self.dependencies:
            source = dependency.source_node_id
            target = dependency.target_node_id
            if source not in reachable or target not in reachable:
                continue
            prerequisites[source].add(target)
            dependants[target].add(source)

        layers: List[Tuple[str, ...]] = []
        remaining = set(reachable)

        while remaining:
            ready = sorted(
                node_id
                for node_id in remaining
                if not (prerequisites[node_id] & remaining)
            )
            if not ready:
                layers.append(tuple(sorted(remaining)))
                break

            layers.append(tuple(ready))
            for node_id in ready:
                remaining.remove(node_id)

        return tuple(layers)


def dependencies_from_relationships(
    relationships: Sequence[dict],
    *,
    scan_id: Optional[str] = None,
    source_type: str = "canonical_relationship",
) -> Tuple[Dependency, ...]:
    """Convert explicitly dependency-shaped relationships into observations.

    Generic structural relationships such as ``contains`` and ``uses`` are
    intentionally not reinterpreted as dependencies. This prevents v0.6 from
    manufacturing dependency facts from topology structure alone.
    """
    dependency_types = {
        "USES_ALGORITHM",
        "USES_LIBRARY",
        "USES_PROTOCOL",
        "USES_CERTIFICATE",
        "USES_KEY",
        "USES_HSM",
        "APPLICATION_USES_COMPONENT",
        "COMPONENT_USES_LIBRARY",
        "SERVICE_CONNECTS_TO_SERVICE",
        "SERVICE_DEPENDS_ON_SERVICE",
        "CERTIFICATE_SIGNED_BY",
        "CERTIFICATE_AUTHENTICATES",
        "KEY_PROTECTED_BY",
        "ARTIFACT_PROTECTED_BY",
        "MIGRATION_BLOCKED_BY",
        "MIGRATION_REQUIRES",
        "MIGRATION_AFFECTS",
        "MIGRATION_REPLACES",
    }

    result: List[Dependency] = []
    for relationship in relationships:
        relationship_type = str(
            relationship.get("relationship_type", "")
        ).strip().upper()
        if relationship_type not in dependency_types:
            continue

        source_id = str(relationship.get("source_id", "")).strip()
        target_id = str(relationship.get("target_id", "")).strip()
        if not source_id or not target_id:
            continue

        dependency_id = str(
            relationship.get("relationship_id")
            or f"{source_id}|{relationship_type}|{target_id}"
        )

        result.append(
            Dependency(
                dependency_id=dependency_id,
                source_node_id=source_id,
                target_node_id=target_id,
                relationship_type=relationship_type,
                confidence=str(
                    relationship.get("confidence", "unknown")
                ).lower(),
                directness="direct",
                evidence_ids=list(
                    relationship.get("evidence_ids", []) or []
                ),
                protocol=relationship.get("protocol"),
                purpose=relationship.get("purpose"),
                effective_from=relationship.get("effective_from"),
                effective_until=relationship.get("effective_until"),
                observed_at=relationship.get("observed_at"),
                scan_id=scan_id,
                source_type=source_type,
                source_reference=relationship.get("source_reference"),
            )
        )

    return tuple(
        sorted(
            result,
            key=lambda item: (
                item.source_node_id,
                item.target_node_id,
                item.relationship_type,
                item.dependency_id,
            ),
        )
    )
