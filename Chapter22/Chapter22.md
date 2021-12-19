# 22장.  Background Jobs 
- 응용 프로그램의 일부로 실행해야 하는 복잡한 프로세스 구현
- 10장에서 구현한 이메일 기능은 사용자가 이메일을 전송할 때 3~4초가 걸림
- 위와 같은 문제를 해결하기 위해 스레드를 사용했지만 프로세스가 복잡하면 무용지물
- 사용자가 데이터를 요청할 수 있는 내보내기 기능을 구현

### Introduction to Task Queues
- task queue는 작업 프로세스가 수행하는 task 실행 요청을 편리하게 해결
- 작업 프로세스는 응용 프로그램과 독립적으로 실행됨
- 작업 프로세스와 응용 프로그램의 통신은 메시지 queue를 통해 상호작용
- python는 task queue로 __celery__ , __Redis queue(RQ)__ 를  가장 많이 사용
- 해당 챕터에서는 __RQ__ 를 사용


### Using RQ
- RQ는 파이썬 패키지
- 응용 프로그램과 RQ workers은 Redis message queue를 통해 통신
- RQ는 windows의 기본 python 인터프리터에서 실행되지 않음(Unix 에물레이션에서만 RQ를 사용할 수 있음)


### Creating a Task
- RQ를 사용해서 task 생성

```python
import time

def example(seconds):
    print('Starting task')
    for i in range(seconds):
        print(i)
        time.sleep(1)
    print('Task completed')
```

### Running the RQ Worker
- task이 생성되었기에 사용자가 task를 시작할 수 있음
- task를 병렬로 실행할 수 있음

```shell
$ rq worker microblog-tasks
```

### Executing Tasks
- 사용자가 요청한 task 실행

```shell
>>> from redis import Redis
>>> import rq
>>> queue = rq.Queue('microblog-tasks', connection=Redis.from_url('redis://'))
>>> job = queue.enqueue('app.tasks.example', 23)
>>> job.get_id()
'c651de7f-21a8-4068-afd5-8b982a6f6d32'
```

- __Queue__ : 애플리케이션에서 보낸 task를 나타냄
- __enqueue()__ : queue에 task를 추가
- __get_id()__ : 작업에 할당된 고유 식별자 받기 


### Reporting Task Progress
- 사용자에게 task 진행 상황을 보고

```python
import time
from rq import get_current_job

def example(seconds):
    job = get_current_job()
    print('Starting task')
    for i in range(seconds):
        job.meta['progress'] = 100.0 * i / seconds
        job.save_meta()
        print(i)
        time.sleep(1)
    job.meta['progress'] = 100
    job.save_meta()
    print('Task completed')
```

- __get_current_job__ 을 사용하여 task의 현재 상태를 받아옴
- __meta__ 속성은 애플리케이션 상호작용한 데이터가 저장되는 딕셔너리 타입
- __progress__ task가 어느정도 진행됐는지 %로 표현


### Database Representation of Tasks
- 애플리케이션이 사용자가 실행 중인 작업을 추적하기 위해 일부 정보를 데이터베이스 테이블로 유지


```python
class Task(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    complete = db.Column(db.Boolean, default=False)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100
```

- 해당 모델에서 받아오는 ID는 RQ에서 사용하는 ID이기 때문에 문자열
- __get_rq_job()__ 메소드는 task ID에서 RQ 인스턴스를 로드하는 도우미 메소드
- __get_progress()__ 메소드는 get_rq_job() 기반으로 task의 진행률을 반환

- 위와 같은 기능을 쉘에서도 사용할 수 있도록 __microblog.py__ 파일에 코드 추가

```python
from app import create_app, db, cli
from app.models import User, Post, Message, Notification, Task

app = create_app()
cli.register(app)

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 'Message': Message,
            'Notification': Notification, 'Task': Task}
```

### Integrating RQ with the Flask Application
- Redis 서비스 연결 URL 추가

```python
class Config(object):
    # ...
    Integrating RQ with the Flask Application
```

- 애플리케이션 팩토리 기능에 Redis 및 RQ 초기화 코드 추가

```python
from redis import Redis
import rq

# ...

def create_app(config_class=Config):
    # ...
    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue('microblog-tasks', connection=app.redis)

    # ...
```

- __app.task_queue__ 작업이 제출된 큐가 될 것
- 응용 프로그램에 대기열을 연결하면 응용 프로그램의 어느 곳에서나 __current_app.task_queue__ 액세스하는데 사용할 수 있음.
- USer 모델에서 도우미 메소드 추가

