import datetime
from fasthtml.common import *
from auth import hash_password, verify_password
from fastlite import NotFoundError
from models import users
from logger import logger

login_redir = RedirectResponse('/login', status_code=303)

custom_css = Style("""
    body { font-family: system-ui, sans-serif; }
    .user-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.85rem 1rem;
        border: 1px solid var(--pico-muted-border-color);
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }
    .user-info { display: flex; flex-direction: column; gap: 0.2rem; }
    .user-meta { font-size: 0.82rem; color: var(--pico-muted-color); }
    .badge {
        display: inline-block;
        padding: 0.15rem 0.45rem;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: bold;
        margin-left: 0.4rem;
    }
    .badge-admin { background: #e67e22; color: white; }
    .badge-archived { background: #95a5a6; color: white; }
    .action-btn {
        padding: 0.4rem 0.9rem;
        font-size: 0.85rem;
        border-radius: 6px;
        cursor: pointer;
        border: none;
        color: white;
    }
    .btn-archive { background: #e74c3c; }
    .btn-unarchive { background: #27ae60; }
    .btn-create { background: #2980b9; }
    .search-row { display: flex; gap: 1rem; align-items: center; margin-bottom: 1.2rem; }
    .search-row input { flex: 1; margin: 0; }
    #user-list { min-height: 3rem; }
    .empty-state { color: var(--pico-muted-color); padding: 1rem 0; }
    .error-msg { color: #e74c3c; margin-bottom: 0.5rem; font-size: 0.9rem; }
    .auth-card { max-width: 420px; margin: 4rem auto; }
    .auth-footer { text-align: center; margin-top: 1rem; font-size: 0.9rem; }
    .page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; }
""")


def before(req, sess):
    auth = req.scope['auth'] = sess.get('auth', None)
    if not auth:
        return login_redir


bware = Beforeware(before, skip=['/login', '/register'])

app = FastHTML(
    before=bware,
    hdrs=(
        Link(rel='stylesheet', href='https://unpkg.com/@picocss/pico@2/css/pico.min.css'),
        custom_css,
    ),
)


# ── Shared components ──────────────────────────────────────────────────────────

def navbar(auth):
    return Nav(
        Ul(Li(Strong('User Account Manager'))),
        Ul(
            Li(A('Active Users', href='/')),
            Li(A('Archived', href='/archived')),
            Li(A(f'Logout ({auth})', href='/logout')),
        ),
    )


def user_row(user, action='archive'):
    badges = []
    if user.is_admin:
        badges.append(Span('admin', cls='badge badge-admin'))
    if action == 'unarchive':
        badges.append(Span('archived', cls='badge badge-archived'))

    action_form = Form(
        Button(
            'Archive' if action == 'archive' else 'Unarchive',
            cls=f'action-btn btn-{action}',
            type='submit',
        ),
        method='post',
        action=f'/archive/{user.username}' if action == 'archive' else f'/unarchive/{user.username}',
    )

    return Div(
        Div(
            Div(Strong(user.username), *badges),
            Div(user.email, cls='user-meta'),
            Div(f'Created: {user.created_at}', cls='user-meta'),
            cls='user-info',
        ),
        action_form,
        cls='user-row',
        id=f'user-{user.username}',
    )


# ── Auth routes ────────────────────────────────────────────────────────────────

@app.get('/login')
def login_get(error: str = ''):
    messages = {
        'invalid': 'Invalid username or password.',
        'archived': 'This account has been archived.',
    }
    error_msg = P(messages[error], cls='error-msg') if error in messages else ''

    form = Form(
        error_msg,
        Label('Username', Input(name='username', placeholder='Enter username', required=True)),
        Label('Password', Input(name='pwd', type='password', placeholder='Enter password', required=True)),
        Button('Login', type='submit', style='width:100%; margin-top:0.5rem;'),
        method='post',
        action='/login',
    )
    return (
        Title('Login – User Account Manager'),
        Main(
            Article(
                H2('Sign In'),
                form,
                P(A('Create an account', href='/register'), cls='auth-footer'),
                cls='auth-card',
            ),
            cls='container',
        ),
    )


@app.post('/login')
def login_post(username: str, pwd: str, sess):
    logger.info(f'Login attempt: {username}')
    try:
        user = users[username]
        if user.archived:
            logger.warning(f'Archived user attempted login: {username}')
            return RedirectResponse('/login?error=archived', status_code=303)
        if verify_password(pwd, user.pwd):
            sess['auth'] = username
            logger.info(f'Successful login: {username}')
            return RedirectResponse('/', status_code=303)
    except NotFoundError:
        logger.warning(f'Login failed – user not found: {username}')
    except Exception as e:
        logger.error(f'Login error for {username}: {e}')
    return RedirectResponse('/login?error=invalid', status_code=303)


