# 12장. Dates and Times

### Timezone Hell
- python으로 웹 브라우저에서 사용자에게 날짜와 시간을 렌더링하는 것은 비효율적
- python은 사람마다 시간의 결과를 다르게 반환

```python
>>> from datetime import datetime
>>> str(datetime.now())
'2021-06-28 16:06:30.439388'
>>> str(datetime.utcnow())
'2021-06-28 23:06:51.406499'
```

- 서버는 위치에 관계없이 일관되고 독립적인 시간을 관리
- UTC 시간 대는 게시물이 작성된 시간을 파악하기 어려움
- 즉, 사용자의 편의성을 떨어뜨림


### Timezone Conversions
- 사용자의 시간대를 알고, 표준 날짜 및 시간을 Javascript API를 통해 노출
- 기존 방식: 사용자가 응용 프로그램에 처음 로그온할 때, 브라우저가 서버에게 로그인 시간을 보내기
  서버가 시간대를 알면 사용자 세션에 시간을 유지하거나 데이터베이스에 저장하여 템플릿과 렌더링

- 새로운 방식: 서버에서 변경하지 않고, JavaScript를 사용해 client에게 현지 시간으로 변환하여 제공


### Introducing Moment.js and Flask-Moment
- moment.js는 날짜 및 시간을 렌더링을 편리하게 해주는 Javascript 라이브러리
- moment.js를 응용 프로그램에서 쉽게 통합할 수 있도록 해주는 Flask-Moment 만들기
- moment.js를 항상 사용할 수 있도록 기본 템플릿에 추가
  <script></script> 태그 사용

  ```html
  {% block scripts %}
    {{ super() }}
    {{ moment.include_moment() }}
  {% endblock %}
  ```
  
### Using Moment.js
- 브라우저에서 __moment__ class 사용하기
- __moment__ class는 ISO 8601 포맷을 사용
- ISO 8601 형식: {{ year }}-{{ month }}-{{ day }}T{{ hour }}:{{ minute }}:{{ second }}{{ timezone }}

```python
t = moment('2021-06-28T21:45:23Z')
```

- Flask-Moment를 사용해 타임스탬프 렌더링

```html
{% if user.last_seen %}
<p>Last seen on: {{ moment(user.last_seen).format('LLL') }}</p>
{% endif %}
```

- JavaScript 라이브러리와 유사한 구문을 사용
- 차이점은 moment() 인수가 ISO 8601 문자열이 아니라 python datetime 객체라는 것
- Flask-Moment는 각 게시물 앞에 사용자의 이름을 첨부하는 것을 가능하게 해줌 

```html
<a href="{{ url_for('user', username=post.author.username) }}">
    {{ post.author.username }}
</a>
said {{ moment(post.timestamp).fromNow() }}:
<br>
{{ post.body }}
```