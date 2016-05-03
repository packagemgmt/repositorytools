Vagrant.configure("2") do |config|
  config.vm.box = "OracleLinux-7"
  config.vm.box_url = "http://cloud.terry.im/vagrant/oraclelinux-7-x86_64.box"

  # folder sharing doesn't work there
  #config.vm.box = "fedora22"
  #config.vm.box_url = "http://download.fedoraproject.org/pub/fedora/linux/releases/22/Cloud/x86_64/Images/Fedora-Cloud-Base-Vagrant-22-20150521.x86_64.vagrant-virtualbox.box"

  $script = <<SCRIPT
echo "Provisioning"
cd /vagrant

sudo yum-builddep -y *.spec
sudo yum -y install git rpm-build mock rpmdevtools python-tox
sudo usermod -a -G mock vagrant

echo "export VENV_HOME=/home/vagrant/" >> /etc/bashrc
make testenv
echo "Provisioning done."
SCRIPT

  ## Use all the defaults:
  config.vm.provision "shell", inline: $script
end
