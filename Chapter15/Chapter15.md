# 15장. A Better Application Structure
- microblog를 유지보수하기 쉽도록 함

### Current Limitations
- 현재 존재하는 2가지 문제
  1. 모든 기능이 모듈 및 템플릿을 통해 분산되어 있음
     기능형 모듈, 웹 양식용 모듈, 오류용 모듈, 이메일용 모듈, HTML 템플릿용 모듈 등으로 분산되어 있음
  2. Flask 응용 프로그램 인스턴스는 app/__init__.py에서 전역변수로 생성되어야 사용 가능
   이는 테스트 시나리오가 복잡해질수록 문제가 됨
   전역변수로 선언되기 때문에 나중에 수행되는 테스트에 영향을 줌

- 위와 같은 문제를 해결하기 위해 리팩토링할 것

### Blueprints
- __Blueprints__ : 애플리케이션의 하위 집합을 나타내는 논리적인 구조
- 코드를 구성하는데 도움을 주는 애플리케이션 기능이 저장되는 임시 저장소

#### Error Handling Blueprint
- 오류 처리를 위한 기능을 캡슐화하는 blueprints

```text
app/
    errors/                             <-- blueprint package
        __init__.py                     <-- blueprint creation
        handlers.py                     <-- error handlers
    templates/
        errors/                         <-- error templates
            404.html
            500.html
    __init__.py                         <-- blueprint registration
```

- 두 개의 오류 템플릿을 분리
- 애플리케이션 인스턴수가 생성되면 app/errors/__init__.py 모듈에서 blueprint 생성 후에 app/__init__.py에 blueprint 등록
- blueprint 생성 코드

```python
from flask import Blueprint

bp = Blueprint('errors', __name__)

from app.errors import handlers
```
- blueprint class는 blueprint의 이름, 인수를 가지지만 현 코드에서는 이름만 사용
- blueprint 객체가 생성된 후에 __handlers.py__ 모듈을 import 하여 blueprint에 등록
- import handlers 를 마지막에 둠으로 사이클을 피함
- app/__init__.py에 아래와 같은 코드를 삽입함으로 blueprint 등록

```python
from app.errors import bp as errors_bp
app.register_blueprint(errors_bp)
```

#### Authentication Blueprint
- 애플리케이션 인증 기능 리팩토링 

```text
app/
    auth/                               <-- blueprint package
        __init__.py                     <-- blueprint creation
        email.py                        <-- authentication emails
        forms.py                        <-- authentication forms
        routes.py                       <-- authentication routes
    templates/
        auth/                           <-- blueprint templates
            login.html
            register.html
            reset_password_request.html
            reset_password.html
    __init__.py                         <-- blueprint registration
```

- blueprint의 루트를 정의할 때, __@app.route__ 데코레이션 대신 __@bp.route__ 를 사용
- blueprint의 루트를 정의할 때, blueprint의 이름을 반드시 인수로 사용
  ex) url_for('auth.login')
- 아래 코드와 같이 삽입함으로 __auth blueprint__ 등록

```python
from app.auth import bp as auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')
```

- blueprint의 경로와 다른 경로 분리


#### Main Application Blueprint
- 애플리케이션의 핵심 로직이 포함
- 핵심 기능이기 때문에 템플릿을 같은 위치에 둠


### The Application Factory Pattern
- 전역변수로 애플리케이션을 유지해야 하는 경우를 줄였기 때문에 애플리케이션 인스턴스를 생성하는 함수를 추가 

```python
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app)

    # ... no changes to blueprint registration

    if not app.debug and not app.testing:
        # ... no changes to logging setup

    return app
```

- 2단계 과정이 필요
  1. 전역 범위에서 생성되지만, 인수는 전달되지 않음
     응용 프로그램에 연결되지 않은 인스턴스가 생성됨
  2. 응용 프로그램이 init_app()될 때, 애플리케이션 팩토리 함수가 호출되어 인수와 애플리케이션 인스턴스가 바인딩
     애플리케이션 팩토리 함수는 __microblog.py__ 에서 호출
     
- __app/email.py__ 코드를 수정하여 애플리케이션 인스턴스를 다른 스레드로 전달

```python
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email,
           args=(current_app._get_current_object(), msg)).start()
```     

- __app/cli.py__ 코드를 수정하여 사용자가 정의하는 명령을 등록하는 함수에 애플리케이션 인수 전달

```python
def register(app):
    # ...    
```

### Unit Testing Improvements
- 단위 테스트를 수행할 때 데이터베이스와 개발 리소스를 방해하지 않는 애플리케이션 구성
- 애플리케이션이 추가되기 전 테스트 구성을 지정할 수 있는 기회 부여
- __create_app()__ 함수를 __config.py__ 에 정의함으로 애플리케이션을 인수로 전달받아도 인스턴스 생성

```python
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
```

- __setUp()__ , __tearDown()__ 함수 목적에 맞게 재정의

```python
class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
```

- 반드시 아래와 같은 문장을 추가해야 오류없이 애플리케이션 인스턴스 생성 가능

``` shell
>>> app = create_app()
>>> app.app_context().push()
```

### Environment Variables
- 서버를 구동하기 전에 여러 환경변수를 설정해야 했음
- secret key, email server information, database URL, Microsoft Translator API key이 포함되어 있음
- 새 터미널을 열 때마다 환경변수를 설정해야 함
- __.env__ 파일에 환경변수를 저장함으로 해당 문제 해결
- __config.py__ 파일에 아래와 같은 코드를 추가함으로 __.env__ 파일 가져옴

```python
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))
```

- __.env__ 파일은 아래와 같이 정의

```text
SECRET_KEY=a-really-long-and-unique-key-that-nobody-knows
MAIL_SERVER=localhost
MAIL_PORT=25
MS_TRANSLATOR_KEY=<your-translator-key-here>
```

### Requirements File
- 해당 응용프로그램을 수행할 때 필요한 패키지를 __requirements.txt__ 에 정의
- 아래 코드를 통해 가상환경에 설치된 패키지를 __requirements.txt__ 에 작성

```shell
$ pip freeze > requirements.txt
```

- 아래 코드를 통해 __requirements.txt__ 에 정의된 패키지를 install

```shell
$ pip install -r requirements.txt
```