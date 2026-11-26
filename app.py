from datetime import datetime, timedelta, timezone
from html import escape
import sqlite3

import streamlit as st

import db


st.set_page_config(page_title="Filmnote · 포토 다이어리", page_icon="📷", layout="wide")
st.html("<style>" + (db.ROOT / "style.css").read_text(encoding="utf-8") + "</style>")


@st.cache_resource
def start_database():
    db.initialize()
    return True


start_database()
s = st.session_state
s.setdefault("page", "feed")
me = db.current_user(s.get("token"))
uid = me["user_id"] if me else 0
KST = timezone(timedelta(hours=9))
PALETTE = [("#efdbb2", "#66451b"), ("#e0e9d1", "#375136"), ("#e9deda", "#643b39"),
           ("#dbe5ee", "#364b61"), ("#e7deee", "#584567")]


def go(page, **state):
    s.update(state)
    s.page = page
    st.rerun()


def notify(message):
    s.notice = message
    st.rerun()


def ask_login(after=None):
    go("auth", after_login=after or s.page)


def perform(action, *args):
    try:
        return True, action(*args)
    except ValueError as error:
        st.error(str(error))
    except sqlite3.IntegrityError:
        st.error("대상 정보가 변경됐어요. 화면을 새로 열어 주세요.")
    except (sqlite3.OperationalError, OSError):
        st.error("저장소를 사용할 수 없어요. 폴더 권한과 남은 공간을 확인한 후 다시 시도해 주세요.")
    return False, None


def title(text, aside=""):
    st.html(f'<div class="titleline"><h1>{escape(text)}</h1><span class="date">{escape(aside)}</span></div>')


def empty(text):
    st.html(f'<div class="empty">{escape(text)}</div>')


def section(text):
    st.html(f'<h2 class="paneltitle">{escape(text)}</h2>')


def small(text):
    st.html(f'<div class="tiny">{escape(text)}</div>')


def avatar(user, large=False):
    bg, fg = PALETTE[(user["user_id"] - 1) % len(PALETTE)]
    size = " large" if large else ""
    return f'<span class="avatar{size}" aria-hidden="true" style="background:{bg};color:{fg}">{escape(user["name"][:1])}</span>'


def show_photo(path, *, width="stretch"):
    if path and db.photo_path(path).is_file():
        st.image(str(db.photo_path(path)), width=width)
    elif path:
        empty("사진 파일을 찾을 수 없어요.")


def show_post(pid):
    go("detail", post_id=pid, return_page=s.page)


def open_profile(other):
    go("profile", profile_id=other)


def explore(*, tag=None, place=None):
    s["search_text"] = ""
    s["search_tag"] = tag or "전체 태그"
    s["search_place"] = place
    s["search_mode"] = "최신순"
    go("explore")


def masthead():
    with st.container(key="mast"):
        logo, home, find, account, publish = st.columns([4.2, 1.1, 1.1, 1.55, 1.6], vertical_alignment="center")
        logo.html('<div class="brand"><i class="camera" aria-hidden="true"></i><b>Filmnote.</b></div>')
        for col, label, icon, page in [(home, "피드", "home", "feed"), (find, "탐색", "search", "explore")]:
            active = "active_nav" if s.page == page else "nav"
            if col.button(label, icon=f":material/{icon}:", key=active + page, type="tertiary", width="stretch"):
                go(page)
        if account.button("내 프로필" if me else "로그인", icon=":material/account_circle:",
                          type="tertiary", width="stretch", key="nav_account"):
            if me:
                open_profile(uid)
            ask_login("feed")
        if publish.button("새 게시물", icon=":material/add:", type="primary", width="stretch", key="nav_write"):
            if not me:
                ask_login("compose")
            go("compose")


def discussion(pid):
    entries = db.comments(pid)
    if not entries:
        small("첫 댓글을 남겨 보세요.")
    for row in entries:
        st.html(f'<div class="caption"><b>{escape(row["username"])}</b> &nbsp;{escape(row["content"])}</div>')
        if me and row["user_id"] == uid:
            if st.button("내 댓글 삭제", key=f"rmcomment_{row['comment_id']}", type="tertiary"):
                if perform(db.remove_comment, uid, row["comment_id"])[0]:
                    notify("댓글을 삭제했어요.")
    if me:
        with st.form(f"comment_form_{pid}", clear_on_submit=True):
            message = st.text_input("댓글", max_chars=300, placeholder="댓글을 남겨 보세요", key=f"message_{pid}")
            sent = st.form_submit_button("댓글 등록")
        if sent and perform(db.add_comment, uid, pid, message)[0]:
            notify("댓글을 등록했어요.")
    elif st.button("로그인하고 댓글 쓰기", key=f"logincomment_{pid}"):
        ask_login()


