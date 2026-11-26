insert into user (username, email, password_hash, name, bio, created_at) values
('gachon_kim', 'gachon1@gachon.ac.kr', '!', '김가천', 'AI소프트웨어학부 재학생', CURRENT_TIMESTAMP),
('seoul_lee', 'seoul@gachon.ac.kr', '!', '이서울', '축구 직관과 카페 투어', CURRENT_TIMESTAMP),
('seongsu_park', 'seongsu@gachon.ac.kr', '!', '박성수', '성수동 카페 기록', CURRENT_TIMESTAMP),
('matjip_choi', 'matjip@gachon.ac.kr', '!', '최맛집', '맛집 탐방 계정', CURRENT_TIMESTAMP),
('coding_jung', 'coding@gachon.ac.kr', '!', '정개발', '데이터베이스 공부 중', CURRENT_TIMESTAMP);

insert into place (place_name, category, address) values
('어니언 성수', '카페', '서울 성동구 아차산로 8'),
('가천식당', '식당', '성남시 수정구 성남대로 1342'),
('상암 월드컵경기장', '기타', '서울 마포구 월드컵로 240'),
('블루보틀 성수', '카페', '서울 성동구 아차산로 7'),
('복정동 우동집', '식당', '성남시 수정구 복정로 15');

insert into post (user_id, place_id, content, created_at) values
(1, 1, '성수동 어니언에서 빵이랑 커피 한 잔!', CURRENT_TIMESTAMP),
(2, 3, '오늘 상암 직관 승리! 분위기 최고였습니다.', CURRENT_TIMESTAMP),
(3, 4, '블루보틀 라떼는 언제 마셔도 맛있어요.', CURRENT_TIMESTAMP),
(4, 2, '학교 앞 가천식당 제육볶음 맛집 인정합니다.', CURRENT_TIMESTAMP),
(5, null, 'DB 워크숍 과제 마무리 완료!', CURRENT_TIMESTAMP),
(1, 5, '시험 기간에 먹는 따뜻한 우동 한 그릇.', CURRENT_TIMESTAMP),
(2, 1, '어니언 성수 평일 오전 재방문!', CURRENT_TIMESTAMP),
(3, 2, '오늘 점심은 가천식당에서 먹었습니다.', CURRENT_TIMESTAMP),
(4, 1, '성수동 베이커리 투어 다녀왔어요.', CURRENT_TIMESTAMP),
(5, 4, '노트북 들고 코딩하러 카페 왔습니다.', CURRENT_TIMESTAMP);

insert into post_photo (post_id, photo_url, display_order) values
(1, 'uploads/demo/post1_1.jpg', 1),
(1, 'uploads/demo/post1_2.jpg', 2),
(1, 'uploads/demo/post1_3.jpg', 3),
(2, 'uploads/demo/post2_1.jpg', 1),
(2, 'uploads/demo/post2_2.jpg', 2),
(3, 'uploads/demo/post3_1.jpg', 1),
(4, 'uploads/demo/post4_1.jpg', 1),
(6, 'uploads/demo/post6_1.jpg', 1),
(7, 'uploads/demo/post7_1.jpg', 1),
(8, 'uploads/demo/post8_1.jpg', 1),
(9, 'uploads/demo/post9_1.jpg', 1),
(10, 'uploads/demo/post10_1.jpg', 1);

insert into comment (post_id, user_id, content, created_at) values
(1, 2, '빵 맛있어 보이네요!', CURRENT_TIMESTAMP),
(1, 3, '팡도르 추천합니다.', CURRENT_TIMESTAMP),
(2, 1, '직관 승리 부럽습니다!', CURRENT_TIMESTAMP),
(2, 4, '날씨도 좋아 보이네요.', CURRENT_TIMESTAMP),
(2, 5, '다음엔 저도 같이 가요!', CURRENT_TIMESTAMP),
(3, 1, '라떼 진짜 고소하죠.', CURRENT_TIMESTAMP),
(4, 2, '오늘 점심은 여기로 가야겠네요.', CURRENT_TIMESTAMP),
(4, 5, '계란말이도 맛있어요.', CURRENT_TIMESTAMP),
(5, 1, '과제 고생하셨습니다!', CURRENT_TIMESTAMP),
(5, 3, '화이팅입니다!', CURRENT_TIMESTAMP),
(6, 4, '국물이 진해 보여요.', CURRENT_TIMESTAMP),
(7, 3, '평일 오전이 한산하죠.', CURRENT_TIMESTAMP),
(8, 1, '가성비 최고죠.', CURRENT_TIMESTAMP),
(9, 2, '사진 잘 나왔네요!', CURRENT_TIMESTAMP),
(10, 4, '열공하세요!', CURRENT_TIMESTAMP);

insert into likes (user_id, post_id, created_at) values
(2, 1, CURRENT_TIMESTAMP), (3, 1, CURRENT_TIMESTAMP), (4, 1, CURRENT_TIMESTAMP), (5, 1, CURRENT_TIMESTAMP),
(1, 2, CURRENT_TIMESTAMP), (3, 2, CURRENT_TIMESTAMP), (4, 2, CURRENT_TIMESTAMP),
(1, 4, CURRENT_TIMESTAMP), (2, 4, CURRENT_TIMESTAMP),
(1, 3, CURRENT_TIMESTAMP),
(2, 5, CURRENT_TIMESTAMP),
(3, 7, CURRENT_TIMESTAMP);

insert into follow (follower_id, following_id, created_at) values
(1, 2, CURRENT_TIMESTAMP), (1, 3, CURRENT_TIMESTAMP), (1, 4, CURRENT_TIMESTAMP),
(2, 1, CURRENT_TIMESTAMP), (2, 3, CURRENT_TIMESTAMP),
(3, 1, CURRENT_TIMESTAMP), (3, 4, CURRENT_TIMESTAMP),
(4, 1, CURRENT_TIMESTAMP), (4, 2, CURRENT_TIMESTAMP),
(5, 1, CURRENT_TIMESTAMP);

insert into hashtag (tag_name) values
('#성수카페'), ('#맛집추천'), ('#직관일기'), ('#가천대'), ('#일상');

insert into post_hashtag (post_id, tag_id) values
(1, 1), (1, 5),
(2, 3), (2, 5),
(3, 1),
(4, 2), (4, 4),
(5, 4), (5, 5),
(6, 2),
(7, 1),
(9, 1);
