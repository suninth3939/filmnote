# Filmnote

사진과 장소를 함께 기록하는 한국어 Streamlit 앱입니다. 처음 열면 샘플 피드를 둘러볼 수 있습니다. **새 게시물 → 체험 계정으로 시작**을 선택하면 바로 사진을 올릴 수 있습니다. 개인 계정은 **로그인 → 회원가입**에서 만듭니다.

## 실행

Python 3.12에서 검증했습니다. ZIP을 풀고 `filmnote` 폴더 안에서 시작하세요.

- **Windows**에서는 `run.bat`를 더블클릭하세요. 처음 실행할 때 인터넷으로 패키지를 내려받고 프로젝트의 `.venv`에 설치합니다. Python과 Python Launcher 또는 PATH 등록이 필요합니다.
- **터미널**에서는 아래 명령을 실행하세요. 가상환경을 사용한다면 먼저 활성화하세요.

```shell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

브라우저에서 기본 주소 `http://localhost:8501`을 엽니다. 포트를 사용 중이면 터미널에 표시된 주소를 확인하세요. 서버 종료는 터미널에서 Ctrl+C를 누르면 됩니다.

## 사용

| 화면 | 할 수 있는 일 |
| --- | --- |
| 피드 | 최신 게시물 보기, 팔로잉·좋아요 피드 전환, 사진 넘기기, 좋아요와 댓글 작성·취소 |
| 새 게시물 | 사진 1~10장의 순서 미리보기, 본문·장소·해시태그 작성 |
| 탐색 | 본문·계정·장소·태그 검색, 태그·장소 필터, 인기순 정렬, 사진 2장 이상 모아보기 |
| 프로필 | 작성자 게시물과 팔로워·팔로잉 목록 보기, 팔로우·언팔로우, 내 이름·소개 수정 |
| 내 게시물 | 카드의 **편집**으로 본문·장소·태그 수정, 확인 후 게시물 삭제 |

공용 체험 계정은 `gachon_kim`이며 비밀번호는 `FilmnoteDemo1!`입니다. 체험 계정으로 작성한 내용은 그 계정을 사용하는 사람에게 공유됩니다. 개인 계정 비밀번호는 **내 프로필 → 계정 설정**에서 바꿀 수 있습니다.

## 데이터와 사진

| 경로 | 용도 |
| --- | --- |
| `data/micro_sns.sqlite3` | SQLite 데이터베이스 |
| `data/uploads/<UUID>.jpg` | 새로 올린 사진 |
| `data/uploads/demo/` | 샘플 게시물의 사진 |
| `schema.sql` | 원본 설계를 바탕으로 한 테이블 10개와 인덱스 |
| `seed/sample.sql`, `seed/photos/` | 새 DB를 처음 만들 때 사용하는 샘플 데이터와 이미지 |
| `db.py` | DB 초기화, 로그인, 피드 조회, 게시물·사진 저장 |
| `app.py`, `style.css` | Streamlit 화면과 스타일 |

첨부된 MySQL SQL의 테이블 이름, 주요 열, 외래 키와 관계, 사용자 5명·장소 5곳·게시물 10개의 초기 데이터를 SQLite로 옮겼습니다. DB가 없는 폴더에서 시작하면 한 번만 초기화합니다. 원본 SQL의 수정·삭제 예시는 화면에서 해당 기능을 사용할 때 실행하는 쿼리로 반영했습니다.

사진은 JPG·PNG·WebP를 지원합니다. 한 장당 10MB, 3,200만 화소까지 받습니다. 파일 내용을 검사한 뒤 방향을 보정하고 긴 변 1,920픽셀 이하의 JPEG로 저장합니다. `post_photo.photo_url`에는 `uploads/파일명.jpg` 형태의 상대 경로를, `display_order`에는 선택 순서를 기록합니다. 게시물을 삭제하면 연결된 사진 파일, 사진 행, 댓글, 좋아요, 태그 연결도 정리됩니다.

기록을 옮길 때는 앱을 종료하고 `data/` 폴더 전체를 복사하세요. `FILMNOTE_DATA_DIR` 환경 변수로 저장 폴더를 바꿀 수 있습니다. 로그인은 현재 Streamlit 연결에서 유지되며 브라우저를 새로고침하면 다시 로그인합니다.

## 샘플 사진

원본 SQL에 파일명만 있는 게시물을 위해 내장 이미지 생성 도구로 예시 사진을 만들었습니다. 카페·경기장·음식을 담은 한 장의 콘택트 시트를 12장으로 나눠 `seed/photos/`에 저장했습니다.

<details><summary>생성 프롬프트</summary>

Use case: photorealistic-natural. A single photographic contact sheet for a Seoul photo diary, 2048 by 1536 landscape, exactly THREE equal columns and FOUR equal rows of rectangular landscape photographs, precisely aligned 3x4 grid filling entire canvas edge to edge, NO gutters, frames, spacers, words, watermarks, lettering or logo. All twelve photos individual realistic 35mm editorial travel snapshots in natural light, distinct subjects, vivid details, warm neutrals, lovely luminous green accents. Row 1 left to right: a golden pile of crisp croissants on a dark tray in a Seongsu bakery; a powdered-sugar pandoro pastry beside coffee on a wood table; sunny red-brick industrial Korean cafe courtyard with plants. Row 2: wide green soccer pitch in a packed modern Seoul football stadium at twilight; close view of the green corner flag and soccer ball at stadium; a creamy latte with rosetta latte art on an oak table. Row 3: Korean gochujang stir-fried pork and rice lunch with banchan; a steaming bowl of thick udon and scallions; morning light falling on a cafe window and round wooden chair. Row 4: overhead colorful Korean rice-and-side-dishes student lunch tray; flaky laminated pastries and a paper bread bag in a bakery display; wide editorial landscape photo of open silver laptop on the left and iced latte glass on the right on a walnut worktable in a bright, sun-drenched Seoul cafe, green trees visible through the window. Accurate 3 columns, 4 rows. Whole image forms a photographic contact sheet without text or borders.

</details>
