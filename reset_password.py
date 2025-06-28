#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
密码重置工具
用于重置团队反馈管理系统中用户的密码
"""

import sqlite3
import sys
import getpass
from werkzeug.security import generate_password_hash

def get_db_connection():
    """获取数据库连接"""
    try:
        conn = sqlite3.connect('feedback_system.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"数据库连接失败: {e}")
        return None

def list_users():
    """列出所有用户"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        users = conn.execute('SELECT username, email, name, is_admin FROM users ORDER BY username').fetchall()
        print("\n系统中的用户列表:")
        print("-" * 60)
        print(f"{'用户名':<15} {'邮箱':<25} {'姓名':<10} {'管理员'}")
        print("-" * 60)
        
        for user in users:
            admin_status = "是" if user['is_admin'] else "否"
            print(f"{user['username']:<15} {user['email']:<25} {user['name']:<10} {admin_status}")
        print("-" * 60)
        
    except sqlite3.Error as e:
        print(f"查询用户失败: {e}")
    finally:
        conn.close()

def reset_password(username, new_password=None):
    """重置指定用户的密码"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        # 检查用户是否存在
        user = conn.execute('SELECT id, username, name FROM users WHERE username = ?', (username,)).fetchone()
        if not user:
            print(f"错误: 用户 '{username}' 不存在")
            return False
        
        # 如果没有提供新密码，则提示输入
        if not new_password:
            print(f"\n为用户 '{user['name']}' ({username}) 重置密码")
            while True:
                new_password = getpass.getpass("请输入新密码: ")
                if len(new_password) < 6:
                    print("密码长度至少为6位，请重新输入")
                    continue
                
                confirm_password = getpass.getpass("请确认新密码: ")
                if new_password != confirm_password:
                    print("两次输入的密码不一致，请重新输入")
                    continue
                break
        
        # 生成密码哈希
        password_hash = generate_password_hash(new_password)
        
        # 更新密码
        conn.execute('UPDATE users SET password = ? WHERE username = ?', (password_hash, username))
        conn.commit()
        
        print(f"\n✅ 用户 '{user['name']}' ({username}) 的密码已成功重置")
        return True
        
    except sqlite3.Error as e:
        print(f"重置密码失败: {e}")
        return False
    finally:
        conn.close()

def main():
    """主函数"""
    print("团队反馈管理系统 - 密码重置工具")
    print("=" * 40)
    
    if len(sys.argv) < 2:
        print("\n使用方法:")
        print("  python reset_password.py list                    # 列出所有用户")
        print("  python reset_password.py reset <用户名>          # 重置指定用户密码")
        print("  python reset_password.py reset <用户名> <新密码>  # 直接设置新密码")
        print("\n示例:")
        print("  python reset_password.py list")
        print("  python reset_password.py reset admin")
        print("  python reset_password.py reset tongjiahao newpass123")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        list_users()
    
    elif command == 'reset':
        if len(sys.argv) < 3:
            print("错误: 请指定要重置密码的用户名")
            print("使用方法: python reset_password.py reset <用户名>")
            return
        
        username = sys.argv[2]
        new_password = sys.argv[3] if len(sys.argv) > 3 else None
        
        if new_password and len(new_password) < 6:
            print("错误: 密码长度至少为6位")
            return
        
        reset_password(username, new_password)
    
    else:
        print(f"错误: 未知命令 '{command}'")
        print("支持的命令: list, reset")

if __name__ == '__main__':
    main()