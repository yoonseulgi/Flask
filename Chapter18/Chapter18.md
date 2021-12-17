# 18장. Deployment on Heroku
- 실제 사용자가 사용할 수 있도록 배포
- 해당 chapter에서는 Heroku 환경만 고려
    
  
### Hosting on Heroku
- __Heroku__ : Java, Node.js, python 등 여러 언어를 지원하는 __Paas__
- git으로 배포되기 때문에 git repository에 애플리케이션이 저장되어 있어야 함


### Creating a Heroku account
- Heroku에 배포하기 전에 계정 생성

### Installing the Heroku CLI
- window, Mac OS, Linux 등 다른 운영체제 사용할 수 있는 상호작용할 수 있는 명령어 도구 
- login을 거친 후 heroku 다운로드
```shell
$ heroku login
```

### Setting Up Git
- git 다운로드 받기
- 애플리케이셔이 저장된 git repository와 연동

```shell
$ git clone https://github.com/miguelgrinberg/microblog
$ cd microblog
$ git checkout v0.18
```
- git checkout 명령은 응용 프로그램이 있는 특정 커밋을 선택

### Creating a Heroku Application
- heroku에 새로운 애플리케이션을 등록하기 위해 루트 디렉토리에서 app:create 명령을 사용해 애플리케이션의 이름을 인수로 전달

```shell
$ heroku apps:create flask-microblog
Creating flask-microblog... done
http://flask-microblog.herokuapp.com/ | https://git.heroku.com/flask-microblog.git
```


### The Ephemeral File System
- heroku 플랫폼은 가상화된 플랫폼에서 실행되는 임시 파일이기에 가상 서버를 깨끗한 상태로 다시 설정할 수 있음
- 다음과 같은 3가지 문제 발생
  1. SQLite 데이터베이스 엔진은 디스크 파일에 데이터를 씀
  2. 응용 프로그램에 대한 로그도 파일 시스템에 기록
  3. 컴파일된 언어 번역 저장소는 로컬 파일에 기록
  
  
### Working with a Heroku Postgres Database
- 1번 문제 해결을 위해 다른 데이터베이스엔진인 __postgre__ 사용

```shell
$ heroku addons:add heroku-postgresql:hobby-dev
```

- heroku에서 postgre 데이터베이스를 사용하기 위해 postgres:// -> postgresql:// 바뀐 URL 사용
- Config 클래스에서 문자열 교체 작업 수행

```python
class Config(object):
    # ...
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace(
        'postgres://', 'postgresql://') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    # ...
```

### Logging to stdout
- 2번 문제 해결을 위한 방법
- 응용 프로그램이 출력하는 모든 내용은 heroku logs 명령을 사용할 때 저장 및 반환 됨
- 옵션을 사용하여 파일에 저장할지, stdout에 저장할지 선택 가능


### Compiled Translations
- 3번 문제 해결을 위한 방법
- heroku에 제공된 시작 명령에 flask 번역 컴파일 명령을 포함하여 서버가 다시 시작될 때마다 해당 파일이 다시 컴파일 되도록 하는 것

### Elasticsearch Hosting
- elasticsearch는 heroku에서 제공하지 않음
- __addons__ 을 사용하여 

```shell
$ heroku addons:create searchbox:starter
```

- elasticsearch 서비스를 배포 및 URL 연결

```shell
$ heroku config:get SEARCHBOX_URL
<your-elasticsearch-url>
$ heroku config:set ELASTICSEARCH_URL=<your-elasticsearch-url>
heroku config:set SECRET_KEY=<your-secret_key>
```

### Updates to Requirements
- heroku에서 python 애플리케이션용으로 권장하는 서버인 gunicorn 사용

### The Procfile
- heroku에게 응용 프로그램을 실행하는 방법을 알려주어야 함
- 응용 프로그램의 루트 디렉토리에 __procfile__ 이라는 파일 사용

```text
Procfile:
- 응용 프로그램의 루트 디렉토리에 __procfile__ 이라는 파일 사용
Procfile:
```

- heroku config에 FLASK_APP=microblog.py 세팅하기

```shell
$ heroku config:set FLASK_APP=microblog.py
Setting FLASK_APP and restarting flask-microblog... done, v6
FLASK_APP: microblog.py
```

### Deploying the Application
- 배포 실행
1. heroku 서버에 애플리케이션 업로드

```shell
$ git checkout -b deploy
$ git push heroku deploy:main
```

- 로컬 저장소에서 작업한 경우 commit 및 push 수행

```shell
$ git commit -a -m "heroku deployment changes"
$ git push heroku main  # you may need to use "master" instead of "main"
```

### Deploying Application Updates
- 새로운 코드가 생성되면 git push 명령을 사용해서 git에 업로드하면 됨