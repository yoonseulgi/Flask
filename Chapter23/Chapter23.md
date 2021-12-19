# 23장. Application Programming Interfaces (APIs)
- API를 사용하면 클라이언트 측에서 응용프로그램의 리소스와 직접 작업할 수 있고, 정보를 사용자에게 제공하는 방법을 클라이언트 측에서 담당

### REST as a Foundation of API Design
- Representational State Transfer의 약자
- 6가지 특성이 있음

#### Client-Server
- 클라이언트-서버 원칙은 클라이언트와 서버의 역할이 명확하게 구분되어야 함


#### Layered System
- 해당 원칙은 서버와 클라이언트가 통신해야 할 때 중개자에게 연결될 수 있음
- 클라이언트가 요청을 보낼 때 방식의 차이가 없어야 함
- 대량 요청을 처리할 때 필요함

#### Cache
- 해당 원칙은 시스템 성능을 향상하기 위해 자주 수신되는 요청을 캐시에 저장


#### Code On Demand
- 서버가 클라이언트에 대한 응답으로 실행 코드를 제공할 수 있음

#### Stateless
- REST API는 주어진 클라이언트가 요청을 보낼 때마다 불러올 클라이언트 상태를 저장해서는 안 된다고 명시되어 있음

#### Uniform Interface
- 고유한 리소스 식별자는 각 리소스에 고유한 URL을 할당하여 얻을 수 있음 
- 자체 설명 메시지는 클라이언트와 서버 간에 교환되는 요청 및 응답에 상대방이 필요로 하는 모든 정보가 포함


### Implementing an API Blueprint
- Microblog에 API를 추가
- API 경로를 포함하는 blue print 구현

```shell
$ mkdir app/api
```

- 사이클을 피하기 위해 ```from app.api``` 을 마지막에 구현

__init.py__: 
```python
from flask import Blueprint

bp = Blueprint('api', __name__)

from app.api import users, errors, tokens
```

- 사용자 API 리소스의 자리를 표시하는 모듈

__users.py__ :
```python
from app.api import bp

@bp.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    pass

@bp.route('/users', methods=['GET'])
def get_users():
    pass

@bp.route('/users/<int:id>/followers', methods=['GET'])
def get_followers(id):
    pass

@bp.route('/users/<int:id>/followed', methods=['GET'])
def get_followed(id):
    pass

@bp.route('/users', methods=['POST'])
def create_user():
    pass

@bp.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    pass
```

- 오류를 처리하기 위한 도우미 메소드 정의

__errors.py__  :
```python
def bad_request():
    pass
```

- 인증을 위한 서브 시스템
- 클라이언트가 로그인할 수 있는 방법을 제공

__tokens.py__  :
```python
def get_token():
    pass

def revoke_token():
    pass
```

- 새로운 blue print 팩토리 함수

__app/init.py__

```python
def create_app(config_class=Config):
    app = Flask(__name__)

    # ...

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
```

### Representing Users as JSON Objects
- API를 구현할 리소스의 표현 방식 결정
- 사용자와 함께 작동하는 API 구현이 목적이기에 JSON 사용

```json
{
        "id": 123,
    "username": "susan",
    "password": "my-password",
    "email": "susan@example.com",
    "last_seen": "2021-06-20T15:04:27Z",
    "about_me": "Hello, my name is Susan!",
    "post_count": 7,
    "follower_count": 35,
    "followed_count": 21,
    "_links": {
        "self": "/api/users/123",
        "followers": "/api/users/123/followers",
        "followed": "/api/users/123/followed",
        "avatar": "https://www.gravatar.com/avatar/..."
    }
}
```

- __password__ : 새 사용자가 등록될 때만 사용
- __email__ : 사용자가 자신의 정보를 요청할 때만 삽입되는 요소
- __post_count__ , __follower_count__ , __followed_count__ : 데이터베이스에는 저장되지 않고 사용자에게만 제공되는 가상 필드
- ___links__ : 하이퍼미디어 구현을 요구하는 요소



- json의 장점 중 하나는 json 데이터 형식을 python으로 변환
- __to_dict()__ 메소드는 사용자 개체를 python -> json
```python
from flask import url_for

class User(UserMixin, db.Model):
    # ...

    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'last_seen': self.last_seen.isoformat() + 'Z',
            'about_me': self.about_me,
            'post_count': self.posts.count(),
            'follower_count': self.followers.count(),
            'followed_count': self.followed.count(),
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'followers': url_for('api.get_followers', id=self.id),
                'followed': url_for('api.get_followed', id=self.id),
                'avatar': self.avatar(128)
            }
        }
        if include_email:
            data['email'] = self.email
        return data
```
- __email__ 은 사용자가 자신의 정보를 요청할 때만 포함되어야 하기 때문에 조건문에 걸어줌
- ___links__ 은 url_for()을 사용해 URL을 생성

