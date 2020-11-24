#!/usr/bin/env python3
# Copyright 2020 Google LLC
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
"""Test cases for Assured Workloads."""

import os
import unittest

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

# Set dunder unittest in the global scope for pretty unit test results
__unittest = True

class TestAssuredWorkloads(unittest.TestCase):
  """Test cases for Assured Workloads. Note that this test requires the
  PROJECT_ID environment variable to be set."""

  def setUp(self) -> None:
    """Call super class' setup and define some variables."""
    super().setUp()
    PROJECT_ID = os.getenv('PROJECT_ID', 'my-project')
    ORG_ID = os.getenv('ORG_ID', 'my-org')
    REGION = os.getenv('REGION', 'us-central1')
    self.project_id = PROJECT_ID
    self.org_id = ORG_ID
    self.region = REGION

  def test_assured_workloads(self):
    """Testing Assured Workload settings."""
    # Get application-default credentials and initialize API client
    credentials = GoogleCredentials.get_application_default()
    project = 'projects/' + self.project_id
    service = discovery.build('assuredworkloads',
                              'v1beta1',
                              credentials=credentials)
    try:
      request = service.organizations().locations().workloads().list(
          parent='organizations/{org}/locations/{loc}'.format(
              org=self.org_id,
              loc=self.region
          )
      )
      workloads = request.execute()
      w = workloads['workloads']
      # left off here. err 403 on api endpoint
    except Exception as e:
      pass
