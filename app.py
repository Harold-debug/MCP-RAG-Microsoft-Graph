import asyncio
import os
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from mcp_use import MCPAgent, MCPClient


async def run_memory_chat():
    """
    Run a memory chat with the agent.
    """
    # Create MCPClient from configuration dictionary
    load_dotenv()
    config_file = "mcp_with_hardcoded_auth.json"
    print("initializing chat")
    
    # Create client directly from config file
    client = MCPClient.from_config_file(config_file)
    
    # Create sessions for all configured servers
    print("Creating MCP sessions...")
    await client.create_all_sessions(auto_initialize=True)
    
    # Create LLM
    llm = ChatBedrock(model="anthropic.claude-3-5-sonnet-20240620-v1:0", region_name="us-east-1")

    # Create agent with the client and auto_initialize=True
    agent = MCPAgent(llm=llm, client=client, max_steps=30, memory_enabled=True, auto_initialize=True)
    
    print("====interactive mcp chat=====")
    try:
        while True:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Exiting...")
                break
            if user_input.lower() in ["clear", "reset"]:
                agent.clear_conversation_history()
                print("Memory cleared")
                continue
            print("Assistant: ", end="", flush=True)
            try:
                result = await agent.run(user_input)
                print(f"{result}")
            except Exception as e:
                print(f"Error: {e}")
                print("Please try again.")
    finally:
        if client and client.sessions:
            await client.close_all_sessions()

if __name__ == "__main__":
    asyncio.run(run_memory_chat())