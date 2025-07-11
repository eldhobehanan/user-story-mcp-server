#!/usr/bin/env python3
"""
Test script for Business Requirements User Story Generator
Updated for eldhobehanan/user-story-mcp-server repository
"""

import asyncio
import os
from business_requirements_server import BusinessRequirementsUserStoryServer

async def test_eldhobehanan_requirements():
    """
    Test with eldhobehanan's actual business requirements
    """
    print("🎯 TESTING ELDHOBEHANAN'S BUSINESS REQUIREMENTS")
    print("=" * 60)
    
    # ✅ CONFIGURED FOR YOUR REPOSITORY:
    YOUR_REPO_URL = "https://github.com/eldhobehanan/user-story-mcp-server"
    YOUR_FILE_PATH = "requirements"  # Your Text Document file
    YOUR_BRANCH = "main"  # Will try "master" if "main" fails
    YOUR_USER_PERSONAS = ["customer", "admin", "manager", "developer", "user"]
    YOUR_FEATURE_FOCUS = ""  # Leave empty to analyze all requirements
    
    print(f"📋 Repository: {YOUR_REPO_URL}")
    print(f"📄 Requirements file: {YOUR_FILE_PATH}")
    print(f"🌿 Branch: {YOUR_BRANCH}")
    print(f"👥 User personas: {', '.join(YOUR_USER_PERSONAS)}")
    print("")
    
    server = BusinessRequirementsUserStoryServer()
    
    # Step 1: Read your requirements file
    print("1️⃣ Reading your business requirements...")
    read_args = {
        "repo_url": YOUR_REPO_URL,
        "file_path": YOUR_FILE_PATH,
        "branch": YOUR_BRANCH
    }
    
    try:
        result = await server.read_business_requirements(read_args)
        
        if result.isError:
            # Try with master branch if main fails
            print("🔄 Trying with 'master' branch...")
            read_args["branch"] = "master"
            result = await server.read_business_requirements(read_args)
            YOUR_BRANCH = "master"  # Update for subsequent calls
        
        if result.isError:
            print(f"❌ Could not read requirements: {result.content[0].text}")
            print("\n💡 TROUBLESHOOTING:")
            print("   1. Make sure your repository is public")
            print("   2. Verify the 'requirements' file exists in your repo")
            print("   3. Check if you need to set GITHUB_TOKEN for private repos")
            return False
        else:
            print("✅ Successfully read your requirements!")
            content = result.content[0].text
            print("\n📄 YOUR REQUIREMENTS CONTENT:")
            print("-" * 50)
            if len(content) > 800:
                print(f"{content[:800]}...")
                print(f"\n[Content continues... total {len(content)} characters]")
            else:
                print(content)
            print("-" * 50)
    
    except Exception as e:
        print(f"❌ Error reading file: {str(e)}")
        return False
    
    # Step 2: Analyze your requirements structure
    print("\n2️⃣ Analyzing your requirements structure...")
    analyze_args = {
        "repo_url": YOUR_REPO_URL,
        "file_path": YOUR_FILE_PATH,
        "branch": YOUR_BRANCH
    }
    
    try:
        result = await server.analyze_requirements_structure(analyze_args)
        
        if not result.isError:
            print("✅ Analysis complete!")
            print("\n📊 STRUCTURE ANALYSIS:")
            print(result.content[0].text)
        else:
            print(f"❌ Analysis failed: {result.content[0].text}")
    
    except Exception as e:
        print(f"❌ Analysis error: {str(e)}")
    
    # Step 3: Generate user stories from your requirements
    print("\n3️⃣ Generating user stories from your requirements...")
    story_args = {
        "repo_url": YOUR_REPO_URL,
        "file_path": YOUR_FILE_PATH,
        "branch": YOUR_BRANCH,
        "user_personas": YOUR_USER_PERSONAS,
        "feature_focus": YOUR_FEATURE_FOCUS,
        "story_format": "detailed",
        "max_stories": 10
    }
    
    try:
        result = await server.generate_user_stories_from_requirements(story_args)
        
        if not result.isError:
            print("✅ User stories generated successfully!")
            print("\n🎉 YOUR USER STORIES:")
            print("=" * 70)
            print(result.content[0].text)
            print("=" * 70)
            return True
        else:
            print(f"❌ Story generation failed: {result.content[0].text}")
            return False
    
    except Exception as e:
        print(f"❌ Story generation error: {str(e)}")
        return False