def post_card(row):
    pid = row["post_id"]
    with st.container(key=f"card_{pid}", gap="small"):
        posted = datetime.fromisoformat(row["created_at"]).replace(tzinfo=timezone.utc).astimezone(KST)
        location = escape(row["place_name"] or "장소 미지정")
        st.html(f'<div class="author">{avatar(row)}<div class="byline"><strong>{escape(row["username"])}</strong>'
                f'<span>{location}</span></div><span class="meta">{posted:%m.%d · %H:%M}</span></div>')
        pictures = db.photos(pid)
        if pictures:
            pos_key = f"photo_pos_{pid}"
            pos = s.get(pos_key, 0) % len(pictures)
            show_photo(pictures[pos]["photo_url"])
            if len(pictures) > 1:
                with st.container(horizontal=True, horizontal_alignment="center", vertical_alignment="center"):
                    if st.button("이전", key=f"prev_{pid}", icon=":material/chevron_left:", type="tertiary"):
                        s[pos_key] = (pos - 1) % len(pictures)
                        st.rerun()
                    small(f"{pos+1} / {len(pictures)}")
                    if st.button("다음", key=f"next_{pid}", icon=":material/chevron_right:", type="tertiary"):
                        s[pos_key] = (pos + 1) % len(pictures)
                        st.rerun()
        with st.container(horizontal=True, key=f"actions_{pid}", vertical_alignment="center"):
            heart = "♥" if row["liked"] else "♡"
            if st.button(f"{heart} {row['like_count']}", help="좋아요 취소" if row["liked"] else "좋아요",
                         key=f"like_{pid}", type="tertiary"):
                if not me:
                    ask_login()
                if perform(db.like, uid, pid, not row["liked"])[0]:
                    st.rerun()
            if st.button(f"댓글 {row['comment_count']}", key=f"comments_{pid}", icon=":material/chat_bubble_outline:", type="tertiary"):
                s[f"thread_{pid}"] = not s.get(f"thread_{pid}", False)
                st.rerun()
            if st.button("프로필", key=f"author_{pid}", type="tertiary", icon=":material/person_outline:"):
                open_profile(row["user_id"])
            if uid == row["user_id"] and st.button("편집", key=f"edit_{pid}", type="tertiary", icon=":material/edit:"):
                go("edit", post_id=pid)
        st.html(f'<div class="caption">{escape(row["content"])}</div>')
        if row["tags"]:
            st.html(f'<div class="tagline">{escape(row["tags"])}</div>')
        if s.get(f"thread_{pid}"):
            st.divider()
            discussion(pid)


def rail():
    with st.container(key="rail"):
        with st.container(key="side_popular"):
            section("인기 게시물")
            for row in db.feed(mode="popular", limit=3):
                with st.container(key=f"hot_{row['post_id']}"):
                    pic, text = st.columns([1, 2.7], gap="small", vertical_alignment="center")
                    with pic:
                        if row["cover"]:
                            show_photo(row["cover"])
                        else:
                            st.html(avatar(row))
                    with text:
                        label = row["content"][:24] + ("…" if len(row["content"]) > 24 else "")
                        if st.button(label, key=f"hot_open_{row['post_id']}", type="tertiary"):
                            show_post(row["post_id"])
                        small(f"♡ {row['like_count']}  ·  {row['username']}")
        with st.container(key="side_places"):
            section("많이 기록된 장소")
            for place in db.places()[:3]:
                if st.button(f"{place['place_name']} · {place['posts']}개", icon=":material/location_on:",
                             key=f"place_{place['place_id']}", type="tertiary"):
                    explore(place=place["place_id"])
        with st.container(key="side_tags"):
            section("인기 태그")
            with st.container(horizontal=True, gap="small"):
                for tag in db.trending_tags()[:5]:
                    if st.button(tag["tag_name"], key="rail_" + tag["tag_name"]):
                        explore(tag=tag["tag_name"])


def page_of_posts(grid=False, **filters):
    signature = (s.page, uid, tuple(filters.items()))
    if s.get("list_signature") != signature:
        s.list_signature = signature
        s.list_limit = 6
    rows = db.feed(uid, **filters, limit=s.list_limit + 1)
    visible = rows[:s.list_limit]
    if not rows:
        empty("아직 표시할 게시물이 없어요.")
    if grid:
        for start in range(0, len(visible), 3):
            for col, item in zip(st.columns(3), visible[start:start+3]):
                with col, st.container(key=f"tile_{item['post_id']}", gap="small"):
                    if item["cover"]:
                        show_photo(item["cover"])
                    else:
                        small("텍스트 게시물")
                    if st.button(item["content"], key=f"open_{item['post_id']}", type="tertiary"):
                        show_post(item["post_id"])
                    small(f"@{item['username']}  ·  ♡ {item['like_count']}")
    else:
        for item in visible:
            post_card(item)
    if len(rows) > s.list_limit and st.button("게시물 더 보기", width="stretch"):
        s.list_limit += 6
        st.rerun()


