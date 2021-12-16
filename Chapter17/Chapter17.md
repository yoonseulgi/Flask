# 17장.  Deployment on Linux 
- 실제 사용자가 사용할 수 있도록 배포
- 해당 chapter에서는 리눅스 환경만 고려


### Traditional Hosting
- 서버 정하기
- 해당 튜토리얼은 VirtualBox 사용


### Creating an Ubuntu Server
- VM 환경설정을 위한 __Vagrantfile__ 파일 생성

```text
Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/focal64"
  config.vm.network "private_network", ip: "192.168.33.10"
  config.vm.provider "virtualbox" do |vb|
    vb.memory = "2048"
  end
end
```


### Using a SSH Client
- 가상서버를 사용하는 경우 서버를 생성할 때 IP 주소 부여
- 아래와 같은 명령어를 수행하여 새로운 서버 생성

```shell
$ ssh root@<server-ip-address>
```

- 암호를 입력하는 메시지가 뜸
  서버에서 자동 로그인 or 사용자 입력 등 다양한 옵션을 선택할 수 있음
  
  
### Password-less Logins
- 가상환경인 경우, 사용자가 암호를 사용하지 않고 로그인하도록 구성하는 것이 좋음

```shell
$ adduser --gecos "" ubuntu
$ usermod -aG sudo ubuntu
$ su ubuntu
$ ls ~/.ssh
id_rsa  id_rsa.pub
```

- __id_rsa__ , __id_rsa.pub__ 두 개의 파일이 존재하다면 키가 생성된 것
- 아래와 같은 명령어를 실행하여 비밀키와 공개키로 구성된 SSH키의 쌍을 생성

```shell
$ ssh-keygen
```

### Securing Your Server

- 비밀번호를 사용하지 않기 때문에 공격의 대상이 될 수 있음
  루트 로그인 불가능하게 설정
  sudo 명령어 비활성화
  
- 방화벽 설치

```shell
$ sudo apt-get install -y ufw
$ sudo ufw allow ssh
$ sudo ufw allow http
$ sudo ufw allow 443/tcp
$ sudo ufw --force enable
$ sudo ufw status
```
  
### Installing Base Dependencies
- 다음과 같은 패키지 설치가 필요함
  1. python interpretor
  2. mysql-server
  3. supervisor: 서버를 모니터링 하다가 문제가 발생하면 자동으로 재시작
  4. nginx: 외부 요청을 받아 애플리케이션에게 전달
  5. git: git 레파지토리에서 다운
  
```shell
$ sudo apt-get -y update
$ sudo apt-get -y install python3 python3-venv python3-dev
$ sudo apt-get -y install mysql-server postfix supervisor nginx git
```

### Installing the Application
- 우분투 사용자의 홈 디렉토리에 소스코드를 다운(git 레파지토리에서) 

```shell
$ git clone https://github.com/miguelgrinberg/microblog
$ cd microblog
$ git checkout v0.17
```

- 가상환경을 만들고, 응용 프로그램을 구동하기 위해 필요한 모든 패키지를 가상환경에 설치
- 지금까지 응용 프로그램을 위해 설치한 패키지는 __requirements.txt__ 에 저장되어 있음 

```shell
$ python3 -m venv venv
$ source venv/bin/activate
(venv) $ pip install -r requirements.txt
```

- 배포와 관련된 3가지 패키지를 사용
  1. gunicorn package : python app을 위한 패키지
  2. pymysql package : SQLAlchemy와 MySQL을 함께 작동할 수 있도록 하기 위한 패키지
  3. cryptography package : pymysql에서 MySQL 데이터베이스 서버에 대한 인증
  
```shell
 $ pip install gunicorn pymysql cryptography
```

- 환경변수 설정하기

```text
SECRET_KEY=52cb883e323b48d78a0a36e8e951ba4a
MAIL_SERVER=localhost
MAIL_PORT=25
DATABASE_URL=mysql+pymysql://microblog:<db-password>@localhost:3306/microblog
MS_TRANSLATOR_KEY=<your-translator-key-here>
```

- SECRET_KEY는 아래와 같이 생성
```shell
python3 -c "import uuid; print(uuid.uuid4().hex)"
```


### Setting Up MySQL
- 데이터베이스 서버 관리

```shell
$ sudo mysql -u root
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 8
Server version: 8.0.25-0ubuntu0.20.04.1 (Ubuntu)

Copyright (c) 2000, 2021, Oracle and/or its affiliates.

Oracle is a registered trademark of Oracle Corporation and/or its
affiliates. Other names may be trademarks of their respective
owners.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql>
```

- microblog라는 새로운 데이터베이스를 만드는 명령과 전체 접근 권한이 있는 사용자를 만드는 명령
- 전체 접근 권한을 가진 사용자와 root의 비밀번호를 다르게 설정

```shell 
mysql> create database microblog character set utf8 collate utf8_bin;
mysql> create user 'microblog'@'localhost' identified by '<db-password>';
mysql> grant all privileges on microblog.* to 'microblog'@'localhost';
mysql> flush privileges;
mysql> quit;
```

### Setting Up Gunicorn and Supervisor
- __Gunicorn__ 웹 서버 사용
- microblog를 gunicorn에서 실행

```shell
$ gunicorn -b localhost:8000 -w 4 microblog:app
```

- -b 옵션: 요청을 수신할 위치를 gunicorn에 알림
- -w 옵션: gunicorn이 수행할 작업자 수
- microblog:app 인수: gunicorn에게 애플리케이션 인스턴스를 로드하는 방법을 제공


### Setting Up Nginx
- 안전한 배포를 위해 암호화될 포트 443으로 구성되도록 설정

```shell
$ mkdir certs
$ openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 \
  -keyout certs/key.pem -out certs/cert.pem
```

- nginx에서 웹 사이트를 제공하려면 구성 파일을 작성
- __/etc/nginx/sites-enabled__ 위치에 __microblog__ 파일 작성


### Deploying Application Updates
- 애플리케이션 업그레이드를 처리하는 방법
- 다음과 같은 명령어를 통해 애플리케이션 업그레이드 


```shell 
$ git pull                              # download the new version
$ sudo supervisorctl stop microblog     # stop the current server
$ flask db upgrade                      # upgrade the database
$ flask translate compile               # upgrade the translations
sudo supervisorctl start microblog    # start a new server
```
