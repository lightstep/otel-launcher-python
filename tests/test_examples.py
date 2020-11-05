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
from multiprocessing import Process
from os import environ

from pytest import skip

from opentelemetry.launcher.examples.client import send_requests
from opentelemetry.launcher.examples.server import receive_requests


def test_example(monkeypatch):
    if environ.get("LS_ACCESS_TOKEN") is None:
        skip(
            "Environment variable LS_ACCESS_TOKEN is not set, "
            "set again and rerun"
        )

    monkeypatch.setenv("OTEL_PYTHON_METER_PROVIDER", "sdk_meter_provider")
    monkeypatch.setenv("LS_SERVICE_NAME", "metrics_testing")

    otel_python_meter_provider = environ.get("OTEL_PYTHON_METER_PROVIDER")
    environ["OTEL_PYTHON_METER_PROVIDER"] = "sdk_meter_provider"

    ls_service_name = environ.get("LS_SERVICE_NAME")
    environ["LS_SERVICE_NAME"] = "metrics_testing"

    try:
        server_process = Process(target=receive_requests)
        client_process = Process(target=send_requests)

        server_process.start()
        client_process.start()

        client_process.join()

        sleep(5)

        print("Go to your metrics dashboard and check for exported metrics")
        print("Are there exported metrics in your metrics dashboard (Y/N)?")

        response = input()
        assert (
            response == "Y" or response == "y"
        ), "No metrics exported to your metrics dashboard"
    finally:
        if otel_python_meter_provider is not None:
            environ[
                "OTEL_PYTHON_METER_PROVIDER"
            ] = otel_python_meter_provider

        if ls_service_name is not None:
            environ["LS_SERVICE_NAME"] = ls_service_name
