import asyncio
import logging
from datetime import datetime, timedelta
import streamlit as st

from src.auth.token_manager import TokenManager
from src.mcp.client import MCPClientManager
from src.ui.chat import ChatInterface
from src.utils.config import load_msal_config, check_required_vars, init_session_state

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="SharePoint RAG Chat",
    page_icon="💬",
    layout="wide"
)

async def check_token_refresh() -> None:
    """Check if the access token needs to be refreshed."""
    if st.session_state.last_token_refresh:
        time_since_refresh = datetime.now() - st.session_state.last_token_refresh
        if time_since_refresh > timedelta(minutes=55):
            st.info("🔄 Refreshing access token...")
            await refresh_mcp()

async def refresh_mcp() -> None:
    """Refresh the MCP connection with a new token."""
    token = st.session_state.token_manager.get_token()
    if token:
        tools, agent = await st.session_state.mcp_client.initialize(token)
        if tools and agent:
            st.session_state.agent = agent
            st.session_state.last_token_refresh = datetime.now()
            st.success("✅ Token refreshed!")
        else:
            st.error("❌ Failed to refresh token")
            st.session_state.initialized = False
    else:
        st.error("❌ Failed to obtain new token")
        st.session_state.initialized = False

async def handle_chat() -> None:
    """Handle the chat interface and message processing."""
    if not st.session_state.initialized:
        st.info("👆 Please initialize the MCP connection using the button in the sidebar to start chatting.")
        return

    # Check if token needs refresh
    await check_token_refresh()
    
    # Display existing messages
    ChatInterface.display_messages(st.session_state.messages)
    
    # Handle new messages
    if prompt := st.chat_input("Ask about your SharePoint files..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            with st.spinner("🤔 Thinking..."):
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
                    logger.error(error_msg, exc_info=True)
                    ChatInterface.display_error(error_msg, message_placeholder)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

def main():
    """Main application entry point."""
    # Initialize session state
    init_session_state()
    
    # Check required variables
    missing_vars = check_required_vars()
    if missing_vars:
        st.error(f"❌ Missing required variables: {', '.join(missing_vars)}")
        st.error("Please set up your .streamlit/secrets.toml file with the required variables.")
        st.stop()
    
    # Header
    st.title("💬 SharePoint RAG Chat")
    st.markdown("Chat with your SharePoint files using AI-powered search and retrieval.")
    
    # Initialize components if not already done
    if "token_manager" not in st.session_state:
        st.session_state.token_manager = TokenManager(load_msal_config())
    if "mcp_client" not in st.session_state:
        st.session_state.mcp_client = MCPClientManager()
    
    # Sidebar
    with st.sidebar:
        st.header("Settings")
        if not st.session_state.initialized:
            st.warning("⚠️ MCP Not Connected")
            if st.button("🔄 Initialize MCP Connection"):
                with st.spinner("Initializing MCP connection..."):
                    st.info("🔐 Interactive Authentication Required")
                    token = st.session_state.token_manager.get_token()
                    
                    if token:
                        tools, agent = asyncio.run(st.session_state.mcp_client.initialize(token))
                        if tools and agent:
                            st.session_state.agent = agent
                            st.session_state.initialized = True
                            st.success("✅ MCP connection initialized!")
                        else:
                            st.error("❌ Failed to initialize MCP connection")
                    else:
                        st.error("❌ Failed to obtain access token")
        else:
            st.success("✅ MCP Connected")
            if st.button("🔍 Check Auth Status"):
                async def check_status(session):
                    return await session.call_tool("get-auth-status", {})
                
                try:
                    status = asyncio.run(st.session_state.mcp_client.execute_with_session(check_status))
                    st.json(status)
                except Exception as e:
                    st.error(f"❌ Failed to check status: {str(e)}")
                    
            if st.button("🗑️ Clear Chat History"):
                st.session_state.messages = []
                st.success("Chat history cleared!")
    
    # Run chat interface
    asyncio.run(handle_chat())
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.8rem;'>
        Powered by MCP (Model Context Protocol) and Claude 3.5 Sonnet
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()