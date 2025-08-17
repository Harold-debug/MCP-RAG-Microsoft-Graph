import logging
from typing import Optional, Tuple, Any
import streamlit as st
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import AgentExecutor
from langchain_aws import ChatBedrock
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from ..utils.config import get_config_value

logger = logging.getLogger(__name__)

class MCPClientManager:
    """Manages MCP client sessions and agent interactions."""
    
    def __init__(self):
        """Initialize the MCP client manager."""
        self.server_params = None
        
    def create_server_params(self, access_token: str) -> StdioServerParameters:
        """
        Create MCP server parameters with the given access token.
        
        Args:
            access_token: The access token for Microsoft Graph API
            
        Returns:
            StdioServerParameters: The configured server parameters
        """
        self.server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@merill/lokka"],
            env={
                "USE_ACCESS_TOKEN": "true",
                "MS_GRAPH_ACCESS_TOKEN": access_token,
                "AZURE_CLIENT_ID": get_config_value("AZURE_CLIENT_ID"),
                "AZURE_TENANT_ID": get_config_value("AZURE_TENANT_ID"),
                "AZURE_REDIRECT_URI": get_config_value("AZURE_REDIRECT_URI", "http://localhost:8501")
            }
        )
        return self.server_params
        
    async def initialize(self, access_token: str) -> Tuple[Optional[Any], Optional[AgentExecutor]]:
        """
        Initialize the MCP client and create an agent.
        
        Args:
            access_token: The access token for Microsoft Graph API
            
        Returns:
            Tuple[Optional[Any], Optional[AgentExecutor]]: The tools and agent if successful
        """
        try:
            # Create MCP server parameters
            server_params = self.create_server_params(access_token)
            logger.info("Creating MCP connection with params: %s", server_params)
            
            st.info("🔧 Initializing MCP connection...")
            
            # Initialize MCP client and load tools
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the session
                    await session.initialize()
                    
                    # Create agent prompt
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", "You are a helpful AI assistant that helps users interact with their SharePoint files and Microsoft Graph data. Use the available tools to help answer questions."),
                        MessagesPlaceholder(variable_name="chat_history"),
                        ("human", "{input}"),
                        MessagesPlaceholder(variable_name="agent_scratchpad")
                    ])
                    
                    # Initialize LangChain components
                    llm = ChatBedrock(
                        model="anthropic.claude-3-5-sonnet-20240620-v1:0",
                        region_name=get_config_value("AWS_DEFAULT_REGION", "us-east-1"),
                        streaming=True
                    )
                    
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
                        handle_parsing_errors=True
                    )
                    
                    st.success("✅ MCP Connected!")
                    return tools, agent
                    
        except Exception as e:
            error_msg = f"❌ Error initializing MCP: {str(e)}"
            logger.error(error_msg, exc_info=True)
            st.error(error_msg)
            return None, None
            
    async def execute_with_session(self, func):
        """
        Execute a function within a new MCP session.
        
        Args:
            func: Async function to execute with the session
        """
        if not self.server_params:
            raise ValueError("MCP client not initialized")
            
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await func(session)
            
    async def cleanup(self):
        """Clean up MCP resources."""
        # Nothing to clean up since we create fresh connections for each operation
        pass 