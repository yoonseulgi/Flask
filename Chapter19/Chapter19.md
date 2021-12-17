# 19장. Deployment on Docker Containers
- 실제 사용자가 사용할 수 있도록 배포
- 해당 chapter에서는 Docker 환경만 고려
- 컨테이너는 애플리케이션과 구동 환경을 완전히 격리시킨 상태에서 실행되도록 함
- 커널은 공유하지만 자체 파일 시스템이 존재해 격리 수준 높은 편

### Installing Docker
- 도커 홈페이지에서 다운
- Hyper-v가 필요


### Building a Container Image
- 이미지 빌드용 컨테이너 제작
- 네트워킹, 시작 옵션 등과 관련된 다양한 설정과 함께 컨테이너 파일 시스템의 완전한 표현이 포함
- 새로운 이미지가 생성될 때마다 애플리케이션 재설치해야 하는 문제가 존재
- 스크립트 파일을 통해 이미지 생성을 위해 만들어야 하는 파일에서 빌드 지침을 읽고 실행
- 설치 프로그램 스크립트

__Dockerfile:__
```text
FROM python:slim
RUN useradd microblog
WORKDIR /home/microblog

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn

COPY app app
COPY migrations migrations
COPY microblog.py config.py boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP microblog.py

RUN chown -R microblog:microblog ./
USER microblog

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
```



- 이미지는 콜론이나 이름으로 구분하는 것이 변형되지 않음
- __RUN명령어__ 는 컨테이너 켄텍스트에서 임의의 명령을 실행
- __useradd명령어__ 는 root로 응용 프로그램을 실행하는 것은 위험함으로 새로운 사용자 정의 
- __WORKDIR 명령어__ 는 애플리케이션이 설치될 기본 디렉토리를 설정
- __COPY 명령어__ 는 시스템에서 컨테이너 파일 시스템으로 파일을 전송
  해당 명령어를 통해 requirements.txt 파일을 컨테이너 파일 시스템에 있는 마이크로 블로그 사용자의 홈 디렉토리에 복사
- __RUN chmod 명령어__ 는 새 boot.sh 파일이 실행 파일로 올브라게 설정되었는지 확인
- __ENV 명령어__ 는 컨테이너 내부에 환경 변수를 설정
- __USER 명령어__ 새 마이크로블로그 사용자를 모든 후속 지침과 컨테이너가 시작될 때를 기본값으로 설정
- __EXPOSE 명령어__ 해당 컨테이너가 서버에 사용할 포트를 구성
- __ENTRYPOINT 명령어__ 컨터네이너가 시작될 때 실행되어야 하는 기본 명령을 정의

__boot.sh__
```text
#!/bin/bash
source venv/bin/activate
flask db upgrade
flask translate compile
exec gunicorn -b :5000 --access-logfile - --error-logfile - microblog:app
```

- 가상 환경을 활성화하고 마이그레이션 프레임워크를 통해 데이터베이스를 업그레이드, 언어 번역을 컴파일, gunicorn으로 서버 실행하는 코드
- __exec__ : exec는 스크립트를 실행하는 프로세스를 트리거하여 새 프로세스로 시작하지 않고 지정된 명령으로 대체
  도커는 컨테이너에서 실행되는 첫 번째 프로세스와 연결하여 수명을 연장하는 것이 중요
- -t 인수는 새 컨테이너 이미지의 이름과 태그를 설정  

```shell
$ docker build -t microblog:latest .
```

### Starting a Container
- 이미지가 이미 생성되었으므로 이제 애플리케이션의 컨테이너 버전 실행 가능

```shell
$ docker run --name microblog -d -p 8000:5000 --rm microblog:latest
```

- --name 옵션은 새 컨테이너의 이름을 제공
- -d 옵션은 도커의 백그라운드에서 컨테이너를 실행
- -p 옵션은 컨테이너 포트를 호스트 포트에 매핑
- 첫 번째 포트는 호스트 포트, 두 번째 포트는 컨테이너 내부 포트
- --rm 옵션은 컨테이너가 종료되면 삭제


