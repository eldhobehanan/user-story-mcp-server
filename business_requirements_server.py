import asyncio
import json
import os
import re
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
import aiohttp
import base64
from urllib.parse import urlparse

class BusinessRequirementsUserStoryServer:
    def __init__(self):
        print("Initializing Business Requirements User Story Server...")
        self.app = Server("business-requirements-user-story-generator")
        self.github_token = os.getenv('GITHUB_TOKEN')
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
                        name="read_business_requirements",
                        description="Read business requirements document from Git repository",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "repo_url": {
                                    "type": "string",
                                    "description": "GitHub repository URL (e.g., https://github.com/user/repo)"
                                },
                                "file_path": {
                                    "type": "string",
                                    "description": "Path to business requirements file (e.g., 'requirements.md', 'docs/business-requirements.txt')"
                                },
                                "branch": {
                                    "type": "string",
                                    "description": "Branch name (default: main)",
                                    "default": "main"
                                }
                            },
                            "required": ["repo_url", "file_path"]
                        }
                    ),
                    Tool(
                        name="generate_user_stories_from_requirements",
                        description="Generate user stories from business requirements document",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "repo_url": {
                                    "type": "string",
                                    "description": "GitHub repository URL"
                                },
                                "file_path": {
                                    "type": "string",
                                    "description": "Path to business requirements file"
                                },
                                "branch": {
                                    "type": "string",
                                    "description": "Branch name (default: main)",
                                    "default": "main"
                                },
                                "user_personas": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "User personas/types (e.g., ['customer', 'admin', 'manager', 'developer'])",
                                    "default": ["user", "admin", "manager"]
                                },
                                "feature_focus": {
                                    "type": "string",
                                    "description": "Focus on specific feature/section (optional)"
                                },
                                "story_format": {
                                    "type": "string",
                                    "description": "Story format: 'standard', 'detailed', or 'agile'",
                                    "default": "standard"
                                },
                                "max_stories": {
                                    "type": "integer",
                                    "description": "Maximum number of stories to generate (default: 10)",
                                    "default": 10
                                }
                            },
                            "required": ["repo_url", "file_path"]
                        }
                    ),
                    Tool(
                        name="analyze_requirements_structure",
                        description="Analyze the structure and content of business requirements document",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "repo_url": {
                                    "type": "string",
                                    "description": "GitHub repository URL"
                                },
                                "file_path": {
                                    "type": "string",
                                    "description": "Path to business requirements file"
                                },
                                "branch": {
                                    "type": "string",
                                    "description": "Branch name (default: main)",
                                    "default": "main"
                                }
                            },
                            "required": ["repo_url", "file_path"]
                        }
                    )
                ]
            )

        @self.app.call_tool()
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            print(f"call_tool called with: {request.params.name}")
            if request.params.name == "read_business_requirements":
                return await self.read_business_requirements(request.params.arguments)
            elif request.params.name == "generate_user_stories_from_requirements":
                return await self.generate_user_stories_from_requirements(request.params.arguments)
            elif request.params.name == "analyze_requirements_structure":
                return await self.analyze_requirements_structure(request.params.arguments)
            else:
                raise ValueError(f"Unknown tool: {request.params.name}")

    def parse_github_url(self, repo_url: str) -> tuple[str, str]:
        """Parse GitHub URL to extract owner and repo name."""
        if repo_url.startswith('git@github.com:'):
            parts = repo_url.replace('git@github.com:', '').replace('.git', '').split('/')
        else:
            parsed = urlparse(repo_url)
            parts = parsed.path.strip('/').split('/')
        
        if len(parts) >= 2:
            return parts[0], parts[1]
        else:
            raise ValueError(f"Invalid GitHub URL format: {repo_url}")

    async def fetch_github_api(self, url: str) -> Dict[str, Any]:
        """Fetch data from GitHub API."""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'BusinessRequirementsUserStoryGenerator/1.0'
        }
        
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    raise ValueError("Repository or file not found")
                elif response.status == 403:
                    raise ValueError("Access denied. Check GitHub token or repository permissions")
                else:
                    raise ValueError(f"GitHub API error: {response.status}")

    async def get_file_content(self, owner: str, repo: str, file_path: str, branch: str = "main") -> str:
        """Get specific file content from GitHub API."""
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
        response = await self.fetch_github_api(url)
        
        if response.get('encoding') == 'base64':
            try:
                content = base64.b64decode(response['content']).decode('utf-8')
                return content
            except UnicodeDecodeError:
                # Try with different encoding
                content = base64.b64decode(response['content']).decode('utf-8', errors='ignore')
                return content
        else:
            return response.get('content', '')

    async def read_business_requirements(self, args: Dict[str, Any]) -> CallToolResult:
        """Read business requirements document from Git repository."""
        try:
            repo_url = args.get("repo_url")
            file_path = args.get("file_path")
            branch = args.get("branch", "main")

            if not repo_url or not file_path:
                return CallToolResult(
                    content=[TextContent(type="text", text="Error: repo_url and file_path are required")],
                    isError=True
                )

            owner, repo = self.parse_github_url(repo_url)
            print(f"Reading requirements from: {owner}/{repo}/{file_path} (branch: {branch})")

            # Get file content
            content = await self.get_file_content(owner, repo, file_path, branch)
            
            result_text = f"Business Requirements Document\n"
            result_text += f"Repository: {owner}/{repo}\n"
            result_text += f"File: {file_path}\n"
            result_text += f"Branch: {branch}\n"
            result_text += f"Content Length: {len(content)} characters\n\n"
            result_text += "=" * 50 + "\n"
            result_text += "DOCUMENT CONTENT:\n"
            result_text += "=" * 50 + "\n\n"
            result_text += content

            return CallToolResult(
                content=[TextContent(type="text", text=result_text)]
            )

        except Exception as e:
            error_msg = str(e)
            print(f"Error reading requirements: {error_msg}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error reading business requirements: {error_msg}")],
                isError=True
            )

    async def analyze_requirements_structure(self, args: Dict[str, Any]) -> CallToolResult:
        """Analyze the structure and content of business requirements document."""
        try:
            repo_url = args.get("repo_url")
            file_path = args.get("file_path")
            branch = args.get("branch", "main")

            owner, repo = self.parse_github_url(repo_url)
            content = await self.get_file_content(owner, repo, file_path, branch)

            # Analyze document structure
            analysis = self.analyze_document_structure(content)
            
            result_text = f"Requirements Document Analysis\n"
            result_text += f"Repository: {owner}/{repo}/{file_path}\n\n"
            
            result_text += f"📊 DOCUMENT STATISTICS:\n"
            result_text += f"• Total lines: {analysis['total_lines']}\n"
            result_text += f"• Total words: {analysis['total_words']}\n"
            result_text += f"• Total characters: {analysis['total_chars']}\n\n"
            
            result_text += f"🔍 STRUCTURE ANALYSIS:\n"
            result_text += f"• Headers found: {len(analysis['headers'])}\n"
            result_text += f"• Requirements identified: {len(analysis['requirements'])}\n"
            result_text += f"• Features mentioned: {len(analysis['features'])}\n"
            result_text += f"• User roles found: {len(analysis['user_roles'])}\n\n"
            
            if analysis['headers']:
                result_text += f"📋 DOCUMENT SECTIONS:\n"
                for i, header in enumerate(analysis['headers'][:10], 1):
                    result_text += f"{i}. {header}\n"
                if len(analysis['headers']) > 10:
                    result_text += f"... and {len(analysis['headers']) - 10} more sections\n"
                result_text += "\n"
            
            if analysis['requirements']:
                result_text += f"✅ SAMPLE REQUIREMENTS FOUND:\n"
                for i, req in enumerate(analysis['requirements'][:5], 1):
                    result_text += f"{i}. {req[:100]}{'...' if len(req) > 100 else ''}\n"
                if len(analysis['requirements']) > 5:
                    result_text += f"... and {len(analysis['requirements']) - 5} more requirements\n"
                result_text += "\n"
            
            if analysis['user_roles']:
                result_text += f"👥 USER ROLES IDENTIFIED:\n"
                for role in analysis['user_roles']:
                    result_text += f"• {role}\n"
                result_text += "\n"
            
            result_text += f"🎯 RECOMMENDED USER STORY APPROACH:\n"
            result_text += f"• Suggested user personas: {', '.join(analysis['user_roles'] or ['user', 'admin', 'manager'])}\n"
            result_text += f"• Estimated user stories: {analysis['estimated_stories']}\n"
            result_text += f"• Complexity level: {analysis['complexity_level']}\n"

            return CallToolResult(
                content=[TextContent(type="text", text=result_text)]
            )

        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error analyzing requirements: {str(e)}")],
                isError=True
            )

    async def generate_user_stories_from_requirements(self, args: Dict[str, Any]) -> CallToolResult:
        """Generate user stories from business requirements document."""
        try:
            repo_url = args.get("repo_url")
            file_path = args.get("file_path")
            branch = args.get("branch", "main")
            user_personas = args.get("user_personas", ["user", "admin", "manager"])
            feature_focus = args.get("feature_focus", "")
            story_format = args.get("story_format", "standard")
            max_stories = args.get("max_stories", 10)

            owner, repo = self.parse_github_url(repo_url)
            content = await self.get_file_content(owner, repo, file_path, branch)

            print(f"Generating user stories from {file_path} for personas: {user_personas}")

            # Extract requirements from content
            requirements = self.extract_requirements_from_document(content, feature_focus)
            
            # Generate user stories
            user_stories = self.generate_user_stories(
                requirements, user_personas, story_format, max_stories
            )

            result = f"USER STORIES GENERATED FROM BUSINESS REQUIREMENTS\n"
            result += f"Repository: {owner}/{repo}/{file_path}\n"
            result += f"Generated: {len(user_stories)} user stories\n"
            result += f"User Personas: {', '.join(user_personas)}\n"
            if feature_focus:
                result += f"Feature Focus: {feature_focus}\n"
            result += f"Story Format: {story_format}\n\n"
            result += "=" * 60 + "\n\n"
            
            result += "\n\n".join(user_stories)

            return CallToolResult(
                content=[TextContent(type="text", text=result)]
            )

        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error generating user stories: {str(e)}")],
                isError=True
            )

    def analyze_document_structure(self, content: str) -> Dict[str, Any]:
        """Analyze the structure of the business requirements document."""
        lines = content.split('\n')
        
        analysis = {
            'total_lines': len(lines),
            'total_words': len(content.split()),
            'total_chars': len(content),
            'headers': [],
            'requirements': [],
            'features': [],
            'user_roles': [],
            'estimated_stories': 0,
            'complexity_level': 'Medium'
        }

        # Find headers (markdown style or numbered)
        header_patterns = [
            r'^#{1,6}\s+(.+)$',  # Markdown headers
            r'^\d+\.\s+(.+)$',   # Numbered sections
            r'^[A-Z][A-Z\s]+:?\s*$',  # ALL CAPS headers
            r'^(.+)\n=+$',       # Underlined headers
            r'^(.+)\n-+$'        # Underlined headers with dashes
        ]
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            for pattern in header_patterns:
                match = re.match(pattern, line)
                if match:
                    header_text = match.group(1).strip()
                    if len(header_text) > 3 and len(header_text) < 100:
                        analysis['headers'].append(header_text)
                    break

        # Find requirements
        requirement_keywords = [
            'shall', 'should', 'must', 'will', 'needs to', 'required to',
            'user can', 'system shall', 'application must', 'feature should',
            'requirement:', 'req:', 'user story:', 'as a', 'i want', 'so that'
        ]
        
        for line in lines:
            line = line.strip()
            if len(line) > 20:
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in requirement_keywords):
                    analysis['requirements'].append(line)

        # Find user roles
        user_role_patterns = [
            r'\bas an?\s+([a-z]+(?:\s+[a-z]+)?)\b',
            r'\b([a-z]+(?:\s+[a-z]+)?)\s+(?:can|should|must|will)\b',
            r'\buser\s+type:?\s*([a-z]+(?:\s+[a-z]+)?)\b',
            r'\brole:?\s*([a-z]+(?:\s+[a-z]+)?)\b'
        ]
        
        content_lower = content.lower()
        for pattern in user_role_patterns:
            matches = re.findall(pattern, content_lower)
            for match in matches:
                role = match.strip()
                if role and len(role) < 20 and role not in ['user', 'system', 'application']:
                    if role not in analysis['user_roles']:
                        analysis['user_roles'].append(role)

        # Common user roles if none found
        if not analysis['user_roles']:
            common_roles = ['admin', 'manager', 'customer', 'operator', 'viewer']
            for role in common_roles:
                if role in content_lower:
                    analysis['user_roles'].append(role)

        # Estimate stories and complexity
        analysis['estimated_stories'] = min(max(len(analysis['requirements']), 3), 15)
        
        if len(analysis['requirements']) > 20:
            analysis['complexity_level'] = 'High'
        elif len(analysis['requirements']) < 5:
            analysis['complexity_level'] = 'Low'
        else:
            analysis['complexity_level'] = 'Medium'

        return analysis

    def extract_requirements_from_document(self, content: str, feature_focus: str = "") -> List[str]:
        """Extract actionable requirements from the business document."""
        lines = content.split('\n')
        requirements = []
        
        # Enhanced requirement detection patterns
        requirement_patterns = [
            r'(?:shall|should|must|will|needs?\s+to|required\s+to)\s+(.+)',
            r'(?:user|system|application)\s+(?:can|shall|should|must|will)\s+(.+)',
            r'(?:the\s+)?(?:system|application|software)\s+(?:provides?|enables?|allows?|supports?)\s+(.+)',
            r'(?:users?\s+)?(?:can|should|must|will|able\s+to)\s+(.+)',
            r'(?:feature|functionality|capability):\s*(.+)',
            r'(?:requirement|req):\s*(.+)',
            r'as\s+an?\s+\w+,?\s+i\s+want\s+(?:to\s+)?(.+?)(?:\s+so\s+that|$)',
        ]
        
        for line in lines:
            line = line.strip()
            if len(line) < 10 or line.startswith('#'):
                continue
                
            line_lower = line.lower()
            
            # Apply feature focus filter
            if feature_focus and feature_focus.lower() not in line_lower:
                continue
            
            for pattern in requirement_patterns:
                match = re.search(pattern, line_lower)
                if match:
                    requirement = match.group(1).strip()
                    if len(requirement) > 10:
                        # Clean up the requirement
                        requirement = re.sub(r'\s+', ' ', requirement)
                        requirements.append(requirement)
                    break
            
            # Also look for bullet points or numbered items that sound like requirements
            if (re.match(r'^[\*\-\+•]\s+', line) or re.match(r'^\d+\.?\s+', line)):
                cleaned_line = re.sub(r'^[\*\-\+•\d\.]\s*', '', line)
                if len(cleaned_line) > 15:
                    line_lower = cleaned_line.lower()
                    if any(word in line_lower for word in ['user', 'system', 'shall', 'should', 'must', 'can', 'will']):
                        requirements.append(cleaned_line)

        return requirements[:20]  # Limit to prevent too many stories

    def generate_user_stories(self, requirements: List[str], user_personas: List[str], 
                            story_format: str, max_stories: int) -> List[str]:
        """Generate user stories from extracted requirements."""
        if not requirements:
            return [self.generate_default_story(user_personas[0] if user_personas else "user")]
        
        stories = []
        
        for i, requirement in enumerate(requirements[:max_stories]):
            if i >= max_stories:
                break
                
            # Cycle through user personas
            user_persona = user_personas[i % len(user_personas)]
            
            # Extract action and benefit
            action = self.extract_action_from_requirement(requirement)
            benefit = self.extract_benefit_from_requirement(requirement)
            
            # Generate story based on format
            if story_format == "detailed":
                story = self.generate_detailed_story(i + 1, user_persona, action, benefit, requirement)
            elif story_format == "agile":
                story = self.generate_agile_story(i + 1, user_persona, action, benefit)
            else:  # standard
                story = self.generate_standard_story(i + 1, user_persona, action, benefit)
            
            stories.append(story)
        
        return stories

    def generate_standard_story(self, story_num: int, user_persona: str, action: str, benefit: str) -> str:
        """Generate a standard user story."""
        story = f"**User Story {story_num}:**\n"
        story += f"As a {user_persona}, I want to {action}, so that {benefit}.\n\n"
        story += f"**Acceptance Criteria:**\n"
        story += f"• Given that I am a {user_persona}\n"
        story += f"• When I {action}\n"
        story += f"• Then {benefit}\n"
        story += f"• And the system provides appropriate feedback"
        return story

    def generate_detailed_story(self, story_num: int, user_persona: str, action: str, 
                              benefit: str, original_requirement: str) -> str:
        """Generate a detailed user story."""
        story = f"**User Story {story_num}:**\n"
        story += f"As a {user_persona}, I want to {action}, so that {benefit}.\n\n"
        story += f"**Original Requirement:**\n{original_requirement}\n\n"
        story += f"**Acceptance Criteria:**\n"
        story += f"• Given that I am a {user_persona} with appropriate permissions\n"
        story += f"• When I {action}\n"
        story += f"• Then {benefit}\n"
        story += f"• And the system responds within acceptable time limits\n"
        story += f"• And appropriate logging and audit trails are maintained\n"
        story += f"• And error handling is graceful and informative\n\n"
        story += f"**Definition of Done:**\n"
        story += f"• Feature is implemented and tested\n"
        story += f"• User acceptance testing is completed\n"
        story += f"• Documentation is updated"
        return story

    def generate_agile_story(self, story_num: int, user_persona: str, action: str, benefit: str) -> str:
        """Generate an agile-focused user story."""
        story = f"**Story #{story_num}:** {action.title()}\n\n"
        story += f"**User Story:**\nAs a {user_persona}, I want to {action}, so that {benefit}.\n\n"
        story += f"**Acceptance Criteria:**\n"
        story += f"- [ ] Given a {user_persona}\n"
        story += f"- [ ] When they {action}\n"
        story += f"- [ ] Then {benefit}\n"
        story += f"- [ ] And system provides feedback\n\n"
        story += f"**Story Points:** TBD\n"
        story += f"**Priority:** TBD"
        return story

    def extract_action_from_requirement(self, requirement: str) -> str:
        """Extract the main action from a requirement."""
        req_lower = requirement.lower()
        
        # Remove common prefixes and clean up
        req_lower = re.sub(r'^(?:the\s+)?(?:system|application|user|users?)\s+(?:can|should|must|will|shall)\s+', '', req_lower)
        req_lower = re.sub(r'^(?:provides?|enables?|allows?|supports?|implements?)\s+', '', req_lower)
        req_lower = re.sub(r'^(?:to\s+)?', '', req_lower)
        
        # Clean up and return
        req_lower = req_lower.strip()
        if req_lower.endswith('.'):
            req_lower = req_lower[:-1]
            
        return req_lower if req_lower else requirement.lower()

    def extract_benefit_from_requirement(self, requirement: str) -> str:
        """Extract or infer the benefit from a requirement."""
        req_lower = requirement.lower()
        
        # Look for explicit benefits
        benefit_patterns = [
            r'so\s+that\s+(.+)',
            r'in\s+order\s+to\s+(.+)',
            r'to\s+ensure\s+(.+)',
            r'enabling\s+(.+)',
            r'resulting\s+in\s+(.+)'
        ]
        
        for pattern in benefit_patterns:
            match = re.search(pattern, req_lower)
            if match:
                return match.group(1).strip()
        
        # Infer benefits based on action keywords
        benefit_mapping = {
            'login': "I can securely access my account and data",
            'register': "I can create an account and use the system",
            'search': "I can quickly find the information I need",
            'view': "I can see relevant information",
            'edit': "I can keep information current and accurate",
            'delete': "I can remove unwanted or obsolete data",
            'create': "I can add new content to the system",
            'save': "my work is preserved and secure",
            'upload': "I can share files with the system",
            'download': "I can access files when needed",
            'manage': "I can control and organize my data",
            'configure': "I can customize the system to my needs",
            'monitor': "I can track important metrics and status",
            'approve': "I can control workflow and quality",
            'report': "I can generate insights and documentation"
        }
        
        for keyword, benefit in benefit_mapping.items():
            if keyword in req_lower:
                return benefit
                
        return "I can accomplish my business objectives efficiently"

    def generate_default_story(self, user_persona: str) -> str:
        """Generate a default story when no requirements are found."""
        return f"**User Story 1:**\nAs a {user_persona}, I want to use the system features, so that I can accomplish my goals efficiently.\n\n**Acceptance Criteria:**\n• Given that I have access to the system\n• When I use the available features\n• Then I can complete my tasks\n• And the system provides helpful feedback"

async def main():
    """Main entry point for the MCP server."""
    print("Starting Business Requirements User Story Server...")
    server = BusinessRequirementsUserStoryServer()
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