import streamlit as st
import asyncio
import os
import logging
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
import time
import msal
import json
from datetime import datetime, timedelta
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables first
load_dotenv()

# Check required environment variables
required_vars = ["AZURE_CLIENT_ID", "AZURE_TENANT_ID"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    st.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
    st.error("Please create a .env file with the required variables.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="SharePoint RAG Chat",
    page_icon="💬",
    layout="wide"
)

# MSAL Configuration
MSAL_CONFIG = {
    "client_id": os.getenv("AZURE_CLIENT_ID"),
    "authority": f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID')}",
    "scope": ["https://graph.microsoft.com/.default"],
    "redirect_uri": os.getenv("AZURE_REDIRECT_URI", "http://localhost:8501")
}

class TokenManager:
    def __init__(self):
        try:
            self.app = msal.PublicClientApplication(
                MSAL_CONFIG["client_id"],
                authority=MSAL_CONFIG["authority"]
            )
        except ValueError as e:
            st.error(f"❌ Failed to initialize MSAL: {str(e)}")
            st.error("Please check your Azure AD configuration.")
            raise
        
    def get_token(self):
        try:
            accounts = self.app.get_accounts()
            if accounts:
                result = self.app.acquire_token_silent(MSAL_CONFIG["scope"], account=accounts[0])
                if result:
                    return result['access_token']
            
            result = self.app.acquire_token_interactive(MSAL_CONFIG["scope"])
            if "access_token" in result:
                return result['access_token']
            return None
        except Exception as e:
            st.error(f"❌ Failed to acquire token: {str(e)}")
            return None

    def clear_token_cache(self):
        accounts = self.app.get_accounts()
        for account in accounts:
            self.app.remove_account(account)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent" not in st.session_state:
    st.session_state.agent = None
if "initialized" not in st.session_state:
    st.session_state.initialized = False
if "token_manager" not in st.session_state:
    st.session_state.token_manager = TokenManager()
if "last_token_refresh" not in st.session_state:
    st.session_state.last_token_refresh = None
if "mcp_read" not in st.session_state:
    st.session_state.mcp_read = None
if "mcp_write" not in st.session_state:
    st.session_state.mcp_write = None

def create_server_params(access_token):
    return StdioServerParameters(
        command="npx",
        args=["-y", "@merill/lokka"],
        env={
            "USE_ACCESS_TOKEN": "true",
            "MS_GRAPH_ACCESS_TOKEN": access_token,
            "AZURE_CLIENT_ID": os.getenv("AZURE_CLIENT_ID"),
            "AZURE_TENANT_ID": os.getenv("AZURE_TENANT_ID"),
            "AZURE_REDIRECT_URI": os.getenv("AZURE_REDIRECT_URI", "http://localhost:8501")
        }
    )

async def initialize_mcp():
    try:
        # Get access token
        access_token = st.session_state.token_manager.get_token()
        if not access_token:
            error_msg = "Failed to obtain access token"
            logger.error(error_msg)
            st.error(error_msg)
            return None, None
            
        # Create MCP server parameters
        server_params = create_server_params(access_token)
        logger.info("Creating MCP connection with params: %s", server_params)
        
        st.info("🔧 Initializing MCP connection...")
        
        # Initialize MCP client
        async with stdio_client(server_params) as (read, write):
            st.session_state.mcp_read = read
            st.session_state.mcp_write = write
            
            # Initialize LangChain components
            llm = ChatBedrock(
                model="anthropic.claude-3-5-sonnet-20240620-v1:0",
                region_name="us-east-1",
                streaming=True
            )
            
            # Create agent prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful AI assistant that helps users interact with their SharePoint files and Microsoft Graph data. Use the available tools to help answer questions."),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad")
            ])
            
            # Load tools and create agent
            async with ClientSession(st.session_state.mcp_read, st.session_state.mcp_write) as session:
                # Initialize the session
                await session.initialize()
                
                logger.info("Loading MCP tools...")
                tools = await load_mcp_tools(session)
                logger.info("Successfully loaded %d tools", len(tools))
                
                # Create agent with proper async configuration
                agent = AgentExecutor(
                    agent=(
                        prompt
                        | llm.bind_tools(tools)
                        | format_to_openai_function_messages
                        | OpenAIFunctionsAgentOutputParser()
                    ),
                    tools=tools,
                    verbose=True,
                    handle_parsing_errors=True  # Add error handling for parsing
                )
                
                st.success("✅ MCP Connected!")
                
                # Store token refresh time
                st.session_state.last_token_refresh = datetime.now()
                
                return tools, agent
            
    except Exception as e:
        error_msg = f"❌ Error initializing MCP: {str(e)}"
        logger.error(error_msg, exc_info=True)
        st.error(error_msg)
        return None, None

# Token refresh check
def check_token_refresh():
    if st.session_state.last_token_refresh:
        time_since_refresh = datetime.now() - st.session_state.last_token_refresh
        if time_since_refresh > timedelta(minutes=55):
            st.info("🔄 Refreshing access token...")
            asyncio.run(refresh_mcp())

async def refresh_mcp():
    tools, agent = await initialize_mcp()
    if tools and agent:
        st.session_state.agent = agent
        st.success("✅ Token refreshed!")
    else:
        st.error("❌ Failed to refresh token")
        st.session_state.initialized = False

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
                st.info("🔐 Interactive Authentication Required")
                tools, agent = asyncio.run(initialize_mcp())
                if tools and agent:
                    st.session_state.agent = agent
                    st.session_state.initialized = True
                    st.success("✅ MCP connection initialized!")
                else:
                    st.error("❌ Failed to initialize MCP connection")
    else:
        st.success("✅ MCP Connected")
        if st.button("🔍 Check Auth Status"):
            if st.session_state.mcp_read and st.session_state.mcp_write:
                async def check_status():
                    async with ClientSession(st.session_state.mcp_read, st.session_state.mcp_write) as session:
                        status = await session.call_tool("get-auth-status", {})
                        st.json(status)
                asyncio.run(check_status())
            else:
                st.warning("No active MCP session.")
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
                    try:
                        # Create a new session for this interaction
                        async with ClientSession(st.session_state.mcp_read, st.session_state.mcp_write) as session:
                            # Initialize the session
                            await session.initialize()
                            
                            # Get the response from the agent
                            try:
                                response = await st.session_state.agent.ainvoke(
                                    {
                                        "input": prompt,
                                        "chat_history": st.session_state.messages[:-1]  # Exclude current message
                                    }
                                )
                                
                                with st.spinner("📡 Streaming response..."):
                                    final_response = stream_mcp_response(response["output"], message_placeholder)
                                st.session_state.messages.append({"role": "assistant", "content": final_response})
                                
                            except Exception as e:
                                logger.error("Agent execution error: %s", str(e), exc_info=True)
                                error_msg = f"❌ Error executing agent: {str(e)}"
                                message_placeholder.error(error_msg)
                                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                                
                    except Exception as e:
                        logger.error("Session error: %s", str(e), exc_info=True)
                        error_msg = f"❌ Error processing request: {str(e)}"
                        message_placeholder.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Run the async chat interface
if __name__ == "__main__":
    asyncio.run(handle_chat())

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8rem;'>
    Powered by MCP (Model Context Protocol) and Claude 3.5 Sonnet
</div>
""", unsafe_allow_html=True)

# Cleanup on app close
async def cleanup():
    if st.session_state.mcp_read and st.session_state.mcp_write:
        try:
            async with ClientSession(st.session_state.mcp_read, st.session_state.mcp_write) as session:
                await session.close()
        except:
            pass

import atexit
atexit.register(lambda: asyncio.run(cleanup())) 