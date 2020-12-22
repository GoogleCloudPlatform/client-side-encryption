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
"""Test cases for KMS keys."""

import os
import unittest

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

# Set dunder unittest in the global scope for pretty unit test results
__unittest = True

class TestKSM(unittest.TestCase):
  """Test configuration of KSM keys in the CMEK project. Note that this test
  requires the CMEK_PROJECT_ID and REGION environment variables to be set."""

  def setUp(self) -> None:
    """Call super class setup and define some variables."""
    super().setUp()
    self.cmek_project_id = os.getenv('CMEK_PROJECT_ID', 'my-cmek-project')
    self.region = os.getenv('REGION', 'us-central1')
    self.all_key_rings = []
    self.all_crypto_keys = []
    # Get application-default credentials and initialize API client
    credentials = GoogleCredentials.get_application_default()
    self.project = 'projects/' + self.cmek_project_id + '/locations/' + self.region
    self.service = discovery.build('cloudkms', 'v1', credentials=credentials)
    # Create cache of all KMS Keys
    self.get_crypto_keys()

  def test_imported_keys(self):
    """Verify that importJob is null, which indicates a generated key."""
    for crypto_key in self.all_crypto_keys:
      crypto_key_version = crypto_key['primary']
      self.assertFalse('importJob' in crypto_key_version, 
            '{crypto_key} is imported'.format(
              crypto_key=crypto_key['name']
      ))

  def test_destroyed_keys(self):
    """Verify that destroyEventTime is null"""
    for crypto_key in self.all_crypto_keys:
      crypto_key_version = crypto_key['primary']
      self.assertFalse('destroyEventTime' in crypto_key_version, 
            '{crypto_key_version} is destroyed'.format(
              crypto_key_version=crypto_key_version['name']
      ))

  def test_version_state_enabled(self):
    """Verify that CryptoKeyVersionState is ENABLED"""
    for crypto_key in self.all_crypto_keys:
      crypto_key_version = crypto_key['primary']
      self.assertEqual(crypto_key_version['state'], 'ENABLED',
            '{crypto_key_version} is not ENABLED'.format(
              crypto_key_version=crypto_key_version['name']
      ))

  def test_key_purpose(self):
    """Verify that CryptoKeyPurpose is ENCRYPT_DECRYPT"""
    for crypto_key in self.all_crypto_keys:
      self.assertEqual(crypto_key['purpose'], 'ENCRYPT_DECRYPT',
            '{crypto_key} purpose is not ENCRYPT_DECRYPT'.format(
              crypto_key=crypto_key['name']
      ))

  def get_crypto_keys(self):
    if (len(self.all_crypto_keys) == 0):
      self.retrieve_all_keys()

  def retrieve_all_keys(self):
    """Fetch all keys from configured project and region."""
    if (len(self.all_key_rings) == 0):
      self.retrieve_all_key_rings()
    # for each keyring, get CryptoKeys
    for key_ring in self.all_key_rings:
      try:
        # Set the next page token to 'first' just so we know not to include that
        # argument in the first list_crypto_keys() call
        next_page = 'first'
        # Iterate over pages of API responses
        while next_page:
            if next_page == 'first':
              request = self.service.projects().locations().keyRings().cryptoKeys().list(parent=key_ring)
            else:
              request = self.service.projects().locations().keyRings().cryptoKeys().list(parent=key_ring, pageToken=next_page)
            response = request.execute()
            if 'nextPageToken' in response:
              next_page = response['nextPageToken']
            else:
              next_page = False
            # Now read the crypto_keys and verify protection level
            crypto_keys = response.get('cryptoKeys')
            for crypto_key in crypto_keys:
              self.all_crypto_keys.append(crypto_key)
      except Exception as e:
        raise e

  def retrieve_all_key_rings(self):
    """Fetch all key_rings from configured project and region."""
    # get list of keyrings, given PROJECT_ID and REGION
    try:      
      # Set the next page token to 'first' just so we know not to include that
      # argument in the first list_crypto_keys() call
      next_page = 'first'
      # Iterate over pages of API responses
      while next_page:
        if next_page == 'first':
          request = self.service.projects().locations().keyRings().list(parent=self.project)
        else:
          request = self.service.projects().locations().keyRings().list(parent=self.project, pageToken=next_page)
        response = request.execute()
        if 'nextPageToken' in response:
          next_page = response['nextPageToken']
        else:
          next_page = False
        # Now read the enabled and disabled APIs and put them in the appropriate
        # list
        key_rings = response.get('keyRings')
        for item in key_rings:
          if item['name']:
            self.all_key_rings.append(item['name'])
    except Exception as e:
      raise e