```python
class User(UserMixin, db.Model):
    # ...

    def launch_task(self, name, description, *args, **kwargs):
        rq_job = current_app.task_queue.enqueue('app.tasks.' + name, self.id,
                                                *args, **kwargs)
        task = Task(id=rq_job.get_id(), name=name, description=description,
                    user=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return Task.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return Task.query.filter_by(name=name, user=self,
                                    complete=False).first()
```

- __launch_task()__ 메소드는 task를 데이터베이스에 추가하는 것과 RQ queue에 제출하는 기능
  새 작업 개체를 추가하지만 commit은 하지 않음
- __get_tasks_in_progress()__ 메소드는 사용자가 처리하지 못한 전체 기능 목록을 반환
- __set_task_in_progress()__ 메소드는 특정 task에 대한 정보를 반환


### Sending Emails from the RQ Task
- 11장에서 구현한 이메일 기능 확장
  1. 첨부파일 기능 추가
  2. 기존 비동기식 이메일 보내기에서 동기식, 비동기식 모두 지원
  
  
- 1번 기능을 추가하기 위해 기존 __send_email()__ 메소드에 __syn__ 인수 추가 

```python
def send_email(subject, sender, recipients, text_body, html_body,
               attachments=None, sync=False):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    if attachments:
        for attachment in attachments:
            msg.attach(*attachment)
    if sync:
        mail.send(msg)
    else:
        Thread(target=send_async_email,
            args=(current_app._get_current_object(), msg)).start()
```

- __attach()__ 메서드는 첨부파일을 정의하는데 3가지 인수를 사용
  파일이름 : 수신자에게 표시될 이름
  미디어 타입 : 이메일 수신자가 첨부파일을 적절하게 렌더링할 수 있도록 파일의 유형을 정의
  실제 파일 데이터 : 첨부파일에 포함된 문자열 or 바이트 시퀀스
  
### Task Helpers
- task가 데이터베이스와 이메일 전송 기능에 접근할 수 있도록 함
- 별도의 프로세스로 실행
- flask 애플리케이션 인스턴스와 애플리케이션 컨텍스트를 추가

__app/tasks.py__ : 
```python
from app import create_app

app = create_app()
app.app_context().push()
```

- RQ 작업자가 가져올 유일한 모듈
- 루트 디렉토리에서 microblog.py 모듈이 애플리케이션을 생성하지만 RQ 작업자는 이에 대해 알지 못하므로 자체 애플리케이션 인스턴스를 생성해야 함

- 사용자가 페이지를 새로 고칠 필요 없이 완료율을 동적으로 업데이트하는 알림 기능 추가
- __tasks.py__ 에 _set_task_progress() 메소드 추가

```python
def _set_task_progress(progress):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        task.user.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': progress})
        if progress >= 100:
            task.complete = True
        db.session.commit()
```

### Implementing the Export Task
- 게시물의 일반적인 구조 내보내기
- __tasks.py__ 파일에 아래와 같은 함수 추가
- try/except 블록으로 래핑하는 이유는 해당 프로젝트에서 정의한 예외를 직접 처리
- 해당 기능은 RQ로 제어되기 때문에 별도의 프로세스에서 실행
- 오류가 발생할 때마다 sys.exc_info()에서 제공하는 오루 정보를 기록
- try구문은 실제 내보내기 기능을 구현하는 코드가 삽입

```python
def export_posts(user_id):
    try:
        # read user posts from database
        user = User.query.get(user_id)
        _set_task_progress(0)
        data = []
        i = 0
        total_posts = user.posts.count()
        for post in user.posts.order_by(Post.timestamp.asc()):
            data.append({'body': post.body,
                         'timestamp': post.timestamp.isoformat() + 'Z'})
            time.sleep(5)
            i += 1
            _set_task_progress(100 * i // total_posts)
            
        # send email with data to user
        send_email('[Microblog] Your blog posts',
                sender=app.config['ADMINS'][0], recipients=[user.email],
                text_body=render_template('email/export_posts.txt', user=user),
                html_body=render_template('email/export_posts.html', user=user),
                attachments=[('posts.json', 'application/json',
                              json.dumps({'posts': data}, indent=4))],
                sync=True)
        
    except:
        # handle unexpected errors
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
    finally:
        # handle clean up
        _set_task_progress(100)
```

- 이메일 템플릿에 내보내기

