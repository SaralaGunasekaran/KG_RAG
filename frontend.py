import time
import requests
import streamlit as st

# ---------------------------------------------------------
# 1. PAGE CONFIG & SESSION MEMORY
# ---------------------------------------------------------
st.set_page_config(
    page_title="Agri AI Assistant",
    page_icon="🌾",
    layout="centered",
)

BACKEND_URL = "http://127.0.0.1:8000/ask"

if "language" not in st.session_state:
    st.session_state.language = "English"

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------------
# 2. CUSTOM FORMAL & ELEGANT GREEN CSS STYLING
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    /* Main Page Light Green Elegant Background */
    .stApp {
        background-color: #f1f8f4;
        font-family: 'Segoe UI', sans-serif;
    }

    /* Fixed Agricultural Green Header Banner */
    .agri-header {
        background: linear-gradient(rgba(20, 68, 42, 0.84), rgba(27, 94, 58, 0.88)),
                    url('https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1400&q=80');
        background-size: cover;
        background-position: center;
        padding: 26px 24px;
        border-radius: 14px;
        color: #ffffff;
        margin-bottom: 18px;
        box-shadow: 0 4px 14px rgba(20, 68, 42, 0.18);
        border-bottom: 4px solid #1b5e3a;
    }
    .agri-header h1 {
        margin: 0;
        font-size: 28px;
        font-weight: 700;
        letter-spacing: 0.4px;
        color: #ffffff;
    }
    .agri-header p {
        margin: 6px 0 0 0;
        font-size: 14px;
        color: #d8f3dc;
    }

    /* Chat Message Cards (No Bot Image, Clean Name Labels) */
    .user-msg-box {
        background-color: #ffffff;
        border-left: 5px solid #2d6a4f;
        padding: 14px 18px;
        border-radius: 10px;
        margin-bottom: 12px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
    }
    .bot-msg-box {
        background-color: #e6f4ea;
        border-left: 5px solid #1b4332;
        padding: 14px 18px;
        border-radius: 10px;
        margin-bottom: 16px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
    }
    .sender-label-user {
        font-weight: 700;
        font-size: 13px;
        color: #2d6a4f;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .sender-label-bot {
        font-weight: 700;
        font-size: 13px;
        color: #1b4332;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .msg-text {
        font-size: 15px;
        color: #1b2620;
        line-height: 1.55;
    }

    /* Highlighted Dark Green Chat Input Box */
    [data-testid="stChatInput"] {
        background-color: #1b4332 !important;
        border: 2px solid #081c15 !important;
        border-radius: 12px !important;
        padding: 4px !important;
        box-shadow: 0 4px 12px rgba(27, 67, 50, 0.25) !important;
    }
    [data-testid="stChatInput"] textarea {
        background-color: #d8f3dc !important; /* Mild soft green inner box */
        color: #1b4332 !important;            /* Dark green typed text for contrast */
        border-radius: 8px !important;
        padding-left: 10px !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #74c69d !important; /* Mild green placeholder text */
        opacity: 1 !important;
    }
    [data-testid="stChatInput"] button {
        color: #d8f3dc !important;
    }

    /* Language Selector Buttons */
    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        border: 1.5px solid #2d6a4f;
        padding: 8px 14px;
        transition: all 0.2s ease;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 3. TOP HEADER BANNER
# ---------------------------------------------------------
subtitle = (
    "Tamil Nadu Government Agricultural & MSME Schemes Knowledge Assistant"
    if st.session_state.language == "English"
    else "தமிழ்நாடு அரசு வேளாண்மை மற்றும் குறு, சிறு, நடுத்தரத் தொழில் திட்டங்களுக்கான AI உதவியாளர்"
)

st.markdown(
    f"""
    <div class="agri-header">
        <h1>🌾 Agri AI Assistant</h1>
        <p>{subtitle}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 4. LANGUAGE SELECTION BUTTONS (ENGLISH / தமிழ்)
# ---------------------------------------------------------
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    if st.button(
        "English" if st.session_state.language != "English" else "✓ English",
        type="primary" if st.session_state.language == "English" else "secondary",
    ):
        st.session_state.language = "English"
        st.rerun()

with col2:
    if st.button(
        "தமிழ்" if st.session_state.language != "Tamil" else "✓ தமிழ்",
        type="primary" if st.session_state.language == "Tamil" else "secondary",
    ):
        st.session_state.language = "Tamil"
        st.rerun()

with col3:
    if st.button("🗑️ Clear Chat" if st.session_state.language == "English" else "🗑️ உரையாடலை அழி"):
        st.session_state.messages = []
        st.rerun()

st.markdown("---")

# ---------------------------------------------------------
# 5. CHAT HISTORY DISPLAY (MEMORY STORAGE)
# ---------------------------------------------------------
chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        welcome_text = (
            "Ask me anything about Tamil Nadu Farmers Welfare Department schemes, subsidies, or seed distribution."
            if st.session_state.language == "English"
            else "தமிழ்நாடு உழவர் நலத்துறை திட்டங்கள், மானியங்கள் அல்லது விதை விநியோகம் குறித்து எதுவும் கேளுங்கள்."
        )
        st.info(welcome_text)

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(
                f"""
                <div class="user-msg-box">
                    <div class="sender-label-user">You</div>
                    <div class="msg-text">{msg["content"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="bot-msg-box">
                    <div class="sender-label-bot">Agri AI Assistant</div>
                    <div class="msg-text">{msg["content"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ---------------------------------------------------------
# 6. HIGHLIGHTED CHAT INPUT & LIVE STREAMING RESPONSE
# ---------------------------------------------------------
placeholder_text = (
    "Type your question about Tamil Nadu Agri schemes here..."
    if st.session_state.language == "English"
    else "தமிழ்நாடு வேளாண் திட்டங்கள் குறித்த உங்கள் கேள்வியை இங்கே தட்டச்சு செய்யவும்..."
)

user_input = st.chat_input(placeholder_text)

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with chat_container:
        st.markdown(
            f"""
            <div class="user-msg-box">
                <div class="sender-label-user">You</div>
                <div class="msg-text">{user_input}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        bot_placeholder = st.empty()
        thinking_msg = (
            "Searching..."
            if st.session_state.language == "English"
            else "தகவல் களஞ்சியத்தில் தேடுகிறது..."
        )
        bot_placeholder.markdown(
            f"""
            <div class="bot-msg-box">
                <div class="sender-label-bot">Agri AI Assistant</div>
                <div class="msg-text"><i>{thinking_msg}</i></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        try:
            response = requests.post(
                BACKEND_URL,
                json={"question": user_input, "language": st.session_state.language},
                timeout=60,
            )
            response.raise_for_status()
            full_answer = response.json().get("answer", "No response received.")
        except Exception as e:
            full_answer = f"Connection Error: Make sure FastAPI backend is running. ({e})"

        streamed_text = ""
        for word in full_answer.split(" "):
            streamed_text += word + " "
            bot_placeholder.markdown(
                f"""
                <div class="bot-msg-box">
                    <div class="sender-label-bot">Agri AI Assistant</div>
                    <div class="msg-text">{streamed_text}▌</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            time.sleep(0.03)

        bot_placeholder.markdown(
            f"""
            <div class="bot-msg-box">
                <div class="sender-label-bot">Agri AI Assistant</div>
                <div class="msg-text">{full_answer}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.session_state.messages.append({"role": "assistant", "content": full_answer})