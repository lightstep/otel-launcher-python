from nox import session


@session(python=["3.5", "3.6", "3.7", "3.8"], reuse_venv=True)
def test(session):
    session.install(".")
    session.install("-r", "requirements-test.txt")

    if session.posargs is None:
        session.run("pytest", "tests")
    else:
        session.run("pytest", *session.posargs)


@session(python=["3.8"])
def lint(session):
    session.install(".")
    session.install("-r", "requirements-test.txt")
    session.install("-r", "requirements-lint.txt")
    session.run("black", "src")
    session.run("isort", "--recursive", "src")
    session.run("pylint", "src")


@session(python=["3.8"])
def coverage(session):
    session.install(".")
    session.install("-r", "requirements-test.txt")
    session.install("-r", "requirements-coverage.txt")
    session.run(
        "pytest",
        "--cov",
        "src/opentelemetry/launcher",
        "--cov-report",
        "xml"
    )
