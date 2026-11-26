"""Filmnote's SQLite queries and local photo storage."""

from contextlib import contextmanager
from hashlib import pbkdf2_hmac, sha256
from io import BytesIO
from pathlib import Path
import hmac
import os
import re
import secrets
import shutil
import sqlite3
import uuid

from PIL import Image, ImageOps, UnidentifiedImageError


ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get("FILMNOTE_DATA_DIR", ROOT / "data")).resolve()
UPLOADS = DATA / "uploads"
DEMO_LOGIN = ("gachon_kim", "FilmnoteDemo1!")
MAX_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 32_000_000


@contextmanager
def connection(*, write=False):
    db = sqlite3.connect(DATA / "micro_sns.sqlite3", timeout=20)
    db.row_factory = sqlite3.Row
    try:
        db.execute("pragma foreign_keys=on")
        if write:
            db.execute("begin immediate")
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()


def run_sql(db, path):
    # Keep schema, sample data and the version marker in one transaction.
    statement = ""
    for line in path.read_text(encoding="utf-8").splitlines(True):
        statement += line
        if sqlite3.complete_statement(statement):
            db.execute(statement)
            statement = ""


def initialize():
    UPLOADS.mkdir(parents=True, exist_ok=True)
    with connection(write=True) as db:
        if db.execute("pragma user_version").fetchone()[0] == 0:
            run_sql(db, ROOT / "schema.sql")
            run_sql(db, ROOT / "seed" / "sample.sql")
            demo = UPLOADS / "demo"
            demo.mkdir(exist_ok=True)
            for row in db.execute("select photo_url from post_photo"):
                dest = photo_path(row["photo_url"])
                shutil.copyfile(ROOT / "seed" / "photos" / dest.name, dest)
            db.execute("update user set password_hash=? where username=?",
                       (hash_password(DEMO_LOGIN[1]), DEMO_LOGIN[0]))
            db.execute("pragma user_version=1")
        # Recover files left by a process interruption between disk and SQL commits.
        referenced = {r[0] for r in db.execute("select photo_url from post_photo")}
        for file in UPLOADS.glob("*.jpg"):
            if re.fullmatch(r"[0-9a-f]{32}\.jpg", file.name) and file.relative_to(DATA).as_posix() not in referenced:
                file.unlink(missing_ok=True)


def all_rows(sql, args=()):
    with connection() as db:
        return db.execute(sql, args).fetchall()


def execute(sql, args=()):
    with connection(write=True) as db:
        return db.execute(sql, args).rowcount


def clean(value, limit, label, required=True):
    value = value.strip()
    if required and not value:
        raise ValueError(f"{label} 내용을 입력해 주세요.")
    if len(value) > limit:
        raise ValueError(f"{label} 항목은 {limit}자까지 입력할 수 있어요.")
    return value


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = pbkdf2_hmac("sha256", password.encode(), salt, 600_000)
    return f"pbkdf2_sha256$600000${salt.hex()}${digest.hex()}"


def verify_password(password, encoded):
    if not encoded.startswith("pbkdf2_sha256$"):
        return False
    _, rounds, salt, digest = encoded.split("$")
    actual = pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds))
    return hmac.compare_digest(actual.hex(), digest)


def validate_password(password):
    if not 8 <= len(password) <= 128:
        raise ValueError("비밀번호는 8~128자로 입력해 주세요.")


def register(username, email, password, name):
    username = username.strip().lower()
    email = clean(email, 100, "이메일").lower()
    name = clean(name, 50, "이름")
    if not re.fullmatch(r"[a-z0-9_.]{3,50}", username):
        raise ValueError("아이디는 영문 소문자, 숫자, 점, 밑줄로 3~50자를 입력해 주세요.")
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise ValueError("이메일 주소를 확인해 주세요.")
    validate_password(password)
    try:
        execute("""insert into user(username,email,password_hash,name,bio,created_at)
                   values(?,?,?,?, '',CURRENT_TIMESTAMP)""", (username, email, hash_password(password), name))
    except sqlite3.IntegrityError as exc:
        raise ValueError("이미 사용 중인 아이디 또는 이메일이에요.") from exc


def token_hash(token):
    return sha256(token.encode()).hexdigest()


def login(username, password):
    with connection(write=True) as db:
        user = db.execute("select * from user where username=?", (username.strip(),)).fetchone()
        if not user or not verify_password(password, user["password_hash"]):
            raise ValueError("아이디와 비밀번호를 확인해 주세요.")
        token = secrets.token_urlsafe(32)
        db.execute("""insert into session(user_id,token_hash,created_at,expires_at)
                      values(?,?,CURRENT_TIMESTAMP,datetime('now','+1 day'))""",
                   (user["user_id"], token_hash(token)))
        return token


