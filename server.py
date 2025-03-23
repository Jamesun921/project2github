from mcp.server.fastmcp import FastMCP
from project2github import create_github_repo, check_git_installed, init_git_repo
import os
from pathlib import Path
import sys
import json

class Project2GitHubMCP(FastMCP):
    def __init__(self):
        print("Initializing Project2GitHubMCP...", file=sys.stderr)
        super().__init__("Project2GitHub Server")
        print("Project2GitHubMCP initialized", file=sys.stderr)
        
        # Debug: Print tool manager information
        print("Tool manager:", file=sys.stderr)
        print(f"Tool manager type: {type(self._tool_manager)}", file=sys.stderr)
        print(f"Tool manager dir: {dir(self._tool_manager)}", file=sys.stderr)
        
        # Register create_repo as a tool
        print("Registering create_repo tool...", file=sys.stderr)
        self._tool_manager.register_tool(
            name="create_repo",
            fn=self.create_repo,
            description="Create a new GitHub repository from a local directory",
            parameters={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "The local directory path to create repository from"},
                    "name": {"type": "string", "description": "The name for the GitHub repository (optional)"},
                    "private": {"type": "boolean", "description": "Whether to create a private repository (optional)"}
                },
                "required": ["directory"]
            }
        )
        
        # Debug: Print all methods and their attributes
        print("Available methods:", file=sys.stderr)
        for name in dir(self):
            attr = getattr(self, name)
            print(f"Method: {name}, Type: {type(attr)}, Has _is_tool: {hasattr(attr, '_is_tool')}", file=sys.stderr)
            if hasattr(attr, '_is_tool'):
                print(f"  _is_tool value: {attr._is_tool}", file=sys.stderr)

    def handle_request(self, request):
        """Handle incoming requests and route them to appropriate tools"""
        print(f"Received request: {request}", file=sys.stderr)
        try:
            operation = request.get('operation')
            params = request.get('params', {})

            if operation == 'list_tools':
                # Use tool manager to get tools
                tools = self._tool_manager.list_tools()
                print(f"Tools from manager: {tools}", file=sys.stderr)
                return {'tools': tools}
            
            if not hasattr(self, operation):
                return {'error': f'Unknown operation: {operation}'}

            tool = getattr(self, operation)
            if not hasattr(tool, '_is_tool') or not tool._is_tool:
                return {'error': f'{operation} is not a tool'}

            result = tool(**params)
            print(f"Sending response: {result}", file=sys.stderr)
            return result

        except Exception as e:
            print(f"Error handling request: {e}", file=sys.stderr)
            return {"error": str(e)}

    def run(self):
        """Override run to add debugging"""
        print("Server starting...", file=sys.stderr)
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                print(f"Received line: {line.strip()}", file=sys.stderr)
                try:
                    request = json.loads(line)
                    response = self.handle_request(request)
                    print(json.dumps(response))
                    sys.stdout.flush()
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON: {line}", file=sys.stderr)
                    print(json.dumps({"error": "Invalid JSON"}))
                    sys.stdout.flush()
            except Exception as e:
                print(f"Error in run loop: {e}", file=sys.stderr)
                print(json.dumps({"error": str(e)}))
                sys.stdout.flush()

    @FastMCP.tool
    def create_repo(self, directory: str, name: str = None, private: bool = False) -> dict:
        """Create a new GitHub repository from a local directory
        
        Args:
            directory (str): The local directory path to create repository from
            name (str, optional): The name for the GitHub repository. Defaults to directory name.
            private (bool, optional): Whether to create a private repository. Defaults to False.
            
        Returns:
            dict: A dictionary containing the result of the operation
                - success (bool): Whether the operation was successful
                - repo_url (str, optional): The URL of the created repository if successful
                - error (str, optional): Error message if the operation failed
        """
        print(f"Received create_repo request: directory={directory}, name={name}, private={private}", file=sys.stderr)
        try:
            # Check if directory exists
            if not os.path.exists(directory):
                return {
                    'success': False,
                    'error': f'Directory {directory} does not exist'
                }

            # Check Git installation
            if not check_git_installed():
                return {
                    'success': False,
                    'error': 'Git is not installed'
                }

            # Initialize Git repository
            if not init_git_repo(directory):
                return {
                    'success': False,
                    'error': 'Failed to initialize Git repository'
                }

            # Get GitHub token
            token = os.getenv('GITHUB_TOKEN')
            if not token:
                return {
                    'success': False,
                    'error': 'GITHUB_TOKEN environment variable is not set'
                }

            # Create GitHub repository
            success = create_github_repo(
                token=token,
                repo_name=name or Path(directory).name,
                directory=directory,
                private=private
            )

            if success:
                return {
                    'success': True,
                    'repo_url': f'https://github.com/{os.getenv("GITHUB_USERNAME")}/{name or Path(directory).name}'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to create GitHub repository'
                }

        except Exception as e:
            print(f"Error in create_repo: {str(e)}", file=sys.stderr)
            return {
                'success': False,
                'error': f'An unexpected error occurred: {str(e)}'
            }

    # @FastMCP.tool
    # def list_repos(self) -> list:
    #     """List all GitHub repositories"""
    #     return list_repos()

    # @FastMCP.tool
    # def delete_repo(self, name: str) -> dict:
    #     """Delete a GitHub repository"""
    #     return delete_repo(name)

def test_mcp():
    """Test the MCP server directly"""
    mcp = Project2GitHubMCP()
    print("Testing list_tools...", file=sys.stderr)
    response = mcp.handle_request({"operation": "list_tools", "params": {}})
    print(f"Response: {response}", file=sys.stderr)
    return response

def main():
    print("Starting MCP server...", file=sys.stderr)
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--test":
            test_mcp()
            return

        mcp = Project2GitHubMCP()
        print("Running MCP server...", file=sys.stderr)
        print("Available tools:", [name for name, _ in mcp.__class__.__dict__.items() if hasattr(getattr(mcp, name), '_is_tool')], file=sys.stderr)
        mcp.run()
    except Exception as e:
        print(f"Error in MCP server: {e}", file=sys.stderr)
        raise

if __name__ == "__main__":
    main()
