import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent
)
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

class UserStoryMCPServer:
    def __init__(self):
        print("Initializing UserStoryMCPServer...")
        self.app = Server("user-story-generator")
        self.docs_service = None
        print("Setting up handlers...")
        self.setup_handlers()
        print("Handlers setup complete.")

    def setup_handlers(self):
        print("Registering list_tools handler...")
        @self.app.list_tools()
        async def list_tools() -> ListToolsResult:
            print("list_tools called")
            return ListToolsResult(
                tools=[
                    Tool(
                        name="read_google_doc",
                        description="Read content from a Google Doc using document ID",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "document_id": {
                                    "type": "string",
                                    "description": "Google Docs document ID (from the URL)"
                                }
                            },
                            "required": ["document_id"]
                        }
                    ),
                    Tool(
                        name="generate_user_stories",
                        description="Generate user stories from Google Doc content",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "document_id": {
                                    "type": "string",
                                    "description": "Google Docs document ID"
                                },
                                "feature_focus": {
                                    "type": "string",
                                    "description": "Optional: specific feature to focus on"
                                }
                            },
                            "required": ["document_id"]
                        }
                    )
                ]
            )

        print("Registering call_tool handler...")
        @self.app.call_tool()
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            print(f"call_tool called with: {request.params.name}")
            if request.params.name == "read_google_doc":
                return await self.read_google_doc(request.params.arguments)
            elif request.params.name == "generate_user_stories":
                return await self.generate_user_stories(request.params.arguments)
            else:
                raise ValueError(f"Unknown tool: {request.params.name}")

    async def authenticate_google(self):
        print("Authenticating with Google...")
        SCOPES = ['https://www.googleapis.com/auth/documents.readonly']
        creds = None

        if os.path.exists('token.json'):
            print("Loading existing credentials...")
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        if not creds or not creds.valid:
            print("Credentials invalid or expired, refreshing...")
            if creds and creds.expired and creds.refresh_token:
                print("Refreshing credentials...")
                creds.refresh(Request())
            else:
                print("Starting OAuth flow...")
                if not os.path.exists('credentials.json'):
                    raise FileNotFoundError("credentials.json not found. Please download it from Google Cloud Console.")

                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)

            print("Saving credentials to token.json...")
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        print("Building Google Docs service...")
        self.docs_service = build('docs', 'v1', credentials=creds)
        print("Google authentication complete.")

    async def read_google_doc(self, args: Dict[str, Any]) -> CallToolResult:
        try:
            print(f"Reading Google Doc with args: {args}")
            if not self.docs_service:
                await self.authenticate_google()

            document_id = args.get("document_id")
            if not document_id:
                print("Error: document_id is required")
                return CallToolResult(
                    content=[TextContent(type="text", text="Error: document_id is required")],
                    isError=True
                )

            print(f"Fetching document with ID: {document_id}")
            document = self.docs_service.documents().get(documentId=document_id).execute()
            content = self.extract_text_from_doc(document)
            
            print(f"Successfully read document: {document.get('title', 'Untitled')}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=("Document: " + document.get('title', 'Untitled') + 
                              "\n\nContent:\n" + content)
                    )
                ]
            )
        except Exception as e:
            print(f"Error reading document: {str(e)}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error reading document: {str(e)}")],
                isError=True
            )

    def extract_text_from_doc(self, document):
        print("Extracting text from document...")
        text = ""
        for element in document.get('body', {}).get('content', []):
            if 'paragraph' in element:
                paragraph = element['paragraph']
                for text_run in paragraph.get('elements', []):
                    if 'textRun' in text_run:
                        text += text_run['textRun']['content']
        print(f"Extracted {len(text)} characters of text")
        return text

    async def generate_user_stories(self, args: Dict[str, Any]) -> CallToolResult:
        try:
            print(f"Generating user stories with args: {args}")
            if not self.docs_service:
                await self.authenticate_google()

            document_id = args.get("document_id")
            feature_focus = args.get("feature_focus", "")

            if not document_id:
                print("Error: document_id is required")
                return CallToolResult(
                    content=[TextContent(type="text", text="Error: document_id is required")],
                    isError=True
                )

            print(f"Fetching document for story generation: {document_id}")
            document = self.docs_service.documents().get(documentId=document_id).execute()
            content = self.extract_text_from_doc(document)

            print(f"Generating stories from content (focus: {feature_focus})")
            user_stories = self.generate_stories_from_content(content, feature_focus)

            result = f"Generated User Stories from: {document.get('title', 'Untitled')}\n\n"
            result += "\n\n".join(user_stories)

            print(f"Generated {len(user_stories)} user stories")
            return CallToolResult(
                content=[TextContent(type="text", text=result)]
            )
        except Exception as e:
            print(f"Error generating stories: {str(e)}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error generating stories: {str(e)}")],
                isError=True
            )

    def generate_stories_from_content(self, content: str, feature_focus: str = "") -> List[str]:
        print("Analyzing content for user stories...")
        stories = []
        lines = content.split('\n')
        requirements = []

        # Enhanced keyword detection
        requirement_keywords = [
            'user', 'customer', 'shall', 'should', 'must', 'requirement',
            'need', 'want', 'allow', 'enable', 'provide', 'feature',
            'functionality', 'capability', 'able to', 'should be able',
            'system must', 'application should', 'interface will'
        ]

        # Extract requirements with better filtering
        for line in lines:
            line = line.strip()
            if len(line) > 20 and not line.startswith('#'):
                if any(keyword in line.lower() for keyword in requirement_keywords):
                    # Clean up the requirement
                    cleaned_req = line.replace('The system', 'the system')
                    cleaned_req = cleaned_req.replace('User', 'user')
                    requirements.append(cleaned_req)

        print(f"Found {len(requirements)} potential requirements")

        # Filter by feature focus if provided
        if feature_focus:
            print(f"Filtering by feature focus: {feature_focus}")
            requirements = [req for req in requirements 
                           if feature_focus.lower() in req.lower()]
            print(f"After filtering: {len(requirements)} requirements")

        # Generate better user stories
        for i, req in enumerate(requirements[:5]):
            story_num = i + 1
            
            # Extract the action from the requirement
            action = self.extract_action_from_requirement(req)
            benefit = self.extract_benefit_from_requirement(req)
            
            story = f"**User Story {story_num}:**\n"
            story += f"As a user, I want to {action}, so that {benefit}.\n\n"
            story += f"**Acceptance Criteria:**\n"
            story += f"• Given that I am a user with appropriate access\n"
            story += f"• When I {action}\n"
            story += f"• Then I should successfully complete the task\n"
            story += f"• And the system should provide appropriate feedback\n"
            story += f"• And the action should be logged/tracked as needed"
            
            stories.append(story)

        return stories if stories else self.generate_default_stories()

    def extract_action_from_requirement(self, requirement: str) -> str:
        """Extract the main action from a requirement."""
        req_lower = requirement.lower()
        
        # Common patterns to extract actions
        if 'able to' in req_lower:
            parts = req_lower.split('able to')
            if len(parts) > 1:
                return parts[1].strip()
        
        if 'shall' in req_lower:
            parts = req_lower.split('shall')
            if len(parts) > 1:
                return parts[1].strip()
        
        if 'should' in req_lower:
            parts = req_lower.split('should')
            if len(parts) > 1:
                return parts[1].strip()
        
        # Default fallback
        return requirement.lower()

    def extract_benefit_from_requirement(self, requirement: str) -> str:
        """Extract or infer the benefit from a requirement."""
        req_lower = requirement.lower()
        
        # Look for explicit benefits
        if 'so that' in req_lower:
            parts = req_lower.split('so that')
            if len(parts) > 1:
                return parts[1].strip()
        
        if 'in order to' in req_lower:
            parts = req_lower.split('in order to')
            if len(parts) > 1:
                return parts[1].strip()
        
        # Infer benefits based on keywords
        if any(word in req_lower for word in ['login', 'authenticate', 'sign in']):
            return "I can securely access the system"
        elif any(word in req_lower for word in ['search', 'find', 'locate']):
            return "I can quickly find what I need"
        elif any(word in req_lower for word in ['save', 'store', 'persist']):
            return "my data is preserved for future use"
        elif any(word in req_lower for word in ['delete', 'remove']):
            return "I can manage my data effectively"
        
        # Default benefit
        return "I can accomplish my goals efficiently"

    def generate_default_stories(self) -> List[str]:
        """Generate default user stories when no requirements are found."""
        print("No requirements found, generating default stories")
        return [
            "**User Story 1:**\nAs a user, I want to access the system, so that I can use its features.\n\n**Acceptance Criteria:**\n• Given that I have valid credentials\n• When I attempt to log in\n• Then I should be granted access\n• And I should see the main interface",
            
            "**User Story 2:**\nAs a user, I want to navigate through the application, so that I can find the features I need.\n\n**Acceptance Criteria:**\n• Given that I am logged in\n• When I use the navigation menu\n• Then I should be able to access different sections\n• And the interface should be intuitive and responsive"
        ]

async def main():
    print("Starting UserStoryMCPServer...")
    server = UserStoryMCPServer()
    print("Server initialized.")
    
    async with stdio_server() as streams:
        print("Streams acquired. Running server...")
        await server.app.run(
            streams[0],
            streams[1],
            server.app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
