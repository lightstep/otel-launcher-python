from nox import session


def install_opentelemetry_deps(session):
    session.install(
        "-egit+https://github.com/ocelotl/opentelemetry-python.git"
        "@660ddb118790214e86fe93ed1e61e9eecb822715#egg=opentelemetry-api"
        "&subdirectory=opentelemetry-api"
    )
    session.install(
        "-egit+https://github.com/ocelotl/opentelemetry-python.git"
        "@660ddb118790214e86fe93ed1e61e9eecb822715#egg=opentelemetry-sdk"
        "&subdirectory=opentelemetry-sdk"
    )
    session.install(
        "-egit+https://github.com/ocelotl/opentelemetry-python.git"
        "@660ddb118790214e86fe93ed1e61e9eecb822715#egg=opentelemetry-proto"
        "&subdirectory=opentelemetry-proto"
    )
    session.install(
        "-egit+https://github.com/ocelotl/opentelemetry-python.git"
        "@660ddb118790214e86fe93ed1e61e9eecb822715"
        "#egg=opentelemetry-exporter-otlp"
        "&subdirectory=exporter/opentelemetry-exporter-otlp"
    )
    session.install(
        "-egit+https://github.com/ocelotl/opentelemetry-python.git"
        "@660ddb118790214e86fe93ed1e61e9eecb822715"
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
