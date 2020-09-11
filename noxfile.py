from nox import session


def install_opentelemetry_deps(session):
    session.install(
        "-egit+https://github.com/open-telemetry/opentelemetry-python.git"
        "@master#egg=opentelemetry-api"
        "&subdirectory=opentelemetry-api"
    )
    session.install(
        "-egit+https://github.com/open-telemetry/opentelemetry-python.git"
        "@master#egg=opentelemetry-sdk"
        "&subdirectory=opentelemetry-sdk"
    )
    session.install(
        "-egit+https://github.com/open-telemetry/opentelemetry-python.git"
        "@master#egg=opentelemetry-proto"
        "&subdirectory=opentelemetry-proto"
    )
    session.install(
        "-egit+https://github.com/open-telemetry/opentelemetry-python.git"
        "@master"
        "#egg=opentelemetry-exporter-otlp"
        "&subdirectory=exporter/opentelemetry-exporter-otlp"
    )
    session.install(
        "-egit+https://github.com/open-telemetry/opentelemetry-python.git"
        "@master"
        "#egg=opentelemetry-instrumentation-system-metrics"
        "&subdirectory=instrumentation/"
        "opentelemetry-instrumentation-system-metrics"
    )


@session(python=["3.5", "3.6", "3.7", "3.8"], reuse_venv=False)
def test(session):
    install_opentelemetry_deps(session)
    session.install(".")
    session.install("-r", "requirements-test.txt")

    if session.posargs is None:
        session.run("pytest", "tests")
    else:
        session.run("pytest", *session.posargs)


@session(python=["3.8"])
def lint(session):
    install_opentelemetry_deps(session)
    session.install(".")
    session.install("-r", "requirements-test.txt")
    session.install("-r", "requirements-lint.txt")
    session.run("black", "src")
    session.run("isort", "--recursive", "src")
    session.run("pylint", "src")


@session(python=["3.8"])
def coverage(session):
    install_opentelemetry_deps(session)
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