- __from_dict()__ 메소드는 사용자 객체를 json -> python

```python
    def from_dict(self, data, new_user=False):
        for field in ['username', 'email', 'about_me']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])
```


### Representing Collections of Users
- 사용자 그룹 API 구현도 필요

```json
{
    "items": [
        { ... user resource ... },
        { ... user resource ... },
        ...
    ],
    "_meta": {
        "page": 1,
        "per_page": 10,
        "total_pages": 20,
        "total_items": 195
    },
    "_links": {
        "self": "http://localhost:5000/api/users?page=1",
        "next": "http://localhost:5000/api/users?page=2",
        "prev": null
    }
}
```
- __items__ : 정의도니 사용자 리소스 목록
- ___meta__ : 클라이언트가 사용자에게 페이지 표현 컨트롤을 표시하는데 우용할 수 있는 컬렉션에 대한 메타데이터 포함
- ___links__ : 이전/다음 페이지 정보 등 클라이언트가 목록 페이지 표현 제공


- 페이지를 표현하는 mixin class 구현

__app/models.py__  : 
```python
class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page, per_page, False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if resources.has_prev else None
            }
        }
        return data
```

- __to_collection_dict()__ :  items, _meta, _links 를 포함하고 있음
- __paginate()__ 쿼리 개체 의 메서드를 사용 하여 웹 애플리케이션의 인덱스, 탐색 및 프로필 페이지에 있는 게시물과 같이 항목의 페이지 정보 얻음
- 해당 mixin class를 User 모델에 부모 클래스로 추가

### Error Handling
- 7장에서 구현한 오류 페이지는 사용자가 이해하기 쉽도록 구현함
- API를 위해 클라이언트 기계가 이해할 수 있는 형태의 오류를 반환

```json
{
    "error": "short error description",
    "message": "error message (optional)"
}
```

- HTTP 프로토콜의 상태 코드를 사용하는 클래스 구현

__errors.py__ : 
```python
from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES

def error_response(status_code, message=None):
    payload = {'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')}
    if message:
        payload['message'] = message
    response = jsonify(payload)
    response.status_code = status_code
    return response
```
- __HTTP_STATUS_CODES__ 는 각 HTTP 상태 코드에 대한 짧은 설명 이름을 제공


### User Resource Endpoints
- API를 사용자가 사용할 수 있도록 구현

#### Retrieving a User
- 단일 사용자 검색 요청 

```python
from flask import jsonify
from app.models import User

@bp.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    return jsonify(User.query.get_or_404(id).to_dict())
```

- __id__ 은 요청된 사용자에 대해 URL의 동적 인수를 수신
- __get_or_404()__ 메서드는 사용자 개체가 있는 경우 id를 반환, 존재하지 않을 때는 id요청을 중단하고 404 오류를 반환



#### Retrieving Collections of Users
- 모든 사용자의 컬렉션을 반환

__users.py__ : 
```python
from flask import request

@bp.route('/users', methods=['GET'])
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(User.query, page, per_page, 'api.get_users')
    return jsonify(data)
```

- 팔로우와 팔로워를 반환하는 코드

```python
@bp.route('/users/<int:id>/followers', methods=['GET'])
def get_followers(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(user.followers, page, per_page,
                                   'api.get_followers', id=id)
    return jsonify(data)

@bp.route('/users/<int:id>/followed', methods=['GET'])
def get_followed(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(user.followed, page, per_page,
                                   'api.get_followed', id=id)
    return jsonify(data)
```

#### Registering New Users
- POST요청 은 새 사용자 계정을 등록

```python
@bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json() or {}
    if 'username' not in data or 'email' not in data or 'password' not in data:
        return bad_request('must include username, email and password fields')
    if User.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')
    if User.query.filter_by(email=data['email']).first():
        return bad_request('please use a different email address')
    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    response = jsonify(user.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_user', id=user.id)
    return response
```

- __request.get_json()__ 은 JSON을 추출하여 Python 구조로 반환 하는 방법을 제공
- username, email, password가 필수 요소인데 하나라도 인수로 받지 않으면 __bad_request()__ 함수를 사용해 클라이언트 오류 반환


#### Editing Users
- 기존 사용자를 수정하는 부분 API로 구현

```python
@bp.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.get_json() or {}
    if 'username' in data and data['username'] != user.username and \
            User.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')
    if 'email' in data and data['email'] != user.email and \
            User.query.filter_by(email=data['email']).first():
        return bad_request('please use a different email address')
    user.from_dict(data, new_user=False)
    db.session.commit()
    return jsonify(user.to_dict())
```

