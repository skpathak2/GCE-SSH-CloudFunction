# GCE-SSH-CloudFunction

This repo holds the Python Code based on [tutorial on ssh to a Compute Engine VM](https://cloud.google.com/compute/docs/tutorials/service-account-ssh) that can be used to ssh to a Google Compute Engine VM via CloudFunction and execute the commands based on an event driven triggers.



## Steps to Configure CloudFunction

1. Clone the `Git Project` (Preferably on [Cloud Shell Terminal](https://cloud.google.com/shell))

    <pre>
    git clone https://github.com/skpathak2/GCE-SSH-CloudFunction.git
    </pre>

2. Navigate to `cloudFunSSH.py` and Update the Following `variables` in the `cloudFunSSH.py`
    ```
    vim cloudFunSSH.py

    main("<bash command>", "<project>", hostname="<public/privateIP>")
    ```

    Example Below
    ```
    main("sudo gsutil cp -r gs://my-bucket .", "my-sandbox", hostname="34.13.04.12")
    ```

> Note:- It is recommended to [Configure Serverless VPC Access](https://cloud.google.com/vpc/docs/configure-serverless-vpc-access) to access the VPC resources (In this case GCE VM's private interface) via private ip.