```html
<p>Dear {{ user.username }},</p>
<p>Please find attached the archive of your posts that you requested.</p>
<p>Sincerely,</p>
<p>The Microblog Team</p>
```

### Export Functionality in the Application
- 내보내기 기능을 애플리케이션에 연결
- __routes.py__ 에 게시물 경로 내보내기와 기능을 볼 수 있는 메소드 추가

```python
@bp.route('/export_posts')
@login_required
def export_posts():
    if current_user.get_task_in_progress('export_posts'):
        flash(_('An export task is currently in progress'))
    else:
        current_user.launch_task('export_posts', _('Exporting posts...'))
        db.session.commit()
    return redirect(url_for('main.user', username=current_user.username))
```

- 사용자가 내보내기를 요청하기 위해 접근할 수 있는 링크를 제공
- 해당 링크는 사용자가 이미 내보내기를 실행하고 있다면 노출되지 않음

```html
    <p>
        <a href="{{ url_for('main.edit_profile') }}">
            {{ _('Edit your profile') }}
        </a>
    </p>
    {% if not current_user.get_task_in_progress('export_posts') %}
    <p>
        <a href="{{ url_for('main.export_posts') }}">
            {{ _('Export your posts') }}
        </a>
    </p>
```

### Progress Notifications
- 부트스트랩에 가로 막대 바로 완성도를 %로 제공 

```html
{% block content %}
    <div class="container">
        {% if current_user.is_authenticated %}
        {% with tasks = current_user.get_tasks_in_progress() %}
        {% if tasks %}
            {% for task in tasks %}
            <div class="alert alert-success" role="alert">
                {{ task.description }}
                <span id="{{ task.id }}-progress">{{ task.get_progress() }}</span>%
            </div>
            {% endfor %}
        {% endif %}
        {% endwith %}
        {% endif %}
        ...
{% endblock %}
```

- 사용자가 새로고침하지 않아도 완료도가 동적으로 업데이트되도록 하는 코드

```html
{% block scripts %}
    ...
    <script>
        ...
        function set_task_progress(task_id, progress) {
            $('#' + task_id + '-progress').text(progress);
        }
    </script>
    ...
{% endblock %}
```

### Deployment Considerations
- 백그라운드 작업을 지원하기 위해 2개의 새로운 구성 요소(Redis 서버와 RQ worker)를 추가
- 배포시 새롭게 추가한 요소를 추가해야 함

#### Deployment on a Linux Server
- 리눅스에서 Redis 추가

```shell
sudo apt-get install redis-server.
```
- RQ worker process 추가

```shell
sudo apt-get install redis-server.
```

#### Deployment on Heroku
- Heroku에서 Redis 추가

```shell
$ heroku addons:create heroku-redis:hobby-dev
```

- RQ worker process 추가
- procfile에 아래와 같이 선언
```text
web: flask db upgrade; flask translate compile; gunicorn microblog:app
worker: rq worker -u $REDIS_URL microblog-tasks
```

```shell
$ heroku ps:scale worker=1
```

#### Docker에 배포
- Docker에 Redis 연결

```shell
$ docker run --name redis -d -p 6379:6379 redis:3-alpine
```
- Redis 환경변수 설정

```shell
$ docker run --name microblog -d -p 8000:5000 --rm -e SECRET_KEY=my-secret-key \
    -e MAIL_SERVER=smtp.googlemail.com -e MAIL_PORT=587 -e MAIL_USE_TLS=true \
    -e MAIL_USERNAME=<your-gmail-username> -e MAIL_PASSWORD=<your-gmail-password> \
    --link mysql:dbserver --link redis:redis-server \
    -e DATABASE_URL=mysql+pymysql://microblog:<database-password>@dbserver/microblog \
    -e REDIS_URL=redis://redis-server:6379/0 \
    microblog:latest
```

- RQ worker 컨테이너 연결

```shell
$ docker run --name rq-worker -d --rm -e SECRET_KEY=my-secret-key \
    -e MAIL_SERVER=smtp.googlemail.com -e MAIL_PORT=587 -e MAIL_USE_TLS=true \
    -e MAIL_USERNAME=<your-gmail-username> -e MAIL_PASSWORD=<your-gmail-password> \
    --link mysql:dbserver --link redis:redis-server \
    -e DATABASE_URL=mysql+pymysql://microblog:<database-password>@dbserver/microblog \
    -e REDIS_URL=redis://redis-server:6379/0 \
    --entrypoint venv/bin/rq \
    microblog:latest worker -u redis://redis-server:6379/0 microblog-tasks
```