def current_user(token):
    if not token:
        return None
    rows = all_rows("""select u.user_id,u.name,u.username,u.bio from session s join user u using(user_id)
                       where token_hash=? and revoked_at is null and expires_at>CURRENT_TIMESTAMP""",
                    (token_hash(token),))
    return rows[0] if rows else None


def logout(token):
    execute("update session set revoked_at=CURRENT_TIMESTAMP where token_hash=?", (token_hash(token),))


def edit_profile(uid, name, bio):
    execute("update user set name=?,bio=? where user_id=?",
            (clean(name, 50, "이름"), clean(bio, 200, "소개", False), uid))


def change_password(uid, old_password, new_password):
    validate_password(new_password)
    with connection(write=True) as db:
        saved = db.execute("select password_hash from user where user_id=?", (uid,)).fetchone()[0]
        if not verify_password(old_password, saved):
            raise ValueError("현재 비밀번호가 일치하지 않아요.")
        db.execute("update user set password_hash=? where user_id=?", (hash_password(new_password), uid))
        db.execute("update session set revoked_at=CURRENT_TIMESTAMP where user_id=? and revoked_at is null", (uid,))


def parse_tags(text):
    result = []
    for word in re.split(r"[\s,#]+", text.strip()):
        if not word:
            continue
        if not re.fullmatch(r"[\w]{1,49}", word):
            raise ValueError("태그에는 한글, 영문, 숫자, 밑줄을 49자까지 사용할 수 있어요.")
        tag = "#" + word.lower()
        if tag not in result:
            result.append(tag)
    return result


def set_tags(db, pid, tags):
    db.execute("delete from post_hashtag where post_id=?", (pid,))
    for tag in tags:
        db.execute("insert or ignore into hashtag(tag_name) values(?)", (tag,))
        db.execute("""insert into post_hashtag(post_id,tag_id)
                      select ?,tag_id from hashtag where tag_name=?""", (pid, tag))


def photo_path(relative):
    path = (DATA / relative).resolve()
    if not path.is_relative_to(UPLOADS) or path == UPLOADS:
        raise ValueError("잘못된 사진 경로예요.")
    return path


def prepare_photo(raw, max_edge=1920):
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError("각 사진은 10MB 이하로 선택해 주세요.")
    try:
        with Image.open(BytesIO(raw)) as im:
            if im.format not in {"JPEG", "PNG", "WEBP"}:
                raise ValueError("JPG, PNG, WebP 사진을 선택해 주세요.")
            if im.width * im.height > MAX_PIXELS:
                raise ValueError("사진은 3,200만 화소 이하로 선택해 주세요.")
            im = ImageOps.exif_transpose(im)
            im.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
            rgba = im.convert("RGBA")
            rgb = Image.new("RGB", rgba.size, "white")
            rgb.paste(rgba, mask=rgba.getchannel("A"))
            output = BytesIO()
            rgb.save(output, format="JPEG", quality=88, optimize=True)
            return output.getvalue()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("사진을 읽을 수 없어요. 다른 이미지로 시도해 주세요.") from exc


def create_post(uid, content, place_id, tag_text, files):
    content = clean(content, 500, "본문")
    tags = parse_tags(tag_text)
    if not 1 <= len(files) <= 10:
        raise ValueError("사진을 1~10장 선택해 주세요.")
    images = [prepare_photo(file) for file in files]
    created = []
    try:
        with connection(write=True) as db:
            pid = db.execute("""insert into post(user_id,place_id,content,created_at)
                                values(?,?,?,CURRENT_TIMESTAMP)""", (uid, place_id, content)).lastrowid
            for order, data in enumerate(images, start=1):
                relative = f"uploads/{uuid.uuid4().hex}.jpg"
                path = photo_path(relative)
                with path.open("xb") as out:
                    created.append(path)
                    out.write(data)
                db.execute("insert into post_photo(post_id,photo_url,display_order) values(?,?,?)",
                           (pid, relative, order))
            set_tags(db, pid, tags)
        return pid
    except BaseException:
        for file in created:
            file.unlink(missing_ok=True)
        raise


def edit_post(uid, pid, content, place_id, tag_text):
    tags = parse_tags(tag_text)
    with connection(write=True) as db:
        changed = db.execute("update post set content=?,place_id=? where post_id=? and user_id=?",
                             (clean(content, 500, "본문"), place_id, pid, uid)).rowcount
        if not changed:
            raise ValueError("이 게시물을 수정할 수 없어요.")
        set_tags(db, pid, tags)


def delete_post(uid, pid):
    with connection(write=True) as db:
        paths = [photo_path(row[0]) for row in db.execute(
            "select photo_url from post_photo where post_id=?", (pid,))]
        if not db.execute("delete from post where post_id=? and user_id=?", (pid, uid)).rowcount:
            raise ValueError("이 게시물을 삭제할 수 없어요.")
    for path in paths:
        path.unlink(missing_ok=True)


