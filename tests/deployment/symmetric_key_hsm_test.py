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
"""Test cases for HSM KMS keys."""

import os
import unittest

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

# Set dunder unittest in the global scope for pretty unit test results
__unittest = True

class TestHSMKeys(unittest.TestCase):
  """Test cases for HSM enabled Keys. Note that this test requires the CMEK_PROJECT_ID
  and REGION environment variables to be set."""

  def setUp(self) -> None:
    """Call super class setup and define some variables."""
    super().setUp()
    self.cmek_project_id = os.getenv('CMEK_PROJECT_ID', 'my-cmek-project')
    self.region = os.getenv('REGION', 'us-central1')


  def test_hsm_keys(self):
    """Test to verify all keys use HSM protection level."""
    # Get application-default credentials and initialize API client
    credentials = GoogleCredentials.get_application_default()
    project = 'projects/' + self.cmek_project_id + '/locations/' + self.region
    service = discovery.build('cloudkms', 'v1', credentials=credentials)

    all_key_rings = []

    # get list of keyrings, given PROJECT_ID and REGION
    try:      
      # Set the next page token to 'first' just so we know not to include that
      # argument in the first list_crypto_keys() call
      next_page = 'first'

      # Iterate over pages of API responses
      while next_page:
        if next_page == 'first':
          request = service.projects().locations().keyRings().list(parent=project)
        else:
          request = service.projects().locations().keyRings().list(parent=project, pageToken=next_page)
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
            all_key_rings.append(item['name'])
    except Exception as e:
      raise e


    # for each keyring, get CryptoKeys
    for key_ring in all_key_rings:
      try:
        # Set the next page token to 'first' just so we know not to include that
        # argument in the first list_crypto_keys() call

        next_page = 'first'
        # Iterate over pages of API responses
        while next_page:
            if next_page == 'first':
              request = service.projects().locations().keyRings().cryptoKeys().list(parent=key_ring)
            else:
              request = service.projects().locations().keyRings().cryptoKeys().list(parent=key_ring, pageToken=next_page)
            response = request.execute()
            if 'nextPageToken' in response:
              next_page = response['nextPageToken']
            else:
              next_page = False
            # Now read the crypto_keys and verify protection level
            crypto_keys = response.get('cryptoKeys')
            for crypto_key in crypto_keys:
              if crypto_key['primary']['protectionLevel']:
                
                # CryptoKeyVersion = CryptoKey.primary
                # ProtectionLevel = CryptoKeyVersion.protection_level
                # assert protection level is google.cloud.kms.v1.ProtectionLevel.HSM
                self.assertEqual(crypto_key['primary']['protectionLevel'], 'HSM', 
                      '{crypto_key} not configured for HSM'.format(
                        crypto_key=crypto_key['name']
                ))
      except Exception as e:
        raise e
