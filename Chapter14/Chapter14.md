# 14장. Ajax
- 실시간 번역 기능을 microblog에도 추가 

### Server-side vs. Client-side
- 전통적인 방법은 클라이언트가 서버에게 HTTP 요청
- 이러한 방법은 서버에서 모든 작업을 수행하고, 클라이언트에서 사용자에게 입력 및 출력을 제공
- 다른 방법으로는 클라이언트가 서버에게 요청을 보내고 웹 페이지로 응답받는 것은 유사하지만, 모든 페이지 데이터를 HTML이 아닌 Javascript도 구성
- 클라이언트가 페이지를 수신하면 서버에 거의 접속하지 않고 자체적으로 작업 수행 가능
- 이러한 유형의 애플리케이션을 SPA(Single Page Application)이라 함

### Live Translation Workflow
- 작성자의 언어로 작성된 게시글을 독자의 언어로 자동 번역해주는 기능 추가
- __Ajax__ 서비스로 구현
- 기존 방식은 기존 페이지가 클라이언트가 번역을 요청한 페이지로 교체
- 본 기술은 여러 페이지를 가지고 있음
- 자동 번역 기능을 추가하려면 몇 단계가 필요
  1. 번역할 텍스트의 언어를 식별할 방법
  2. 다른 언어로 작성된 게시글만 번역(즉, 사용자 선호 언어)
  3. 사용자가 링크를 클릭하면 Ajax 요청을 보낸 후 번역 API에 연결
  4. 서버가 번역된 텍스트 결과를 클라이언트에게 전송하면 해당 결과가 클라이언트 페이지에 동적으로 삽입
  
### Language Identification
- 언어 식별하기
- 파이썬에서 언어를 감지할 수 있는 __langdetect__ 패키지 지원
- 블로그 게시물을 이 패키지에 제공 후 언어 결정
- 데이터베이스의 내용이 변경될 때마다 migration 과정이 필요

```shell
flask db migrate -m "add language to posts"
flask db upgrade
```

- __detect()__ 함수를 통해 언어를 식별

```python
    if form.validate_on_submit():
        try:
            language = detect(form.post.data)
        except LangDetectException:
            language = ''
        post = Post(body=form.post.data, author=current_user,
                    language=language)
```

### Displaying a "Translate" Link
- 번역 링크 추가하기
- 블로그의 모든 페이지에 표시되도록 ___post.html__ 에 코드 추가

```html
    {% if post.language and post.language != g.locale %}
    <br><br>
    <a href="#">{{ _('Translate') }}</a>
    {% endif %}
```


### Using a Third-Party Translation Service
- __Microsoft Translator API__ 사용
- Azure 계정이 필요
- key 받기  
- __config.py__ 파일에 MS_TRANSLATOR_KEY를 추가

```python 
MS_TRANSLATOR_KEY = os.environ.get('MS_TRANSLATOR_KEY')
```
- __Microsoft Translator API__ 는 HTTP 요청을 받는 웹 서비스
- requests 패키지를 install하여 HTTP 요청을 받을 수 있음


### Ajax From The Server
- 사용자가 게시물 아래에 표시되는 번역 링크를 클릭하면 서버에 HTTP 요청이 발생
- 서버가 해당 요청을 처리하는 과정
- Ajax는 비동기 요청으로 XML or JSON 형식의 데이터만 반환
- Microsoft Translator API는 번역된 텍스트를 JSON 형태로 반환

```python
@app.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({'text': translate(request.form['text'],
                                      request.form['source_language'],
                                      request.form['dest_language'])})
```


### Ajax From The Client
- 브라우저 Javascript로 작업
- Javascript가 서버에서 실행되는 번역 함수에 보내야 하는 세가지 인수 얻기
- 블로그 게시물 본문이 포함된 DOM 내에서 노드를 찾아 내용을 읽어야 함
- DOM 노드를 쉽게 식별하기 위해 고유 ID를 첨부( ___post.html__ 파일에 아래 코드 추가 )

```html
                <span id="post{{ post.id }}">{{ post.body }}</span>
```

- 서버에서 번역된 텍스트를 받으면, 해당 텍스트를 삽입할 장소 선정
- '번역' 링크에 대한 고유 ID 필요( ___post.html__ 파일에 아래 코드 추가 )

```html
                <span id="translation{{ post.id }}">
                    <a href="#">{{ _('Translate') }}</a>
                </span>
```

- __base.html__ 파일에 __translate__ 함수를 추가함으로 서버에 비동기 요청을 전송하고, 서버가 응답하면 번역된 텍스트로 교환

```html
    <script>
        function translate(sourceElem, destElem, sourceLang, destLang) {
            $(destElem).html('<img src="{{ url_for('static', filename='loading.gif') }}">');
            $.post('/translate', {
                text: $(sourceElem).text(),
                source_language: sourceLang,
                dest_language: destLang
            }).done(function(response) {
                $(destElem).text(response['text'])
            }).fail(function() {
                $(destElem).text("{{ _('Error: Could not contact server.') }}");
            });
        }
    </script>
```