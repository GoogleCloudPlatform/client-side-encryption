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

class TestOrgPolicy(unittest.TestCase):
  """Test configuration of Organization Policies in the Assured Workload 
  project. Note that this test requires the PROJECT_ID and REGION environment
  variables to be set."""

  all_org_policies = None

  def setUp(self) -> None:
    """Call super class setup and define some variables."""
    super().setUp()
    self.project_id = os.getenv('PROJECT_ID', 'my-project')
    self.region = os.getenv('REGION', 'us-central1')
    # Get application-default credentials and initialize API client
    credentials = GoogleCredentials.get_application_default()
    self.resource = 'projects/' + self.project_id
    self.service = discovery.build('cloudresourcemanager', 'v1', credentials=credentials)
    # Create cache of Org Policies
    self.get_org_policies()

  def test_serial_port_logging(self):
    """Verify that Disable Serial Port Logging constraint is enforced."""
    constraint_name = 'constraints/compute.disableSerialPortLogging'
    self.validate_boolean_policy(constraint_name)

  def test_confidential_vm(self):
    """Verify that Require Confidential VM constraint is enforced."""
    constraint_name = 'constraints/compute.requireConfidentialVm'
    self.validate_boolean_policy(constraint_name)

  def test_shielded_vm(self):
    """Verify that Require Shielded VM constraint is enforced."""
    constraint_name = 'constraints/compute.requireShieldedVm'
    self.validate_boolean_policy(constraint_name)

  def test_restrict_nonconfidential_computing(self):
    """Verify that Restrict Non-Confidential Computing constraint is enforced."""
    constraint_name = 'constraints/compute.restrictNonConfidentialComputing'
    list_policy_type = 'deniedValues'
    expected_values = ['compute.googleapis.com']
    self.validate_list_policy(constraint_name, list_policy_type, expected_values)

  def test_cloud_logging(self):
    """Verify that Disable Cloud Logging constraint is enforced."""
    constraint_name = 'constraints/gcp.disableCloudLogging'
    self.validate_boolean_policy(constraint_name)

  def test_resource_locations(self):
    """Verify that Resource Locations constraint is enforced."""
    constraint_name = 'constraints/gcp.resourceLocations'
    list_policy_type = 'allowedValues'
    expected_values = ['in:us-locations']
    self.validate_list_policy(constraint_name, list_policy_type, expected_values)

  def validate_boolean_policy(self, constraint_name):
    """For given constraint_name, validate booleanPolicy exists 
    and is enforced"""
    constraint = next(
      (policy for policy in self.all_org_policies 
        if policy['constraint'] == constraint_name), 
      None)
    # Assert Constraint is Defined
    self.assertIsNotNone(constraint, 
      '{constraint_name} is missing'
      .format(constraint_name=constraint_name))
    # Assert Constraint has policy
    self.assertIn('enforced', constraint['booleanPolicy'],
      '{constraint_name} is defined, but not enforced'
      .format(constraint_name=constraint_name))
    # Assert Constraint is Enforced
    self.assertTrue(constraint['booleanPolicy']['enforced'], 
      '{constraint_name} is defined, but not enforced'
      .format(constraint_name=constraint_name))

  def validate_list_policy(self, constraint_name, list_policy_type, expected_values):
    """Validate listPolicy is defined and contains expected values"""
    constraint = next(
      (policy for policy in self.all_org_policies 
        if policy['constraint'] == constraint_name), 
      None)
    # Assert Constraint is Defined
    self.assertIsNotNone(constraint, 
      '{constraint_name} is missing'
      .format(constraint_name=constraint_name))
    # Assert listPolicy contains correct policy type
    self.assertListEqual(list(constraint['listPolicy'].keys()), [list_policy_type],
      'Unexected list types in listPolicy in {constraint_name}.  Expected: {list_policy_type}'
      .format(constraint_name=constraint_name, list_policy_type=list_policy_type))
    # Assert listPolicy contains correct values
    actual_values = constraint['listPolicy'][list_policy_type]
    self.assertListEqual(actual_values, expected_values,
      'Unexpected values in {constraint_name}'
      .format(constraint_name=constraint_name))

  def get_org_policies(self):
    if (self.all_org_policies is None):
      self.retrieve_all_org_policies()

  def retrieve_all_org_policies(self):
    """Fetch all Org Policies from configured project and region."""
    org_policies = []
    list_org_policies_request_body = {}
    try:
      # Iterate over pages of API responses
      while True:
        request = self.service.projects().listOrgPolicies(resource=self.resource, body=list_org_policies_request_body)
        response = request.execute()
        for org_policy in response.get('policies', []):
          org_policies.append(org_policy)
        if 'nextPageToken' not in response:
          break
        list_org_policies_request_body['pageToken'] = response['nextPageToken']
      self.__class__.all_org_policies = org_policies
    except Exception as e:
      raise e
