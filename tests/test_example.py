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

from pytest import skip, fail


def test_example():

    if environ.get("LS_ACCESS_TOKEN") is None:
        skip(
            "Environment variable LS_ACCESS_TOKEN is not set, "
            "set again and rerun"
        )

    environment = {"LS_ACCESS_TOKEN": environ.get("LS_ACCESS_TOKEN")}

    try:
        server_process = Popen(
            split(".nox/example-3-8/bin/python3 examples/server.py"),
            start_new_session=True,
            env=environment,
        )

        client_process = Popen(
            split(".nox/example-3-8/bin/python3 examples/client.py"),
            start_new_session=True,
            env=environment,
        )

        sleep(15)

    except Exception as error:
        fail("Unexpected error raised: {}".format(error))

    finally:
        try:
            server_process.terminate()
            client_process.terminate()
        except Exception:
            pass
