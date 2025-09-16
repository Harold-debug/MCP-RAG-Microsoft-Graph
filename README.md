
A powerful AI-powered chat application that enables natural language interaction with SharePoint data through Microsoft Graph API.

## 🚀 Features

- **Natural Language Queries**: Ask questions about your SharePoint sites, files, and content
- **Interactive Authentication**: MSAL-based device code authentication with automatic token refresh
- **Real-time Debugging**: Transparent tool execution with step-by-step visibility
- **Intelligent Error Handling**: Graceful error analysis with helpful explanations and alternatives

## 🏗️ Architecture

### Backbone Stack

- **AI Framework**: LangChain + LangGraph (Agent Orchestration)
- **Tool Protocol**: MCP (Model Context Protocol)
- **SharePoint Integration**: Lokka (MCP Server for Microsoft Graph)
- **Authentication**: MSAL (Microsoft Authentication Library)

### System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │────│  LangChain Agent │────│   AWS Bedrock   │
│   (Chat Interface)│    │  (Tool Orchestrator)│    │  (Claude 3.5)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  MCP Client     │────│   Lokka Server   │────│ Microsoft Graph │
│  (Tool Manager) │    │  (Graph Wrapper) │    │      API        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🔐 Authentication & Authorization

### MSAL Interactive Authentication

The application uses Microsoft Authentication Library (MSAL) with device code flow for secure, user-consented access to SharePoint data.

#### Configuration
```bash
# Azure App Registration
AZURE_CLIENT_ID=your-azure-app-id
AZURE_TENANT_ID=your-tenant-id
```

#### Authentication Process
1. **User Initiation**: User starts a chat session
2. **Device Code**: Application displays device code and URL
3. **User Authentication**: User authenticates with corporate credentials
4. **Token Acquisition**: Application receives access token for SharePoint
5. **Automatic Refresh**: Tokens refresh automatically before expiry

### SharePoint Permission Scopes

The application requests specific Microsoft Graph permissions for SharePoint access:

```python
scopes = [
    "User.Read",           # User profile access
    "Sites.Search.All",      # SharePoint site access
    "Projects.Read",           # Email access
    "MyFiles.Read",
]
```

### Security Features

- **User-Consented Access**: Each user authenticates with their own credentials
- **Permission Respect**: Only accesses SharePoint data user has rights to view
- **Proactive Token Refresh**: Automatic renewal 5 minutes before expiry
- **Read-Only Access**: No write, modify, or delete operations
- **Tenant Isolation**: Access limited to authenticated user's SharePoint data
- **Audit Logging**: All authentication events tracked

## 🛠️ Installation

### Prerequisites

- Python 3.12+
- Microsoft 365 tenant with SharePoint Online licenses
- AWS account with Bedrock access
- Azure App Registration with SharePoint permissions

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd MCP-RAG-Microsoft-Graph
```

2. **Install dependencies**
```bash
poetry install

```

3. **Configure environment variables**
```bash
cp env.example .env
# Edit .env with your configuration
```

4. **Set up Azure App Registration**
   - Go to Azure Portal > App registrations
   - Create new registration
   - Enable "Allow public client flows"
   - Add redirect URI: `http://localhost`
   - Add Microsoft Graph API permissions for SharePoint:
     - `User.Read`

   - Grant admin consent for SharePoint permissions
      - `Sites.Search.All`
     - `Projects.Read`
     - `MyFiles.Read`

5. **Configure AWS Bedrock**
   - Ensure Claude 3.5 Sonnet model access
   - Set up AWS credentials

### Environment Configuration

Create a `.env` file or use Streamlit secrets:

```toml
# .env file
AZURE_CLIENT_ID=your_azure_app_id
AZURE_TENANT_ID=your_tenant_id

# Or .streamlit/secrets.toml
[secrets]
AZURE_CLIENT_ID = "your_azure_app_id"
AZURE_TENANT_ID = "your_tenant_id"
```

## 🚀 Usage

### Starting the Application

```bash
poetry run streamlit run streamlit_app.py
```

### Using the Chat Interface

1. **Initialize Connection**: Click "Initialize MCP Connection" in the sidebar
2. **Authenticate**: Complete device code authentication with your corporate credentials
3. **Start Chatting**: Ask questions about your SharePoint data

### Example Queries

- "Show me my SharePoint sites"
- "What files do I have in my SharePoint document library?"
- "Search for documents about project planning"
- "List all SharePoint lists I have access to"

## 🔧 Configuration

### Agent Configuration

The application uses a sophisticated agent system with:

- **Tool-Calling Agent**: LangChain agent with MCP tool integration
- **Error Handling**: Intelligent error analysis and user guidance
- **Retry Logic**: Limited iterations with early stopping

### MCP Tools

Available tools for SharePoint interaction:

- **`get-auth-status`**: Verify authentication state
- **`Lokka-Microsoft`**: Execute Microsoft Graph API calls for SharePoint
- **`set-access-token`**: Update authentication tokens
- **`add-graph-permission`**: Manage API permissions

## 🐛 Error Handling

### Intelligent Error Management

The application implements a two-tier error handling system:

1. **Primary Agent**: Attempts to fulfill user requests
2. **Error Analysis Agent**: Analyzes failures and provides explanations

### Common Error Scenarios

- **SharePoint License Errors**: Explains when SharePoint Online licenses are missing
- **Permission Errors**: Clarifies SharePoint access rights and next steps
- **Service Unavailable**: Suggests connectivity checks or alternative SharePoint endpoints
- **Data Not Found**: Explains why SharePoint data might not exist or be accessible

### Error Response Format

```
What happened: Brief description of the error
Why it happened: Root cause analysis
What to do: Specific actionable steps
```

## 📊 Debug Information

The application provides comprehensive debugging capabilities:

- **Authentication Status**: Current token state and permissions
- **Tool Execution**: Step-by-step tool calls and responses
- **Error Analysis**: Detailed error context and resolution steps
- **Session State**: Token refresh times and expiry information

## 🔒 Security Considerations

### Data Protection

- **No Data Persistence**: SharePoint data not stored locally
- **Read-Only Access**: No write, modify, or delete operations on SharePoint
- **Secure Communication**: All API calls over HTTPS
- **Token Security**: Automatic refresh and cleanup
- **Permission Respect**: Only accesses SharePoint data user has rights to view



## 🆘 Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Verify Azure app registration configuration
   - Check token validity and SharePoint scopes
   - Ensure device code authentication is working

2. **SharePoint Permission Errors**
   - Verify Microsoft Graph API permissions for SharePoint
   - Check admin consent status for SharePoint permissions
   - Validate SharePoint Online licensing

3. **Tool Execution Errors**
   - Check MCP server connectivity
   - Verify Lokka installation
   - Review debug logs for API calls

### Getting Help

- Check the debug panel for detailed error information
- Review authentication status in the sidebar
- Examine intermediate steps for tool execution details
- Contact support with specific error messages

## 🔄 Updates & Maintenance

### Token Management

- Tokens automatically refresh before expiry
- Manual refresh available via sidebar button
- Session persistence across application restarts

### Monitoring

- Authentication events logged
- Tool execution tracked
- Error patterns monitored

---