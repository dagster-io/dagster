# So you want to reproduce a Buildkite build ad hoc...

1. Launch an Amazon Linux 2 AMI in EC2 (ami-0019ef04ac50be30f). Don't forget to give it a
   descriptive name

2. Ssh in to your new instance, eg:

    ssh ec2-user@127.0.0.1

3. Install the buildkite agent

    sudo sh -c 'echo -e "[buildkite-agent]\nname = Buildkite Pty Ltd\nbaseurl = https://yum.buildkite.com/buildkite-agent/stable/x86_64/\nenabled=1\ngpgcheck=0\npriority=1" > /etc/yum.repos.d/buildkite-agent.repo'

4. Install docker

    sudo yum install -y http://mirror.centos.org/centos/7/extras/x86_64/Packages/container-selinux-2.68-1.el7.noarch.rpm
    sudo yum-config-manager \
        --add-repo \
        https://download.docker.com/linux/centos/docker-ce.repo
    sudo yum install -y docker-ce docker-ce-cli containerd.io
    sudo groupadd docker
    sudo usermod -aG docker $USER

5. Log back in and restart docker

    exit
    ssh ec2-user@127.0.0.1
    sudo systemctl start docker

6. Export the buildkite environment from the job that previously ran.

7. Set `BUILDKITE_BUILD_PATH` and `BUILDKITE_PLUGINS_PATH`

    mkdir -p build
    mkdir -p plugins
    export BUILDKITE_BUILD_PATH=$(pwd)/build
    export BUILDKITE_PLUGINS_PATH=$(pwd)/build

8. Ensure the SSH key you need for GitHub is present and add it to the ssh-agent

    eval `ssh-agent`
    ssh-add private_key

9. Ensure AWS and any other required env variables are set.

10. Run the build:

    buildkite bootstrap
