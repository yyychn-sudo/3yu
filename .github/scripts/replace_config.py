#!/usr/bin/env python3
"""
RustDesk 精确配置替换脚本 - 完全兼容 Windows 和 GitHub Actions
支持多种编码，安全备份和回滚机制
"""

import os
import sys
import shutil
from datetime import datetime

def log_info(message):
    """信息日志"""
    print(f"ℹ️  INFO: {message}")

def log_success(message):
    """成功日志"""
    print(f"✅ SUCCESS: {message}")

def log_warning(message):
    """警告日志"""
    print(f"⚠️  WARNING: {message}")

def log_error(message):
    """错误日志"""
    print(f"❌ ERROR: {message}")

def detect_file_encoding(filepath):
    """
    检测文件编码
    返回: (encoding, confidence) 编码和置信度
    """
    encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin-1', 'cp1252', 'ascii']
    
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                # 读取文件内容进行测试
                content = f.read(1024 * 1024)  # 读取1MB进行测试
                # 尝试解码整个内容（如果之前只读取了部分）
                f.seek(0)
                content = f.read()
                # 额外检查：尝试编码为UTF-8（最终输出编码）
                content.encode('utf-8')
                return encoding, 'high'
        except UnicodeDecodeError:
            continue
        except UnicodeEncodeError:
            # 可以读取但不能编码为UTF-8
            return encoding, 'medium'
        except Exception:
            continue
    
    # 如果所有编码都失败，尝试二进制检测
    try:
        with open(filepath, 'rb') as f:
            raw_data = f.read(4096)
            # 简单的UTF-8检测
            try:
                raw_data.decode('utf-8')
                return 'utf-8', 'low'
            except:
                # 尝试检测BOM
                if raw_data.startswith(b'\xef\xbb\xbf'):
                    return 'utf-8-sig', 'medium'
                return 'latin-1', 'lowest'
    except:
        pass
    
    return 'utf-8', 'unknown'

def backup_file(filepath):
    """创建文件备份"""
    if not os.path.exists(filepath):
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}.backup_{timestamp}"
    
    try:
        shutil.copy2(filepath, backup_path)
        log_info(f"已创建备份: {backup_path}")
        return backup_path
    except Exception as e:
        log_warning(f"创建备份失败: {e}")
        return None

