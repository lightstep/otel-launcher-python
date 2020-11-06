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

from pytest import skip


def test_example():

    if environ.get("LS_ACCESS_TOKEN") is None:
        skip(
            "Environment variable LS_ACCESS_TOKEN is not set, "
            "set again and rerun"
        )

    environment = {
        "OTEL_PYTHON_METER_PROVIDER": "sdk_meter_provider",
        "LS_ACCESS_TOKEN": environ.get("LS_ACCESS_TOKEN")
    }

    try:
        server_process = Popen(
            split(".nox/example-3-8/bin/python3 examples/server.py"),
            start_new_session=True,
            env=environment,
        )

        client_process = Popen(
            split(".nox/example-3-8/bin/python3 examples/client.py"),
            start_new_session=True,
            env=environment
        )

        sleep(15)

        print()
        print("Go to your metrics dashboard and check for exported metrics")
        print("Are there exported metrics in your metrics dashboard (Y/N)?")

        response = input()
        assert (
            response == "Y" or response == "y"
        ), "No metrics exported to your metrics dashboard"
    finally:
        try:
            server_process.terminate()
            client_process.terminate()
        except Exception:
            pass
