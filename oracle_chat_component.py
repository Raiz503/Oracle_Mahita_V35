"""
oracle_chat_component.py
========================
Composant Streamlit qui rend le chat Messenger ET retourne
le texte saisi par l'utilisateur à Streamlit via une valeur de composant.

Utilisation dans Oracle_app.py :
    from oracle_chat_component import chat_messenger
    texte_envoye = chat_messenger(messages=st.session_state.chat_messages, key="oracle_chat")
    if texte_envoye:
        # traiter le message...
"""

import streamlit.components.v1 as components
import json


def chat_messenger(messages: list, height: int = 600, key: str = "oracle_chat") -> str | None:
    """
    Affiche la fenêtre de chat Messenger (toujours ouverte dans l'onglet).
    Retourne le texte tapé par l'utilisateur quand il appuie sur Envoyer,
    sinon retourne None.

    Parameters
    ----------
    messages : list  — historique [{role, content, source?, ts?}, ...]
    height   : int   — hauteur du composant en pixels
    key      : str   — clé unique Streamlit

    Returns
    -------
    str | None — message de l'utilisateur ou None
    """
    msgs_json = json.dumps(messages, ensure_ascii=False)

    HTML = f"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
* {{ box-sizing:border-box; margin:0; padding:0; }}
html, body {{
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: transparent;
}}
.chat-root {{
  display: flex;
  flex-direction: column;
  height: {height}px;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0,0,0,0.25);
}}

/* ── Header ── */
.chat-header {{
  background: #FFD966;
  padding: 13px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}}
