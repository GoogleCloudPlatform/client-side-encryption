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
"""Unittests for the gsutil wrapper."""

import os
import unittest

from encryption_wrapper.common import run_command

import pandas as pd

from google.cloud import storage
from google.cloud.exceptions import NotFound

from scipy.stats import entropy


class TestGsutilWrapper(unittest.TestCase):
  """Test cases for the gsutil wrapper."""

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
    self.client = storage.Client()
    self.bucket = self.client.bucket(self.bucket_name)
    self.blob = self.bucket.blob(self.blob_name)

    # create our local test file
    with open(self.plaintext_path, 'w') as f:
      f.write(self.plaintext)

  def test_application_credentials(self):
    """Ensure our application credentials can copy and list files in GCS."""
    try:
      self.blob.upload_from_filename(self.plaintext_path)
    except Exception:  # pylint: disable=broad-except
      # if we can't upload a blob, just fail
      self.fail()
    try:
      # now check to see that the blob made it
      blobs = [b.name for b in list(self.bucket.list_blobs())]
      self.assertIn(self.blob_name, blobs)
    except NotFound:
      # if the blob isn't in the bucket, fail
      self.fail()

  def test_gsutil_wrapper(self):
    """Test copy to cloud and copy from cloud with local encryption."""
    # first, be sure there's no GCS object named after our blob_name
    try:
      self.bucket.delete_blob(self.blob_name)
    except NotFound:
      # it's ok if it doesn't exist
      pass
    # run the copy to cloud command
    command = ('./gsutil cp --client_side_encryption={key_uri},{creds} '
               '{plaintext_path} {gcs_path}').format(
                   key_uri=self.key_uri,
                   creds=self.creds,
                   plaintext_path=self.plaintext_path,
                   gcs_path=self.gcs_path)
    returncode = run_command(command, 'test upload')
    self.assertEqual(0, returncode)
    # now verify that the object exists in GCS
    try:
      blobs = [b.name for b in list(self.bucket.list_blobs())]
      self.assertIn(self.blob_name, blobs)
    except NotFound:
      self.fail()

    # run the copy from cloud command
    command = ('./gsutil cp --client_side_encryption={key_uri},{creds} '
               '{gcs_path} {plaintext_path}').format(
                   key_uri=self.key_uri,
                   creds=self.creds,
                   plaintext_path=self.plaintext_path,
                   gcs_path=self.gcs_path)
    returncode = run_command(command, 'test download')
    self.assertEqual(0, returncode)
    # now verify that the plaintext was decrypted
    with open(self.plaintext_path, 'r') as f:
      plaintext = f.read()
    self.assertEqual(plaintext, self.plaintext)

  def test_encryption(self):
    """Verify that files copied to GCS have been encrypted."""
    # copy up an encrypted file
    command = ('./gsutil cp --client_side_encryption={key_uri},{creds} '
               '{plaintext_path} {gcs_path}').format(
                   key_uri=self.key_uri,
                   creds=self.creds,
                   plaintext_path=self.plaintext_path,
                   gcs_path=self.gcs_path)
    run_command(command, 'test upload')
    # calculate the Shannon entropy of the plaintext
    plaintext_series = pd.Series(list(self.plaintext))
    plaintext_entropy = entropy(plaintext_series.value_counts())
    # now copy down the encrypted object using the unwrapped GCS client library
    self.blob.download_to_filename(self.plaintext_path)
    with open(self.plaintext_path, 'rb') as f:
      ciphertext_bitearray = f.read()
    ciphertext_series = pd.Series(list(ciphertext_bitearray))
    ciphertext_entropy = entropy(ciphertext_series.value_counts())
    # verify that the entropy of the ciphertext is higher
    self.assertGreater(ciphertext_entropy, plaintext_entropy)
