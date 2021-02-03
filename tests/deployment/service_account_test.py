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
"""Test cases for service accounts."""

import os
import unittest

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

# Set dunder unittest in the global scope for pretty unit test results
__unittest = True

class TestServiceAccounts(unittest.TestCase):
  """Test cases for service accounts. Note that this test requires the
  PROJECT_ID environment variable to be set."""

  def setUp(self) -> None:
    """Call super class' setup and define some variables."""
    super().setUp()
    self.project_id = os.getenv('PROJECT_ID', 'my-project')
    self.cmek_project_id = os.getenv('CMEK_PROJECT_ID', 'cmek-my-project')
    self.org_id = os.getenv('ORG_ID', 'my-org')
    self.region = os.getenv('REGION', 'us-central1')
    self.serviceaccount = 'itar-compute-sa'

  def test_verify_service_account_exists(self):
    """Test that required service account exists."""
    # Get application-default credentials and initialize API client
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('iam',
                              'v1',
                              credentials=credentials)

    try:
      # Retrieve a list of all service accounts in the project
      request = service.projects().serviceAccounts().list(
          name='projects/{project}'.format(
              project=self.project_id
          )
      )
      service_accounts = request.execute()
      # Determine if self.serviceaccount is in the list of SAs
      itar_sa = None
      for sa in service_accounts['accounts']:
        sa_name = sa['name'].split('/')[-1].\
          replace('@{}.iam.gserviceaccount.com'.format(self.project_id), '')
        if sa_name == self.serviceaccount:
          itar_sa = sa_name
      self.assertTrue(itar_sa, 'missing {name} SA in {project}'.format(
          name=self.serviceaccount,
          project=self.project_id
      ))
    except Exception as e: # pylint: disable=broad-except
      raise e

  def test_verify_aw_policy_bindings(self):
    """Test that correct policy bindings are in place for the AW project."""
    # Get application-default credentials and initialize API client
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('cloudresourcemanager',
                              'v1beta1',
                              credentials=credentials)
    # Dict of roles we want to check for SA membership
    roles = {'roles/cloudkms.cryptoKeyEncrypterDecrypter': False,
             'roles/iam.serviceAccountKeyAdmin': False,
             'roles/storage.admin': False,
             'roles/compute.viewer': False,
             'roles/browser': False}
    try:
      request = service.projects().getIamPolicy(
          resource=self.project_id,
          body={}
      )
      policy = request.execute()
      # Build the resource string
      resource = 'serviceAccount:{sa}@{proj}.iam.gserviceaccount.com'.format(
          sa=self.serviceaccount,
          proj=self.project_id
      )
      # Iterate over the policy bindings and flip role membership booleans
      for binding in policy['bindings']:
        if resource in binding['members']:
          roles[binding['role']] = True
      for role in roles.keys():
        self.assertTrue(roles[role], '{resource} missing role {role}'.format(
            resource=resource,
            role=role
        ))
    except Exception as e:  # pylint: disable=broad-except
      raise e

  def test_verify_cmek_policy_bindings(self):
    """Test that correct policy bindings are in place for the CMEK project."""
    # Get application-default credentials and initialize API client
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('cloudresourcemanager',
                              'v1beta1',
                              credentials=credentials)
    # Dict of roles we want to check for SA membership
    roles = {'roles/cloudkms.cryptoKeyEncrypterDecrypter': False,
             'roles/browser': False}
    try:
      request = service.projects().getIamPolicy(
          resource=self.cmek_project_id,
          body={}
      )
      policy = request.execute()
      # Build the resource string
      resource = 'serviceAccount:{sa}@{proj}.iam.gserviceaccount.com'.format(
          sa=self.serviceaccount,
          proj=self.project_id
      )
      # Iterate over the policy bindings and flip role membership booleans
      for binding in policy['bindings']:
        if resource in binding['members']:
          roles[binding['role']] = True
      for role in roles.keys():
        self.assertTrue(roles[role], '{resource} missing role {role}'.format(
            resource=resource,
            role=role
        ))
    except Exception as e:  # pylint: disable=broad-except
      raise e