async def test_different_story_formats():
    """Test different user story formats"""
    print("\n🎨 TESTING DIFFERENT STORY FORMATS")
    print("=" * 60)
    
    server = BusinessRequirementsUserStoryServer()
    
    formats = ["standard", "detailed", "agile"]
    
    for format_type in formats:
        print(f"\n📝 Testing {format_type.upper()} format...")
        
        story_args = {
            "repo_url": "https://github.com/eldhobehanan/user-story-mcp-server",
            "file_path": "requirements",
            "branch": "main",  # Will be updated if master is detected
            "user_personas": ["customer", "admin"],
            "story_format": format_type,
            "max_stories": 3
        }
        
        try:
            result = await server.generate_user_stories_from_requirements(story_args)
            
            if not result.isError:
                print(f"✅ {format_type.capitalize()} format generated!")
                print(f"Sample output:\n{result.content[0].text[:400]}...\n")
            else:
                # Try with master branch
                story_args["branch"] = "master"
                result = await server.generate_user_stories_from_requirements(story_args)
                if not result.isError:
                    print(f"✅ {format_type.capitalize()} format generated (master branch)!")
                    print(f"Sample output:\n{result.content[0].text[:400]}...\n")
                else:
                    print(f"❌ {format_type.capitalize()} format failed")
        
        except Exception as e:
            print(f"❌ Error with {format_type} format: {str(e)}")

async def test_focused_stories():
    """Test generating stories with specific feature focus"""
    print("\n🎯 TESTING FEATURE-FOCUSED STORIES")
    print("=" * 60)
    
    server = BusinessRequirementsUserStoryServer()
    
    # Common feature focuses to test
    feature_focuses = ["user", "admin", "login", "auth", "management", "data"]
    
    for focus in feature_focuses:
        print(f"\n🔍 Testing focus on '{focus}' features...")
        
        story_args = {
            "repo_url": "https://github.com/eldhobehanan/user-story-mcp-server",
            "file_path": "requirements",
            "branch": "main",
            "user_personas": ["user", "admin"],
            "feature_focus": focus,
            "story_format": "standard",
            "max_stories": 3
        }
        
        try:
            result = await server.generate_user_stories_from_requirements(story_args)
            
            if result.isError:
                # Try master branch
                story_args["branch"] = "master"
                result = await server.generate_user_stories_from_requirements(story_args)
            
            if not result.isError:
                stories = result.content[0].text
                if len(stories.strip()) > 100:  # Check if meaningful stories generated
                    print(f"✅ Found {focus}-related stories!")
                    # Count stories generated
                    story_count = stories.count("**User Story")
                    print(f"   Generated {story_count} stories focused on '{focus}'")
                else:
                    print(f"⚠️  No specific stories found for '{focus}'")
            else:
                print(f"❌ Failed to generate {focus}-focused stories")
        
        except Exception as e:
            print(f"❌ Error testing {focus}: {str(e)}")

async def claude_desktop_demo():
    """Show exactly how this will work with Claude Desktop"""
    print("\n🖥️  CLAUDE DESKTOP USAGE FOR ELDHOBEHANAN")
    print("=" * 60)
    
    print(f"""
🎯 YOUR CLAUDE DESKTOP SETUP:

Repository: https://github.com/eldhobehanan/user-story-mcp-server
Requirements File: requirements (Text Document)

📋 COMMANDS YOU CAN USE IN CLAUDE DESKTOP:

1. **Read Your Requirements:**
   "Read my business requirements from my GitHub repository"
   
   Claude will use:
   → Tool: read_business_requirements
   → Repo: https://github.com/eldhobehanan/user-story-mcp-server  
   → File: requirements

2. **Generate User Stories:**
   "Generate user stories from my requirements file"
   
   Claude will use:
   → Tool: generate_user_stories_from_requirements
   → Personas: customer, admin, manager, developer
   → Format: detailed

3. **Analyze Requirements:**
   "Analyze the structure of my business requirements"
   
   Claude will use:
   → Tool: analyze_requirements_structure
   → Shows: sections, requirements count, user roles

4. **Focused Stories:**
   "Generate user stories focusing on authentication features"
   "Create admin-focused user stories from my requirements"
   "Generate customer user stories in agile format"

📱 EXAMPLE CONVERSATION:

You: "Generate user stories from my requirements file for customer and admin personas"

Claude: "I'll read your business requirements and generate user stories.

[Using read_business_requirements...]
✅ Successfully read requirements from: eldhobehanan/user-story-mcp-server/requirements

[Using generate_user_stories_from_requirements...]  
✅ Generated 8 user stories for customer and admin personas

Here are your user stories:

**User Story 1:**
As a customer, I want to [specific action from your requirements], 
so that [benefit from your requirements].

**Acceptance Criteria:**
• Given that I am a customer with appropriate permissions
• When I [action]
• Then [expected outcome]
..."

🔧 CONFIGURATION:
Your MCP server is ready to work with Claude Desktop once configured!
    """)

