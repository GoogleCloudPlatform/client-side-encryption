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
"""Example code for the google-cloud-storage wrapper."""

import os

from encryption_wrapper import storage

PROJECT_ID = os.getenv('PROJECT_ID', 'my-project')
SERVICE_ACCOUNT_NAME = os.getenv('SERVICE_ACCOUNT_NAME', 'wrapper-sa')
REGION = os.getenv('REGION', 'us-central1')
KEYRING_NAME = os.getenv('KEYRING_NAME', 'my-key-ring')
KEY_NAME = os.getenv('KEY_NAME', 'my-key')
CREDS_JSON = os.getenv('CREDS_JSON', os.path.expanduser('~') + '/creds.json')

key_uri = "gcp-kms://projects/{}/locations/{}/keyRings/{}/cryptoKeys/{}".format(
    PROJECT_ID,
    REGION,
    KEYRING_NAME,
    KEY_NAME
)
creds = CREDS_JSON

bucket_name = 'fe-itar'
source_file_name = 'testfile'
destination_blob_name = 'testfile'
destination_file_name = 'testfile'


def upload():
  storage_client = storage.Client(key_uri, creds)
  bucket = storage_client.bucket(bucket_name)
  blob = bucket.blob(destination_blob_name)
  blob.upload_from_filename(source_file_name)


def download():
  storage_client = storage.Client(key_uri, creds)
  bucket = storage_client.bucket(bucket_name)
  blob = bucket.blob(destination_blob_name)
  blob.download_to_filename(destination_file_name)


def main():
  upload()
  download()


if __name__ == '__main__':
  main()
