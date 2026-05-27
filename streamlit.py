import streamlit as st
import requests
import json
import hashlib

# ----------------------------
# CONFIG
# ----------------------------
API_URL = "http://localhost:8001"

st.set_page_config(
    page_title="Document Q/A AI Agent",
    page_icon="📚",
    layout="wide",
)

# ----------------------------
# SESSION STATE
# ----------------------------
if "api_key" not in st.session_state:
    st.session_state.api_key = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "citations" not in st.session_state:
    st.session_state.citations = []

if "selected_doc" not in st.session_state:
    st.session_state.selected_doc = None


# ----------------------------
# UTILS
# ----------------------------
def make_unique_key(c: dict) -> str:
    raw = f"{c.get('doc_id','')}_{c.get('chunk_index','')}_{c.get('chunk_text','')}"
    return hashlib.md5(raw.encode()).hexdigest()


# ----------------------------
# PREMIUM CSS (CLEAN CHATGPT STYLE)
# ----------------------------
st.markdown("""
<style>

    .main-title {
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        color: #9ca3af;
        margin-bottom: 20px;
    }

    .chat-container {
        padding: 10px;
    }

    .citation-card {
        background: #0f172a;
        border: 1px solid #1f2937;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 8px;
        font-size: 13px;
    }

    .api-warning {
        padding: 10px;
        border-radius: 8px;
        background: #1f2937;
        color: #fbbf24;
    }

</style>
""", unsafe_allow_html=True)


# ----------------------------
# SIDEBAR (API KEY GATE)
# ----------------------------
with st.sidebar:

    st.title("⚙️ Control Panel")

    # API KEY LOGIN GATE
    if not st.session_state.api_key:
        st.markdown("### 🔐 Enter API Key")
        api_key = st.text_input("API Key", type="password")

        if st.button("Activate"):
            if api_key:
                st.session_state.api_key = api_key
                st.success("Access Granted")
                st.rerun()
            else:
                st.warning("Please enter API key")

        st.stop()

    st.success("🟢 System Active")

    if st.button("Logout"):
        st.session_state.api_key = None
        st.rerun()

    st.divider()

    # ----------------------------
    # DOCUMENT UPLOAD
    # ----------------------------
    st.subheader("📤 Upload Documents")

    files = st.file_uploader(
        "PDF, DOCX, TXT, MD",
        accept_multiple_files=True,
        type=["pdf", "docx", "csv", "txt", "md"]
    )

    if st.button("Upload & Index"):
        if files:
            with st.spinner("Processing..."):
                multipart_files = [("files", (f.name, f.getvalue())) for f in files]

                res = requests.post(
                    f"{API_URL}/upload",
                    files=multipart_files
                )

                if res.status_code == 200:
                    st.success("Indexed Successfully")
                else:
                    st.error(res.text)

    st.divider()

    # ----------------------------
    # DOCUMENT LIST
    # ----------------------------
    st.subheader("📚 Documents")

    try:
        res = requests.get(f"{API_URL}/documents")
        docs = res.json().get("documents", [])
    except:
        docs = []

    for d in docs:
        with st.expander(f"📄 {d['file_name']}"):
            st.caption(f"{d['file_type']} • {d['total_chunks']} chunks")

            if st.button("Delete", key=f"del_{d['doc_id']}"):
                requests.delete(f"{API_URL}/documents/{d['doc_id']}")
                st.rerun()


# ----------------------------
# HEADER
# ----------------------------
st.markdown("<div class='main-title'>📚 Document Q/A AI Agent</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Ask questions over your documents with cited answers</div>", unsafe_allow_html=True)


# ----------------------------
# STREAMING ENGINE
# ----------------------------
def stream_query(question: str):

    payload = {"question": question, "top_k": 5}

    response = requests.post(
        f"{API_URL}/query/stream",
        json=payload,
        stream=True
    )

    answer_placeholder = st.empty()
    full = ""
    citations = []

    for line in response.iter_lines():
        if not line:
            continue

        decoded = line.decode("utf-8").replace("data: ", "")

        try:
            event = json.loads(decoded)
        except:
            continue

        if event.get("type") == "citations":
            citations = event.get("data", [])

        elif event.get("type") == "token":
            full += event.get("content", "")
            answer_placeholder.markdown(full)

        elif event.get("type") == "done":
            break

    return full, citations


# ----------------------------
# CHAT INPUT
# ----------------------------
query = st.chat_input("Ask your documents...")


# ----------------------------
# CHAT UI
# ----------------------------
if query:

    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):
            answer, citations = stream_query(query)

        st.session_state.citations = citations

        st.markdown("### 📌 Sources")

        seen = set()

        for c in citations:
            uid = f"{c.get('doc_id')}_{c.get('chunk_index')}"

            if uid in seen:
                continue
            seen.add(uid)

            with st.expander(f"📄 {c.get('file_name')} • Page {c.get('page_number')}"):

                st.markdown(c.get("chunk_text", ""))

                st.caption(f"Score: {c.get('relevance_score')}")

                if st.button("Open Document", key=make_unique_key(c)):
                    st.session_state.selected_doc = c.get("doc_id")


# ----------------------------
# RIGHT-SIDE STYLE CITATIONS FEED
# ----------------------------
st.divider()
st.subheader("🧠 Context Memory (Last Query)")

if st.session_state.citations:
    for c in st.session_state.citations:
        st.markdown(
            f"""
            <div class="citation-card">
                <b>{c.get('file_name')}</b><br>
                Page {c.get('page_number')} • Score {c.get('relevance_score')}<br>
                {c.get('chunk_text','')[:250]}...
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.info("Ask a question to see retrieved context.")


# ----------------------------
# DOCUMENT VIEWER
# ----------------------------
st.divider()
st.subheader("📄 Document Viewer")

doc_id = st.text_input("Open Document by ID")

if doc_id:
    try:
        res = requests.get(f"{API_URL}/files/{doc_id}/markdown")

        if res.status_code == 200:
            data = res.json()

            st.markdown(f"### {data.get('file_name')}")
            st.markdown(data.get("content", ""), unsafe_allow_html=True)

        else:
            st.error("Document not found")

    except Exception as e:
        st.error(str(e))