from typing import List

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag_lib import get_llm, retrieve_context, query_augment
from i18n import get_message


app = FastAPI(title="Doris RAG Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str
    history: List[dict] = []


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    query = req.query.strip()
    if not query:
        return ChatResponse(answer="", sources=[])

    augmented_query = query_augment(query, req.history)
    print(get_message("service_original_augmented", query, augmented_query))

    context_df = retrieve_context(augmented_query, top_k=5)

    context_blocks = []
    sources = []
    for _, row in context_df.iterrows():
      filename = row.get("filename", "")
      text = row.get("text", "")
      key = row.get("_key", "")
      location = row.get("location")

      # Normalize values to JSON-serializable types
      try:
        key = str(key) if key is not None else ""
      except Exception:
        key = ""

      # Convert numpy arrays or pandas objects to plain Python lists
      if hasattr(location, "tolist"):
        try:
          location = location.tolist()
        except Exception:
          location = None
      elif isinstance(location, tuple):
        location = list(location)
      elif not isinstance(location, list):
        # Keep None or simple scalars; otherwise drop
        if not (location is None or isinstance(location, (int, float, str))):
          location = None

      block = f"[{get_message('source_label')}: {filename}]\n{text}"
      context_blocks.append(block)
      sources.append(
        {
          "key": key,
          "filename": filename,
          "location": location,
        }
      )

    context_text = "\n\n---\n\n".join(context_blocks)

    history_text = ""
    for turn in req.history:
        role = turn.get("role", "user")
        content = turn.get("content", "")
        history_text += f"{role.upper()}: {content}\n"

    template = get_message("chat_prompt_template")
    prompt = template.format(
        history=history_text.strip(),
        context=context_text.strip(),
        question=query.strip(),
    )

    llm = get_llm()
    resp = llm.invoke(prompt)
    answer = resp.content if hasattr(resp, "content") else str(resp)

    return ChatResponse(answer=answer, sources=sources)


@app.get("/", response_class=HTMLResponse)
async def index():
    html = f"""<!DOCTYPE html>
<html lang="{get_message('html_lang')}">
<head>
  <meta charset="UTF-8" />
  <title>Doris RAG Chat</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; padding: 0; background: #f5f5f5; }}
    #app {{ max-width: 900px; margin: 0 auto; padding: 16px; }}
    .chat-window {{ background: #fff; border-radius: 8px; padding: 16px; height: 70vh; overflow-y: auto; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }}
    .msg {{ margin-bottom: 12px; }}
    .msg-user {{ text-align: right; }}
    .msg-user .bubble {{ background: #1677ff; color: #fff; margin-left: auto; }}
    .msg-assistant .bubble {{ background: #f0f0f0; }}
    .bubble {{ display: inline-block; padding: 8px 12px; border-radius: 16px; max-width: 70%; white-space: pre-wrap; }}
    .input-area {{ margin-top: 12px; display: flex; gap: 8px; }}
    .input-area textarea {{ flex: 1; resize: vertical; min-height: 60px; padding: 8px; }}
    .input-area button {{ padding: 8px 16px; }}
    .sources {{ font-size: 12px; color: #666; margin-top: 4px; }}
  </style>
</head>
<body>
  <div id="app">
    <h2>Doris RAG Chat</h2>
    <div class="chat-window" id="chat"></div>
    <div class="input-area">
      <textarea id="input" placeholder="{get_message('ui_placeholder')}"></textarea>
      <button id="send">{get_message('ui_send')}</button>
    </div>
  </div>

  <script>
    const chatEl = document.getElementById('chat');
    const inputEl = document.getElementById('input');
    const sendBtn = document.getElementById('send');

    let history = [];

    function appendMessage(role, text, sources) {{
      const div = document.createElement('div');
      div.className = 'msg msg-' + role;
      const bubble = document.createElement('div');
      bubble.className = 'bubble';
      bubble.textContent = text;
      div.appendChild(bubble);

      if (sources && sources.length > 0 && role === 'assistant') {{
        const sdiv = document.createElement('div');
        sdiv.className = 'sources';
        sdiv.textContent = '{get_message('ui_source_ref')}' + sources.map(s => {{
          const name = s.filename || s.path || 'source';
          const loc = (s.location !== undefined && s.location !== null) ? ` @ ${{Array.isArray(s.location) ? s.location.join(',') : s.location}}` : '';
          return name + loc;
        }}).join(' | ');
        div.appendChild(sdiv);
      }}

      chatEl.appendChild(div);
      chatEl.scrollTop = chatEl.scrollHeight;
    }}

    async function send() {{
      const text = inputEl.value.trim();
      if (!text) return;

      appendMessage('user', text);
      history.push({{ role: 'user', content: text }});
      inputEl.value = '';
      sendBtn.disabled = true;
      appendMessage('assistant', '{get_message('ui_thinking')}', []);

      try {{
        const resp = await fetch('/api/chat', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ query: text, history }})
        }});

        const data = await resp.json();
        const children = chatEl.children;
        if (children.length > 0) {{
          chatEl.removeChild(children[children.length - 1]);
        }}

        if (!resp.ok) {{
          console.error(data);
          appendMessage('assistant', '{get_message('ui_error_prefix')}' + (data.detail || resp.statusText), []);
          return;
        }}

        history.push({{ role: 'assistant', content: data.answer }});
        appendMessage('assistant', data.answer, data.sources || []);
      }} catch (err) {{
        console.error(err);
        appendMessage('assistant', '{get_message('ui_request_failed')}', []);
      }} finally {{
        sendBtn.disabled = false;
      }}
    }}

    sendBtn.addEventListener('click', send);
    inputEl.addEventListener('keydown', (e) => {{
      if (e.key === 'Enter' && !e.shiftKey) {{
        e.preventDefault();
        send();
      }}
    }});
  </script>
</body>
</html>"""
    return HTMLResponse(content=html, status_code=200)
