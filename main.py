# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "python-fasthtml",
#     "fastlite",
# ]
# ///
"""FastHTML multi-tenant todo — one file, zero config."""

from fasthtml.common import *
from fastlite import database
from dataclasses import dataclass
import os

DATA_DIR = os.environ.get("DATA_DIR", "/data")
os.makedirs(DATA_DIR, exist_ok=True)

@dataclass
class Todo:
    id:    int = None
    title: str = ''
    done:  bool = False

_dbs = {}

def get_todos(tenant: str):
    if tenant not in _dbs:
        db = database(f"{DATA_DIR}/{tenant}.db")
        _dbs[tenant] = db.create(Todo, pk='id')
    return _dbs[tenant]

app, rt = fast_app(
    secret_key='change-me-in-production',
    live=False,
    hdrs=[Style("""
    body{font-family:system-ui;max-width:600px;margin:2rem auto;padding:0 1rem}
    h1{font-size:1.5rem}
    ul{list-style:none;padding:0}
    li{display:flex;align-items:center;gap:.5rem;padding:.4rem 0;border-bottom:1px solid #eee}
    .toggle{text-decoration:none;font-size:1.2rem;opacity:.3;cursor:pointer}
    .toggle.done{opacity:1;color:green}
    .title-done{text-decoration:line-through;opacity:.5}
    .delete{text-decoration:none;color:#c00;margin-left:auto;cursor:pointer}
    .todo-form{display:flex;gap:.5rem;margin-bottom:1rem}
    .todo-input{flex:1;padding:.4rem;font-size:1rem}
    button{padding:.4rem 1rem}
    code{background:#f4f4f4;padding:.15rem .3rem;border-radius:3px;font-size:.85rem}
    .meta{margin-top:2rem;font-size:.85rem;color:#666}
    """)],
)

def tid(id): return f'todo-{id}'

def mk_todo(t, tenant):
    done_cls = 'done' if t.done else ''
    return Li(
        A('✓', hx_put=f'/{tenant}/toggle/{t.id}', hx_target=f'#{tid(t.id)}',
          hx_swap='outerHTML', cls=f'toggle {done_cls}'),
        Span(t.title, cls='title-done' if t.done else ''),
        A('✕', hx_delete=f'/{tenant}/todo/{t.id}', hx_target=f'#{tid(t.id)}',
          hx_swap='outerHTML', cls='delete'),
        id=tid(t.id),
    )

@rt('/')
def index():
    return Titled('FastHTML Multi-tenant Todo',
        P('Each tenant gets their own SQLite database. Pick one:'),
        Ul(
            Li(A('acme', href='/acme')),
            Li(A('berens', href='/berens')),
            Li(A('client-47', href='/client-47')),
        ),
        Div(P(Code('fastlite'), ' — MiniDataAPI for SQLite.'), cls='meta'),
    )

@rt('/{tenant}')
def home(tenant: str):
    todos = get_todos(tenant)
    items = [mk_todo(t, tenant) for t in todos()]
    return Titled(f'Tenant: {tenant}',
        Form(
            Input(name='title', placeholder='What needs doing?', autofocus=True, cls='todo-input'),
            Button('Add', type='submit'),
            hx_post=f'/{tenant}/todo', hx_target='#todo-list', hx_swap='beforeend',
            hx_on__after_request="this.reset()", cls='todo-form',
        ),
        Ul(*items, id='todo-list'),
        Div(
            P('Try: ', A('/acme', href='/acme'), ' · ', A('/berens', href='/berens'),
              ' · ', A('/client-47', href='/client-47'), ' — each is isolated.'),
            cls='meta',
        ),
    )

@rt('/{tenant}/todo', methods=['post'])
def add_todo(tenant: str, title: str):
    t = get_todos(tenant).insert(Todo(title=title))
    return mk_todo(t, tenant)

@rt('/{tenant}/toggle/{id}', methods=['put'])
def toggle(tenant: str, id: int):
    todos = get_todos(tenant)
    t = todos[id]
    todos.update(Todo(id=t.id, title=t.title, done=not t.done))
    return mk_todo(todos[id], tenant)

@rt('/{tenant}/todo/{id}', methods=['delete'])
def delete(tenant: str, id: int):
    get_todos(tenant).delete(id)
    return ''

serve(host='0.0.0.0', port=8080)
