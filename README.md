# Client Side Encryption wrapper

This project wraps `gsutil` and the Python client library for Google Cloud Storage in order to perform local encryption and decryption.

## Installation

The process for installing this encryption wrapper is as follows:
1. Install the [latest release](https://github.com/GoogleCloudPlatform/client-side-encryption/releases/latest). For example:

```bash
wget https://github.com/GoogleCloudPlatform/client-side-encryption/releases/download/v0.9.2/client_side_encryption_0.9.2.deb
apt-get update
apt-get install -y ./client_side_encryption_0.9.2.deb
```

2. Create a KMS key (note that this should be in the same region as the instances that will be calling KMS)
3. Create a service account
4. Assign roles to the service account
5. Download the service account's credentials file

### Service Account

This encryption wrapper requires a service account with the Cloud KMS Encrypter/Decrypter role. For example:

```bash
export PROJECT_ID=your-project-id
export SERVICE_ACCOUNT_NAME=wrapper-sa
gcloud config set project ${PROJECT_ID}

gcloud kms keyrings create my-key-ring --location us-central1
gcloud kms keys create my-key \
    --keyring my-key-ring \
    --location us-central1 \
    --purpose encryption \
    --protection-level=hsm

gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME}
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/cloudkms.cryptoKeyEncrypterDecrypter"
gcloud iam service-accounts keys create creds.json \
  --iam-account ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com
```

## Usage

To use the `gsutil` wrapper's encryption features, include the `--client_side_encryption` argument in your invocation. This arguments takes as a value a tuple that consists of the KMS URI and path to the service account creds.json file.

Example:

```bash
$ export PROJECT_ID=your-project-id
$ export SERVICE_ACCOUNT_NAME=wrapper-sa
$ export REGION=us-central1
$ export KEYRING_NAME=my-key-ring
$ export KEY_NAME=my-key
$ echo 'this is cleartest' > testfile
$ ./gsutil cp --client_side_encryption=gcp-kms://projects/${PROJECT_ID}/locations/${REGION}/keyRings/${KEYRING_NAME}/cryptoKeys/${KEY_NAME},creds.json testfile gs://fe-itar/
gsutil is being wrapped. Standard gsutil available at: /snap/bin/gsutil
encrypted testfile
Copying file:///home/jasoncallaway_google_com/.gsutil-wrapper//testfile [Content-Type=application/octet-stream]...
/ [1 files][  183.0 B/  183.0 B]                                                
Operation completed over 1 objects/183.0 B.
$
$ /snap/bin/gsutil cp gs://fe-itar/testfile /tmp/testfile
Copying gs://fe-itar/testfile...
/ [1 files][  183.0 B/  183.0 B]                                                
Operation completed over 1 objects/183.0 B.                                      
$ cat /tmp/testfile 
�
$z����Ґ�)���    H�S� �P'� �x�e��� Y*W
 

zN�=�1�5p� ��˞ %
 �5u
���U�k��)N0�U�q         ��p ��~ ٝ�}??
 �_���Y  ����  �<���-�z�W�aRJnb �'� !_�R�U���
                                         �F���Gou� �,
$ 
$ ./gsutil cp --client_side_encryption=gcp-kms://projects/${PROJECT_ID}/locations/${REGION}/keyRings/${KEYRING_NAME}/cryptoKeys/${KEY_NAME},creds.json gs://fe-itar/testfile /tmp/testfile
gsutil is being wrapped. Standard gsutil available at: /snap/bin/gsutil
Copying gs://fe-itar/testfile...
/ [1 files][  183.0 B/  183.0 B]                                                
Operation completed over 1 objects/183.0 B.
decrypted /tmp/testfile
$ cat /tmp/testfile 
this is cleartext
```

Using the Python client library wrapper is easy. You only have to make two modifications to your existing code:
1. The import statement
2. The GCS Client constructor

Example:

```python
import os

# first change -- use this storage instead of "from google.cloud import storage"
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

bucket_name = 'my_bucket'
source_file_name = 'testfile'
destination_blob_name = 'testfile'
destination_file_name = 'testfile'


def upload():
  # second change -- provide the key URI and creds file path to the constructor
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
```

## Contributing

Want to help make these wrappers better? Check out our [contributing](CONTRIBUTING.md) guide.
