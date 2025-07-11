#!/usr/bin/env python3
"""
Test script for Git User Story Generator
This tests the functionality with real GitHub repositories
"""

import asyncio
import os
from server import GitUserStoryMCPServer

# Test repositories - you can replace these with your own
TEST_REPOSITORIES = [
    {
        "name": "Simple Example",
        "url": "https://github.com/octocat/Hello-World",
        "branch": "master",  # This repo uses 'master' not 'main'
        "description": "GitHub's simple example repository"
    },
    {
        "name": "React Project",
        "url": "https://github.com/facebook/react",
        "branch": "main",
        "description": "Popular React JavaScript library"
    },
    {
        "name": "VS Code",
        "url": "https://github.com/microsoft/vscode",
        "branch": "main", 
        "description": "Microsoft Visual Studio Code editor"
    }
]

class TestGitUserStoryGenerator:
    def __init__(self):
        self.server = GitUserStoryMCPServer()
        
    async def test_basic_connection(self):
        """Test 1: Basic GitHub API connection"""
        print("🔧 TEST 1: Testing GitHub API connection...")
        
        try:
            # Test with the simplest possible repository
            args = {
                "repo_url": "https://github.com/octocat/Hello-World",
                "branch": "master"
            }
            
            result = await self.server.analyze_git_repo(args)
            
            if result.isError:
                print("❌ Basic connection failed:", result.content[0].text)
                return False
            else:
                print("✅ GitHub API connection working!")
                print("📄 Sample content preview:")
                print(result.content[0].text[:200] + "...\n")
                return True
                
        except Exception as e:
            print(f"❌ Connection test failed: {str(e)}")
            return False

    async def test_user_story_generation(self):
        """Test 2: User story generation"""
        print("📝 TEST 2: Testing user story generation...")
        
        try:
            args = {
                "repo_url": "https://github.com/octocat/Hello-World",
                "branch": "master",
                "user_types": ["developer", "user"]
            }
            
            result = await self.server.generate_user_stories_from_repo(args)
            
            if result.isError:
                print("❌ User story generation failed:", result.content[0].text)
                return False
            else:
                print("✅ User story generation working!")
                print("📖 Generated stories preview:")
                print(result.content[0].text[:300] + "...\n")
                return True
                
        except Exception as e:
            print(f"❌ User story test failed: {str(e)}")
            return False

    async def test_with_your_repo(self, your_repo_url):
        """Test 3: Test with your specific repository"""
        print(f"🎯 TEST 3: Testing with your repository: {your_repo_url}")
        
        try:
            # First analyze the repo
            analyze_args = {
                "repo_url": your_repo_url,
                "branch": "main"  # Try main first, then master if it fails
            }
            
            result = await self.server.analyze_git_repo(analyze_args)
            
            if result.isError and "master" not in result.content[0].text:
                # Try with master branch
                print("🔄 Trying with 'master' branch...")
                analyze_args["branch"] = "master"
                result = await self.server.analyze_git_repo(analyze_args)
            
            if result.isError:
                print("❌ Your repo analysis failed:", result.content[0].text)
                return False
            
            print("✅ Your repository analysis successful!")
            print("📋 Repository info:")
            print(result.content[0].text[:400] + "...\n")
            
            # Now generate user stories
            story_args = {
                "repo_url": your_repo_url,
                "branch": analyze_args["branch"],
                "user_types": ["user", "admin", "developer"]
            }
            
            story_result = await self.server.generate_user_stories_from_repo(story_args)
            
            if story_result.isError:
                print("❌ User story generation failed:", story_result.content[0].text)
                return False
            
            print("📚 Generated user stories for your repo:")
            print(story_result.content[0].text)
            return True
            
        except Exception as e:
            print(f"❌ Your repo test failed: {str(e)}")
            return False

    async def test_feature_extraction(self):
        """Test 4: Feature extraction from code"""
        print("🔍 TEST 4: Testing feature extraction...")
        
        try:
            args = {
                "repo_url": "https://github.com/microsoft/vscode",
                "file_patterns": ["*.json", "*.md"]
            }
            
            result = await self.server.extract_features_from_code(args)
            
            if result.isError:
                print("❌ Feature extraction failed:", result.content[0].text)
                return False
            else:
                print("✅ Feature extraction working!")
                print("🔧 Extracted features preview:")
                print(result.content[0].text[:200] + "...\n")
                return True
                
        except Exception as e:
            print(f"❌ Feature extraction test failed: {str(e)}")
            return False

    async def test_different_repositories(self):
        """Test 5: Test with different types of repositories"""
        print("🌐 TEST 5: Testing with different repository types...")
        
        success_count = 0
        
        for repo_info in TEST_REPOSITORIES:
            print(f"\n📦 Testing {repo_info['name']}: {repo_info['description']}")
            
            try:
                args = {
                    "repo_url": repo_info["url"],
                    "branch": repo_info["branch"]
                }
                
                result = await self.server.analyze_git_repo(args)
                
                if not result.isError:
                    print(f"  ✅ {repo_info['name']} - Success!")
                    success_count += 1
                else:
                    print(f"  ❌ {repo_info['name']} - Failed: {result.content[0].text[:100]}")
                    
            except Exception as e:
                print(f"  ❌ {repo_info['name']} - Error: {str(e)}")
        
        print(f"\n📊 Repository test results: {success_count}/{len(TEST_REPOSITORIES)} successful")
        return success_count > 0

    async def check_environment(self):
        """Check environment setup"""
        print("🔧 ENVIRONMENT CHECK:")
        
        # Check GitHub token
        token = os.getenv('GITHUB_TOKEN')
        if token:
            print(f"✅ GitHub token found (starts with: {token[:10]}...)")
        else:
            print("⚠️  No GitHub token found - you'll have rate limits (60 requests/hour)")
            print("   Set token with: export GITHUB_TOKEN=your_token_here")
        
        # Check required imports
        try:
            import aiohttp
            print("✅ aiohttp library available")
        except ImportError:
            print("❌ aiohttp not installed - run: pip install aiohttp")
            return False
            
        print("")
        return True

async def main():
    """Run all tests"""
    print("🚀 STARTING GIT USER STORY GENERATOR TESTS")
    print("=" * 50)
    
    tester = TestGitUserStoryGenerator()
    
    # Check environment first
    env_ok = await tester.check_environment()
    if not env_ok:
        print("❌ Environment setup issues found. Please fix and try again.")
        return
    
    # Run tests
    tests = [
        ("Basic Connection", tester.test_basic_connection),
        ("User Story Generation", tester.test_user_story_generation),
        ("Feature Extraction", tester.test_feature_extraction),
        ("Different Repositories", tester.test_different_repositories),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {str(e)}")
            results.append((test_name, False))
    
    # Test with user's repository if provided
    print(f"\n{'='*20} Your Repository Test {'='*20}")
    print("💡 To test with YOUR repository, edit this script and add your repo URL")
    print("   Or run: await tester.test_with_your_repo('https://github.com/yourusername/yourrepo')")
    
    # Print summary
    print(f"\n{'='*20} TEST SUMMARY {'='*20}")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is working correctly.")
        print("\n🚀 Next steps:")
        print("   1. Replace repository URLs with your own")
        print("   2. Customize user types and feature focus")
        print("   3. Integrate with your workflow")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    # TO TEST YOUR OWN REPOSITORY:
    # Uncomment and edit the line below with your repo URL
    # YOUR_REPO_URL = "https://github.com/yourusername/yourrepo"
    
    asyncio.run(main())