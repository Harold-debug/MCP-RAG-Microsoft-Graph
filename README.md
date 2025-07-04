# MCP-RAG-Microsoft-Graph

 
A Streamlit-based chat interface that uses MCP (Model Context Protocol) to interact with Microsoft 365 services and other Microsoft services using AI-powered search and retrieval.
 
## Features
 
- 💬 **Interactive Chat Interface**: Beautiful Streamlit-based chat UI
- 🔍 **AI-Powered Search**: Uses Claude 3.5 Sonnet to understand and answer questions about Microsoft 365 files and services
- 🔗 **MCP Integration**: Leverages Model Context Protocol for seamless tool integration
- 🧠 **Conversation Memory**: Maintains context across chat sessions
- 🎨 **Modern UI**: Clean, responsive design with real-time chat experience
 
## Prerequisites
 
- Python 3.12+
- Poetry (for dependency management)
- Azure AD App Registration with Microsoft Graph permissions
- AWS Bedrock access for Claude 3.5 Sonnet
- Node.js (for Lokka MCP server)
 
## Setup
 
1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd sharepoint-rag-demo
   ```
 
2. **Install dependencies**:
   ```bash
   poetry install
   ```
 
3. **Configure Azure AD credentials**:

   **Option A: Interactive Authentication (For production)**
   - Create an Azure AD app registration
   - Grant Microsoft Graph permissions (Sites.Read.All, Files.Read.All, User.Read, Mail.Read, etc.)
   - **Do NOT generate a client secret** - interactive auth doesn't need one
   - Configure redirect URI: `http://localhost:3000` Platform: Mobile & Desktop App
   - Update `mcp_with_interactive_auth.json` with your credentials:
   ```json
   {
     "mcpServers": {
       "Lokka-Microsoft": {
         "command": "npx",
         "args": ["-y", "@merill/lokka"],
         "env": {
           "TENANT_ID": "your-tenant-id",
           "CLIENT_ID": "your-client-id",
           "USE_INTERACTIVE": "true",
           "REDIRECT_URI": "http://localhost:3000"
         }
       }
     }
   }
   ```

   **Option B: Hardcoded Authentication (Recommended for development)**
   - Create an Azure AD app registration
   - Grant Microsoft Graph permissions (Sites.Read.All, Files.Read.All, User.Read, Mail.Read, etc.)
   - Generate a client secret
   - Update `mcp_with_hardcoded_auth.json` with your credentials:
   ```json
   {
     "mcpServers": {
       "Lokka-Microsoft": {
         "command": "npx",
         "args": ["-y", "@merill/lokka"],
         "env": {
           "TENANT_ID": "your-tenant-id",
           "CLIENT_ID": "your-client-id",
           "CLIENT_SECRET": "your-client-secret-value"
         }
       }
     }
   }
   ```
 
4. **Set up AWS credentials** (for Bedrock):
   ```bash
   export AWS_ACCESS_KEY_ID=your-access-key
   export AWS_SECRET_ACCESS_KEY=your-secret-key
   export AWS_DEFAULT_REGION=us-east-1
   ```
 
## Usage
 
### Command Line Interface
 
Run the command-line version:
```bash
poetry run python app.py
```
 
### Web Interface
 
Run the Streamlit web app:
```bash
poetry run streamlit run streamlit_app.py
```
 
Then open your browser to `http://localhost:8501`
 
## How to Use
 
### Web Interface (Streamlit)
1. **Initialize Connection**: Click "Initialize MCP Connection" in the sidebar
   - For interactive auth: A browser window will open for authentication
   - Complete the Microsoft login process
   - The `mcp_use.MCPClient` automatically creates sessions and initializes tools
2. **Start Chatting**: Type questions about your Microsoft 365 files and services
   - The `mcp_use.MCPAgent` processes your queries and orchestrates MCP tools
   - Built-in conversation memory maintains context across interactions
3. **Examples**:
   - "What files do I have in my OneDrive/SharePoint?"
   - "Find documents about project planning"
   - "Show me recent presentations"
   - "What's in the shared documents folder?"
   - "Show me my recent emails"
   - "Find calendar events for this week"
   - "What Teams channels do I have access to?"

### Command Line Interface
The CLI version uses hardcoded authentication and provides a simple text-based interface for testing and development. It uses the same `mcp_use` library for MCP integration.
 
## Architecture
 
- **Frontend**: Streamlit for the web interface
- **Backend**: MCP (Model Context Protocol) for tool integration via `mcp_use` library
- **LLM**: Claude 3.5 Sonnet via AWS Bedrock
- **Microsoft 365 Integration**: Lokka MCP server for Microsoft Graph API access to SharePoint, OneDrive, Outlook, Teams, and other Microsoft services
- **Conversational Agent**: `mcp_use.MCPAgent` handles natural language processing and tool orchestration
- **MCP Client**: `mcp_use.MCPClient` manages MCP server connections and sessions
 
## Troubleshooting
 
### Common Issues
 
1. **"Tenant does not have a Microsoft 365 license"**: Your Azure AD tenant needs appropriate Microsoft 365 licensing
2. **Authentication errors**: 
   - For hardcoded auth: Ensure your client secret is the actual secret value, not the secret ID
   - For interactive auth: Make sure redirect URI is set to `http://localhost:3000`
3. **MCP connection issues**: Check that all config values are set correctly
4. **Interactive auth browser issues**: Ensure your browser allows popups and can access `http://localhost:3000`
 
### Debug Mode
 
For debugging, you can run the command-line version which provides more detailed error messages.
 
## Key Libraries Used

- **mcp_use**: Core library for MCP integration and conversational AI
  - `MCPClient.from_config_file()`: Creates MCP client from JSON configuration file
  - `MCPAgent`: Conversational agent that combines LLM with MCP tools for natural language interaction
  - Automatic session management with `create_all_sessions(auto_initialize=True)`
  - Built-in conversation memory with `memory_enabled=True`
  - Tool initialization with `auto_initialize=True`
  - Conversation history management with `clear_conversation_history()`
- **Lokka**: MCP server for Microsoft Graph API integration
- **Streamlit**: Web interface framework
- **LangChain AWS**: Claude 3.5 Sonnet integration via AWS Bedrock

## License
 
 
## Contributing
 
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request
 