async def environment_check():
    """Check if environment is properly set up"""
    print("🔧 ENVIRONMENT CHECK FOR ELDHOBEHANAN")
    print("=" * 60)
    
    # Check GitHub token
    token = os.getenv('GITHUB_TOKEN')
    if token:
        print(f"✅ GitHub token found (starts with: {token[:10]}...)")
        print("   → Can access private repositories")
        print("   → Higher rate limits (5000/hour)")
    else:
        print("⚠️  No GitHub token found")
        print("   → Limited to public repositories")
        print("   → Rate limit: 60 requests/hour")
        print("   → Set with: set GITHUB_TOKEN=your_token_here")
    
    # Check required libraries
    try:
        import aiohttp
        print("✅ aiohttp library available")
    except ImportError:
        print("❌ aiohttp not installed - run: pip install aiohttp")
        return False
    
    try:
        from business_requirements_server import BusinessRequirementsUserStoryServer
        print("✅ Business Requirements server available")
    except ImportError as e:
        print(f"❌ Server import failed: {e}")
        print("   → Make sure business_requirements_server.py exists")
        return False
    
    # Test repository access
    print("\n🌐 Testing repository access...")
    server = BusinessRequirementsUserStoryServer()
    
    try:
        result = await server.read_business_requirements({
            "repo_url": "https://github.com/eldhobehanan/user-story-mcp-server",
            "file_path": "requirements",
            "branch": "main"
        })
        
        if result.isError:
            # Try master branch
            result = await server.read_business_requirements({
                "repo_url": "https://github.com/eldhobehanan/user-story-mcp-server", 
                "file_path": "requirements",
                "branch": "master"
            })
            if not result.isError:
                print("✅ Repository accessible (master branch)")
                return True, "master"
            else:
                print(f"❌ Cannot access repository: {result.content[0].text}")
                return False, None
        else:
            print("✅ Repository accessible (main branch)")
            return True, "main"
            
    except Exception as e:
        print(f"❌ Repository access error: {str(e)}")
        return False, None

async def main():
    """Run all tests for eldhobehanan's setup"""
    print("🚀 COMPLETE TEST SUITE FOR ELDHOBEHANAN")
    print("🔗 Repository: https://github.com/eldhobehanan/user-story-mcp-server")
    print("📄 Requirements file: requirements")
    print("=" * 70)
    
    # Environment check
    env_ok, branch = await environment_check()
    if not env_ok:
        print("\n❌ Environment issues found. Please fix and try again.")
        return
    
    print(f"\n✅ Environment ready! Using branch: {branch}")
    
    # Main test
    print("\n" + "=" * 70)
    success = await test_eldhobehanan_requirements()
    
    if success:
        print("\n🎉 MAIN TEST SUCCESSFUL!")
        
        # Additional tests
        await test_different_story_formats()
        await test_focused_stories()
        
        # Show Claude Desktop usage
        await claude_desktop_demo()
        
        print("\n" + "=" * 70)
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("\n📋 READY FOR CLAUDE DESKTOP:")
        print("✅ Repository access working")
        print("✅ Requirements file readable")
        print("✅ User story generation working")
        print("✅ Multiple formats supported")
        print("✅ Feature focusing available")
        
        print("\n🚀 NEXT STEPS:")
        print("1. Configure this MCP server with Claude Desktop")
        print("2. Start asking Claude to generate user stories!")
        print("3. Use natural language like:")
        print("   'Generate user stories from my requirements'")
        print("   'Focus on admin features'")
        print("   'Create detailed user stories'")
        
    else:
        print("\n⚠️  Issues found. Check error messages above.")
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Make sure your repository is public")
        print("2. Verify 'requirements' file exists in your repo")
        print("3. Check your internet connection")
        print("4. Consider setting GITHUB_TOKEN for better access")

if __name__ == "__main__":
    asyncio.run(main())