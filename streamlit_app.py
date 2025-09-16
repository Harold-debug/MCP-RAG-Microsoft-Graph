import streamlit as st
import asyncio
import logging
from datetime import datetime, timedelta
from src.mcp.client import MCPClientManager
from src.ui.chat import ChatInterface
from src.utils.config import init_session_state, get_graph_access_token_from_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

init_session_state()

# Page configuration
st.set_page_config(
    page_title="SharePoint RAG Chat",
    page_icon="💬",
    layout="wide"
)

if "mcp_client" not in st.session_state:
    st.session_state.mcp_client = MCPClientManager()

async def initialize_mcp():
    try:
        access_token = get_graph_access_token_from_config()
        if not access_token:
            st.error("❌ MS_GRAPH_ACCESS_TOKEN not set. Add it to .streamlit/secrets.toml or environment.")
            return None, None
        tools, agent = await st.session_state.mcp_client.initialize(access_token)
        if tools and agent:
            st.session_state.agent = agent
            st.session_state.last_token_refresh = datetime.now()
            return tools, agent
        return None, None
    except Exception as e:
        st.error(f"❌ Error initializing MCP: {str(e)}")
        return None, None

# Token refresh check
def check_token_refresh():
    if st.session_state.last_token_refresh:
        time_since_refresh = datetime.now() - st.session_state.last_token_refresh
        if time_since_refresh > timedelta(minutes=55):
            st.info("🔄 Refreshing access token...")
            asyncio.run(refresh_mcp())

async def refresh_mcp():
    access_token = get_graph_access_token_from_config()
    if not access_token:
        st.error("❌ MS_GRAPH_ACCESS_TOKEN not set.")
        st.session_state.initialized = False
        return
    success = await st.session_state.mcp_client.refresh_token(access_token)
    if success:
        st.session_state.last_token_refresh = datetime.now()
        st.success("✅ Token refreshed!")
    else:
        st.error("❌ Failed to refresh token")
        st.session_state.initialized = False

# (no local streaming helper needed; we use ChatInterface.stream_response)

# Header
st.title("💬 SharePoint RAG Chat")
st.markdown("Chat with your SharePoint files using AI-powered search and retrieval.")

with st.sidebar:
    st.header("Settings")
    if not st.session_state.initialized:
        st.warning("⚠️ MCP Not Connected")
        if st.button("🔄 Initialize MCP Connection"):
            with st.spinner("Initializing MCP connection..."):
                tools, agent = asyncio.run(initialize_mcp())
                if tools and agent:
                    st.session_state.initialized = True
                    st.success("✅ MCP connection initialized!")
                else:
                    st.error("❌ Failed to initialize MCP connection")
    else:
        st.success("✅ MCP Connected")
        if st.button("🔄 Force Token Refresh"):
            asyncio.run(refresh_mcp())
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.success("Chat history cleared!")

# Main chat interface
async def handle_chat():
    if not st.session_state.initialized:
        st.info("👆 Please initialize the MCP connection using the button in the sidebar to start chatting.")
    else:
        # Check if token needs refresh
        check_token_refresh()
        
        ChatInterface.display_messages(st.session_state.messages)
        
        if prompt := st.chat_input("Ask about your SharePoint files..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                with st.spinner("🤔 Thinking..."):
                    try:
                        try:
                            async def execute_agent(session):
                                response = await st.session_state.agent.ainvoke({
                                    "input": prompt,
                                    "chat_history": st.session_state.messages[:-1]
                                })
                                return response
                            response = await st.session_state.mcp_client.execute_with_session(execute_agent)
                            with st.spinner("📡 Streaming response..."):
                                final_response = ChatInterface.stream_response(response["output"], message_placeholder)
                            st.session_state.messages.append({"role": "assistant", "content": final_response})
                        except Exception as e:
                            error_msg = f"❌ Error processing request: {str(e)}"
                            logging.getLogger(__name__).error(error_msg, exc_info=True)
                            ChatInterface.display_error(error_msg, message_placeholder)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
                                
                    except Exception as e:
                        logger.error("Session error: %s", str(e), exc_info=True)
                        error_msg = f"❌ Error processing request: {str(e)}"
                        message_placeholder.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Run the async chat interface
if __name__ == "__main__":
    asyncio.run(handle_chat())

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8rem;'>
    Powered by MCP (Model Context Protocol)
</div>
""", unsafe_allow_html=True)