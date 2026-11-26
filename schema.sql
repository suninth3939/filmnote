-- 회원
create table user (
    user_id integer primary key autoincrement,
    username varchar(50) collate nocase not null unique,
    email varchar(100) collate nocase not null unique,
    password_hash varchar(255) not null,
    name varchar(50) not null,
    bio varchar(200),
    created_at datetime not null
);

-- 로그인 세션
create table session (
    session_id integer primary key autoincrement,
    user_id int not null,
    token_hash varchar(255) not null unique,
    created_at datetime not null,
    expires_at datetime not null,
    revoked_at datetime,
    foreign key (user_id) references user(user_id) on delete cascade,
    check (expires_at > created_at)
);

-- 장소
create table place (
    place_id integer primary key autoincrement,
    place_name varchar(100) not null,
    category varchar(50) not null,
    address varchar(200) not null,
    check (category in ('카페', '식당', '기타'))
);

-- 게시글
create table post (
    post_id integer primary key autoincrement,
    user_id int not null,
    place_id int,
    content varchar(500) not null,
    created_at datetime not null,
    foreign key (user_id) references user(user_id) on delete cascade,
    foreign key (place_id) references place(place_id) on delete set null
);

-- 게시글 사진
create table post_photo (
    photo_id integer primary key autoincrement,
    post_id int not null,
    photo_url varchar(200) not null,
    display_order int not null,
    foreign key (post_id) references post(post_id) on delete cascade,
    unique (post_id, display_order),
    check (display_order >= 1 and display_order <= 10)
);

-- 댓글
create table comment (
    comment_id integer primary key autoincrement,
    post_id int not null,
    user_id int not null,
    content varchar(300) not null,
    created_at datetime not null,
    foreign key (post_id) references post(post_id) on delete cascade,
    foreign key (user_id) references user(user_id) on delete cascade
);

-- 좋아요
create table likes (
    user_id int not null,
    post_id int not null,
    created_at datetime not null,
    primary key (user_id, post_id),
    foreign key (user_id) references user(user_id) on delete cascade,
    foreign key (post_id) references post(post_id) on delete cascade
);

-- 팔로우
create table follow (
    follower_id int not null,
    following_id int not null,
    created_at datetime not null,
    primary key (follower_id, following_id),
    foreign key (follower_id) references user(user_id) on delete cascade,
    foreign key (following_id) references user(user_id) on delete cascade,
    check (follower_id <> following_id)
);

-- 해시태그
create table hashtag (
    tag_id integer primary key autoincrement,
    tag_name varchar(50) collate nocase not null unique
);

-- 게시글-해시태그 매핑
create table post_hashtag (
    post_id int not null,
    tag_id int not null,
    primary key (post_id, tag_id),
    foreign key (post_id) references post(post_id) on delete cascade,
    foreign key (tag_id) references hashtag(tag_id) on delete cascade
);



create index post_author_idx on post(user_id, post_id desc);
create index post_place_idx on post(place_id);
create index comment_post_idx on comment(post_id, comment_id);
create index likes_post_idx on likes(post_id);
create index follow_target_idx on follow(following_id);
create index hashtag_posts_idx on post_hashtag(tag_id);
