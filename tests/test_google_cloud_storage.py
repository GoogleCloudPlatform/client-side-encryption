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
"""Test cases for the google-cloud-storage wrapper."""

import os
import unittest

from encryption_wrapper import storage

from google.cloud.exceptions import NotFound


class TestGCSWrapper(unittest.TestCase):
  """Test cases for the google-cloud-storage wrapper."""

  def setUp(self) -> None:
    """Call super class' setup and define some variables."""
    super().setUp()
    PROJECT_ID = os.getenv('PROJECT_ID', 'my-project')
    SERVICE_ACCOUNT_NAME = os.getenv('SERVICE_ACCOUNT_NAME', 'wrapper-sa')
    REGION = os.getenv('REGION', 'us-central1')
    KEYRING_NAME = os.getenv('KEYRING_NAME', 'my-key-ring')
    KEY_NAME = os.getenv('KEY_NAME', 'my-key')
    CREDS_JSON = os.getenv('CREDS_JSON',
                           os.path.expanduser('~') + '/creds.json')
    BUCKET_NAME = os.getenv('BUCKET_NAME', 'my-bucket')
    BLOB_NAME = os.getenv('BLOB_NAME', 'testobject')
    self.key_uri = "gcp-kms://projects/{}/locations/{}/keyRings/{}/cryptoKeys/{}".format(
        PROJECT_ID,
        REGION,
        KEYRING_NAME,
        KEY_NAME
    )
    self.creds = CREDS_JSON
    self.plaintext = 'this is plaintext'
    self.plaintext_path = '/tmp/testobject'
    self.bucket_name = BUCKET_NAME
    self.blob_name = BLOB_NAME
    self.gcs_path = "gs://{}/{}".format(BUCKET_NAME, BLOB_NAME)

    # initialize GSC objects
    self.client = storage.Client(self.key_uri, self.creds)
    self.bucket = self.client.bucket(self.bucket_name)
    self.blob = self.bucket.blob(self.blob_name)

    # create our local test file
    with open(self.plaintext_path, 'w') as f:
      f.write(self.plaintext)

  def test_upload(self):
    """Test copy to cloud with local encryption."""
    # first, be sure there's no GCS object named after our blob_name
    try:
      self.bucket.delete_blob(self.blob_name)
    except NotFound:
      # it's ok if it doesn't exist
      pass
    # now upload the file with local encryption
    try:
      self.blob.upload_from_filename(self.plaintext_path)
    except Exception:  # pylint: disable=broad-except
      self.fail()
    # now verify that the object exists in GCS
    try:
      blobs = [b.name for b in list(self.bucket.list_blobs())]
      self.assertIn(self.blob_name, blobs)
    except NotFound:
      self.fail()

  def test_download(self):
    """Test copy from cloud with local decryption."""
    # copy down the file
    self.blob.download_to_filename(self.plaintext_path)
    # now verify that the plaintext was decrypted
    with open(self.plaintext_path, 'r') as f:
      plaintext = f.read()
    self.assertEqual(plaintext, self.plaintext)