- 지정된 사용자가 없는 경우 404 오류 반환


### API Authentication
- API endpoint를 보호하기 위해 가장 확실한 방법은 ```@login_required``` 이라는 flask 데코레이터를 사용하는 것
- 문제 1. 인증되지 않은 사용자를 감지하면 로그인 페이지로 리디렉션됨
  이는 401 에러로 처리되어야 함
  
  
#### Tokens In the User Model
- API 인증 요구 사항을 위ㅔ해 토큰 인증 체계 를 사용
- 클라이언트가 API와 상호 작용을 시작하려면 사용자 이름과 암호로 인증하는 임시 토큰을 요청
- 클라이언트는 토큰이 유효한 동안 토큰으로 인증하여 API 요청을 보낼 수 있음

```python
import base64
from datetime import datetime, timedelta
import os

class User(UserMixin, PaginatedAPIMixin, db.Model):
    # ...
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)

    # ...

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user
```


#### Token Requests
- API를 작성할 때 클라이언트가 항상 웹 애플리케이션에 연결된 웹 브라우저가 되지는 않을 수 있음
- API의 가장 큰 장점은 스마트폰 앱과 같은 독립 실행형 클라이언트 또는 브라우저 기반 단일 페이지 애플리케이션이 백엔드 서비스에 액세스하는 것
- __Flask-HTTPAuth__ 를 이용해 클라이언트와 서버 간의 상호 작용을 단순화
- __Flask-HTTPAuth__ 는 모든 API 친화적인 인증 메커니즘을 제공

__auth.py__ : 
```python
from flask_httpauth import HTTPBasicAuth
from app.models import User
from app.api.errors import error_response

basic_auth = HTTPBasicAuth()

@basic_auth.verify_password
def verify_password(username, password):
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        return user

@basic_auth.error_handler
def basic_auth_error(status):
    return error_response(status)
```

- 사용자 토큰 생성 코드

__tokens.py__ : 
```python
from flask import jsonify
from app import db
from app.api import bp
from app.api.auth import basic_auth

@bp.route('/tokens', methods=['POST'])
@basic_auth.login_required
def get_token():
    token = basic_auth.current_user().get_token()
    db.session.commit()
    return jsonify({'token': token})
```

#### Protecting API Routes with Tokens
- API endpoint에 사용자 토큰을 확인하는 기능 추가

```python
from flask_httpauth import HTTPTokenAuth

token_auth = HTTPTokenAuth()

@token_auth.verify_token
def verify_token(token):
    return User.check_token(token) if token else None

@token_auth.error_handler
def token_auth_error(status):
    return error_response(status)
```

- 토큰 인증 시 사용자의 경로를 보호하는 코드
- ```@token_auth.login_required``` flask 데코레이터 사용
- 데코레이터는 사용자가 먼저 생성되어야 하기 때문에 사용자 생성에 필요한 정보를 받아오는 메소드에 모두 추가

```python 
from flask import abort
from app.api.auth import token_auth

@bp.route('/users/<int:id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    # ...

@bp.route('/users', methods=['GET'])
@token_auth.login_required
def get_users():
    # ...

@bp.route('/users/<int:id>/followers', methods=['GET'])
@token_auth.login_required
def get_followers(id):
    # ...

@bp.route('/users/<int:id>/followed', methods=['GET'])
@token_auth.login_required
def get_followed(id):
    # ...

@bp.route('/users', methods=['POST'])
def create_user():
    # ...

@bp.route('/users/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_user(id):
    if token_auth.current_user().id != id:
        abort(403)
    # ...
```

#### Revoking Tokens

```python
from app.api.auth import token_auth

@bp.route('/tokens', methods=['DELETE'])
@token_auth.login_required
def revoke_token():
    token_auth.current_user().revoke_token()
    db.session.commit()
    return '', 204
```

- __DELETE__ 요청을 통해 토큰을 무효화


### API Friendly Error Messages
- API가 오류 없이 수신할 수 있는 형식으로 오류를 반환
- __wants_json_response()__ JSON or HTML 선호도를 비교하여 선호도가 높은 타입으로 반환

```python
from flask import render_template, request
from app import db
from app.errors import bp
from app.api.errors import error_response as api_error_response

def wants_json_response():
    return request.accept_mimetypes['application/json'] >= \
        request.accept_mimetypes['text/html']

@bp.app_errorhandler(404)
def not_found_error(error):
    if wants_json_response():
        return api_error_response(404)
    return render_template('errors/404.html'), 404

@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if wants_json_response():
        return api_error_response(500)
    return render_template('errors/500.html'), 500
```
