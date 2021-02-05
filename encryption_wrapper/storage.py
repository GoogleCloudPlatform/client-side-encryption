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
"""Provides Cloud KMS + Tink local encryption and decryption of files.

For use with the google-cloud-storage Python module.
"""

import os
import random
import shutil
import string

from encryption_wrapper import encryption

from google.cloud import storage


# Global variables
_GSUTIL = os.getenv('GSUTIL_ACTUAL', '/snap/bin/gsutil')
_TMP_LOCATION = os.getenv('GSUTIL_TMP_LOCATION',
                          os.path.expanduser('~') + '/.gsutil-wrapper/')


class Client(storage.Client):
  """Wrap the google-cloud-storage Client class."""

  def __init__(self, key_uri, creds, tmp_location=_TMP_LOCATION):
    """Init class for our Client wrapper.

    Args:
      key_uri: string with the resource identifier for the KMS symmetric key
      creds: path to the creds.json file with the service account key for KMS
      tmp_location: path to swap location for local encryption and decryption

    Returns:
      None
    """
    self.key_uri = key_uri
    self.creds = creds
    random_str = ''.join(
        (random.choice(string.ascii_letters + string.digits) for i in range(8)))
    self.tmp_location = tmp_location + random_str + '/'
    super().__init__()

  def bucket(self, bucket_name, user_project=None):
    """Wrapper for the bucket function.

    Args:
      bucket_name: same as real bucket_name
      user_project: same as real user_project

    Returns:
      Bucket: wrapped Bucket class
    """

    # Return the wrapped Bucket class from below
    return Bucket(
        client=self,
        name=bucket_name,
        user_project=user_project,
        key_uri=self.key_uri,
        creds=self.creds)


class Bucket(storage.Bucket):
  """Wrap the google-cloud-storage Bucket class."""

  def __init__(self, client, name, user_project, key_uri, creds):
    """Init class for our Bucket wrapper.

    Args:
      client: wrapped Client class
      name: same as real bucket name
      user_project: same as real user_project
      key_uri: string with the resource identifier for the KMS symmetric key
      creds: path to the creds.json file with the service account key for KMS

    Returns:
      None
    """
    self.key_uri = key_uri
    self.creds = creds
    super().__init__(client, name, user_project)

  def blob(self,
           blob_name,
           chunk_size=None,
           encryption_key=None,
           kms_key_name=None,
           generation=None):
    """Wrapper for the blob function.

    Args:
      blob_name: same as real blob_name
      chunk_size: same as real chunk_size
      encryption_key: same as real encryption_key
      kms_key_name: same as real kms_key_name
      generation: same as real generation

    Returns:
      Blob: wrapped Blob class
    """

    # Return the wrapped Blob class from below
    return Blob(
        blob_name=blob_name,
        bucket=self,
        chunk_size=chunk_size,
        encryption_key=encryption_key,
        kms_key_name=kms_key_name,
        generation=generation,
        key_uri=self.key_uri,
        creds=self.creds)


class Blob(storage.Blob):
  """Wrap the google-cloud-storage Blob class."""

  def __init__(self,
               blob_name,
               bucket,
               chunk_size=None,
               encryption_key=None,
               kms_key_name=None,
               generation=None,
               key_uri=None,
               creds=None):
    """Init class for our Bucket wrapper.

    Args:
      blob_name: same as real blob_name
      bucket: same as real bucket
      chunk_size: same as real chunk_size
      encryption_key: same as real encryption_key
      kms_key_name: same as real kms_key_name (note this is for server-side
        encryption, not client-side, so don't use this for ITAR use cases)
      generation: same as real generation
      key_uri: string with the resource identifier for the KMS symmetric key
      creds: path to the creds.json file with the service account key for KMS

    Returns:
      None
    """
    self.key_uri = key_uri
    self.creds = creds
    self.e = encryption.EncryptWithTink(self.key_uri, self.creds)
    super().__init__(blob_name, bucket, chunk_size, encryption_key,
                     kms_key_name, generation)

  def upload_from_filename(self,
                           file_obj,
                           rewind=False,
                           size=None,
                           content_type=None,
                           num_retries=None,
                           client=None,
                           predefined_acl=None,
                           if_generation_match=None,
                           if_generation_not_match=None,
                           if_metageneration_match=None,
                           if_metageneration_not_match=None,
                           timeout=60,
                           checksum=None):
    """Wrapped upload_from_filname function.

    This will encrypt locally using
       Tink before handing the encrypted file path to the real
       upload_from_filename.

    Args:
      file_obj: same as real file_obj
      rewind: same as real rewind
      size: same as real size
      content_type: same as real content_type
      num_retries: same as real num_retries
      client: wrapped Client class
      predefined_acl: same as real predefined_acl
      if_generation_match: same as real if_generation_match
      if_generation_not_match: same as real if_generation_not_match
      if_metageneration_match: same as real if_metageneration_match
      if_metageneration_not_match: same as real if_metageneration_not_match
      timeout: same as real timeout
      checksum: same as real

    Returns:
      None
    """

    # Encrypt the file
    encrypted_file_obj = self.e.encrypt(file_obj)

    # Hand off to real upload_from_filename, but with the encrypted filename
    # instead of the cleartext one
    super().upload_from_filename(
        encrypted_file_obj,
        content_type,
        client,
        predefined_acl,
        if_generation_match,
        if_generation_not_match,
        if_metageneration_match,
        if_metageneration_not_match,
        timeout=60,
        checksum='md5')

    # Apply custom metadata. We instanciate a new GCS Client here so we don't
    # default to any from outer scopes
    metadata_client = storage.Client()
    metadata_bucket = metadata_client.get_bucket(self.bucket.name)
    metadata_blob = metadata_bucket.get_blob(self.name)
    metadata = {'client-side-encrypted': 'true'}
    metadata_blob.metadata = metadata
    metadata_blob.patch(client=metadata_client)

    # Clean up
    shutil.rmtree(_TMP_LOCATION)

  def download_to_filename(self,
                           filename,
                           client=None,
                           start=None,
                           end=None,
                           raw_download=False,
                           if_generation_match=None,
                           if_generation_not_match=None,
                           if_metageneration_match=None,
                           if_metageneration_not_match=None,
                           timeout=60,
                           checksum='md5'):
    """Wrapped upload_from_filname function.

    This will encrypt locally using
           Tink before handing the encrypted file path to the real
           upload_from_filename.

    Args:
      filename: same as real filename
      client: wrapped Client class
      start: same as real start
      end: same as real end
      raw_download: same as real raw_download
      if_generation_match: same as real if_generation_match
      if_generation_not_match: same as real if_generation_not_match
      if_metageneration_match: same as real if_metageneration_match
      if_metageneration_not_match: same as real if_metageneration_not_match
      timeout: same as real timeout
      checksum: same as real checksum

    Returns:
      None
    """

    # Download first
    super().download_to_filename(filename, client, start, end, raw_download,
                                 if_generation_match, if_generation_not_match,
                                 if_metageneration_match,
                                 if_metageneration_not_match, timeout, checksum)

    # Then decrypt
    self.e.decrypt(filename)

    # Clean up
    shutil.rmtree(_TMP_LOCATION)





