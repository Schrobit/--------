#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库查看工具
用于查看团队反馈管理系统中的数据库数据
"""

import sqlite3
import sys
import os
from datetime import datetime

def get_db_connection():
    """获取数据库连接"""
    try:
        conn = sqlite3.connect('feedback_system.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"数据库连接失败: {e}")
        return None

def show_table_structure(conn, table_name):
    """显示表结构"""
    try:
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print(f"\n=== {table_name} 表结构 ===")
        print(f"{'序号':<4} {'字段名':<20} {'类型':<15} {'非空':<6} {'默认值':<15} {'主键':<6}")
        print("-" * 70)
        
        for col in columns:
            cid, name, type_, notnull, default, pk = col
            print(f"{cid:<4} {name:<20} {type_:<15} {'是' if notnull else '否':<6} {str(default) if default else '':<15} {'是' if pk else '否':<6}")
            
    except sqlite3.Error as e:
        print(f"查看表结构失败: {e}")

def show_table_data(conn, table_name, limit=10):
    """显示表数据"""
    try:
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_count = cursor.fetchone()[0]
        
        cursor = conn.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        rows = cursor.fetchall()
        
        print(f"\n=== {table_name} 表数据 (总计: {total_count} 条, 显示前 {min(limit, total_count)} 条) ===")
        
        if not rows:
            print("表中暂无数据")
            return
            
        # 获取列名
        columns = [description[0] for description in cursor.description]
        
        # 打印表头
        header = " | ".join([f"{col:<15}" for col in columns])
        print(header)
        print("-" * len(header))
        
        # 打印数据行
        for row in rows:
            row_data = []
            for item in row:
                if item is None:
                    row_data.append("NULL")
                elif isinstance(item, str) and len(item) > 15:
                    row_data.append(item[:12] + "...")
                else:
                    row_data.append(str(item))
            
            print(" | ".join([f"{data:<15}" for data in row_data]))
            
    except sqlite3.Error as e:
        print(f"查看表数据失败: {e}")

def show_all_tables(conn):
    """显示所有表名"""
    try:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        print("\n=== 数据库中的所有表 ===")
        for i, table in enumerate(tables, 1):
            print(f"{i}. {table[0]}")
        
        return [table[0] for table in tables]
        
    except sqlite3.Error as e:
        print(f"获取表列表失败: {e}")
        return []

def show_feedback_summary(conn):
    """显示反馈数据统计摘要"""
    try:
        print("\n=== 反馈数据统计摘要 ===")
        
        # 按状态统计
        cursor = conn.execute("""
            SELECT status, COUNT(*) as count 
            FROM feedback 
            GROUP BY status 
            ORDER BY count DESC
        """)
        status_stats = cursor.fetchall()
        
        print("\n按状态统计:")
        for status, count in status_stats:
            print(f"  {status}: {count} 条")
        
        # 按用户统计
        cursor = conn.execute("""
            SELECT u.name, COUNT(f.id) as feedback_count
            FROM users u
            LEFT JOIN feedback f ON u.id = f.user_id
            GROUP BY u.id, u.name
            ORDER BY feedback_count DESC
        """)
        user_stats = cursor.fetchall()
        
        print("\n按用户统计:")
        for name, count in user_stats:
            print(f"  {name}: {count} 条反馈")
        
        # 有答案的反馈统计
        cursor = conn.execute("""
            SELECT 
                SUM(CASE WHEN has_answer = 1 THEN 1 ELSE 0 END) as with_answer,
                SUM(CASE WHEN has_answer = 0 OR has_answer IS NULL THEN 1 ELSE 0 END) as without_answer,
                COUNT(*) as total
            FROM feedback
        """)
        answer_stats = cursor.fetchone()
        
        print("\n答案统计:")
        print(f"  有答案: {answer_stats[0]} 条")
        print(f"  无答案: {answer_stats[1]} 条")
        print(f"  总计: {answer_stats[2]} 条")
        
    except sqlite3.Error as e:
        print(f"获取统计信息失败: {e}")

def search_feedback(conn, keyword):
    """搜索反馈内容"""
    try:
        cursor = conn.execute("""
            SELECT f.id, u.name, f.content, f.status, f.created_at
            FROM feedback f
            JOIN users u ON f.user_id = u.id
            WHERE f.content LIKE ? OR f.answer LIKE ?
            ORDER BY f.created_at DESC
        """, (f"%{keyword}%", f"%{keyword}%"))
        
        results = cursor.fetchall()
        
        print(f"\n=== 搜索结果: '{keyword}' (找到 {len(results)} 条) ===")
        
        if not results:
            print("未找到匹配的反馈")
            return
        
        for result in results:
            print(f"\nID: {result[0]}")
            print(f"提交人: {result[1]}")
            print(f"内容: {result[2][:100]}{'...' if len(result[2]) > 100 else ''}")
            print(f"状态: {result[3]}")
            print(f"提交时间: {result[4]}")
            print("-" * 50)
            
    except sqlite3.Error as e:
        print(f"搜索失败: {e}")

def main():
    """主函数"""
    print("团队反馈管理系统 - 数据库查看工具")
    print("=" * 40)
    
    # 检查数据库文件是否存在
    if not os.path.exists('feedback_system.db'):
        print("错误: 数据库文件 'feedback_system.db' 不存在")
        print("请确保在项目根目录下运行此脚本")
        return
    
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        while True:
            print("\n请选择操作:")
            print("1. 查看所有表")
            print("2. 查看表结构")
            print("3. 查看表数据")
            print("4. 查看反馈统计摘要")
            print("5. 搜索反馈内容")
            print("6. 退出")
            
            choice = input("\n请输入选项 (1-6): ").strip()
            
            if choice == '1':
                tables = show_all_tables(conn)
                
            elif choice == '2':
                tables = show_all_tables(conn)
                if tables:
                    table_name = input("\n请输入要查看的表名: ").strip()
                    if table_name in tables:
                        show_table_structure(conn, table_name)
                    else:
                        print("表名不存在")
                        
            elif choice == '3':
                tables = show_all_tables(conn)
                if tables:
                    table_name = input("\n请输入要查看的表名: ").strip()
                    if table_name in tables:
                        try:
                            limit = int(input("请输入要显示的行数 (默认10): ") or "10")
                            show_table_data(conn, table_name, limit)
                        except ValueError:
                            print("请输入有效的数字")
                    else:
                        print("表名不存在")
                        
            elif choice == '4':
                show_feedback_summary(conn)
                
            elif choice == '5':
                keyword = input("\n请输入搜索关键词: ").strip()
                if keyword:
                    search_feedback(conn, keyword)
                else:
                    print("请输入有效的关键词")
                    
            elif choice == '6':
                print("\n感谢使用!")
                break
                
            else:
                print("无效选项，请重新选择")
                
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n程序运行出错: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    main()