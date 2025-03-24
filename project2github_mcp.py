#!/usr/bin/env python3
import os
import sys
import json
import argparse
from github import Github
from pathlib import Path
from dotenv import load_dotenv
import subprocess
import platform

def check_git_installed():
    """检查是否安装了Git"""
    try:
        subprocess.run(['git', '--version'], check=True, capture_output=True)
        return {
            "result": {
                "success": True,
                "message": "Git已安装"
            }
        }
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {
            "error": {
                "code": -32000,
                "message": "错误: 请先安装Git"
            }
        }

def init_git_repo(directory):
    """初始化Git仓库"""
    try:
        # 检查是否已经是Git仓库
        result = subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], 
                              cwd=directory, capture_output=True, text=True)
        is_git_repo = result.returncode == 0

        if not is_git_repo:
            subprocess.run(['git', 'init'], cwd=directory, check=True, capture_output=True)
        
        # 检查是否有未暂存的更改
        status = subprocess.run(['git', 'status', '--porcelain'], 
                              cwd=directory, capture_output=True, text=True)
        
        if status.stdout.strip():
            subprocess.run(['git', 'add', '.'], cwd=directory, check=True, capture_output=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], 
                         cwd=directory, check=True, capture_output=True)
        
        return {
            "result": {
                "success": True,
                "message": "Git仓库初始化成功"
            }
        }
    except subprocess.CalledProcessError as e:
        return {
            "error": {
                "code": -32001,
                "message": f"Git操作失败: {e}"
            }
        }

def create_github_repo(token, repo_name, directory, private=False):
    """创建GitHub仓库并推送代码"""
    try:
        # 创建GitHub实例
        g = Github(token)
        user = g.get_user()
        
        # 创建远程仓库
        repo = user.create_repo(repo_name, private=private)
        
        # 添加远程仓库
        subprocess.run(['git', 'remote', 'add', 'origin', repo.clone_url], 
                      cwd=directory, check=True, capture_output=True)
        
        # 推送代码
        subprocess.run(['git', 'push', '-u', 'origin', 'master'], 
                      cwd=directory, check=True, capture_output=True)
        
        return {
            "result": {
                "success": True,
                "message": "仓库创建成功",
                "url": repo.html_url,
                "clone_url": repo.clone_url
            }
        }
    except Exception as e:
        return {
            "error": {
                "code": -32002,
                "message": f"创建GitHub仓库失败: {e}"
            }
        }

def handle_command(command):
    """处理MCP命令"""
    try:
        data = json.loads(command)
        if "jsonrpc" not in data or data["jsonrpc"] != "2.0":
            return {
                "jsonrpc": "2.0",
                "id": data.get("id"),
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: Not JSON-RPC 2.0"
                }
            }
            
        cmd_id = data.get("id")
        method = data.get("method")
        params = data.get("params", {})
        
        if not method:
            return {
                "jsonrpc": "2.0",
                "id": cmd_id,
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: Method not specified"
                }
            }
        
        response = {
            "jsonrpc": "2.0",
            "id": cmd_id
        }
        
        if method == "check_git":
            result = check_git_installed()
            response.update(result)
            
        elif method == "init_repo":
            directory = params.get("directory")
            if not directory:
                response["error"] = {
                    "code": -32602,
                    "message": "缺少directory参数"
                }
            else:
                directory = Path(directory).resolve()
                if not directory.exists():
                    response["error"] = {
                        "code": -32602,
                        "message": f"目录 {directory} 不存在"
                    }
                else:
                    result = init_git_repo(directory)
                    response.update(result)
            
        elif method == "create_repo":
            required_params = ["token", "directory", "repo_name"]
            missing_params = [p for p in required_params if p not in params]
            if missing_params:
                response["error"] = {
                    "code": -32602,
                    "message": f"缺少参数: {', '.join(missing_params)}"
                }
            else:
                directory = Path(params["directory"]).resolve()
                if not directory.exists():
                    response["error"] = {
                        "code": -32602,
                        "message": f"目录 {directory} 不存在"
                    }
                else:
                    result = create_github_repo(
                        params["token"],
                        params["repo_name"],
                        directory,
                        params.get("private", False)
                    )
                    response.update(result)
            
        else:
            response["error"] = {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
            
        return response
            
    except json.JSONDecodeError:
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": "Parse error: Invalid JSON"
            }
        }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }

def main():
    """MCP服务器主循环"""
    print(json.dumps({
        "jsonrpc": "2.0",
        "id": "init",
        "result": {
            "success": True,
            "message": "MCP服务器已启动"
        }
    }, ensure_ascii=False))
    sys.stdout.flush()
    
    while True:
        try:
            # 从标准输入读取命令
            command = input()
            if not command:
                continue
                
            # 处理命令并返回结果
            result = handle_command(command)
            
            # 输出JSON格式的响应
            print(json.dumps(result, ensure_ascii=False))
            sys.stdout.flush()
            
        except EOFError:
            break
        except Exception as e:
            print(json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }, ensure_ascii=False))
            sys.stdout.flush()

if __name__ == "__main__":
    main() 