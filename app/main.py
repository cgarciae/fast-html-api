from typing import Annotated, Iterable
from fastapi import Depends, FastAPI, Form as _Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import fasthtml.common as fasthtml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from .database import Todo
import fastcore.xml as _


class FastHTMLResponse(HTMLResponse):
  def render(self, content) -> bytes:
    print(type(content))
    if isinstance(content, str):
      pass
    elif isinstance(content[2], dict):
      content = fasthtml.to_xml(content)
    else:
      content = "\n".join(fasthtml.to_xml(c) for c in content)
    print(content)
    return super().render(content)


# ------------------------------------------------------------
# App
# ------------------------------------------------------------


engine = create_engine(
  "sqlite:///database.db", connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency
def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()


app = FastAPI()

# serve files under static
app.mount("/static", StaticFiles(directory="static"), name="static")


def TodoComponent(todo: Todo, *, edit: bool):
  if not edit:
    return _.Article(id=f"todo-{todo.id}")(
      _.H3(f"{todo.title}"),
      _.Button(
        cls=f"{'outline' if todo.completed else ''} primary",
        hx_post=f"/todos/{todo.id}/toogle",
        hx_target=f"#todo-{todo.id}",
      )("Active"),
      _.Button(
        cls="secondary",
        hx_get=f"/todos/{todo.id}/edit",
        hx_target=f"#todo-{todo.id}",
      )("Edit"),
      _.Button(
        cls="contrast",
        hx_delete=f"/todos/{todo.id}",
        hx_target=f"#todo-{todo.id}",
        hx_swap="delete",
      )("Delete"),
    )
  else:
    return _.Article(id=f"todo-{todo.id}")(
      _.Form(hx_post=f"/todos/{todo.id}/save", hx_target=f"#todo-{todo.id}")(
        _.Input(
          name="title",
          value=todo.title,
          placeholder="Enter todo title...",
        ),
        _.Button(type="submit")("Save"),
      )
    )


def TodosComponent(todos: Iterable[Todo]):
  return _.Div(
    _.H1("Todos"),
    _.Button(
      hx_post="/todos/new",
      hx_target="#todos",
      hx_swap="beforeend",
    )("Add"),
    _.Div(id="todos")(*[TodoComponent(todo, edit=False) for todo in todos]),
  )


def CounterComponent():
  return _.Article(hx_state="")(
    _.Button(
      onclick="$state(this).count += 1",
      hx_effect="""
        this.style.backgroundColor = $state(this).count > 3 ? 'red' : $state(this).count < -3 ? 'blue' : '';
      """,
    )("+"),
    _.P(
      hx_bind="innerText=count:Number",
    )("0"),
    _.Button(
      onclick="$state(this).count -= 1",
    )("-"),
  )


@app.get("/", response_class=FastHTMLResponse)
def index(db: Session = Depends(get_db)):
  todos = db.query(Todo).all()

  return (
    _.Title("App"),
    _.Link(
      rel="stylesheet",
      href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css",
    ),
    _.Script(src="https://unpkg.com/htmx.org@2.0.1/dist/htmx.js"),
    _.Script(src="/static/signals.js", type="module"),
    _.Script(src="/static/hx-state.js"),
    _.Body(cls="container", style="width: 50%;")(
      TodosComponent(todos),
    ),
    CounterComponent(),
  )


@app.post("/todos/{todo_id}/toogle", response_class=FastHTMLResponse)
def toogle(todo_id: int, db: Session = Depends(get_db)):
  todo: Todo | None = db.query(Todo).get(todo_id)
  assert todo is not None
  todo.completed = not todo.completed
  db.commit()

  return TodoComponent(todo, edit=False)


# edit
@app.get("/todos/{todo_id}/edit", response_class=FastHTMLResponse)
def edit(todo_id: int, db: Session = Depends(get_db)):
  todo: Todo | None = db.query(Todo).get(todo_id)
  assert todo is not None
  return TodoComponent(todo, edit=True)


# save
@app.post("/todos/{todo_id}/save", response_class=FastHTMLResponse)
def save(todo_id: int, title: Annotated[str, _Form()], db: Session = Depends(get_db)):
  todo: Todo | None = db.query(Todo).get(todo_id)
  assert todo is not None
  todo.title = title
  db.commit()
  return TodoComponent(todo, edit=False)


# new
@app.post("/todos/new", response_class=FastHTMLResponse)
def new(db: Session = Depends(get_db)):
  todo = Todo(title="", completed=False)
  db.add(todo)
  db.commit()
  return TodoComponent(todo, edit=True)


@app.delete("/todos/{todo_id}")
def delete(todo_id: int, db: Session = Depends(get_db)):
  db.query(Todo).filter(Todo.id == todo_id).delete()
  db.commit()


if __name__ == "__main__":
  import uvicorn

  uvicorn.run("app.main:app", host="0.0.0.0", port=5001, reload=True)
