# Copyright Lightstep Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from time import sleep
from subprocess import Popen
from shlex import split
from os import environ
from random import randint

from pytest import fixture


@fixture
def setup_teardown():

    if environ.get("LS_ACCESS_TOKEN") is None:
        raise Exception(
            "Environment variable LS_ACCESS_TOKEN is not set, "
            "set again and rerun."
        )

    environment = {"LS_ACCESS_TOKEN": environ.get("LS_ACCESS_TOKEN")}

    identifier = f"{randint(0, 999):03}"

    server_process = Popen(
        split(
            ".nox/example-3-9/bin/python3 examples/server.py {}".format(
                identifier
            )
        ),
        start_new_session=True,
        env=environment,
    )

    sleep(5)

    client_process = Popen(
        split(
            ".nox/example-3-9/bin/python3 examples/client.py {}".format(
                identifier
            )
        ),
        start_new_session=True,
        env=environment,
    )

    sleep(5)

    yield identifier

    server_process.terminate()
    client_process.terminate()


def test_example(setup_teardown):

    assert input(
        "Check your Explorer tab in app.lightstep.com. The following "
        "spans should be displayed:\n"
        "\n"
        "parent-{identifier}\n"
        "    child-0-{identifier}\n"
        "    child-1-{identifier}\n"
        "        request to http://localhost:8000/hello\n"
        "            HTTP GET\n"
        "                /hello\n"
        "    request to http://localhost:8000/shutdown\n"
        "        HTTP GET\n"
        "            /shutdown\n"
        "\n"
        "Type \"y\" if the expected spans are displayed."
        "\n".format(identifier=setup_teardown)
    ) == "y"
