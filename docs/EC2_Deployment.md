## EC2 deployment

This section explains how to launch an Amazon EC2 virtual machine and connect to it. The steps assume an Amazon Linux instance and a repository that you can access.

### 1. Launch an EC2 instance

In the AWS Management Console:

1. Sign in to AWS, open **EC2**, and choose **Launch instance**.
2. Enter a name for the instance so you can recognize it later.
3. Under **Application and OS Images**, choose an Amazon Linux image, such as Amazon Linux 2023.
4. Choose an instance type. For learning and testing, use an eligible low-cost or free-tier option if available to your account.
5. Under **Key pair (login)**, create or select a key pair if you plan to connect from your computer with SSH. Download and keep the `.pem` private key somewhere secure; AWS does not let you download it again later.
6. Under **Network settings**, create or select a security group. Add an inbound rule for SSH: type **SSH**, port `22`, source **My IP**. This allows SSH connections from your current public IP address only.
7. Review the settings and choose **Launch instance**.

After launch, open **EC2 > Instances** and select the new instance. Wait until its instance state is **Running** and its status checks have passed. In the instance details, find and copy its **Public IPv4 address**. You will use this address to connect.

### 2. Allow dashboard access for testing

The dashboard uses port `5000`. Add an inbound rule for this port only if you need to open the dashboard directly in a browser for testing. Keep the source set to **My IP** so the dashboard is not exposed to everyone on the internet. This rule is separate from SSH on port `22`.

To add the rule after the instance has been created:

1. In the EC2 console, choose **Instances** in the left navigation and select your instance.
2. On the instance details page, open the **Security** tab.
3. Under **Security groups**, choose the security group name linked to the instance.
4. Open **Inbound rules** and choose **Edit inbound rules**.
5. Choose **Add rule**, then set **Type** to **Custom TCP**. Set **Port range** to `5000`, **Source** to **My IP**, and add a description such as `Heartbeat dashboard testing`.
6. Choose **Save rules**.

If you are not testing the dashboard in a browser, you can skip this port `5000` rule. Do not use `0.0.0.0/0` as the source for this testing rule; that would allow connections from any IP address.

### 3. Connect to the instance

You can connect either from the AWS console or from a terminal on your computer.

#### Option A: Connect in the AWS console

1. Go to **EC2 > Instances** and select your running instance.
2. Choose **Connect** near the top of the page.
3. Open the **EC2 Instance Connect** tab and choose **Connect**.

If the EC2 Instance Connect option is unavailable or the connection fails, use SSH from a terminal instead.

#### Option B: Connect using SSH

First open a terminal and change directory to the folder containing your `.pem` key. For example, if the key is in your Downloads folder:

**Bash (Linux or macOS)**

```bash
cd "$HOME/Downloads"
chmod 400 my-ec2-key.pem
ssh -i my-ec2-key.pem ec2-user@EC2_PUBLIC_IP
```

**PowerShell (Windows)**

```powershell
Set-Location "$HOME\Downloads"
ssh -i .\my-ec2-key.pem ec2-user@EC2_PUBLIC_IP
```

Before running the command, replace `my-ec2-key.pem` with your key's actual filename and replace `EC2_PUBLIC_IP` with the instance's **Public IPv4 address**. Keep the key filename and IP address together with the `-i` and SSH destination as shown. The first time you connect, SSH may ask whether you trust the host; type `yes` if the displayed address matches your EC2 instance.

When the connection succeeds, your terminal is now running commands on the EC2 instance. Type `exit` and press Enter when you want to disconnect.
otheriwse go to the ec2 instance and click on connect 