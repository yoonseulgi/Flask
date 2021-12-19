# 21장. User Notifications
- 페이지 새로고침 없이 탐색 모음에 나타나는 사용자 알림과 개인 메시지 기능 추가
- 즉, 사용자에게 경과 및 알림을 표시하는 기능

### Private Messages
- 사용자 프로필 페이지를 방문하면 해당 사용자에게 비공개 메시지를 보낼 수 있는 링크 존재
- 해당 링크를 클릭하면 비공개 메시지를 받을 수 있는 페이지로 이동


#### Database Support for Private Messages
- 첫 번째 작업. 개인 메시지를 지원하도록 데이터베이스 확장
- 메시지 모델 클래스는 수신자와 발신자를 가짐

```python
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Message {}>'.format(self.body)
```

- 사용자에게 메시지 기능 지원

```python
class User(UserMixin, db.Model):
    # ...
    messages_sent = db.relationship('Message',
                                    foreign_keys='Message.sender_id',
                                    backref='author', lazy='dynamic')
    messages_received = db.relationship('Message',
                                        foreign_keys='Message.recipient_id',
                                        backref='recipient', lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime)

    # ...

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(
            Message.timestamp > last_read_time).count()
```

- author과 recipient 역방향 관계
- last_message_Read_time 함수는 다음과 같은 곳에 사용
  사용자가 메시지 페이지를 마지막으로 방문한 시간을 표시
  읽지 않은 메시지 확인
  최신 타임스탬프로 사용
  
  
### Sending a Private Message
- 메시지 수락을 위한 코드

```python
class MessageForm(FlaskForm):
    message = TextAreaField(_l('Message'), validators=[
        DataRequired(), Length(min=0, max=140)])
    submit = SubmitField(_l('Submit'))
```

- 메시지 수락 form을 html 템플릿을 사용해서 웹 페이지로 렌더링

```html
{% extends "base.html" %}
{% import 'bootstrap/wtf.html' as wtf %}

{% block app_content %}
    <h1>{{ _('Send Message to %(recipient)s', recipient=recipient) }}</h1>
    <div class="row">
        <div class="col-md-4">
            {{ wtf.quick_form(form) }}
        </div>
    </div>
{% endblock %}
```


- __routes.py__ 에 __send_message()__ 함수를 추가함으로 실제로 전송할 수 있도록 구현

``` python
@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        db.session.commit()
        flash(_('Your message has been sent.'))
        return redirect(url_for('main.user', username=recipient))
    return render_template('send_message.html', title=_('Send Message'),
                           form=form, recipient=recipient)
```

- 메시지 전송 링크는 사용자 프로필 페이지에 있음. 
- 사용자 프로필과 메시지 전송 링크 연결

```html
{% if user != current_user %}
<p>
    <a href="{{ url_for('main.send_message',
                        recipient=user.username) }}">
        {{ _('Send private message') }}
    </a>
</p>
{% endif %}
```


### Viewing Private Messages
- 사용자가 메시지를 볼 수 있는 기능
- __routes.py__ 에 __messages()__ 함수 추가

```python
@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)
```

- __last_message_read_time__ 로 현재 시간으로 페이지를 업데이트하고, 사용자가 현재까지 메시지를 모두 읽음으로 표시
- __messages.html__ 을 작성하여 메시지 페이지 만들기

- 사용자에게 메시지 보기 기능에 접근 구너한을 부여하기 위해 __base.html__ 에 정의

```html
    {% if current_user.is_anonymous %}
    ...
    {% else %}
    <li>
        <a href="{{ url_for('main.messages') }}">
            {{ _('Messages') }}
        </a>
    </li>
    ...
    {% endif %}
```


### Static Message Notification Badge
- 사용자에게 메시지가 왔음을 알려주는 기능
- __base.html__ 에 아래와 같은 코드를 정의함으로 해당 페이지와 렌더링

```html
    <li>
        <a href="{{ url_for('main.messages') }}">
            {{ _('Messages') }}
            {% set new_messages = current_user.new_messages() %}
            {% if new_messages %}
            <span class="badge">{{ new_messages }}</span>
            {% endif %}
        </a>
    </li>
```

