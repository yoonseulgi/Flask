# 13장. I18n and L10n 
- __I18n and L10n__ 는 Internationalization과 Localization의 약자

### Introduction to Flask-Babel
- __flask-babel__ 라이브러리를 install하여 번역 기능 사용\
```python
pip install flask-babel
```

- 해당 튜토리얼의 예는 스페인어를 영어로 번역
- __config.py__ 에 환경변수를 추가
- 해당 코드는 언어 코드만 사용하고 있지만, 더 구체적인 번역이 필요하다면 국가 코드를 추가

```python
    LANGUAGES = ['en', 'es']
```

- Babel은 localeselector 데코레이터를 제공
- 데코레이트된 함수는 해당 요청에 사용할 언어 번역을 선택

```python
@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])
```

- __accept_languages__ : 클라이언트가 언어 번역을 요청할 수 있는 인터페이스
  응용 프로그램의 기본으로 설정된 언어를 default 값으로 설정

### Marking Texts to Translate In Python Source Code
- 응용 프로그램은 언어를 제공할 때 text 형태로 제공
- Flask-Babel은 text로 된 파일을 gettext를 사용해 별도의 번역파일로 추출( _() 함수)
- __lazy_gettext()__ 를 사용해 양식 필드와 연결


### Marking Texts to Translate In Templates
- _() 함수는 템플릿 파일에서도 사용 가능
- 아래와 같은 코드를 ___post.html__ 파일에 추가

```html
        {% set user_link %}
            <a href="{{ url_for('user', username=post.author.username) }}">
                {{ post.author.username }}
            </a>
        {% endset %}
        {{ _('%(username)s said %(when)s',
            username=user_link, when=moment(post.timestamp).fromNow()) }}
```

### Extracting Text to Translate
- _() 및 _l()이 있는 응용 프로그램은 pybabel 명령어를 사용해 .pot 파일로 추출
- .pot 파일은 이식 가능한 개체 템플릿
- 추출 프로세스에는 번역 가능한 텍스트를 위해 작은 구성 파일이 필요
- __babel.cfg__ 파일 작성
- text 파일을 .pot 파일로 추출하는 명령어

```shell
pybabel extract -F babel.cfg -k _l -o messages.pot .
```

### Generating a Language Catalog
- 기본 언어 외에 번역을 지원할 언어 설정
- 해당 튜토리얼에선 스페인어 사용

```shell
pybabel init -i messages.pot -d app/translations -l es
```

- -l 옵션에 지정된 언어로 -d 옵션으로 지정된 위치에 message.pot 파일을 저장
- __messages.po__ 파일에 일부

```python
#: app/email.py:21
msgid "[Microblog] Reset Your Password"
msgstr "[Microblog] Nueva Contraseña"
```

- 번역을 컴파일하기 위해 아래와 같은 명령어를 사용

```shell
pybabel compile -d app/translations
```

- compile 명령어 실행 결과 __messages.mo__ 파일이 생성
- __messages.mo__ 을 응용 프로그램에서 사용하고 싶다면 브라우저의 설정을 변경하거나 __localeselector__ 함수
- __localeselector__ 함수는 모든 텍스트를 지정된 언어로 번역하여 표시

### Updating the Translations
- _() or _l() 함수가 일부 텍스트를 놓친 경우 발생 가능
- 아래와 같은 명령어를 실행하여 해당 문제 해결
- 새로운 __messages.pot__ 파일 생성

```shell
pybabel extract -F babel.cfg -k _l -o messages.pot .
pybabel update -i messages.pot -d app/translations
```

### Translating Dates and Times
- __moment.js__ 를 사용해 날짜와 시간 맞게 적절히 구성
- 지원하는 언어를 늘리기 싶다면 언어의 목록을 추가하면 됨
- 추가한 목록을 __get_locale()__ 함수에 추가

```python
@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])
```

### Marking Texts to Translate In Python Source Code
- 응용 프로그램은 텍스트를 지원하는 모든 언어로 번역해야 함
- 즉, text -> Flask-Babel이 scan -> gettext 사용 -> 별도의 번역 파일 추출

### Command-Line Enhancements
- 응용 프로그램에서 pybabel 명령을 실행하는 간단한 명령 만들기
  __flask translate init LANG__ : 새로운 언어 추가
  __flask translate update__ : 모든 언어 repository를 업데이트
  __flask translate compile__ : 모든 언어 repository를 컴파일
- Flask는 click 패키지에 의존
- __app.cli.group()__ 데코레이터를 통해 __tanslate()__ 함수 등록

```python
from app import app

@app.cli.group()
def translate():
    """Translation and localization commands."""
    pass
```

- flask translate --help 문장을 실행하면 정의한 3가지 옵션이 출력

```shell
Commands:
  compile  Compile all languages.
  init     Initialize a new language.
  update   Update all languages.
```

