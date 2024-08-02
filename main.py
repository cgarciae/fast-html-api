
from typing import Iterable
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import fasthtml.common as fasthtml
from fasthtml.components import *

app = FastAPI()

class FastHTMLResponse(HTMLResponse):
  def render(self, content) -> bytes:
    if isinstance(content, str):
      pass
    elif isinstance(content, fasthtml.FT):
      content = fasthtml.to_xml(content)
    elif isinstance(content, Iterable):
      content = "\n".join(fasthtml.to_xml(c) for c in content)
    return super().render(content)

@app.get("/", response_class=FastHTMLResponse)
def index():
  return [
    Title("App"), 
    H1("Hello, World!"), 
    P("This is a paragraph."),
  ]

if __name__ == "__main__":
  import uvicorn
  uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=True)