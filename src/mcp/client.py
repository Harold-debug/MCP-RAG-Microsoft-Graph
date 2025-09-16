import logging
from typing import Optional, Tuple, Any
import streamlit as st
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_aws import ChatBedrockConverse
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
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
                "USE_CLIENT_TOKEN": "true",
                # Provide an initial token; server also supports dynamic updates via tool
                "ACCESS_TOKEN": access_token
            }
        )
        return self.server_params
        
    async def initialize(self, access_token: str) -> Tuple[Optional[Any], Optional[Any]]:
        """
        Initialize the MCP client and create an agent.
        
        Args:
            access_token: The access token for Microsoft Graph API
            
        Returns:
            Tuple[Optional[Any], Optional[Any]]: The tools and agent if successful
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
                    
                    # Set the access token using Lokka's set-access-token tool
                    logger.info("Setting access token in Lokka...")
                    try:
                        await session.call_tool("set-access-token", {"accessToken": access_token})
                        logger.info("Successfully set access token in Lokka")
                    except Exception as e:
                        logger.warning(f"Could not set access token via tool (this is normal for some versions): {e}")
                    
                    # Initialize LangChain LLM using Bedrock Converse API (supports tools)
                    llm = ChatBedrockConverse(
                        model="anthropic.claude-3-5-sonnet-20240620-v1:0",
                        region_name="us-east-1"
                    )
                    
                    logger.info("Loading MCP tools...")
                    tools = await load_mcp_tools(session)
                    tool_names = [getattr(t, "name", str(t)) for t in tools]
                    logger.info("Successfully loaded %d tools: %s", len(tools), ", ".join(tool_names))
                    
                    # Build tool-calling agent prompt
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", "You are an assistant that uses MCP tools (Lokka) to answer questions about Microsoft Graph and SharePoint. Prefer 'get-auth-status' to diagnose auth and query tools to fetch tenant/site data. Be precise and cite which tool was used."),
                        MessagesPlaceholder("chat_history"),
                        ("human", "{input}"),
                        MessagesPlaceholder("agent_scratchpad"),
                    ])

                    # Create tool-calling agent and executor (verbose for step logs)
                    core_agent = create_tool_calling_agent(llm, tools, prompt)
                    agent = AgentExecutor(
                        agent=core_agent,
                        tools=tools,
                        verbose=True,
                        return_intermediate_steps=True,
                        handle_parsing_errors=True,
                    )
                    
                    st.success("✅ MCP Connected!")
                    return tools, agent
                    
        except Exception as e:
            error_msg = f"❌ Error initializing MCP: {str(e)}"
            logger.error(error_msg, exc_info=True)
            st.error(error_msg)
            return None, None
            
    async def execute_agent(self, input_text: str, chat_history: list):
        """
        Execute the agent with a new MCP session for each execution.
        
        Args:
            input_text: User input text
            chat_history: List of previous messages
            
        Returns:
            Agent execution result
        """
        if not self.server_params:
            raise ValueError("MCP client not initialized")
        
        try:
            # Create a new session for this execution
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Set the access token in this session
                    try:
                        await session.call_tool("set-access-token", {"accessToken": self.server_params.env["ACCESS_TOKEN"]})
                    except Exception as e:
                        logger.warning(f"Could not set access token in session: {e}")
                    
                    # Load tools for this session
                    tools = await load_mcp_tools(session)
                    
                    # Initialize LLM
                    llm = ChatBedrockConverse(
                        model="anthropic.claude-3-5-sonnet-20240620-v1:0",
                        region_name="us-east-1"
                    )
                    
                    # Build tool-calling agent prompt
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", """You are a helpful AI assistant that uses MCP tools (Lokka) to answer questions about Microsoft Graph and SharePoint data. 

Your approach should be:
1. Always start by checking authentication status with 'get-auth-status' to understand available permissions
2. Use appropriate Microsoft Graph API calls via 'Lokka-Microsoft' to fetch requested data
3. If you encounter errors, analyze them intelligently and provide helpful explanations
4. When errors occur, explain what they mean, why they happened, and suggest alternatives
5. Be empathetic and solution-oriented in your responses
6. Always cite which tools you used and what data you found

