import argparse
import logging
import subprocess
import time
import uuid

import googleapiclient.discovery
import requests


# Global variables
SERVICE_ACCOUNT_METADATA_URL = (
    'http://metadata.google.internal/computeMetadata/v1/instance/'
    'service-accounts/default/email')
HEADERS = {'Metadata-Flavor': 'Google'}

# [END imports_and_variables]

# def gce_ssh(event, context):  <This is to be used with Gen1 CloudFunction>
def gce_ssh(*args, **kwargs):

    """Triggered by a change to a Cloud Storage bucket.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    # [START run_command_local]
    def execute(cmd, cwd=None, capture_output=False, env=None, raise_errors=True):
        """Execute an external command (wrapper for Python subprocess)."""
        logging.info('Executing command: {cmd}'.format(cmd=str(cmd)))
        stdout = subprocess.PIPE if capture_output else None
        process = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=stdout)
        output = process.communicate()[0]
        returncode = process.returncode
        if returncode:
            # Error
            if raise_errors:
                raise subprocess.CalledProcessError(returncode, cmd)
            else:
                logging.info('Command returned error status %s', returncode)
        if output:
            logging.info(output)
        return returncode, output
    # [END run_command_local]


    # [START create_key]
    def create_ssh_key(oslogin, account, private_key_file=None, expire_time=300):
        """Generate an SSH key pair and apply it to the specified account."""
        private_key_file = private_key_file or '/tmp/key-' + str(uuid.uuid4())
        execute(['ssh-keygen', '-t', 'rsa', '-N', '', '-f', private_key_file])

        with open(private_key_file + '.pub', 'r') as original:
            public_key = original.read().strip()

        # Expiration time is in microseconds.
        expiration = int((time.time() + expire_time) * 1000000)

        body = {
            'key': public_key,
            'expirationTimeUsec': expiration,
        }
        oslogin.users().importSshPublicKey(parent=account, body=body).execute()
        return private_key_file
    # [END create_key]


    # [START run_command_remote]
    def run_ssh(cmd, private_key_file, username, hostname):
        """Run a command on a remote system."""
        ssh_command = [
            'ssh', '-i', private_key_file, '-o', 'StrictHostKeyChecking=no',
            '{username}@{hostname}'.format(username=username, hostname=hostname),
            cmd,
        ]
        ssh = subprocess.Popen(
            ssh_command, shell=False, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        result = ssh.stdout.readlines()
        return result if result else ssh.stderr.readlines()

    # [END run_command_remote]


    # [START main]
    def main(cmd, project, instance=None, zone=None, oslogin=None, account=None, hostname=None, username=None):
        """Run a command on a remote system."""

        # Create the OS Login API object.
        oslogin = oslogin or googleapiclient.discovery.build('oslogin', 'v1')

        # Identify the service account ID if it is not already provided.
        account = account or requests.get(
            SERVICE_ACCOUNT_METADATA_URL, headers=HEADERS).text
        if not account.startswith('users/'):
            account = 'users/' + account

        # Create a new SSH key pair and associate it with the service account.
        private_key_file = create_ssh_key(oslogin, account)

        # Using the OS Login API, get the POSIX user name from the login profile
        # for the service account.
        profile = oslogin.users().getLoginProfile(name=account).execute()
        username = username or profile.get('posixAccounts')[0].get('username')

        # Create the hostname of the target instance using the instance name,
        # the zone where the instance is located, and the project that owns the
        # instance.
        hostname = hostname or '{instance}.{zone}.c.{project}.internal'.format(
            instance=instance, zone=zone, project=project)

        # Run a command on the remote instance over SSH.
        result = run_ssh(cmd, private_key_file, username, hostname)

        # Print the command line output from the remote instance.
        # Use .rstrip() rather than end='' for Python 2 compatability.
        for line in result:
            print(line.decode('utf-8').rstrip('\n\r'))

        # Shred the private key and delete the pair.
        execute(['shred', private_key_file])
        execute(['rm', private_key_file])
        execute(['rm', private_key_file + '.pub'])


    # file = event
    print("Below are the all the avaliable arguments")
    for arg in args:
        print(arg)
    main("sudo gsutil cp -r gs://mubuck.", "my-sandbox", hostname="MyIPAddress")
    # print(f"Processing file: {file['name']}.") <To be used with Gen1 CloudFunction>