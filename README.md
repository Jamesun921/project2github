# Project2GitHub

A powerful tool for automatically uploading local projects to GitHub. Supports both command-line interface and MCP (Model Context Protocol) integration with Cursor IDE.

## Features

- 🚀 One-click project upload to GitHub
- 🔒 Support for private repositories
- 🔄 Automatic Git initialization and configuration
- 🛠️ MCP integration with Cursor IDE
- 📝 Detailed logging and error handling
- 🌐 Environment variable based configuration

## Prerequisites

- Python 3.6+
- Git installed and configured
- GitHub account and personal access token
- Cursor IDE (for MCP integration)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/project2github.git
cd project2github
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your GitHub token:
Create a `.env` file in the project root:
```bash
GITHUB_TOKEN=your_github_personal_access_token
```

## Usage

### Command Line Interface

Upload a project directory to GitHub:
```bash
python project2github.py /path/to/your/project --name optional-repo-name --private
```

Options:
- `directory`: Path to the local directory to upload (required)
- `--name`: Custom repository name (optional, defaults to directory name)
- `--private`: Create a private repository (optional, defaults to true)

### Cursor IDE Integration (MCP)

1. Start the MCP server:
```bash
python project2github.py --mcp
# or use the provided batch file:
start_mcp_server.bat
```

2. Configure in Cursor IDE:
   - Add MCP server with command: `python path/to/project2github.py --mcp`
   - Server name: `github-project-manager`

3. Use through Cursor's interface with the following parameters:
```json
{
    "directory": "/path/to/your/project",
    "name": "optional-repo-name",
    "private": true
}
```

## Logging

The tool maintains detailed logs in `github_mcp.log` for troubleshooting and monitoring.

## Error Handling

- Validates Git installation
- Checks for valid GitHub token
- Verifies directory existence
- Handles Git initialization and push errors
- Provides detailed error messages and logging

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [PyGithub](https://github.com/PyGithub/PyGithub)
- Integrated with [Cursor IDE](https://cursor.sh/) using MCP
- Inspired by the need for streamlined GitHub project initialization
