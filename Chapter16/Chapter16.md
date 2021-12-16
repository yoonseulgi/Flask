# 16장. Full-Text Search
- 사용자가 자연어를 사용하여 원하는 게시글을 찾을 수 있도록 검색 기능 추가
- 전체 페이지를 검색하는 것이 아닌 작은 부분인 사용자 게시글을 검색
  ex) 'dog'을 검색했을 때 'dog'가 포함된 모든 사용자의 게시글을 반환
  
### Introduction to Full-Text Search Engines
- Full-Text Search Engines은 관계형 데이터베이스처럼 표준화되어 있지 않음
- 데이터베이스는 텍스트 검색을 지원
- Flask는 SQLite, MySQL, PostgreSQL, MongoDB, CouchDB 등 모두 사용 가능
- ELK stack 중 E는 Elasticsearch을 뜻하며 검색 엔진임
- Elasticsearc 사용

### Installing Elasticsearch
- pip install을 통해 Elasticsearch 설치 
- Elasticsearch 설치 후 http://localhost:9200 브라우저에서 Elasticsearch가 가동 중인지 확인 가능

### Elasticsearch Tutorial
- Elasticsearch에 대한 연결을 생성하려면 Elasticsearch 클래스에 인스턴스를 생성하고 연결 URL을 인수로 전달

```shell
>>> from elasticsearch import Elasticsearch
>>> es = Elasticsearch('http://localhost:9200')
```

- elasticsearch의 데이트(Json개체)는 인덱스에 기록
- 저장된 각 문서에 대해 elasticsearch는 고유한 ID와 저장할 데이터가 있는 사전을 사용

```shell 
>>> es.index(index='my_index', id=1, body={'text': 'this is a test'})
>>> es.index(index='my_index', id=2, body={'text': 'a second test'})
```

- 검색 테스트
```shell
>>> es.search(index='my_index', body={'query': {'match': {'text': 'this test'}}})
```

- __es.search()__ 를 통해 검색 결과 확인
- 분석 점수가 높을수록 많이 일치 즉, 동일한 문장은 점수가 1, 유사도가 낮아질수록 0으로 수렴

```python
{
    'took': 309,
    'timed_out': False,
    '_shards': {'total': 1, 'successful': 5, 'skipped': 0, 'failed': 0},
    'hits': {
        'total': {'value': 2, 'relation': 'eq'},
        'max_score': 0.82713,
        'hits': [
            {
                '_index': 'my_index',
                '_type': '_doc',
                '_id': '1',
                '_score': 0.82713,
                '_source': {'text': 'this is a test'}
            },
            {
                '_index': 'my_index',
                '_type': '_doc',
                '_id': '2',
                '_score': 0.1936807,
                '_source': {'text': 'a second test'}
            }
        ]
    }
}
```

### Elasticsearch Configuration
- elasticsearch와 flask 연결
- __config.py__ 에 elasticsearch URL을 인수로 전달

```python
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
```

- elasticsearch를 응용 프로그램이 실행될 때마다 가동하고 싶다면 .env 파일에 정의

```text
ELASTICSEARCH_URL=http://localhost:9200
```


### A Full-Text Search Abstraction
- 기능 추가가 필요한 경우를 대비하여 다른 모델로 쉽게 확장할 수 있도록 검색 기능을 추상화

- 인덱싱할 모델과 모델 안의 필드를 나타내는 방법을 찾는 것
- __models.py__ 파일에 __Post__ 클래스에 속성을 정의

```python
    __searchable__ = ['body']
```

- __app/search.py__ 에 elasticsearch와 상호작용할 코드를 구현
- 애플리케이션과 독립시킴으로 elasticsearch의 코드를 수정하더라도 애플리케이션은 문제없이 구동 가능
- 3가지 기능 필요
  1. 전체 텍스트를 인덱스에 추가
  2. 인덱스 삭제(게시글 삭제를 지원하기 위해)
  3. 검색어를 실행
  
-  __app/search.py__  
```python
from flask import current_app

def add_to_index(index, model):
    if not current_app.elasticsearch:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    current_app.elasticsearch.index(index=index, id=model.id, body=payload)

def remove_from_index(index, model):
    if not current_app.elasticsearch:
        return
    current_app.elasticsearch.delete(index=index, id=model.id)

def query_index(index, query, page, per_page):
    if not current_app.elasticsearch:
        return [], 0
    search = current_app.elasticsearch.search(
        index=index,
        body={'query': {'multi_match': {'query': query, 'fields': ['*']}},
              'from': (page - 1) * per_page, 'size': per_page})
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    return ids, search['hits']['total']['value']
```


### Integrating Searches with SQLAlchemy
- 문제 2개 존재
  1. 결과가 숫자 ID 목록으로 제공되는 문제
  2. 게시글이 추가되거나 제거될 때 애플리케이션이 인덱싱을 호출해야만 함
  
- 문제 1번 해결: 렌더링을 위해 템플릿으로 전달할 수 있도록 SQLAlchemy 모델이 필요
  SQLAlchemy query를 만들어 해결
- 문제 2번 해결: 인덱싱 변경을 자동으로 발생시키는 SQLAlchemy 이벤트 사용
- __UserMixin class__ 에 2개의 솔루션을 구현

```python 
class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        #...
    @classmethod
    def before_commit(cls, session):
        #...
    @classmethod
    def after_commit(cls, session):
        #...
    @classmethod
    def reindex(cls):
        #...
```

- 위에서 정의한 메소드는 클래스를 인수로 전달받음(self 인수를 cls로 변경해서 사용)
  1. search() 메소드
     query_index() 함수를 래핑하여 객체 ID 목록을 실제 객체로 대체
  2. before_commit()/after_commit() 메소드
     commit이 발생하기 전/후에 트리거되는 SQLAlchemy 이벤트
     before_commit()은 session.new, session.dirty, session.deleted 등 commit 후에 사용하기 힘든 객체를 선언
     after_commit()은 elasticsearch가 수행되기 적절한 타이밍
     _changes 를 통해 변동이 발생했음을 확인하고, __app/search.py__ 인덱싱 호출
  3. reindex() 메소드
     모든 게시글을 초기로드로 수행하는 도우미 메소드
  
  
### Search Form
- GET 요청 사용

```python
class SearchForm(FlaskForm):
    q = StringField(_l('Search'), validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)
```

- 해당 양식은 모든 페이지가 참고할 수 있어야 함
- 모든 경로에 해당 양식 개체를 추가해야 하기에  코드 중복이 발생할 수 있음
- 위와 같은 코드 중복 문제 가 발생하지 않도록 전체 응용 프로그램에 해당 양식을 구현


### Search View Function
- 검색 결과를 볼 수 있는 기능
- 기존에 제출한 양식이 유효한지 검사하기 위해 사용했던 form.validate_on_submit() 메소드는 POST 요청일 때만 작동하기 때문에 사용할 수 없음
- 해당 양식은 GET 요청을 사용하기 때문에 form.validate()를 사용
- search.html 