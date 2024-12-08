#!/usr/bin/env python3
import os
import sys
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
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("错误: 请先安装Git")
        return False

def init_git_repo(directory):
    """初始化Git仓库"""
    try:
        subprocess.run(['git', 'init'], cwd=directory, check=True, capture_output=True)
        subprocess.run(['git', 'add', '.'], cwd=directory, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=directory, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Git操作失败: {e}")
        return False

def create_github_repo(token, repo_name, directory, private=False):
    """创建GitHub仓库并推送代码"""
    try:
        # 创建GitHub实例
        g = Github(token)
        user = g.get_user()
        
        # 创建远程仓库
        repo = user.create_repo(repo_name, private=private)
        print(f"GitHub仓库创建成功: {repo.html_url}")
        
        # 添加远程仓库
        subprocess.run(['git', 'remote', 'add', 'origin', repo.clone_url], 
                      cwd=directory, check=True, capture_output=True)
        
        # 推送代码
        subprocess.run(['git', 'push', '-u', 'origin', 'master'], 
                      cwd=directory, check=True, capture_output=True)
        
        print(f"代码已成功推送到GitHub！")
        print(f"仓库地址: {repo.html_url}")
        return True
    except Exception as e:
        print(f"创建GitHub仓库失败: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='将本地目录上传到GitHub')
    parser.add_argument('directory', help='要上传的本地目录路径')
    parser.add_argument('--name', help='GitHub仓库名称（默认使用目录名）')
    parser.add_argument('--private', action='store_true', help='创建私有仓库')
    args = parser.parse_args()

    # 加载环境变量
    load_dotenv()
    github_token = os.getenv('GITHUB_TOKEN')
    
    if not github_token:
        print("错误: 未设置GITHUB_TOKEN环境变量")
        print("请在.env文件中设置GITHUB_TOKEN=your_token")
        return

    # 检查目录是否存在
    directory = Path(args.directory).resolve()
    if not directory.exists():
        print(f"错误: 目录 {directory} 不存在")
        return

    # 获取仓库名称
    repo_name = args.name if args.name else directory.name

    # 检查Git是否安装
    if not check_git_installed():
        return

    # 初始化Git仓库
    if not init_git_repo(directory):
        return

    # 创建GitHub仓库并推送代码
    create_github_repo(github_token, repo_name, directory, args.private)

if __name__ == '__main__':
    main()