def safe_replace_in_file(filepath, search_text, replace_text, max_backups=3):
    """
    安全地在文件中替换文本，支持各种编码
    """
    if not os.path.exists(filepath):
        log_error(f"文件不存在: {filepath}")
        return False
    
    if not search_text or not replace_text:
        log_warning("搜索文本或替换文本为空")
        return False
    
    # 检测文件编码
    encoding, confidence = detect_file_encoding(filepath)
    log_info(f"检测到文件编码: {encoding} (置信度: {confidence})")
    
    # 创建备份
    backup_path = backup_file(filepath)
    
    try:
        # 使用检测到的编码读取文件
        with open(filepath, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()
        
        original_content = content
        
        # 检查搜索文本是否存在
        if search_text not in content:
            # 尝试二进制搜索（以防编码问题）
            with open(filepath, 'rb') as f:
                binary_content = f.read()
                search_bytes = search_text.encode('utf-8')
                if search_bytes in binary_content:
                    # 找到二进制匹配，但文本不匹配，说明有编码问题
                    log_warning("文本不匹配但二进制匹配，可能存在编码转换问题")
                    # 使用二进制替换
                    replace_bytes = replace_text.encode('utf-8')
                    new_binary_content = binary_content.replace(search_bytes, replace_bytes)
                    with open(filepath, 'wb') as f:
                        f.write(new_binary_content)
                    log_success(f"使用二进制模式替换成功: {filepath}")
                    return True
                else:
                    log_warning(f"未找到搜索文本: '{search_text[:50]}...'")
                    return False
        
        # 执行替换
        new_content = content.replace(search_text, replace_text)
        
        # 检查是否实际发生了替换
        if new_content == original_content:
            log_warning("替换后内容未变化")
            return False
        
        # 统计替换次数
        replace_count = original_content.count(search_text)
        log_info(f"找到 {replace_count} 处匹配")
        
        # 以UTF-8编码写入（确保一致性）
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # 验证写入
        with open(filepath, 'r', encoding='utf-8') as f:
            verify_content = f.read()
            if replace_text in verify_content:
                log_success(f"替换成功: {filepath} (替换了 {replace_count} 处)")
                return True
            else:
                raise Exception("验证失败: 替换文本未在新文件中找到")
                
    except UnicodeDecodeError as e:
        log_error(f"解码失败: {e}")
        # 尝试回滚
        if backup_path and os.path.exists(backup_path):
            try:
                shutil.copy2(backup_path, filepath)
                log_info(f"已从备份恢复: {backup_path}")
            except:
                log_error("恢复备份失败")
        return False
        
    except Exception as e:
        log_error(f"替换过程中发生错误: {e}")
        # 尝试回滚
        if backup_path and os.path.exists(backup_path):
            try:
                shutil.copy2(backup_path, filepath)
                log_info(f"已从备份恢复: {backup_path}")
            except:
                log_error("恢复备份失败")
        return False

def cleanup_old_backups(filepath, keep_count=3):
    """清理旧的备份文件"""
    if not os.path.exists(filepath):
        return
    
    dir_name = os.path.dirname(filepath)
    base_name = os.path.basename(filepath)
    
    backups = []
    for filename in os.listdir(dir_name):
        if filename.startswith(f"{base_name}.backup_"):
            backup_path = os.path.join(dir_name, filename)
            if os.path.isfile(backup_path):
                backups.append((backup_path, os.path.getmtime(backup_path)))
    
    # 按修改时间排序（从旧到新）
    backups.sort(key=lambda x: x[1])
    
    # 删除多余的备份
    for i in range(len(backups) - keep_count):
        try:
            os.remove(backups[i][0])
            log_info(f"清理旧备份: {os.path.basename(backups[i][0])}")
        except Exception as e:
            log_warning(f"删除备份失败: {e}")

def main():
    print("=" * 60)
    print("🛠️  RustDesk Configuration Replacement")
    print("=" * 60)
    
    # 获取配置
    RELAY_SERVER = os.environ.get('RELAY_SERVER', '').strip()
    RS_PUB_KEY = os.environ.get('RS_PUB_KEY', '').strip()
    CUSTOM_API_URL = os.environ.get('CUSTOM_API_URL', '').strip()
    
    # 显示配置（隐藏敏感信息）
    def mask_sensitive(text, max_show=8):
        if not text:
            return '(default)'
        if len(text) <= max_show:
            return text
        return text[:max_show] + '...' + text[-4:] if len(text) > 12 else text[:max_show] + '...'
    
    print(f"🔧 Relay Server: {mask_sensitive(RELAY_SERVER)}")
    print(f"🔑 RSA Key: {mask_sensitive(RS_PUB_KEY)}")
    print(f"🌐 API URL: {mask_sensitive(CUSTOM_API_URL)}")
    print("-" * 60)
    
    # 检查是否有自定义配置
    if not RELAY_SERVER and not RS_PUB_KEY and not CUSTOM_API_URL:
        log_info("No custom configuration provided, using defaults")
        return 0
    
    success_count = 0
    operations = []
    
    # 1. 替换中继服务器
    if RELAY_SERVER:
        operations.append({
            'name': 'Relay Server',
            'file': 'libs/hbb_common/src/config.rs',
            'search': '"rs-ny.rustdesk.com"',
            'replace': f'"{RELAY_SERVER}"'
        })
    
    # 2. 替换 RSA 公钥
    if RS_PUB_KEY:
        operations.append({
            'name': 'RSA Key',
            'file': 'libs/hbb_common/src/config.rs',
            'search': '"OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw="',
            'replace': f'"{RS_PUB_KEY}"'
        })
    
    # 3. 替换 API 地址
    if CUSTOM_API_URL:
        operations.append({
            'name': 'API URL',
            'file': 'src/common.rs',
            'search': '"https://admin.rustdesk.com"',
            'replace': f'"{CUSTOM_API_URL}"'
        })
    
    log_info(f"开始执行 {len(operations)} 项配置替换...")
    
    # 执行所有替换操作
    for op in operations:
        print(f"\n📝 正在处理: {op['name']}")
        print(f"   文件: {op['file']}")
        print(f"   搜索: {op['search'][:50]}...")
        print(f"   替换: {op['replace'][:50]}...")
        
        if safe_replace_in_file(op['file'], op['search'], op['replace']):
            success_count += 1
            # 清理旧备份
            cleanup_old_backups(op['file'], keep_count=2)
    
    # 输出结果
    print("\n" + "=" * 60)
    print("📊 执行结果汇总")
    print("=" * 60)
    
    total_operations = len(operations)
    
    if success_count == total_operations and total_operations > 0:
        print(f"🎉 全部成功! {success_count}/{total_operations} 项配置已替换")
        print("所有自定义配置已成功应用")
    elif success_count > 0:
        print(f"⚠️  部分成功: {success_count}/{total_operations} 项配置已替换")
        if total_operations - success_count == 1:
            print("1 项配置替换失败，请检查日志")
        else:
            print(f"{total_operations - success_count} 项配置替换失败，请检查日志")
    else:
        print("❌ 全部失败: 0 项配置已替换")
        print("请检查:")
        print("1. 配置文件路径是否正确")
        print("2. 搜索文本是否匹配")
        print("3. 文件编码是否正确")
    
    # 提供调试信息
    print("\n🔍 调试信息:")
    print(f"   工作目录: {os.getcwd()}")
    print(f"   Python 版本: {sys.version}")
    print(f"   系统编码: {sys.getdefaultencoding()}")
    
    # 检查文件是否存在
    for op in operations:
        exists = os.path.exists(op['file'])
        print(f"   {op['file']}: {'✅ 存在' if exists else '❌ 不存在'}")
    
    return 0 if success_count > 0 else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  操作被用户中断")
        sys.exit(130)
    except Exception as e:
        log_error(f"脚本执行异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
