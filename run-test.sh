ansible-galaxy collection build
ansible-galaxy collection install ashemyakin-test_mod-1.0.0.tar.gz -f -p  ~/collections
ansible-playbook sample.yml -vvvvv