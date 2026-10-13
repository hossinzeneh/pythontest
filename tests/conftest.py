"""Pytest options shared by the tests in this folder."""


def pytest_addoption(parser) -> None:
    """Add a flag that rewrites the visual baseline instead of comparing it."""
    parser.addoption(
        "--update-snapshots",
        action="store_true",
        default=False,
        help="Save a new visual baseline instead of comparing it.",
    )