def home_page():
    now = datetime.now(KST)
    title("오늘의 피드", f"{now:%Y. %m. %d} · {'월화수목금토일'[now.weekday()]}요일")
    main, side = st.columns([2.15, 1], gap="large")
    with main:
        choice = st.pills("피드 선택", ["전체", "팔로잉", "좋아요"], default="전체",
                          label_visibility="collapsed", key="feed_mode") or "전체"
        if choice != "전체" and not me:
            empty("로그인하면 내 " + choice + " 피드를 볼 수 있어요.")
            if st.button("로그인하기", key="login_filter"):
                ask_login("feed")
        else:
            page_of_posts(mode={"전체": "all", "팔로잉": "following", "좋아요": "liked"}[choice])
    with side:
        rail()


def explore_page():
    title("탐색")
    term = st.text_input("검색", key="search_text", placeholder="본문, 계정, 장소 또는 해시태그 검색")
    c1, c2, c3 = st.columns(3)
    tags = ["전체 태그"] + [r[0] for r in db.all_rows(
        "select distinct h.tag_name from hashtag h join post_hashtag ph using(tag_id) order by h.tag_name")]
    locs = {p["place_id"]: p["place_name"] for p in db.places()}
    if s.get("search_tag") not in tags:
        s.search_tag = tags[0]
    tag = c1.selectbox("해시태그", tags, key="search_tag")
    place = c2.selectbox("장소", [None, *locs], format_func=lambda key: locs.get(key, "전체 장소"), key="search_place")
    sort = c3.selectbox("보기 방식", ["최신순", "인기순", "사진 2장 이상"], key="search_mode")
    page_of_posts(True, term=term, tag="" if tag == tags[0] else tag, place=place,
                  mode={"최신순": "all", "인기순": "popular", "사진 2장 이상": "album"}[sort])


def enter(token):
    s.token = token
    s.notice = "로그인했어요."
    go(s.pop("after_login", "feed"))


def auth_page():
    with st.container(key="account_box"):
        title("계정")
        mode = st.segmented_control("계정 메뉴", ["로그인", "회원가입"], default="로그인",
                                    label_visibility="collapsed") or "로그인"
        if mode == "로그인":
            with st.form("login"):
                username = st.text_input("아이디", max_chars=50)
                password = st.text_input("비밀번호", type="password", max_chars=128)
                submit = st.form_submit_button("로그인", type="primary", width="stretch")
            if submit:
                ok, token = perform(db.login, username, password)
                if ok:
                    enter(token)
            st.divider()
            small("공용 체험 계정으로 샘플 피드에 사진과 댓글을 남길 수 있어요.")
            if st.button("체험 계정으로 시작", icon=":material/photo_camera:", width="stretch"):
                ok, token = perform(db.login, *db.DEMO_LOGIN)
                if ok:
                    enter(token)
        else:
            with st.form("join"):
                name = st.text_input("이름", max_chars=50)
                username = st.text_input("아이디", placeholder="영문 소문자, 숫자, 점, 밑줄", max_chars=50)
                email = st.text_input("이메일", max_chars=100)
                password = st.text_input("비밀번호", placeholder="8자 이상", type="password", max_chars=128)
                submit = st.form_submit_button("가입하고 시작", type="primary", width="stretch")
            if submit and perform(db.register, username, email, password, name)[0]:
                ok, token = perform(db.login, username, password)
                if ok:
                    enter(token)


