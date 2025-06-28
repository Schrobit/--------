#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件功能测试脚本
使用方法：
  python test_email.py test          # 测试邮件配置
  python test_email.py check         # 检查并发送每日提醒
  python test_email.py manual <用户名> # 手动发送提醒给指定用户
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from email_service import test_email_config, check_and_send_reminders, send_manual_reminder

def main():
    if len(sys.argv) < 2:
        print("使用方法：")
        print("  python test_email.py test          # 测试邮件配置")
        print("  python test_email.py check         # 检查并发送每日提醒")
        print("  python test_email.py manual <用户名> # 手动发送提醒给指定用户")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'test':
        print("=== 测试邮件配置 ===")
        test_email_config()
        
    elif command == 'check':
        print("=== 检查并发送每日提醒 ===")
        check_and_send_reminders()
        
    elif command == 'manual':
        if len(sys.argv) < 3:
            print("错误：请提供用户名")
            print("使用方法：python test_email.py manual <用户名>")
            return
        
        username = sys.argv[2]
        print(f"=== 手动发送提醒给用户: {username} ===")
        result = send_manual_reminder(username)
        
        if result['success']:
            print(f"✅ 成功发送提醒邮件给 {result['username']}")
        else:
            print(f"❌ 发送失败: {result['message']}")
            
    else:
        print(f"未知命令: {command}")
        print("支持的命令: test, check, manual")

if __name__ == '__main__':
    main()