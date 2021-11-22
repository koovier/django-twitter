#!/usr/bin/env bash

echo 'Start!'

sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.6 2

cd /vagrant

sudo apt-get update
# sudo apt-get install -y apache2
# if ! [ -L /var/www ]; then
#   rm -rf /var/www
#   ln -fs /vagrant /var/www
# fi

# apt-get install -y git

# if pip | cout \|
# wget https://bootstrap.pypa.io/get-pip.py
# sudo python get-pip.py
if [ ! -f "/usr/bin/pip" ]; then
  sudo apt-get install -y python3-pip
  sudo apt-get install -y python-setuptools
  sudo ln -s /usr/bin/pip3 /usr/bin/pip
else
  echo "pip3 已安装"
fi

# 升级pip，目前存在问题，read timed out，看脸，有时候可以，但大多时候不行
# python -m pip install --upgrade pip
# 换源完美解决
# 安装pip所需依赖
pip install --upgrade setuptools -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install --ignore-installed wrapt -i https://pypi.tuna.tsinghua.edu.cn/simple
# 安装pip最新版
pip install -U pip -i https://pypi.tuna.tsinghua.edu.cn/simple
# 根据 requirements.txt 里的记录安装 pip package，确保所有版本之间的兼容性
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

sudo apt-get install tree

# 安装配置mysql8
if ! [ -e /vagrant/mysql-apt-config_0.8.15-1_all.deb ]; then
	wget -c https://dev.mysql.com/get/mysql-apt-config_0.8.15-1_all.deb
fi

sudo dpkg -i mysql-apt-config_0.8.15-1_all.deb

sudo apt-get update

sudo DEBIAN_FRONTEND=noninteractivate apt-get install -y mysql-server
sudo apt-get install -y libmysqlclient-dev
pip install mysqlclient


# 设置mysql的root账户的密码为yourpassword
# 创建名为twitter的数据库
sudo mysql -u root << EOF
	ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'yourpassword';
	flush privileges;
	show databases;
	CREATE DATABASE IF NOT EXISTS twitter;
EOF
# fi


# 修改mysql密码&创建database
# 设置密码为password
# ALTER USER 'root'@'localhost' IDENTIFIED BY '*{password}*';
# ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '新密码';
# 创建名为twitter的数据库
# CRESTE DATABASE twitter;

# django界面以及admin

cd /vagrant

python manage.py migrate

# superuser名字
USER="admin"
# superuser密码
PASS="admin"
# superuser邮箱
MAIL="admin@twitter.com"
script="
from django.contrib.auth.models import User;

username = '$USER';
password = '$PASS';
email = '$MAIL';

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password);
    print('Superuser created.');
else:
    print('Superuser creation skipped.');
"
printf "$script" | python manage.py shell



# 如果想直接进入/vagrant路径下
# 请输入vagrant ssh命令进入
# 手动输入
# 输入ls -a
# 输入 vi .bashrc
# 在最下面，添加cd /vagrant

echo 'All Done!'
