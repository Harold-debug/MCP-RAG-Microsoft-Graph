# MCP-RAG-Microsoft-Graph

 
A Streamlit-based chat interface that uses MCP (Model Context Protocol) to interact with SharePoint files using AI-powered search and retrieval.
 
## Features
 
- 💬 **Interactive Chat Interface**: Beautiful Streamlit-based chat UI
- 🔍 **AI-Powered Search**: Uses Claude 3.5 Sonnet to understand and answer questions about SharePoint files
- 🔗 **MCP Integration**: Leverages Model Context Protocol for seamless tool integration
- 🧠 **Conversation Memory**: Maintains context across chat sessions
- 🎨 **Modern UI**: Clean, responsive design with real-time chat experience
 
## Prerequisites
 
- Python 3.12+
- Poetry (for dependency management)
- Azure AD App Registration with SharePoint permissions
- AWS Bedrock access for Claude 3.5 Sonnet
 
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
   - Create an Azure AD app registration
   - Grant SharePoint permissions (Sites.Read.All, Files.Read.All)
   - Generate a client secret
   - Update `all_mcp.json` with your credentials:
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
 
1. **Initialize Connection**: Click "Initialize MCP Connection" in the sidebar
2. **Start Chatting**: Type questions about your SharePoint files
3. **Examples**:
   - "What files do I have in my SharePoint?"
   - "Find documents about project planning"
   - "Show me recent presentations"
   - "What's in the shared documents folder?"
 
## Architecture
 
- **Frontend**: Streamlit for the web interface
- **Backend**: MCP (Model Context Protocol) for tool integration
- **LLM**: Claude 3.5 Sonnet via AWS Bedrock
- **SharePoint Integration**: Lokka MCP server for Microsoft Graph API access
 
## Troubleshooting
 
### Common Issues
 
1. **"Tenant does not have a SPO license"**: Your Azure AD tenant needs SharePoint Online licensing
2. **Authentication errors**: Ensure your client secret is the actual secret value, not the secret ID
3. **MCP connection issues**: Check that all environment variables are set correctly
 
### Debug Mode
 
For debugging, you can run the command-line version which provides more detailed error messages.
 
## License
 
MIT License - see LICENSE file for details.
 
## Contributing
 
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request
 