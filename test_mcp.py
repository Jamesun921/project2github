import json
import sys

def main():
    # 发送请求
    request = {
        "operation": "list_tools",
        "params": {}
    }
    print(json.dumps(request))
    sys.stdout.flush()

if __name__ == "__main__":
    main() 