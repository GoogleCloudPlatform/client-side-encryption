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
"""Common functions."""

import subprocess
import sys


def error_and_exit(message):
  """Helper function to print errors and exit with sig 1."""
  print('encryption_wrapper wrapper ERROR: {}'.format(message))
  sys.exit(1)


def run_command(cmd, description):
  """Helper function to execute commands.

  Args:
    cmd: the command to execute
    description: description of the command, for logging purposes

  Returns:
    results: output from the executed command
  """

  try:
    p = subprocess.Popen(cmd,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    while True:
      # print command output as it happens
      line = p.stdout.readline()
      if not line:
        break
      else:
        print(str(line.strip(), 'utf-8'))
  except subprocess.SubprocessError as command_exception:
    error_and_exit('{} failed: {}'.format(description,
                                          str(command_exception)))

  # now communicate with the subprocess to the returncode property is set
  p.communicate()
  return p.returncode
