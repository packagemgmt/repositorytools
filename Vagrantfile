Vagrant.configure("2") do |config|
  config.vm.box = "OracleLinux-7"
  config.vm.box_url = "http://cloud.terry.im/vagrant/oraclelinux-7-x86_64.box"

  $script = <<SCRIPT
echo "Provisioning"
cd /vagrant

sudo yum-builddep -y *.spec
sudo yum -y install git rpm-build mock rpmdevtools
sudo usermod -a -G mock vagrant
make venv
echo "Provisioning done."
SCRIPT

  ## Use all the defaults:
  config.vm.provision "shell", inline: $script
end