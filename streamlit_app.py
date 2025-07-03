import streamlit as st
import asyncio
import os
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from mcp_use import MCPAgent, MCPClient
import time

# Page configuration
st.set_page_config(
    page_title="SharePoint RAG Chat",
    page_icon="💬",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stTextInput > div > div > input {
        background-color: #f0f2f6;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .chat-message.assistant {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .chat-message .message-content {
        margin-bottom: 0.5rem;
    }
    .chat-message .timestamp {
        font-size: 0.8rem;
        color: #666;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "client" not in st.session_state:
    st.session_state.client = None
if "agent" not in st.session_state:
    st.session_state.agent = None
if "initialized" not in st.session_state:
    st.session_state.initialized = False

# MCP initialization

def initialize_mcp():
    try:
        load_dotenv()
        config_file = "mcp_with_interactive_auth.json"
        client = MCPClient.from_config_file(config_file)
        st.info("🔧 Initializing MCP connection... Please complete authentication in the browser.")
        asyncio.run(client.create_all_sessions(auto_initialize=True))
        st.success("✅ MCP Connected!")
        llm = ChatBedrock(
            model="anthropic.claude-3-5-sonnet-20240620-v1:0",
            region_name="us-east-1",
            streaming=True
        )
        agent = MCPAgent(llm=llm, client=client, max_steps=10, memory_enabled=True, auto_initialize=True)
        return client, agent
    except Exception as e:
        st.error(f"❌ Error initializing MCP: {e}")
        st.error("💡 Make sure your Azure app registration has the correct redirect URI configured and no client secret is set for interactive auth.")
        return None, None

# Streaming (realtime)
def stream_mcp_response(response_data, message_placeholder):
    try:
        if isinstance(response_data, list):
            full_response = ""
            for item in response_data:
                if isinstance(item, dict) and 'text' in item:
                    text = item['text']
                    text = text.replace('\n\n', '\n').strip()
                    full_response += text
                    message_placeholder.markdown(full_response)
                    time.sleep(0.003)
            return full_response
        elif isinstance(response_data, str):
            full_response = ""
            for char in response_data:
                full_response += char
                message_placeholder.markdown(full_response)
                time.sleep(0.01)
            return full_response
        else:
            message_placeholder.markdown(str(response_data))
            return str(response_data)
    except Exception as e:
        st.error(f"Error during streaming: {e}")
        message_placeholder.markdown(str(response_data))
        return str(response_data)

# Header
st.title("💬 SharePoint RAG Chat")
st.markdown("Chat with your SharePoint files using AI-powered search and retrieval.")

# Sidebar
with st.sidebar:
    st.header("Settings")
    if not st.session_state.initialized:
        st.warning("⚠️ MCP Not Connected")
        if st.button("🔄 Initialize MCP Connection"):
            with st.spinner("Initializing MCP connection..."):
                st.info("🔐 Interactive Authentication Required. A browser window will open for authentication. Please complete the login process.")
                client, agent = initialize_mcp()
                if client and agent:
                    st.session_state.client = client
                    st.session_state.agent = agent
                    st.session_state.initialized = True
                    st.success("✅ MCP connection initialized!")
                else:
                    st.error("❌ Failed to initialize MCP connection")
                    st.error("💡 Check that your Azure app registration is configured correctly")
    else:
        st.success("✅ MCP Connected")
        if st.button("🔍 Check Auth Status"):
            if st.session_state.client and st.session_state.client.sessions:
                session = list(st.session_state.client.sessions.values())[0]
                async def check_status():
                    try:
                        status = await session.call_tool("get-auth-status", {})
                        st.json(status)
                    except Exception as e:
                        st.error(f"Auth check failed: {e}")
                asyncio.run(check_status())
            else:
                st.warning("No active session to check status.")
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            if st.session_state.agent:
                st.session_state.agent.clear_conversation_history()
            st.success("Chat history cleared!")

# Main chat interface
if not st.session_state.initialized:
    st.info("👆 Please initialize the MCP connection using the button in the sidebar to start chatting.")
else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if prompt := st.chat_input("Ask about your SharePoint files..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            with st.spinner("🤔 Thinking..."):
                response = asyncio.run(st.session_state.agent.run(prompt))
            with st.spinner("📡 Streaming response..."):
                final_response = stream_mcp_response(response, message_placeholder)
        st.session_state.messages.append({"role": "assistant", "content": final_response})

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8rem;'>
    Powered by MCP (Model Context Protocol) and Claude 3.5 Sonnet
</div>
""", unsafe_allow_html=True)

# Cleanup on app close
def cleanup():
    if st.session_state.client:
        try:
            asyncio.run(st.session_state.client.close_all_sessions())
        except:
            pass
import atexit
atexit.register(cleanup) 