Common error scenarios and how to handle them:
- License errors: Explain the licensing issue and suggest alternative data sources
- Permission errors: Clarify what permissions are needed and how to request them
- Service unavailable: Suggest checking connectivity or trying different endpoints
- Data not found: Explain why the data might not exist and suggest related queries

Be precise, helpful, and always provide actionable next steps when possible."""),
                        MessagesPlaceholder("chat_history"),
                        ("human", "{input}"),
                        MessagesPlaceholder("agent_scratchpad"),
                    ])

                    # Create tool-calling agent and executor
                    core_agent = create_tool_calling_agent(llm, tools, prompt)
                    agent = AgentExecutor(
                        agent=core_agent,
                        tools=tools,
                        verbose=True,
                        return_intermediate_steps=True,
                        handle_parsing_errors=True,
                        max_iterations=3,  # Limit retries to prevent infinite loops
                        early_stopping_method="generate",  # Stop early if stuck
                    )
                    
                    # Execute the agent
                    try:
                        result = await agent.ainvoke({
                            "input": input_text,
                            "chat_history": chat_history
                        })
                        return result
                    except Exception as agent_error:
                        # If agent fails, let the agent itself handle the error by providing context
                        logger.warning(f"Agent execution failed: {agent_error}")
                        
                        # Create a new agent with error handling context
                        error_context = f"""
The previous attempt to fulfill your request encountered an error: {str(agent_error)}

Please analyze this error and provide a helpful response to the user. Consider:
1. What the error means in practical terms
2. Why this error might have occurred
3. What the user can do to resolve it or work around it
4. Be empathetic and constructive in your response

Original user request: {input_text}
"""
                        
                        # Create a new agent instance for error handling
                        error_llm = ChatBedrockConverse(
                            model="anthropic.claude-3-5-sonnet-20240620-v1:0",
                            region_name="us-east-1"
                        )
                        
                        error_prompt = ChatPromptTemplate.from_messages([
                            ("system", "You are a helpful AI assistant that explains technical errors clearly and concisely. When explaining errors, focus on:\n1. What happened (brief description of the error)\n2. Why it likely happened (root cause - permissions, licensing, connectivity, etc.)\n3. What can be done about it (specific actionable steps)\n\nKeep your response focused, practical, and solution-oriented. Be direct and helpful."),
                            ("human", "{input}")
                        ])
                        
                        error_agent = error_prompt | error_llm
                        
                        # Get the agent's response to the error
                        error_response = await error_agent.ainvoke({"input": error_context})
                        error_text = error_response.content if hasattr(error_response, 'content') else str(error_response)
                        
                        return {
                            "output": error_text,
                            "intermediate_steps": [("Error Analysis", str(agent_error))]
                        }
                    
        except Exception as e:
            logger.error(f"Agent execution error: {e}")
            # Return a graceful error response instead of raising
            return {
                "output": f"I'm experiencing technical difficulties: {str(e)}\n\nPlease try again or contact support if the issue persists.",
                "intermediate_steps": []
            }

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
                # Set the access token in this session
                try:
                    await session.call_tool("set-access-token", {"accessToken": self.server_params.env["ACCESS_TOKEN"]})
                except Exception as e:
                    logger.warning(f"Could not set access token in session: {e}")
                return await func(session)
            
    async def cleanup(self):
        """Clean up MCP resources."""
        # Nothing to clean up since we create fresh connections for each operation
        pass
        
    async def refresh_token(self, new_access_token: str) -> bool:
        """
        Refresh the access token in the current MCP session.
        
        Args:
            new_access_token: The new access token
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.server_params:
                logger.warning("No server params available for token refresh")
                return False
                
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    await session.call_tool("set-access-token", {"accessToken": new_access_token})
                    logger.info("Successfully refreshed access token in Lokka")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            return False 