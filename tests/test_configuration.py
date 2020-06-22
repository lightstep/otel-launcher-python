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

import unittest
from unittest.mock import patch

import pytest
from opentelemetry.lightstep import get_tracer


class TestConfiguration(unittest.TestCase):
    def test_all_environment_variables_used(self):
        pass

    def test_no_service_name(self):
        with patch("sys.exit") as exit_mock:
            with self.assertLogs(level="ERROR") as log:
                get_tracer()
                self.assertIn("missing service_name", log.output[0])
            assert exit_mock.called

    def test_no_token(self):
        with patch("sys.exit") as exit_mock:
            with self.assertLogs(level="ERROR") as log:
                get_tracer(service_name="service-123")
                self.assertIn("missing token", log.output[0])
            assert exit_mock.called
