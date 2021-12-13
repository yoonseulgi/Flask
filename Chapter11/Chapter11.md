# 11장. Facelift
- 응용 프로그램 발전시키긴

### CSS Frameworks
- 웹 페이지를 만드는 것을 쉽게 해줌
- 일반적으로 사용되는 사용자 인터페이스 CSS 프레임워크를 제공

### Introducing Bootstrap
- CSS 프레임워크 중 인기있는 프레임워크
- 주요 웹 브라우저에서 유사한 모양제공
- pip으로 flask-bootstrap 설치 가능

```shell
$ pip install flask-bootstrap
```

### Using Flask-Bootstrap
- __base.html__ 파일에 정의하면 응용 프로그램이 참조 가능
- bootstrap 기본 템플릿을 맞출 때 다음과 같이 3단계 계층 사용
  1. Bootstrap 프레임워크 파일을 포함하는 페이지의 기본 구조를 제공
  2. 페이지의 구현 제공
  3. 페이지 콘텐츠 제공
- __title block__ : <title></title> 태그를 사용해 페이지 제목 정의
- __navbar__: 탐색 모음을 정의하는데 사용하는 선택적 블록
- 콘텐츠 블록의 최상위 컨테이너 정의 및 플래시 메시지 렌더링
  
### Rendering Bootstrap Form

```html
{% extends "base.html" %}
{% import 'bootstrap/wtf.html' as wtf %}

{% block app_content %}
    <h1>Register</h1>
    <div class="row">
        <div class="col-md-4">
            {{ wtf.quick_form(form) }}
        </div>
    </div>
{% endblock %}
```

- import문은 python import와 유사하게 작동
- __wtf.quick_form()__ 을 추가하여 bootstrap 프레임워크에 정의된 스타일 사용

### Rendering of Blog Posts
- 단일 블로그를 렌더링하는 ___post.html__ 하위 템플릿 추상화

### Rendering Pagination Links

```html
    <nav aria-label="...">
        <ul class="pager">
            <li class="previous{% if not prev_url %} disabled{% endif %}">
                <a href="{{ prev_url or '#' }}">
                    <span aria-hidden="true">&larr;</span> Newer posts
                </a>
            </li>
            <li class="next{% if not next_url %} disabled{% endif %}">
                <a href="{{ next_url or '#' }}">
                    Older posts <span aria-hidden="true">&rarr;</span>
                </a>
            </li>
        </ul>
    </nav>
```

- 더이상 보여줄 컨텐츠가 없을 때 링크를 비활성화 시킴(링크가 회색으로 표시)