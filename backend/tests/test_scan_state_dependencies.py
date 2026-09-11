from model.scan_state_builder import build_scan_state


def test_scan_state_preserves_dependency_projection():
    report = {
        "metadata": {
            "target": "/tmp/example",
            "generated_at": (
                "2026-09-11T00:00:00+00:00"
            ),
        },
        "applications": [
            {
                "application_id": "application:example",
            }
        ],
        "canonical_artifacts": [],
        "evidence": [],
        "business_contexts": [],
        "relationships": [],
        "dependencies": [
            {
                "dependency_id": "dependency:test",
                "source_node_id": "component:a",
                "target_node_id": "library:cryptography",
                "relationship_type": (
                    "COMPONENT_USES_LIBRARY"
                ),
            }
        ],
        "risk_landscape": {},
        "summary": {},
    }

    state = build_scan_state(report)

    assert len(state.dependencies) == 1
    assert (
        state.dependencies[0]["dependency_id"]
        == "dependency:test"
    )
