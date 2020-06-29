from nox import session


@session(python=["3.6", "3.7", "3.8"])
def test(session):
    session.install(".")
    session.install("-r", "requirements-dev.txt")
    session.run("pytest", "tests")


@session
def lint(session):
    session.install("-r", "requirements-dev.txt")
    session.run("black", "src")
