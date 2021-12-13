# 10장. Email Support
- 인증 관련 문제를 해결하기 위해 이메일 기능 추가
- 비밀번호 재설정 기능 추가

### Introduction to Flask-Mail
- Flask-Mail이라는 널리 사용되는 확장 라이브러리 존재

```shell
$ pip install flask-mail
```

- 비밀번호 재설정을 위한 보안 토큰 사용 라이브러리

```shell
$ pip install pyjwt
```

- 터미널에 아래와 같은 코드를 실행함으로 메일 기능을 테스트할 수 있음


```shell
$ python -m smtpd -n -c DebuggingServer localhost:8025
$ set MAIL_SERVER=localhost
$ set MAIL_PORT=8025
```

- 실제 이메일 주소를 전송하고 싶다면 실제 이메일 서버를 사용
- 아래와 같이 환경설정해줌으로 Gmail로 메일 전송 가능
- Gmail를 사용하고 싶지 않다면 SendGrid에서 무료 계정 사용 가능

```shell
$ set MAIL_SERVER=smtp.googlemail.com
$ set MAIL_PORT=587
$ set MAIL_USE_TLS=1
$ set MAIL_USERNAME=<your-gmail-username>
$ set MAIL_PASSWORD=<your-gmail-password>
```

### Flask-Mail Usage
- python shell에서 메일 보내기

```python
>>> from flask_mail import Message
>>> from app import mail
>>> msg = Message('test subject', sender=app.config['ADMINS'][0],
... recipients=['your-email@example.com'])
>>> msg.body = 'text body'
>>> msg.html = '<h1>HTML body</h1>'
>>> mail.send(msg)
```

### A Simple Email Framework
- 이메일을 보낼 때 도움을 주는 함수 작성
- Flask-Mail에서 지원하지 않는 참조 및 숨은 참조 등과 같은 기능을 지원

### Requesting a Password Reset
- 비밀번호 재설정 요청 기능
- 사용자가 비밀번호 재설정을 요청할 수 있는 옵션 추가

```html
    <p>
        Forgot Your Password?
        <a href="{{ url_for('reset_password_request') }}">Click to Reset It</a>
    </p>
```

- 사용자가 링크를 클릭하면 비밀번호 재설정을 위한 인증으로 이메일을 요구하는 웹 양식이 나타남

```python
class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')
```

- __routes.py__ 파일에 보기 기능 양식 추가


### Password Reset Tokens
- __send_password_reset_email()__ 메소드 함수를 구현하기 전에 
- 이메일을 통해 사용자에게 비밀번호 재설정 가능한 링크 전송
- 링크를 클릭하면 비밀번호 재설정 페이지로 이동
- 링크는 토큰으로 제공 및 변경 가능한 사용자인지 토큰을 통해 검증
- 토큰 기능으로 JWT(Json Web Token)를 사용
- JWT의 작동 원리

```python
>>> import jwt
>>> token = jwt.encode({'a': 'b'}, 'my-secret', algorithm='HS256')
>>> token
'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhIjoiYiJ9.dvOo58OBDHiuSHD4uW88nfJik_sfUHq1mDi4G0'
>>> jwt.decode(token, 'my-secret', algorithms=['HS256'])
{'a': 'b'}
```

- 토큰을 안전하게 만들려면 암호 서명을 만드는데 사용할 비밀키를 제공
- 비밀번호 재설정에 사용될 토큰 : {'reset_password': user_id, 'exp': token_expiration}

### Sending a Password Reset Email
- __send_password_reset_email()__ 함수는 암호 재설정 이메일을 생성하기 위해 __sned_email()__ 함수에 의존
- Text와 render_template() 함수를 사용해 템플릿을 생성

### Resetting a User Password
- 위의 기능을 통해 사용자가 받은 비밀번호 재설정 링크를 클릭하면 사용자의 비밀번호를 요청하는 기능
- 사용자가 로그인되어 있는지 확인 후 토큰을 통해 사용자가 누구인지 확인
- 토큰이 유효할 경우 새로운 비밀번호를 설정하는 양식을 사용자에게 제공

### Asynchronous Emails
- 이메일을 보내면 애플리케이션 속도가 느려짐(이메일을 보낼 때 발생하는 상호작용 때문)
- 위와 같은 문제를 해결하기 위해 __send_email()__ 함수를 비동기 적으로 작동시킴
- 비동기식 작동이란 함수가 호출될 때 이메일 전송 작업이 백그라운드에서 발생하도록 하여 속도를 향상
- python에선 스레드 및 멀티 프로세스 사용

```python
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)
s

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()
```