### Dynamic Message Notification Badge
- 정적 메시지 알림은 페이지가 새롭게 로드될 때마다 배지가 표시되는 단점이 존재
- 위와 같은 문제는 사용자가 해당 페이지에 오래 머물면 새로운 메시지가 표시되지 않는 문제가 발생
- 동적 메시지 알림 기능으로 사용자가 새롭게 페이지를 로드하지 않더라도 새로운 메시지를 표시
- __badge__ 가 페이지에 렌더링되어 메시지를 동적으로 알림
- __base.html__ 에 배지를 위한 코드 추가
- visible 속성을 사용해 배지를 항상 보이게 하거나 보이지 않게 할 수 있음
- 해당 배지는 메시지가 0일 때 보이지 않도록 설정

```html
<li>
    <a href="{{ url_for('main.messages') }}">
        {{ _('Messages') }}
        {% set new_messages = current_user.new_messages() %}
        <span id="message_count" class="badge"
              style="visibility: {% if new_messages %}visible
                                 {% else %}hidden {% endif %};">
            {{ new_messages }}
        </span>
    </a>
</li>
```

- 배지의 숫자를 표시하는 코드

```html
{% block scripts %}
    <script>
        // ...
        function set_message_count(n) {
            $('#message_count').text(n);
            $('#message_count').css('visibility', n ? 'visible' : 'hidden');
        }
    </script>
{% endblock %}
```

### Delivering Notifications to Clients
- 클라이언트 측에서 사용자가 읽지 않은 메시지를 주기적으로 업데이트하는 메커니즘 추가
- 업데이트가 발생하면 __set_message_count()__ 함수를 통해 사용자에게 업데이트를 알리는 함수 호출
- 서버가 업데이트 발생을 클라이언트에게 전달하는데 2가지 방법 존재
  1. 클라이언트가 비동기식 요청을 보내 주기적으로 서버에 업데이트를 요청
     클라이언트는 읽지 않은 메시지 수를 나타내는 배지와 페이지 요소를 업데이트하는데 사용
     장점) 구현이 간단
  2. 서버가 데이터를 클라이언트에 자유롭게 push할 수 있도록 클라이언트와 서버 사이를 연결
     새로운 메시지 업데이트뿐만 아니라 다른 유형의 이벤트 변화도 지원할 수 있음
     프로토콜 수준에서 수정이 필요함(websocket 지원이 필요)
     장점) 서비스를 지연없이 지원 가능
     단점) 서버가 모든 클라이언트와 영구적인 연결을 유지해야 함
     
- 해당 챕터에서는 클라이언트 업데이트 목록을 함께 호출하는 콜백함수 
- 사용자 모델과 함께 모든 사용자에 대한 알림을 추적하는 모델 추가

```python
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))
```
- 페이로드 변수는 알림의 유형마다 값이 달라짐(리스트, 디셔너리, 스트링 등)


- 플라스크 쉘에서 자동으로 가져오도록 하기 위해 __microblog.py__ 에 __Message__ , __Notification__ 모델을 추가


```python
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 'Message': Message,
            'Notification': Notification}
```

- __User class__ 에 __add_notification()__ 함수를 추가하여 도움 기능 추가

```python
    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n
```

- 사용자 알림을 데이터베이스에 추가할 뿐만 아니라 동일한 이름의 알림이 있으면 최신 알림으로 교체함
- 읽지 않은 메시지 수가 변경되는 모든 위치에서 __add_notification()__ 호출
  두 곳에서 발생
  1. send_message()
  
  ```python
         def send_message(recipient):
            # ...
            if form.validate_on_submit():
                # ...
                user.add_notification('unread_message_count', user.new_messages())
                db.session.commit()
                # ...
            # ...
  ```
  
  2. 사용자가 메시지 페이지로 이동할 때
  
  ```python
          @bp.route('/messages')
          @login_required
          def messages():
              current_user.last_message_read_time = datetime.utcnow()
              current_user.add_notification('unread_message_count', 0)
              db.session.commit()
              # ...
  ```
  
- 위의 기능들이 실제로 구동될 수 있도록 __base.html__ 에 렌더링 
- 사용자가 로그인 했을 때만 메시지 기능이 구동되도록 메시지 기능 코드를 템플릿의 조건부로 추가

```html
{% if current_user.is_authenticated %}
$(function() {
    var since = 0;
    setInterval(function() {
        $.ajax('{{ url_for('main.notifications') }}?since=' + since).done(
            function(notifications) {
                for (var i = 0; i < notifications.length; i++) {
                    if (notifications[i].name == 'unread_message_count')
                        set_message_count(notifications[i].data);
                    since = notifications[i].timestamp;
                }
            }
        );
    }, 10000);
});
{% endif %}
```
