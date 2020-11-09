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
import shutil
import stat

from encryption_wrapper.common import error_and_exit

import tink
from tink import aead
from tink.core import TinkError
from tink.integration import gcpkms


_TMP_LOCATION = os.getenv('GSUTIL_TMP_LOCATION',
                          os.path.expanduser('~') + '/.gsutil-wrapper/')


class EncryptWithTink(object):
  """Perform local encryption and decryption with Tink."""

  def __init__(self, key_uri, creds, tmp_location=_TMP_LOCATION):
    """Init class for EncryptWithTink.

    Args:
      key_uri: string with the resource identifier for the KMS symmetric key
      creds: path to the creds.json file with the service account key for KMS
      tmp_location: temporary directory for encryption and decryption

    Returns:
      None
    """

    self.tmp_location = tmp_location
    # Make the tmp dir if it doesn't exist
    if not os.path.isdir(self.tmp_location):
      # noinspection PyUnusedLocal
      try:
        os.makedirs(self.tmp_location)
      except FileExistsError:
        # This is ok because the directory already exists
        pass
      except OSError as os_error:
        error_and_exit(str(os_error))

    # Initialize Tink
    try:
      aead.register()
      self.key_template = aead.aead_key_templates.AES128_EAX
      self.keyset_handle = tink.new_keyset_handle(self.key_template)
      gcp_client = gcpkms.GcpKmsClient(key_uri, creds)
      gcp_aead = gcp_client.get_aead(key_uri)
      self.env_aead = aead.KmsEnvelopeAead(self.key_template, gcp_aead)
    except TinkError as tink_init_error:
      error_and_exit('tink initialization failed: ' + str(tink_init_error))

  def encrypt(self, filepath):
    """encrypt a file locally.

    Args:
      filepath: path to the file to be encrypted

    Returns:
      encrypted_filepath: path to the locally encrypted file
    """
    # TODO(b/170396289): handle wildcards and recursive copies

    # file type validation; can't handle directories or FIFOs
    if os.path.isdir(filepath):
      error_and_exit('cannot encrypt a directory')
    elif stat.S_ISFIFO(os.stat(filepath).st_mode):
      error_and_exit('cannot encrypt a FIFO')

    # tmp location and name for the encrypted file
    filename = os.path.basename(filepath)
    encrypted_filepath = self.tmp_location + '/' + filename
    try:
      shutil.copyfile(filepath, encrypted_filepath)
    except OSError as copy_error:
      error_and_exit(str(copy_error))

    # read the file, encrypt it, write it to the tmp location
    try:
      with open(filepath, 'rb') as f:
        plaintext = f.read()
      ciphertext = self.env_aead.encrypt(plaintext, b'')
      with open(encrypted_filepath, 'wb') as f:
        f.write(ciphertext)
    except TinkError as encryption_error:
      error_and_exit(str(encryption_error))

    return encrypted_filepath

  def decrypt(self, filepath):
    """decrypt a file locally.

    Args:
      filepath: path to the file to be decrypted

    Returns:
      decrypted_filepath: path to the locally decrypted file
    """

    # filename and paths to tmp directory
    filename = os.path.basename(filepath)
    decrypted_filepath = self.tmp_location + '/' + filename

    # read the ciphertext, decrypt it, write it to the tmp location, then
    # overwrite the encrypted file with the decrypted file, finally remove
    # the encrypted file from the tmp location
    try:
      with open(filepath, 'rb') as f:
        ciphertext = f.read()
      cleartext = self.env_aead.decrypt(ciphertext, b'')
      with open(decrypted_filepath, 'wb') as f:
        f.write(cleartext)
      shutil.copyfile(decrypted_filepath, filepath)
      os.unlink(decrypted_filepath)
    except TinkError as decryption_error:
      error_and_exit(str(decryption_error))

    return decrypted_filepath
