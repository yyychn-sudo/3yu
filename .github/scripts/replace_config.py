#!/usr/bin/env python3
"""
RustDesk 精确配置替换脚本 - 完全兼容 Windows
"""

import os
import sys

def log_info(message):
    print(f"INFO: {message}")

def log_success(message):
    print(f"SUCCESS: {message}")

def log_warning(message):
    print(f"WARNING: {message}")

def main():
    print("=" * 60)
    print("RustDesk Configuration Replacement")
    print("=" * 60)
    
    # 获取配置
    RELAY_SERVER = os.environ.get('RELAY_SERVER', '').strip()
    RS_PUB_KEY = os.environ.get('RS_PUB_KEY', '').strip()
    CUSTOM_API_URL = os.environ.get('CUSTOM_API_URL', '').strip()
    
    print(f"Relay Server: {RELAY_SERVER or '(default)'}")
    print(f"RSA Key: {'*' * 20 if RS_PUB_KEY else '(default)'}")
    print(f"API URL: {CUSTOM_API_URL or '(default)'}")
    
    if not RELAY_SERVER and not RS_PUB_KEY and not CUSTOM_API_URL:
        print("No custom configuration provided")
        return
    
    success = 0
    
    # 1. 替换中继服务器
    if RELAY_SERVER:
        try:
            with open("libs/hbb_common/src/config.rs", 'r') as f:
                content = f.read()
            
            if '"rs-ny.rustdesk.com"' in content:
                content = content.replace('"rs-ny.rustdesk.com"', f'"{RELAY_SERVER}"')
                with open("libs/hbb_common/src/config.rs", 'w') as f:
                    f.write(content)
                log_success("Relay server replaced")
                success += 1
        except Exception as e:
            log_warning(f"Failed to replace relay server: {e}")
    
    # 2. 替换 RSA 公钥
    if RS_PUB_KEY:
        try:
            with open("libs/hbb_common/src/config.rs", 'r') as f:
                content = f.read()
            
            if '"OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw="' in content:
                content = content.replace('"OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw="', f'"{RS_PUB_KEY}"')
                with open("libs/hbb_common/src/config.rs", 'w') as f:
                    f.write(content)
                log_success("RSA key replaced")
                success += 1
        except Exception as e:
            log_warning(f"Failed to replace RSA key: {e}")
    
    # 3. 替换 API 地址
    if CUSTOM_API_URL:
        try:
            with open("src/common.rs", 'r') as f:
                content = f.read()
            
            if '"https://admin.rustdesk.com"' in content:
                content = content.replace('"https://admin.rustdesk.com"', f'"{CUSTOM_API_URL}"')
                with open("src/common.rs", 'w') as f:
                    f.write(content)
                log_success("API URL replaced")
                success += 1
        except Exception as e:
            log_warning(f"Failed to replace API URL: {e}")
    
    # 简单验证（不使用特殊字符）
    print(f"\nResults: {success} configurations replaced")
    
    if success == 3:
        print("All configurations replaced successfully!")
    elif success > 0:
        print(f"Partially successful: {success}/3")
    else:
        print("No configurations were replaced")

if __name__ == "__main__":
    main()
