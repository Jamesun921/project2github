#!/usr/bin/env python3
import os
import sys
import argparse
from github import Github
from pathlib import Path
from dotenv import load_dotenv
import subprocess
import platform
from mcp.server.fastmcp import FastMCP, Context
import json

def check_git_installed():
    """Check if Git is installed"""
    try:
        subprocess.run(['git', '--version'], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Please install Git first")
        return False

def init_git_repo(directory):
    """Initialize a Git repository"""
    try:
        # Check if it's already a Git repository
        result = subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], 
                              cwd=directory, capture_output=True, text=True)
        is_git_repo = result.returncode == 0

        if not is_git_repo:
            subprocess.run(['git', 'init'], cwd=directory, check=True, capture_output=True)
        
        # Check for unstaged changes
        status = subprocess.run(['git', 'status', '--porcelain'], 
                              cwd=directory, capture_output=True, text=True)
        
        if status.stdout.strip():
            subprocess.run(['git', 'add', '.'], cwd=directory, check=True, capture_output=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], 
                         cwd=directory, check=True, capture_output=True)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Git operation failed: {e}")
        return False

def create_github_repo(token, repo_name, directory, private=False):
    """Create a GitHub repository and push code"""
    try:
        # Create GitHub instance
        g = Github(token)
        user = g.get_user()
        
        # Create remote repository
        repo = user.create_repo(repo_name, private=private)
        print(f"GitHub repository created successfully: {repo.html_url}")
        
        # Add remote repository
        subprocess.run(['git', 'remote', 'add', 'origin', repo.clone_url], 
                      cwd=directory, check=True, capture_output=True)
        
        # Push code
        subprocess.run(['git', 'push', '-u', 'origin', 'master'], 
                      cwd=directory, check=True, capture_output=True)
        
        print(f"Code successfully pushed to GitHub!")
        print(f"Repository URL: {repo.html_url}")
        return True
    except Exception as e:
        print(f"Failed to create GitHub repository: {e}")
        return False

# Create FastMCP instance
mcp = FastMCP()

@mcp.tool()
def upload_to_github(ctx: Context, directory: str, name: str = None, private: bool = False) -> dict:
    """
    Upload a local directory to GitHub
    
    Args:
        ctx (Context): MCP context
        directory (str): Path to the local directory to upload
        name (str, optional): GitHub repository name (defaults to directory name)
        private (bool, optional): Whether to create a private repository, defaults to False
    
    Returns:
        dict: Dictionary containing the operation result
    """
    try:
        # Load environment variables
        load_dotenv()
        github_token = os.getenv('GITHUB_TOKEN')
        
        if not github_token:
            return {
                "success": False,
                "error": "GITHUB_TOKEN environment variable not set, please set GITHUB_TOKEN=your_token in .env file"
            }

        # Check if directory exists
        directory = Path(directory).resolve()
        if not directory.exists():
            return {
                "success": False,
                "error": f"Directory {directory} does not exist"
            }

        # Get repository name
        repo_name = name if name else directory.name

        # Check if Git is installed
        if not check_git_installed():
            return {
                "success": False,
                "error": "Please install Git first"
            }

        # Initialize Git repository
        if not init_git_repo(directory):
            return {
                "success": False,
                "error": "Failed to initialize Git repository"
            }

        # Create GitHub repository and push code
        if create_github_repo(github_token, repo_name, directory, private):
            return {
                "success": True,
                "message": f"Code successfully pushed to GitHub!",
                "repo_name": repo_name
            }
        else:
            return {
                "success": False,
                "error": "Failed to create or push to GitHub repository"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--mcp":
        # MCP mode
        print("MCP Server started. Waiting for JSON input...")
        print("Example input format:")
        print('{"directory": "/path/to/directory", "name": "repo_name", "private": false}')
        print("\nPlease enter your JSON command and press Enter:")
        
        try:
            # Read input from stdin
            input_data = sys.stdin.readline().strip()
            if not input_data:
                print("Error: No input received")
                return
                
            # Parse JSON
            try:
                command = json.loads(input_data)
                if not isinstance(command, dict):
                    print("Error: Input must be a JSON object")
                    return
                    
                # Validate required fields
                if "directory" not in command:
                    print("Error: 'directory' field is required")
                    return
                    
                # Execute command
                result = upload_to_github(None, command["directory"], 
                                       command.get("name"), 
                                       command.get("private", False))
                
                # Print result
                print(json.dumps(result, indent=2))
                
            except json.JSONDecodeError:
                print("Error: Invalid JSON format")
                return
                
        except KeyboardInterrupt:
            print("\nServer stopped by user")
        except Exception as e:
            print(f"Error: {str(e)}")
    else:
        # Original command-line mode
        parser = argparse.ArgumentParser(description='Upload a local directory to GitHub')
        parser.add_argument('directory', help='Path to the local directory to upload')
        parser.add_argument('--name', help='GitHub repository name (defaults to directory name)')
        parser.add_argument('--private', action='store_true', help='Create a private repository')
        args = parser.parse_args()

        result = upload_to_github(None, args.directory, args.name, args.private)
        if result["success"]:
            print(result["message"])
        else:
            print(f"Error: {result['error']}")

if __name__ == '__main__':
    main()