@app.get('/register')
def register_get(error: str = ''):
    error_msg = P('Username already taken.', cls='error-msg') if error == 'exists' else ''

    form = Form(
        error_msg,
        Label('Username', Input(name='username', placeholder='Choose a username', required=True)),
        Label('Email', Input(name='email', type='email', placeholder='Enter your email', required=True)),
        Label('Password', Input(name='pwd', type='password', placeholder='Choose a password', required=True)),
        Button('Create Account', type='submit', style='width:100%; margin-top:0.5rem;'),
        method='post',
        action='/register',
    )
    return (
        Title('Register – User Account Manager'),
        Main(
            Article(
                H2('Create Account'),
                form,
                P(A('Back to login', href='/login'), cls='auth-footer'),
                cls='auth-card',
            ),
            cls='container',
        ),
    )


@app.post('/register')
def register_post(username: str, email: str, pwd: str, sess):
    logger.info(f'Registration attempt: {username}')
    try:
        users[username]
        logger.warning(f'Registration failed – username taken: {username}')
        return RedirectResponse('/register?error=exists', status_code=303)
    except NotFoundError:
        pass

    is_first = len(list(users())) == 0
    users.insert(dict(
        username=username,
        email=email,
        pwd=hash_password(pwd),
        is_admin=is_first,
        archived=False,
        created_at=datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
    ))
    logger.info(f'New user registered: {username} (admin={is_first})')
    sess['auth'] = username
    return RedirectResponse('/', status_code=303)


@app.get('/logout')
def logout(auth, sess):
    logger.info(f'User logged out: {auth}')
    del sess['auth']
    return login_redir


# ── Dashboard ──────────────────────────────────────────────────────────────────

@app.get('/')
def index(auth):
    active = [u for u in users() if not u.archived]
    rows = [user_row(u) for u in active] or [P('No active users.', cls='empty-state')]

    search = Input(
        name='q',
        placeholder='Search by username or email…',
        hx_post='/search',
        hx_trigger='keyup changed delay:300ms',
        hx_target='#user-list',
        hx_swap='innerHTML',
    )
    create_btn = A(
        Button('+ Create User', cls='action-btn btn-create', type='button'),
        href='/create',
    )

    return (
        Title('Active Users – User Account Manager'),
        navbar(auth),
        Main(
            Div(H2('Active Users'), create_btn, cls='page-header'),
            Div(search, cls='search-row'),
            Div(*rows, id='user-list'),
            cls='container',
        ),
    )


@app.post('/search')
def search(q: str = ''):
    term = q.strip().lower()
    active = [u for u in users() if not u.archived]
    if term:
        active = [u for u in active if term in u.username.lower() or term in u.email.lower()]
    if not active:
        return P('No users found.', cls='empty-state')
    return tuple(user_row(u) for u in active)


# ── Create user ────────────────────────────────────────────────────────────────

@app.get('/create')
def create_get(auth, error: str = ''):
    error_msg = P('Username already taken.', cls='error-msg') if error == 'exists' else ''

    form = Form(
        error_msg,
        Label('Username', Input(name='username', placeholder='Enter username', required=True)),
        Label('Email', Input(name='email', type='email', placeholder='Enter email', required=True)),
        Label('Password', Input(name='pwd', type='password', placeholder='Set initial password', required=True)),
        Label(
            Input(type='checkbox', name='is_admin', value='on'),
            ' Grant admin privileges',
            style='display:flex; align-items:center; gap:0.5rem;',
        ),
        Button('Create Account', type='submit', style='width:100%; margin-top:0.5rem;'),
        method='post',
        action='/create',
    )
    return (
        Title('Create User – User Account Manager'),
        navbar(auth),
        Main(
            H2('Create New User'),
            Article(form, style='max-width:480px;'),
            cls='container',
        ),
    )


@app.post('/create')
def create_post(username: str, email: str, pwd: str, auth, is_admin: str = ''):
    logger.info(f"Admin '{auth}' creating user: {username}")
    try:
        users[username]
        logger.warning(f'Create user failed – username taken: {username}')
        return RedirectResponse('/create?error=exists', status_code=303)
    except NotFoundError:
        pass

    users.insert(dict(
        username=username,
        email=email,
        pwd=hash_password(pwd),
        is_admin=bool(is_admin),
        archived=False,
        created_at=datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
    ))
    logger.info(f'User created: {username}')
    return RedirectResponse('/', status_code=303)


# ── Archive / Unarchive ────────────────────────────────────────────────────────

@app.post('/archive/{username}')
def archive(username: str, auth):
    try:
        users.update({'archived': True}, username)
        logger.info(f"Admin '{auth}' archived user: {username}")
    except Exception as e:
        logger.error(f'Error archiving {username}: {e}')
    return RedirectResponse('/', status_code=303)


@app.get('/archived')
def archived_page(auth):
    archived = [u for u in users() if u.archived]
    rows = [user_row(u, action='unarchive') for u in archived] or [
        P('No archived users.', cls='empty-state')
    ]
    return (
        Title('Archived Users – User Account Manager'),
        navbar(auth),
        Main(
            H2('Archived Users'),
            Div(*rows, id='user-list'),
            cls='container',
        ),
    )


@app.post('/unarchive/{username}')
def unarchive(username: str, auth):
    try:
        users.update({'archived': False}, username)
        logger.info(f"Admin '{auth}' unarchived user: {username}")
    except Exception as e:
        logger.error(f'Error unarchiving {username}: {e}')
    return RedirectResponse('/archived', status_code=303)


serve()
