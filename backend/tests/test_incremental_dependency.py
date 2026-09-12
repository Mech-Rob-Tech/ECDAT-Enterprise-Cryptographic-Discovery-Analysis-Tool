"""Deterministic unit tests for incremental dependency planning."""

from analysis.incremental_dependency import (
    FileChange,
    IncrementalDependencyPlanner,
)


def test_build_plan_classifies_changes_deterministically():
    planner = IncrementalDependencyPlanner()

    plan = planner.build_plan(
        [
            FileChange("z.py", "modified"),
            FileChange("a.py", "added"),
            FileChange("m.py", "unchanged"),
            FileChange("b.py", "deleted"),
        ]
    )

    assert plan.unchanged == ("m.py",)
    assert plan.added == ("a.py",)
    assert plan.modified == ("z.py",)
    assert plan.deleted == ("b.py",)

    assert plan.changed_paths == (
        "a.py",
        "b.py",
        "z.py",
    )

    assert plan.affected_paths == (
        "a.py",
        "b.py",
        "z.py",
    )


def test_empty_changes_produce_empty_plan():
    plan = IncrementalDependencyPlanner().build_plan([])

    assert plan.unchanged == ()
    assert plan.added == ()
    assert plan.modified == ()
    assert plan.deleted == ()
    assert plan.affected_paths == ()
    assert plan.changed_paths == ()


def test_duplicate_paths_are_deterministic():
    planner = IncrementalDependencyPlanner()

    plan = planner.build_plan(
        [
            FileChange("crypto.py", "modified"),
            FileChange("crypto.py", "modified"),
        ]
    )

    assert plan.modified == ("crypto.py",)
    assert plan.changed_paths == ("crypto.py",)


def test_unchanged_files_are_not_reprocessed():
    plan = IncrementalDependencyPlanner().build_plan(
        [
            FileChange("crypto.py", "unchanged"),
            FileChange("service.py", "modified"),
        ]
    )

    assert plan.unchanged == ("crypto.py",)
    assert plan.affected_paths == ("service.py",)


def test_added_modified_and_deleted_are_all_affected():
    plan = IncrementalDependencyPlanner().build_plan(
        [
            FileChange("new.py", "added"),
            FileChange("changed.py", "modified"),
            FileChange("removed.py", "deleted"),
        ]
    )

    assert plan.affected_paths == (
        "changed.py",
        "new.py",
        "removed.py",
    )


def test_invalid_change_type_is_rejected():
    planner = IncrementalDependencyPlanner()

    try:
        planner.build_plan(
            [FileChange("crypto.py", "renamed")]
        )
    except ValueError as exc:
        assert "unsupported change type" in str(exc)
    else:
        raise AssertionError(
            "Expected invalid change type to raise ValueError"
        )


def test_empty_path_is_rejected():
    planner = IncrementalDependencyPlanner()

    try:
        planner.build_plan(
            [FileChange("", "modified")]
        )
    except ValueError as exc:
        assert "path must not be empty" in str(exc)
    else:
        raise AssertionError(
            "Expected empty path to raise ValueError"
        )
