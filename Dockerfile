FROM ubuntu:latest

RUN apt-get update && \
    apt-get install -y python3 python3-dev python3-pip python3-jmespath && \
    apt-get install -y openssh-client iputils-ping sshpass wget

RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip3 install ansible

RUN mkdir /var/workdir/
WORKDIR /var/workdir

COPY sample.yml /var/workdir
COPY ansible.cfg /var/workdir

RUN ansible-galaxy collection install ashemyakin.test_mod -p ./collections



ENTRYPOINT ansible-playbook sample.yml -vvvvv