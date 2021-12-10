# 8장. Followers
      
      
      
      
### Database Relationships Revisited
- 데이터베이스에는 사용자를 나타내는 테이블이 있기에 링크를 모델링 가능


#### * One-to-Many
- 예로 사용자와 게시물 관계
- 한 명의 사용자가 여러 개의 게시물을 작성할 수 있음.
- 관계의 '다'쪽(게시물)에서 외래 키를 사용


#### * Many-to-Many
- 예로 학생과 교사 관계
- 학생은 여러 명의 교사에게 수업을 들을 수 있음
- 교사는 여러 명의 학생을 가르칠 수 있음
- 다 대 다 관계를 표현하려면 보조 테이블이 필요함(관계를 나타내는 테이블)
- 관계를 나타내는 보조 테이블은 학생, 교사 각 테이블의 기본키를 가지고 있음


#### * Many-to-One and One-to-One
- 다대일 관계는 일대다 관계와 유사할 수 있음
- 차이점이 있다면 '다수'를 중점으로 본다는 것
- 일대일 관계는 일대다 관계에서 '다'측이 하나의 링크만 가지게 하는 것




### Representing Followers
- 팔로워 테이블은 관계를 나타내는 테이블
- 팔로워 테이블의 레코드는 팔로어 사용자와 팔로어 사용자 간의 연결을 나타낸다.



### Database Model Representation
- 팔로워 테이블(관계를 나타내는 테이블) 표현


```python
followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)
```

- __User__: 자기참조 테이블
- __Secondary__: 관계에 사용되는 연관 테이블을 구성
- __primaryjoin__: 팔로워 사용자를 관계 테이블과 연결

  연결을 위한 join 조건 - 관련된 테이블들의 __follower_id__ 필드로 연결 
- __secondaryjoin__ 
- __backref__: User 개체의 접근되는 방법을 정의 
- __lazy__: User 개체가 아닌 팔로워 개체에 쿼리가 적용됨 

```shell
(venv) $ flask db migrate -m "followers"
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.autogenerate.compare] Detected added table 'followers'
  Generating /home/miguel/microblog/migrations/versions/ae346256b650_followers.py ... done

(venv) $ flask db upgrade
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 37f06a334dbf -> ae346256b650, followers
```


### Adding and Removing "follows"
- SQLAlchemy ORM은 사용자가 팔로우하는 목록 즉, 관계를 기록할 수 있음   
   
```shell
user1.followed.append(user2)
```
- 위와 같은 구문을 통해 user1이 user2를 팔로우하도록 함    


```shell  
user1.followed.remove(user2)
```    
- user1이 user2가 팔로우한 것을 제거
- 팔로우를 설정하고 제고하는 기능을 __models.py__ 함수로 구현하여 사용   
   
   
```python 
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0
```

### Obtaining the Posts from Followed Users
- 로그인한 사용자가 팔로우한 모든 사람이 작성한 게시물을 표시하는 기능을 추가
- 당사자가 원하는 정보를 추출할 수 있는 방법 아래와 같이 함수로 구현

   
```python
    def followed_posts(self):
        return Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id).order_by(
                    Post.timestamp.desc())
```

#### Join

```shell
Post.query.join(followers, (followers.c.followed_id == Post.user_id))
```
- 첫 번째 인수(followrs)는 팔로워할 연관 테이블이고, 두 번째 인수는 조인 조건
  데이터베이스가 게시물과 팔로워 테이블의 데이터를 결합하는 임시 테이블을 생성하기를 원한다는 의미


#### Filters
- 내가 원하는 결과만 보고 싶을 때 사용

```shell
filter(followers.c.follower_id == self.id)   
```
- 괄호 내에는 필터링할 조건
  자신이 팔로우한 사용자만 결과로 반환
    
     
#### Sorting
```shell
order_by(Post.timestamp.desc())
```
- 결가를 원하는 속성으로 정렬

### Combining Own and Followed Posts
- 각 사용자에 맞게 해당 사용자가 팔로워한 목록만 뜨도록 함
- 기존 followed_posts() 함수를 아래와 같이 수정함으로 각 사용자가 팔로워한 목록만 뜨도록 함
```python
    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())
```   


### Unit Testing the User Model
- 단위 테스트를 쉽게 작성 및 실행
- 애플리케이션이 변경될 때마다 테스트를 다시 실행
- 응용 프로그램에 새로운 기능이 추가될 때마다 해당 기눙에 대한 단위 테스트를 작성
   
   
### Integrating Followers with the Application
- 해당 사용자가 팔로워한 사람의 목록만 뜨게하는 기능을 응용 프로그램에 추가
- 웹 변경은 POST 요청으로 구현(GET 요청이 더 쉽지만 CSRF 공격으로 악용될 수 있음)