def editor(editing):
    if not me:
        ask_login("edit" if editing else "compose")
    row = None
    if editing:
        rows = db.feed(uid, post=s.post_id, author=uid)
        if not rows:
            empty("편집할 수 있는 게시물이 없어요.")
            return
        row = rows[0]
    with st.container(key="editor_box"):
        title("게시물 편집" if editing else "새 게시물")
        files = []
        if not editing:
            files = st.file_uploader("사진 선택", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True,
                                     key="upload", help="1~10장 · 장당 10MB 이하 · 선택한 순서대로 표시됩니다.")
            small("사진 1~10장 · JPG, PNG, WebP · 장당 최대 10MB")
            if len(files) > 10:
                st.error("사진은 10장까지 선택할 수 있어요. 목록에서 사진을 줄여 주세요.")
                return
            if files:
                with st.expander(f"업로드 순서 · {len(files)}장", expanded=True):
                    for start in range(0, len(files), 3):
                        batch = files[start:start + 3]
                        for i, (col, file) in enumerate(zip(st.columns(3), batch), start=start + 1):
                            ok, preview = perform(db.prepare_photo, file.getvalue(), 260)
                            if not ok:
                                return
                            col.image(preview, caption=f"{i}. {file.name}", width="stretch")
        locs = {p["place_id"]: p["place_name"] for p in db.places()}
        ids = [None, *locs]
        with st.form("post_edit" if editing else "post_new"):
            content = st.text_area("본문", value=row["content"] if row else "", max_chars=500,
                                   placeholder="이 순간을 기록해 보세요.")
            place = st.selectbox("장소", ids, index=ids.index(row["place_id"]) if row else 0,
                                 format_func=lambda key: locs.get(key, "장소 선택 안 함"))
            tags = st.text_input("해시태그", value=(row["tags"] or "") if row else "", placeholder="#일상 #성수카페")
            saved = st.form_submit_button("변경 저장" if editing else "게시하기", type="primary", width="stretch")
        if saved:
            if editing:
                ok, _ = perform(db.edit_post, uid, row["post_id"], content, place, tags)
                pid = row["post_id"]
            else:
                ok, pid = perform(db.create_post, uid, content, place, tags, [f.getvalue() for f in files])
            if ok:
                s.notice = "게시물을 저장했어요."
                go("detail", post_id=pid, return_page="feed")
        if editing:
            with st.expander("게시물 삭제"):
                st.caption("이 게시물의 사진, 댓글, 좋아요가 함께 삭제됩니다.")
                confirm = st.checkbox("삭제를 확인합니다", key=f"confirm_{row['post_id']}")
                if st.button("이 게시물 삭제", disabled=not confirm):
                    if perform(db.delete_post, uid, row["post_id"])[0]:
                        s.notice = "게시물을 삭제했어요."
                        go("feed")


def profile_page():
    other = s.get("profile_id", uid)
    person = db.profile(other, uid)
    if not person:
        empty("계정을 찾을 수 없어요.")
        return
    title("프로필")
    with st.container(key="profile_box"):
        st.html(f'<div class="author">{avatar(person, True)}<div class="byline"><strong>{escape(person["name"])}</strong>'
                f'<span>@{escape(person["username"])}</span></div></div>')
        if person["bio"]:
            st.html(f'<p class="userbio">{escape(person["bio"])}</p>')
        st.html(f'<div class="statrow"><span><b>{person["posts"]}</b>게시물</span>'
                f'<span><b>{person["followers"]}</b>팔로워</span><span><b>{person["following"]}</b>팔로잉</span></div>')
        if uid != other:
            if st.button("언팔로우" if person["subscribed"] else "팔로우", type="primary"):
                if not me:
                    ask_login()
                if perform(db.follow, uid, other, not person["subscribed"])[0]:
                    st.rerun()
        else:
            with st.expander("계정 설정"):
                with st.form("edit_profile"):
                    name = st.text_input("이름", person["name"], max_chars=50)
                    bio = st.text_area("소개", person["bio"] or "", max_chars=200)
                    saved = st.form_submit_button("프로필 저장")
                if saved and perform(db.edit_profile, uid, name, bio)[0]:
                    notify("프로필을 저장했어요.")
                if me["username"] != db.DEMO_LOGIN[0]:
                    with st.form("change_password"):
                        old = st.text_input("현재 비밀번호", type="password", max_chars=128)
                        new = st.text_input("새 비밀번호", type="password", max_chars=128)
                        changed = st.form_submit_button("비밀번호 변경")
                    if changed and perform(db.change_password, uid, old, new)[0]:
                        s.clear()
                        go("auth", notice="비밀번호를 변경했어요. 다시 로그인해 주세요.")
                if st.button("로그아웃"):
                    db.logout(s.token)
                    s.clear()
                    go("feed", notice="로그아웃했어요.")
    view = st.pills("프로필 보기", ["게시물", "팔로워", "팔로잉"], default="게시물",
                    key=f"profile_view_{other}", label_visibility="collapsed") or "게시물"
    if view == "게시물":
        page_of_posts(True, author=other)
    else:
        people = db.contacts(other, view == "팔로워")
        if not people:
            empty("아직 목록에 표시할 계정이 없어요.")
        for user in people:
            if st.button(f"{user['name']}  ·  @{user['username']}", key=f"contact_{user['user_id']}"):
                open_profile(user["user_id"])


masthead()
if notice := s.pop("notice", None):
    st.toast(notice)
if s.page == "feed":
    home_page()
elif s.page == "explore":
    explore_page()
elif s.page == "auth":
    auth_page()
elif s.page in ("compose", "edit"):
    editor(s.page == "edit")
elif s.page == "profile":
    profile_page()
elif s.page == "detail":
    if st.button("목록으로", icon=":material/arrow_back:", type="tertiary"):
        go(s.get("return_page", "feed"))
    rows = db.feed(uid, post=s.post_id)
    if rows:
        with st.container(width=710):
            post_card(rows[0])
    else:
        empty("삭제된 게시물이에요.")
