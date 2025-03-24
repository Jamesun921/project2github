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
import logging
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("github_mcp.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Custom log handler to capture logs for MCP client
class MCPLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_buffer = []
        self.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    
    def emit(self, record):
        log_entry = self.format(record)
        self.log_buffer.append(log_entry)

def check_git_installed():
    """Check if Git is installed"""
    try:
        result = subprocess.run(['git', '--version'], check=True, capture_output=True)
        logger.info(f"Git version check: {result.stdout.decode().strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Git is not installed")
        print("Error: Please install Git first")
        return False

def init_git_repo(directory):
    """Initialize a Git repository"""
    try:
        # Check if it's already a Git repository
        logger.info(f"Checking if directory is already a Git repository: {directory}")
        result = subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], 
                              cwd=directory, capture_output=True, text=True)
        is_git_repo = result.returncode == 0
        
        if not is_git_repo:
            logger.info("Initializing new Git repository")
            subprocess.run(['git', 'init'], cwd=directory, check=True, capture_output=True)
        else:
            logger.info("Directory is already a Git repository")
        
        # Check for unstaged changes
        logger.info("Checking for unstaged changes")
        status = subprocess.run(['git', 'status', '--porcelain'], 
                              cwd=directory, capture_output=True, text=True)
        
        if status.stdout.strip():
            logger.info("Found unstaged changes, creating initial commit")
            add_result = subprocess.run(['git', 'add', '.'], cwd=directory, capture_output=True, text=True)
            logger.info(f"Git add result: {add_result.stdout if add_result.stdout else 'No output'}")
            
            commit_result = subprocess.run(['git', 'commit', '-m', 'Initial commit'], 
                                        cwd=directory, capture_output=True, text=True)
            logger.info(f"Git commit result: {commit_result.stdout}")
        else:
            logger.info("No unstaged changes found")
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Git operation failed: {str(e)}\nOutput: {e.output.decode() if e.output else 'No output'}")
        print(f"Git operation failed: {e}")
        return False

def create_github_repo(token, repo_name, directory, private=False):
    """Create a GitHub repository and push code"""
    try:
        logger.info(f"Creating GitHub repository: {repo_name} (private: {private})")
        # Create GitHub instance
        g = Github(token)
        user = g.get_user()
        logger.info(f"Authenticated as GitHub user: {user.login}")
        
        # Create remote repository
        repo = user.create_repo(repo_name, private=private)
        logger.info(f"GitHub repository created: {repo.html_url}")
        print(f"GitHub repository created successfully: {repo.html_url}")
        
        # Add remote repository
        logger.info(f"Adding remote repository: {repo.clone_url}")
        remote_result = subprocess.run(['git', 'remote', 'add', 'origin', repo.clone_url], 
                                    cwd=directory, capture_output=True, text=True)
        logger.info(f"Git remote add result: {remote_result.stdout if remote_result.stdout else 'No output'}")
        
        # Push code
        logger.info("Pushing code to GitHub")
        push_result = subprocess.run(['git', 'push', '-u', 'origin', 'master'], 
                                  cwd=directory, capture_output=True, text=True)
        logger.info(f"Git push result: {push_result.stdout}")
        
        print(f"Code successfully pushed to GitHub!")
        print(f"Repository URL: {repo.html_url}")
        return True
    except Exception as e:
        logger.error(f"Failed to create GitHub repository: {str(e)}")
        print(f"Failed to create GitHub repository: {e}")
        return False

# Create FastMCP instance - Configure for use in Cursor
mcp = FastMCP(name="github-project-manager", description="GitHub Project Manager Tool")

@mcp.tool()
def upload_to_github(ctx: Context, directory: str, name: str = None, private: bool = True) -> dict:
    """
    Upload local directory to GitHub
    
    Parameters:
        directory: Absolute path to current working directory to upload
        name: GitHub repository name (defaults to directory name)
        private: Whether to create a private repository, defaults to True
    """
    try:
        # Setup MCP log handler to capture logs
        mcp_handler = MCPLogHandler()
        logger.addHandler(mcp_handler)
        
        logger.info(f"MCP call received - Parameters: directory='{directory}', name='{name}', private={private}")
        logger.info(f"Starting to upload directory: {directory} to GitHub...")
        
        # Load environment variables
        load_dotenv()
        github_token = os.getenv('GITHUB_TOKEN')
        
        if not github_token:
            error_msg = "GITHUB_TOKEN environment variable not set, please set GITHUB_TOKEN=your_token in .env file"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "logs": mcp_handler.log_buffer
            }

        # Normalize path for cross-platform compatibility
        try:
            # Convert to Path object and resolve to absolute path
            directory_path = Path(directory).resolve()
            
            # Check if directory exists
            if not directory_path.exists():
                error_msg = f"Directory {directory_path} does not exist"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "logs": mcp_handler.log_buffer
                }
                
            # Convert back to string using os.path.normpath for consistent path format
            directory = str(directory_path)
            logger.info(f"Normalized directory path: {directory}")
            
        except Exception as e:
            error_msg = f"Error processing directory path: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "logs": mcp_handler.log_buffer
            }

        # Get repository name
        repo_name = name if name else directory_path.name
        logger.info(f"Using repository name: {repo_name}")
        
        # Check if Git is installed
        if not check_git_installed():
            error_msg = "Please install Git first"
            logger.error("Git not installed")
            return {
                "success": False,
                "error": error_msg,
                "logs": mcp_handler.log_buffer
            }

        # Initialize Git repository
        if not init_git_repo(directory):
            error_msg = "Failed to initialize Git repository"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "logs": mcp_handler.log_buffer
            }

        # Create GitHub repository and push code
        if create_github_repo(github_token, repo_name, directory, private):
            success_msg = f"Code successfully pushed to GitHub! Repository name: {repo_name}"
            logger.info(success_msg)
            return {
                "success": True,
                "message": success_msg,
                "repo_name": repo_name,
                "logs": mcp_handler.log_buffer
            }
        else:
            error_msg = "Failed to create or push to GitHub repository"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "logs": mcp_handler.log_buffer
            }
            
    except Exception as e:
        logger.exception(f"Exception occurred: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "logs": mcp_handler.log_buffer if 'mcp_handler' in locals() else []
        }
    finally:
        # Remove the MCP handler to avoid duplicate logs in future calls
        if 'mcp_handler' in locals():
            logger.removeHandler(mcp_handler)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--mcp":
        logger.info(f"Starting GitHub Project Manager MCP Server with args: {sys.argv}")
        print("Starting GitHub Project Manager MCP Server...")
        # Use standard MCP server running mode in Cursor
        mcp.run()
    else:
        # Original command-line mode
        logger.info(f"Starting in CLI mode with args: {sys.argv}")
        parser = argparse.ArgumentParser(description='Upload local directory to GitHub')
        parser.add_argument('directory', help='Path to local directory to upload')
        parser.add_argument('--name', help='GitHub repository name (defaults to directory name)')
        parser.add_argument('--private', action='store_true', help='Create private repository')
        args = parser.parse_args()

        result = upload_to_github(None, args.directory, args.name, args.private)
        if result["success"]:
            print(result["message"])
        else:
            print(f"Error: {result['error']}")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.exception(f"Main program exception: {str(e)}")
        print(f"Error occurred: {str(e)}")
        input("Press Enter to exit...")  # Prevent window from closing
