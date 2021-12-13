# 9장. Pagination

### Submission of Blog Posts
- 사용자가 새 게시물을 입력
- __forms.py__ 파일에 블로그 제출 양식을 PostForm class로 작성
- __index.html__ 파일에 __PostForm class__ 를 정의해줌으로 연동 

### Displaying Blog Posts
- 다음과 같은 함수를 정의함으로 인덱스 뷰를 정의
```python
    posts = [
        { 
            'author': {'username': 'John'}, 
            'body': 'Beautiful day in Portland!' 
        },
        { 
            'author': {'username': 'Susan'}, 
            'body': 'The Avengers movie was so cool!' 
        }
    ]
```
- __route.py__ 파일에 __index()__ 함수에 다음과 같은 코드를 추가함으로 실존하는 게시물로 변경
- __followed_posts__ 메소드는 사용자가 관심있는 게시물을 데이터베이스에서 가져옴

### Making It Easier to Find Users to Follow
- 사용자가 팔로우한 다른 사용자의 게시글을 가져오는 함수 구현

```python
@app.route('/explore')
@login_required
def explore():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('index.html', title='Explore', posts=posts)
```
- 사용자 프로필을 사용자 팀플릿에 작은 템플릿을 추가함으로 다른 템플릿과 분리
```html
<td>
                <a href="{{ url_for('user', username=post.author.username) }}">
                    {{ post.author.username }}
                </a>
                says:<br>{{ post.body }}
            </td>
```


### Pagination of Blog Posts
- 너무 많은 게시물 목록을 관리하는 것은 느린 문제가 있음
```shell
>>> user.followed_posts().paginate(1, 20, False).items
```
- __paginate__ 메서드는 3가지 인수
  1부터 시작하는 페이지 번호
  페이지당 항목 수
  오류 플래그
  
```python
class Config(object):
    ...
    POSTS_PER_PAGE = 3
```
- 페이지 개수 3개로 정의

### Page Navigation
- 사용자가 다음/이전 페이지로 이동할 수 있도록 블로그 하단에 링크를 추가
- __paginate()__ 호출
  has_next: 현재 페이지 이후에 하나 이상의 페이지가 더 있으면 참
  has_prev: 현재 페이지 이전에 하나 이상의 페이지가 더 있으면 참
  next_num: 다음 페이지의 페이지 번호
  prev_num: 이전 페이지의 페이지 번호
- 4가지 요소를 사용해 버튼 링크 렌더링
- __index()__ 에 아래와 같은 코드를 첨부함으로 버튼을 렌더링

```python
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Home', form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)
```

- __explore()__ 다음과 같이 수정
```python
@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("index.html", title='Explore', posts=posts.items,
                          next_url=next_url, prev_url=prev_url)
```

### Pagination in the User Profile Page
- 사용자의 프로필을 일관성 있게 유지하려면 페이지의 스타일을 유지
- __routes.py__ 파일의 __user__ 메소드를 다음과 같이 수정
```python
@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)
```
- 응용 프로그램에 적용되도록 __user.html__ 다음과 같이 수정
```html
    {% for post in posts %}
        {% include '_post.html' %}
    {% endfor %}
    {% if prev_url %}
    <a href="{{ prev_url }}">Newer posts</a>
    {% endif %}
    {% if next_url %}
    <a href="{{ next_url }}">Older posts</a>
    {% endif %}
```

- chapter 9 commit