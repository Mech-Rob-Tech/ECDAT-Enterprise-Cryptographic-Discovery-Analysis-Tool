# Contributing to ECDAT

Thank you for your interest in contributing to ECDAT.

ECDAT is an enterprise cryptographic discovery and analysis platform focused on discovering cryptographic usage, understanding its context, assessing migration implications, and eventually verifying cryptographic state over time.

## Development Workflow

Please use the following workflow:

1. Fork the repository.
2. Create a feature or fix branch from `main`.
3. Make focused changes.
4. Add or update tests where appropriate.
5. Run the relevant checks locally.
6. Push your branch to your fork.
7. Open a pull request against `main`.
8. Address review feedback.
9. Wait for required CI checks to pass.

Do not commit directly to `main`.

## Branch Naming

Use descriptive branch names such as:

- `feature/<short-description>`
- `fix/<short-description>`
- `docs/<short-description>`
- `chore/<short-description>`
- `refactor/<short-description>`

Example:

```text
feature/protocol-context-resolution
