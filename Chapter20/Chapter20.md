### Executing a Function On Page Load
- 각 페이지가 로드되면 Javascript 코드 실행
- 구현할 기능으론 로드된 페이지의 사용자 이름에 대한 모든 링크 검색, 부트스트랩의 팝오버 구성 요소 구성
- __base.html__ 파일에 Jquery를 추가함으로 모든 페이지에서 실행


### Finding DOM Elements with Selectors
- 문제 1. 해당 페이지 안의 모든 사용자의 링크를 찾는 함수 구현
- HTML 요소에는 고유한 ID가 존재
- ```$('#post123')``` 를 사용하면 DOM에 존재하는 해당 사용자의 링크를 찾을 수 있음


### Popovers and the DOM
- 부트스트랩이 DOM에서 팝오버 구성요소를 생성할 수 있음
- 팝오버는 다른 태그에서도 잘 작동 하지만, 팝오버는 ```<a>``` 요소의 자식으로 만들기 때문에 ``<a>``` 태그에 구현 


```html
        <a href="..." class="user_popup">
            username
            <div> ... popover elements here ... </div>
        </a>
```

- 마우스가 이동할 때만 팝오버가 작동하도록 ```<span>``` 태그 사용

```html
        <span class="user_popup">
            <a href="...">
               username
            </a>
            <div> ... popover elements here ... </div>
        </span>
```

- ___post.html__ 에 아래 코드를 추가함으로 리팩토링

```html
                {% set user_link %}
                    <span class="user_popup">
                        <a href="{{ url_for('main.user', username=post.author.username) }}">
                            {{ post.author.username }}
                        </a>
                    </span>
                {% endset %}
```

### Hover Events
- 본 챕터에서 구현하고자 하는 것은 Javascript를 통해 팝오버를 수동으로 다룰 수 있는 것
- 페이지에 Hover 이벤트 구현
- ```element.hover(handlerIn, handlerOut)``` 함수를 사용함으로 Jquery를 자유롭게 사용 가능
- __base.html__ 에 아래와 같은 코드를 추가함으로 마우스가 팝업 페이지로 이동했을 때 hover가 실행되도록 함

```html
    $(function() {
        $('.user_popup').hover(
            function(event) {
                // mouse in event handler
                var elem = $(event.currentTarget);
            },
            function(event) {
                // mouse out event handler
                var elem = $(event.currentTarget);
            }
        )
    });
```

- 지연이 발생했을 때에도 hover가 작동할 수 있도록 시간 차를 허용하는 코드를 추가

```html
    $(function() {
        var timer = null;
        $('.user_popup').hover(
            function(event) {
                // mouse in event handler
                var elem = $(event.currentTarget);
                timer = setTimeout(function() {
                    timer = null;
                    // popup logic goes here
                }, 1000);
            },
            function(event) {
                // mouse out event handler
                var elem = $(event.currentTarget);
                if (timer) {
                    clearTimeout(timer);
                    timer = null;
                }
            }
        )
    });
```

- __setTimeout()__ 은 인수로 주어진 시간 뒤에 함수를 수행


### Ajax Requests
- URL로 전송되는 Ajax 요청에서 username 찾기
- 아래와 같은 코드를 추가함으로 username 찾는 함수 작성

```html
    xhr = $.ajax(
        '/user/' + elem.first().text().trim() + '/popup').done(
            function(data) {
                xhr = null
                // create and display popup here
            }
        );
```


### Popover Creation and Destruction
- Ajax 콜백 함수에서 전달된 인수를 사용해 팝오버 구성
- 팝오버 부트스트랩의 기능은 팝업을 설정하는데 필요한 모든 작업을 수행
- 팝오버의 옵션은 인수로 전달

```html
    function(data) {
        xhr = null;
        elem.popover({
            trigger: 'manual',
            html: true,
            animation: false,
            container: elem,
            content: data
        }).popover('show');
        flask_moment_render_all();
    }
```

- 마우스 아웃 이벤트 핸들러에서 팝업 제거를 처리하는 기능
- 사용자의 마우스가 이벤트 대상 범위에 없다면 팝오버 작업을 중단하는 기능

```html
    function(event) {
        // mouse out event handler
        var elem = $(event.currentTarget);
        if (timer) {
            clearTimeout(timer);
            timer = null;
        }
        else if (xhr) {
            xhr.abort();
            xhr = null;
        }
        else {
            elem.popover('destroy');
        }
    }
```