### Using Third-Party "Containerized" Services
- 컨테이너의 파일 시스템은 임시 파일 시스템
- 컨테이너에서 읽어서 파일 시스템에 데이터를 쓸 때, 컨테이너 파일이 손실되면 데이터베이스의 파일도 손실될 가능성 존재
- 2개의 추가 컨테이너 생성(MySQL 데이터베이스용, Elasticsearch 서비스용)

### Adding a MySQL Container
- MySQL은 도커 실행에 전달해야 하는 환경 변수에 의존
- 도커가 설치된 컴퓨터에서 아래와 같은 명령어를 실행하면, MySQL 서버를 얻을 수 있음 

```shell
$ docker run --name mysql -d -e MYSQL_RANDOM_ROOT_PASSWORD=yes \
    -e MYSQL_DATABASE=microblog -e MYSQL_USER=microblog \
    -e MYSQL_PASSWORD=<database-password> \
    mysql/mysql-server:latest
```

- 애플리케이션 or 도커파일이 변경될 때마다 컨테이너 이미지를 다시 빌드
```shell
$ docker run --name microblog -d -p 8000:5000 --rm -e SECRET_KEY=my-secret-key \
    -e MAIL_SERVER=smtp.googlemail.com -e MAIL_PORT=587 -e MAIL_USE_TLS=true \
    -e MAIL_USERNAME=<your-gmail-username> -e MAIL_PASSWORD=<your-gmail-password> \
    --link mysql:dbserver \
    -e DATABASE_URL=mysql+pymysql://microblog:<database-password>@dbserver/microblog \
    microblog:latest
```

- __--link 옵션__ 은 도커에 컨테이너에 액세스할 수 있는 다른 컨테이너를 만들도록 지시(연결할 컨테이너의 이름 : 생성한 MySQL 이름) 
- 두 컨테이너 간의 링크가 설정되면 SQLAlchemy가 다른 컨테이너의 mysql 데이터베이스 사용을 지시하도록 DATABASE_URL 환경 변수를 설정
  DATABASE_URL은 dbserver를 데이터베이스 호스트 이름, microblog를 데이터베이스 이름과 사용자, MySQL을 시작할 때 선택한 비밀번호를 사용
- boot.sh에 재시도 루프를 추가

__boot.sh__
```text
#!/bin/bash
source venv/bin/activate
while true; do
    flask db upgrade
    if [[ "$?" == "0" ]]; then
        break
    fi
    echo Upgrade command failed, retrying in 5 secs...
    sleep 5
done
flask translate compile
exec gunicorn -b :5000 --access-logfile - --error-logfile - microblog:app
```

### Adding a Elasticsearch Container
- 단일 노드 옵션을 사용하고 오픈 소스 엔진만 있는 "oss" 이미지를 사용

```shell
$ docker run --name elasticsearch -d -p 9200:9200 -p 9300:9300 --rm \
    -e "discovery.type=single-node" \
    docker.elastic.co/elasticsearch/elasticsearch-oss:7.10.2
```

- 2개의 -p 옵션
  해당 컨테이너가 하나가 아닌 두개의 포트에서 수신 대기할 것임을 의미
- 컨테이너 이미지를 참조하는데 사용되는 구문
  로컬에 빌드: name:tag
  MySQL 컨테이너 account/name:tag
  Elasticsearch 이미지 registry/account/name:tag
- Elasticsearch 서비스와 Microblog 컨테이너 연결

```shell
$ docker logs microblog
```

### The Docker Container Registry
- 3개의 컨테이너를 사용하여 전체 애플리케이션을 도커에서 실행

```shell
$ docker tag microblog:latest <your-docker-registry-account>/microblog:latest
```

- 도커 레지스트리에 이미지를 게시하려면 docker push 명령어를 실행

```shell
$ docker push <your-docker-registry-account>/microblog:latest
```


### Deployment of Containerized Applications
- 컨테이너를 로컬에서 테스트하면 도커지원을 제공하는 모든 플랫폼으로 컨테이너를 가져올 수 있음
- YAML 형식의 간단한 텍스트 파일로 높은 수준의 자동화 및 편의성을 제공