.chat-avatar {{
  width: 40px; height: 40px; border-radius: 50%;
  background: linear-gradient(135deg,#7FFFD4,#00b894);
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}}
.chat-header-info {{ flex:1; }}
.chat-header-name {{ color:#1a1a2e; font-weight:800; font-size:15px; }}
.chat-header-status {{ color:#444; font-size:11px; margin-top:1px; }}

/* ── Zone messages ── */
.chat-msgs {{
  flex: 1;
  overflow-y: auto;
  padding: 14px 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: #F0F2F5;
  scrollbar-width: thin;
  scrollbar-color: #7FFFD4 #e0e0e0;
}}
.chat-msgs::-webkit-scrollbar {{ width: 4px; }}
.chat-msgs::-webkit-scrollbar-thumb {{ background:#7FFFD4; border-radius:4px; }}

.welcome {{
  background: #e8f4fd;
  border: 1px solid #c9e6f7;
  border-radius: 14px;
  padding: 12px 14px;
  color: #555;
  font-size: 13px;
  text-align: center;
}}

/* Bulles utilisateur */
.bw-u {{ display:flex; justify-content:flex-end; align-items:flex-end; }}
.bu-u {{
  background: #FFD966;
  color: #1a1a2e;
  padding: 10px 14px;
  border-radius: 20px 20px 4px 20px;
  max-width: 78%; font-size: 14px;
  line-height: 1.45; word-break: break-word;
  box-shadow: 0 1px 4px rgba(0,0,0,0.12);
}}

/* Bulles Oracle */
.bw-b {{ display:flex; justify-content:flex-start; align-items:flex-end; gap:8px; }}
.av-b {{
  width:30px; height:30px; border-radius:50%;
  background:linear-gradient(135deg,#7FFFD4,#00b894);
  display:flex; align-items:center; justify-content:center;
  font-size:14px; flex-shrink:0; margin-bottom:2px;
}}
.bu-b {{
  background: #fff;
  color: #1a1a2e;
  padding: 10px 14px;
  border-radius: 20px 20px 20px 4px;
  max-width: 82%; font-size:14px;
  line-height:1.45; word-break:break-word;
  box-shadow: 0 1px 4px rgba(0,0,0,0.1);
}}
.src-lbl {{ font-size:10px; color:#00b894; font-weight:700; margin-bottom:3px; }}
.msg-ts {{ font-size:10px; color:#aaa; margin-top:4px; text-align:right; }}
.bu-b .msg-ts {{ text-align:left; }}

/* Typing dots */
.typing {{ display:flex; gap:4px; align-items:center; padding:4px 2px; }}
.typing span {{
  width:8px; height:8px; border-radius:50%;
  background:#00b894; opacity:.4;
  animation: bounce 1.1s infinite;
}}
.typing span:nth-child(2) {{ animation-delay:.18s; }}
.typing span:nth-child(3) {{ animation-delay:.36s; }}
@keyframes bounce {{
  0%,80%,100% {{ transform:scale(.7); opacity:.3; }}
  40%          {{ transform:scale(1.1); opacity:1;  }}
}}

/* ── Barre de saisie ── */
.chat-bar {{
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #fff;
  border-top: 1px solid #e5e7eb;
  flex-shrink: 0;
}}
.chat-input {{
  flex: 1; min-width:0;
  background: #F0F2F5;
  border: none; border-radius: 22px;
  padding: 11px 16px;
  font-size: 14px; color: #1a1a2e;
  outline: none;
}}
.chat-input::placeholder {{ color:#aaa; }}
.chat-send {{
  width:42px; height:42px; border-radius:50%;
  background: linear-gradient(135deg,#7FFFD4,#00b894);
  border:none; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  font-size:20px; color:#1a1a2e;
  box-shadow: 0 2px 8px rgba(0,185,148,.4);
  transition: transform .15s;
  flex-shrink: 0;
}}
.chat-send:active {{ transform:scale(.9); }}
</style>
</head>
<body>
<div class="chat-root">

  <!-- Header -->
  <div class="chat-header">
    <div class="chat-avatar">🔮</div>
    <div class="chat-header-info">
      <div class="chat-header-name">Oracle Mahita IA</div>
      <div class="chat-header-status">● En ligne · Assistant pronostics</div>
    </div>
  </div>

  <!-- Messages -->
  <div class="chat-msgs" id="msgs">
    <div class="welcome">🔮 Bonjour ! Posez-moi n'importe quelle question sur vos pronostics, classements ou résultats.</div>
  </div>

  <!-- Input -->
  <div class="chat-bar">
    <input class="chat-input" id="inp" type="text"
           placeholder="Écrivez votre message..." autocomplete="off">
    <button class="chat-send" id="snd" onclick="doSend()">&#10148;</button>
  </div>

</div>

<script>
// ── Données injectées par Python ──
const MSGS = {msgs_json};

function esc(t) {{
  return String(t||'')
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;');
}}

function fmt(ts) {{
  try {{
    const d = new Date(ts);
    return d.getHours().toString().padStart(2,'0') + ':' + d.getMinutes().toString().padStart(2,'0');
  }} catch(e) {{ return ''; }}
}}

function renderAll() {{
  const box = document.getElementById('msgs');
  let h = '<div class="welcome">🔮 Bonjour ! Posez-moi n\\'importe quelle question.</div>';

  MSGS.forEach(function(m) {{
    const t = fmt(m.ts || '');
    if (m.role === 'user') {{
      h += '<div class="bw-u"><div class="bu-u">'
         + esc(m.content)
         + '<div class="msg-ts">' + t + '</div>'
         + '</div></div>';
    }} else {{
      const src = m.source === 'groq' ? '🧠 Groq' : '🤖 Offline';
      h += '<div class="bw-b">'
         +   '<div class="av-b">🔮</div>'
         +   '<div class="bu-b">'
         +     '<div class="src-lbl">' + src + '</div>'
         +     esc(m.content).replace(/\\n/g, '<br>')
         +     '<div class="msg-ts">' + t + '</div>'
         +   '</div>'
         + '</div>';
    }}
  }});

  box.innerHTML = h;
  box.scrollTop = box.scrollHeight;
}}

function showTyping() {{
  const box = document.getElementById('msgs');
  box.innerHTML += '<div id="typing-row" class="bw-b">'
    + '<div class="av-b">🔮</div>'
    + '<div class="bu-b"><div class="typing">'
    + '<span></span><span></span><span></span>'
    + '</div></div></div>';
  box.scrollTop = box.scrollHeight;
}}

function doSend() {{
  const inp = document.getElementById('inp');
  const text = inp.value.trim();
  if (!text) return;
  inp.value = '';
  inp.disabled = true;
  document.getElementById('snd').disabled = true;

  // Affichage immédiat de la bulle utilisateur
  const box = document.getElementById('msgs');
  box.innerHTML += '<div class="bw-u"><div class="bu-u">' + esc(text) + '</div></div>';
  showTyping();

  // ✅ Envoyer la valeur à Streamlit via l'API du composant
  Streamlit.setComponentValue(text);
}}

document.getElementById('inp').addEventListener('keydown', function(e) {{
  if (e.key === 'Enter' && !e.shiftKey) {{
    e.preventDefault();
    doSend();
  }}
}});

// Initialisation
renderAll();
Streamlit.setFrameHeight({height});
</script>
</body>
</html>"""

    result = components.html(
        HTML,
        height=height,
        scrolling=False,
    )

    # components.html ne retourne pas de valeur —
    # on utilise st.query_params comme canal de secours
    # (voir note dans Oracle_app.py)
    return result
