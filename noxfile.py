"""Nox sessions."""
import sys

import nox
from nox_poetry import Session, session

package = "race_service"
locations = "race_service", "tests", "noxfile.py"
nox.options.envdir = ".cache"
nox.options.reuse_existing_virtualenvs = True
nox.options.stop_on_first_error = True
nox.options.sessions = (
    "lint",
    "mypy",
    "pytype",
    "safety",
    "unit_tests",
    "integration_tests",
    "contract_tests",
)


@session(python="3.11")
def clean(session: Session) -> None:
    """Clean the project."""
    session.run(
        "py3clean",
        ".",
        external=True,
    )
    session.run(
        "rm",
        "-rf",
        ".cache",
        external=True,
    )
    session.run(
        "rm",
        "-rf",
        ".pytest_cache",
        external=True,
    )
    session.run(
        "rm",
        "-rf",
        ".pytype",
        external=True,
    )
    session.run(
        "rm",
        "-rf",
        "dist",
        external=True,
    )
    session.run(
        "rm",
        "-rf",
        ".mypy_cache",
        external=True,
    )
    session.run(
        "rm",
        "-f",
        ".coverage",
        external=True,
    )


@session(python="3.11")
def unit_tests(session: Session) -> None:
    """Run the unit test suite."""
    args = session.posargs
    session.install(".")
    session.install(
        "aioresponses",
        "requests",
        "pytest",
        "pytest-mock",
        "pytest-asyncio",
        "pygments",
    )
    session.run(
        "pytest",
        "-m unit",
        "-ra",
        *args,
    )


@session(python="3.11")
def integration_tests(session: Session) -> None:
    """Run the integration test suite."""
    args = session.posargs or ["--cov"]
    session.install(".")
    session.install(
        "coverage[toml]",
        "pytest",
        "pytest-cov",
        "pytest-mock",
        "pytest-aiohttp",
        "requests",
        "aioresponses",
        "pygments",
    )
    session.run(
        "pytest",
        "-m integration",
        "-ra",
        *args,
        env={
            "CONFIG": "test",
            "JWT_SECRET": "secret",
            "ADMIN_USERNAME": "admin",
            "ADMIN_PASSWORD": "password",
            "EVENTS_HOST_SERVER": "events.example.com",
            "EVENTS_HOST_PORT": "8080",
            "COMPETITION_FORMAT_HOST_SERVER": "competition-format.example.com",
            "COMPETITION_FORMAT_HOST_PORT": "8080",
            "USERS_HOST_SERVER": "users.example.com",
            "USERS_HOST_PORT": "8080",
        },
    )


@session(python=["3.11"])
def contract_tests(session: Session) -> None:
    """Run the contract test suite."""
    args = session.posargs
    session.install(".")
    session.install(
        "pytest",
        "pytest-docker",
        "pytest_mock",
        "pytest-asyncio",
        "requests",
        "aioresponses",
        "pygments",
    )
    session.run(
        "pytest",
        "-m contract",
        "-rfE",
        *args,
        env={
            "CONFIG": "production",
            "ADMIN_USERNAME": "admin",
            "ADMIN_PASSWORD": "password",
            "EVENTS_HOST_SERVER": "localhost",
            "EVENTS_HOST_PORT": "8081",
            "COMPETITION_FORMAT_HOST_SERVER": "localhost",
            "COMPETITION_FORMAT_HOST_PORT": "8082",
            "USERS_HOST_SERVER": "localhost",
            "USERS_HOST_PORT": "8083",
            "LOGGING_LEVEL": "INFO",
            "JWT_EXP_DELTA_SECONDS": "3600",
            "JWT_SECRET": "secret",
            "DB_NAME": "races_test",
            "DB_USER": "admin",
            "DB_PASSWORD": "admin",
        },
    )


@session(python="3.11")
def black(session: Session) -> None:
    """Run black code formatter."""
    args = session.posargs or locations
    session.install("black")
    session.run("black", *args)


@session(python="3.11")
def lint(session: Session) -> None:
    """Lint using flake8."""
    args = session.posargs or locations
    session.install(
        "flake8",
        "flake8-annotations",
        "flake8-bandit",
        "flake8-black",
        "flake8-bugbear",
        "flake8-docstrings",
        "flake8-import-order",
        "darglint",
        "flake8-assertive",
    )
    session.run("flake8", *args)


@session(python="3.11")
def safety(session: Session) -> None:
    """Scan dependencies for insecure packages."""
    requirements = session.poetry.export_requirements()
    session.install("safety")
    session.run("safety", "check", "--full-report", f"--file={requirements}")


@session(python="3.11")
def mypy(session: Session) -> None:
    """Type-check using mypy."""
    args = session.posargs or [
        "--install-types",
        "--non-interactive",
        "race_service",
        "tests",
    ]
    session.install(".")
    session.install("mypy", "pytest")
    session.run("mypy", *args)
    if not session.posargs:
        session.run("mypy", f"--python-executable={sys.executable}", "noxfile.py")


@session(python="3.11")
def pytype(session: Session) -> None:
    """Run the static type checker using pytype."""
    args = session.posargs or ["--disable=import-error", *locations]
    session.install("pytype")
    session.run("pytype", *args)


@session(python="3.11")
def coverage(session: Session) -> None:
    """Upload coverage data."""
    session.install("coverage[toml]", "codecov")
    session.run("coverage", "xml", "--fail-under=0")
    session.run("codecov", *session.posargs)
