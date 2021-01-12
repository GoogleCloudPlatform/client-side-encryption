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
"""Test cases for Organizational Policies."""

import os
import unittest

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

# Set dunder unittest in the global scope for pretty unit test results
__unittest = True

class TestConfidentialVM(unittest.TestCase):
  """Test configuration of Confidential Compute for GCE Instances in the 
  Assured Workload project. Note that this test requires the PROJECT_ID 
  and REGION environment variables to be set."""

  all_instances = None

  def setUp(self) -> None:
    """Call super class setup and define some variables."""
    super().setUp()
    self.project_id = os.getenv('PROJECT_ID', 'my-project')
    self.region = os.getenv('REGION', 'us-central1')
    # Get application-default credentials and initialize API client
    credentials = GoogleCredentials.get_application_default()
    self.project = self.project_id
    self.service = discovery.build('compute', 'v1', credentials=credentials)
    # Create cache of GCE Instances
    self.get_instances()

  def test_confidential_vm(self):
    """Verify that Confidential VM Config is Enabled for each Instance."""
    for instance in self.all_instances:
      instance_name = instance.get('name')
      # Verify confidentialInstanceConfig exists
      self.assertIn('confidentialInstanceConfig', instance,
        'Confidential Computing not enabled in instance {instance_name}.'
      .format(instance_name=instance_name))
      # Verify Confidential Computing is Enabled
      self.assertTrue(
        instance['confidentialInstanceConfig']['enableConfidentialCompute'],
        'Confidential Computing not enabled in instance {instance_name}.'
      .format(instance_name=instance_name))

  def get_instances(self):
    if (self.all_instances is None):
      self.retrieve_all_instances()

  def retrieve_all_instances(self):
    """Fetch all instances from configured project and region."""
    zones = []
    instances = []
    # Retrieve all Zones, given Project ID
    try:
      request = self.service.zones().list(project=self.project)
      response = request.execute()
      for zone in response.get('items', []):
        zones.append(zone['name'])
    except Exception as e:
      raise e
    # Retrieve all Instances in each Zone
    try:
      for zone in zones:
        request = self.service.instances().list(project=self.project, zone=zone)
        response = request.execute()
        for instance in response.get('items', []):
          instances.append(instance)
      self.__class__.all_instances = instances
    except Exception as e:
      raise e