def feed(viewer=0, *, mode="all", author=None, post=None, term="", tag="", place=None, limit=12, offset=0):
    where, params = ["1=1"], [viewer]
    if author is not None:
        where.append("p.user_id=?")
        params.append(author)
    if post is not None:
        where.append("p.post_id=?")
        params.append(post)
    if place is not None:
        where.append("p.place_id=?")
        params.append(place)
    if mode == "following":
        where.append("p.user_id in (select following_id from follow where follower_id=?)")
        params.append(viewer)
    if mode == "liked":
        where.append("p.post_id in (select post_id from likes where user_id=?)")
        params.append(viewer)
    if mode == "album":
        where.append("(select count(*) from post_photo x where x.post_id=p.post_id)>=2")
    if tag:
        where.append("""exists (select 1 from post_hashtag ph join hashtag h using(tag_id)
                        where ph.post_id=p.post_id and h.tag_name=?)""")
        params.append(tag)
    if term.strip():
        where.append("""(instr(lower(p.content || ' ' || u.username || ' ' || u.name || ' ' ||
                        coalesce(pl.place_name,'')),lower(?))>0 or exists (
                        select 1 from post_hashtag ph join hashtag h using(tag_id)
                        where ph.post_id=p.post_id and instr(lower(h.tag_name),lower(?))>0))""")
        params.extend([term.strip()] * 2)
    order = "like_count desc, p.post_id desc" if mode == "popular" else "p.post_id desc"
    return all_rows(f"""select p.*,u.username,u.name,pl.place_name,pl.category,
               (select count(*) from likes l where l.post_id=p.post_id) as like_count,
               exists(select 1 from likes l where l.post_id=p.post_id and l.user_id=?) as liked,
               (select count(*) from comment c where c.post_id=p.post_id) as comment_count,
               (select photo_url from post_photo f where f.post_id=p.post_id
                order by display_order limit 1) as cover,
               (select group_concat(h.tag_name,' ') from post_hashtag ph join hashtag h using(tag_id)
                where ph.post_id=p.post_id) as tags
             from post p join user u using(user_id) left join place pl using(place_id)
             where {' and '.join(where)} order by {order} limit ? offset ?""", (*params, limit, offset))


def photos(pid):
    return all_rows("select photo_url from post_photo where post_id=? order by display_order", (pid,))


def comments(pid):
    return all_rows("""select c.*,u.username from comment c join user u using(user_id)
                       where post_id=? order by c.comment_id""", (pid,))


def add_comment(uid, pid, message):
    execute("insert into comment(user_id,post_id,content,created_at) values(?,?,?,CURRENT_TIMESTAMP)",
            (uid, pid, clean(message, 300, "댓글")))


def remove_comment(uid, cid):
    execute("delete from comment where comment_id=? and user_id=?", (cid, uid))


def like(uid, pid, enabled):
    if enabled:
        execute("insert or ignore into likes(user_id,post_id,created_at) values(?,?,CURRENT_TIMESTAMP)", (uid, pid))
    else:
        execute("delete from likes where user_id=? and post_id=?", (uid, pid))


def follow(uid, other, enabled):
    if uid == other:
        raise ValueError("본인을 팔로우할 수 없어요.")
    if enabled:
        execute("insert or ignore into follow(follower_id,following_id,created_at) values(?,?,CURRENT_TIMESTAMP)", (uid, other))
    else:
        execute("delete from follow where follower_id=? and following_id=?", (uid, other))


def profile(uid, viewer):
    rows = all_rows("""select user_id,name,username,bio,
            (select count(*) from post where user_id=u.user_id) as posts,
            (select count(*) from follow where following_id=u.user_id) as followers,
            (select count(*) from follow where follower_id=u.user_id) as following,
            exists(select 1 from follow where following_id=u.user_id and follower_id=?) as subscribed
            from user u where user_id=?""", (viewer, uid))
    return rows[0] if rows else None


def contacts(uid, incoming):
    if incoming:
        return all_rows("""select u.user_id,u.name,u.username from follow f join user u
                           on u.user_id=f.follower_id where f.following_id=? order by u.username""", (uid,))
    return all_rows("""select u.user_id,u.name,u.username from follow f join user u
                       on u.user_id=f.following_id where f.follower_id=? order by u.username""", (uid,))


def places():
    return all_rows("""select pl.*,count(p.post_id) as posts from place pl left join post p using(place_id)
                       group by pl.place_id order by posts desc,pl.place_id""")


def trending_tags():
    return all_rows("""select h.tag_name,count(*) as posts from post_hashtag ph join hashtag h using(tag_id)
                       group by h.tag_id order by posts desc,h.tag_id limit 8""")
