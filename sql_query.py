#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL查询工具
用于直接执行SQL查询语句查看数据库数据
"""

import sqlite3
import sys
import os
from tabulate import tabulate

def get_db_connection():
    """获取数据库连接"""
    try:
        conn = sqlite3.connect('feedback_system.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"数据库连接失败: {e}")
        return None

def execute_query(conn, query):
    """执行SQL查询"""
    try:
        cursor = conn.execute(query)
        
        # 如果是SELECT查询，显示结果
        if query.strip().upper().startswith('SELECT'):
            rows = cursor.fetchall()
            if rows:
                # 获取列名
                columns = [description[0] for description in cursor.description]
                
                # 转换为列表格式以便使用tabulate
                data = []
                for row in rows:
                    data.append([str(item) if item is not None else 'NULL' for item in row])
                
                # 使用tabulate美化输出
                print(tabulate(data, headers=columns, tablefmt='grid'))
                print(f"\n查询结果: {len(rows)} 行")
            else:
                print("查询结果为空")
        else:
            # 对于非SELECT查询，显示影响的行数
            conn.commit()
            print(f"查询执行成功，影响 {cursor.rowcount} 行")
            
    except sqlite3.Error as e:
        print(f"SQL执行失败: {e}")
        conn.rollback()

def show_common_queries():
    """显示常用查询示例"""
    queries = {
        "1": {
            "description": "查看所有用户",
            "sql": "SELECT id, username, name, email, is_admin, created_at FROM users;"
        },
        "2": {
            "description": "查看所有反馈",
            "sql": "SELECT f.id, u.name as 提交人, f.content as 内容, f.status as 状态, f.has_answer as 有答案, f.created_at as 提交时间 FROM feedback f JOIN users u ON f.user_id = u.id ORDER BY f.created_at DESC;"
        },
        "3": {
            "description": "查看待处理的反馈",
            "sql": "SELECT f.id, u.name as 提交人, f.content as 内容, f.created_at as 提交时间 FROM feedback f JOIN users u ON f.user_id = u.id WHERE f.status = '新问题' ORDER BY f.created_at DESC;"
        },
        "4": {
            "description": "查看已解决的反馈",
            "sql": "SELECT f.id, u.name as 提交人, f.content as 内容, f.handler as 处理人, f.updated_at as 处理时间 FROM feedback f JOIN users u ON f.user_id = u.id WHERE f.status = '已解决' ORDER BY f.updated_at DESC;"
        },
        "5": {
            "description": "查看有答案的反馈",
            "sql": "SELECT f.id, u.name as 提交人, f.content as 问题内容, f.answer as 答案, f.status as 状态 FROM feedback f JOIN users u ON f.user_id = u.id WHERE f.has_answer = 1 ORDER BY f.created_at DESC;"
        },
        "6": {
            "description": "按状态统计反馈数量",
            "sql": "SELECT status as 状态, COUNT(*) as 数量 FROM feedback GROUP BY status ORDER BY 数量 DESC;"
        },
        "7": {
            "description": "按用户统计反馈数量",
            "sql": "SELECT u.name as 用户名, COUNT(f.id) as 反馈数量 FROM users u LEFT JOIN feedback f ON u.id = f.user_id GROUP BY u.id, u.name ORDER BY 反馈数量 DESC;"
        },
        "8": {
            "description": "查看最近7天的反馈",
            "sql": "SELECT f.id, u.name as 提交人, f.content as 内容, f.status as 状态, f.created_at as 提交时间 FROM feedback f JOIN users u ON f.user_id = u.id WHERE f.created_at >= datetime('now', '-7 days') ORDER BY f.created_at DESC;"
        },
        "9": {
            "description": "查看通知日志",
            "sql": "SELECT n.id, u.name as 用户, n.notification_type as 通知类型, n.status as 状态, n.sent_at as 发送时间 FROM notification_logs n JOIN users u ON n.user_id = u.id ORDER BY n.sent_at DESC LIMIT 20;"
        },
        "10": {
            "description": "查看操作日志",
            "sql": "SELECT o.id, o.feedback_id as 反馈ID, u.name as 操作人, o.operation_type as 操作类型, o.old_status as 原状态, o.new_status as 新状态, o.created_at as 操作时间 FROM operation_logs o JOIN users u ON o.operator_id = u.id ORDER BY o.created_at DESC LIMIT 20;"
        }
    }
    
    print("\n=== 常用查询示例 ===")
    for key, query in queries.items():
        print(f"{key:2}. {query['description']}")
    
    return queries

def main():
    """主函数"""
    print("团队反馈管理系统 - SQL查询工具")
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
            print("1. 执行自定义SQL查询")
            print("2. 使用常用查询示例")
            print("3. 查看数据库表结构")
            print("4. 退出")
            
            choice = input("\n请输入选项 (1-4): ").strip()
            
            if choice == '1':
                print("\n请输入SQL查询语句 (输入 'quit' 返回主菜单):")
                while True:
                    query = input("SQL> ").strip()
                    if query.lower() == 'quit':
                        break
                    if query:
                        execute_query(conn, query)
                        
            elif choice == '2':
                queries = show_common_queries()
                query_choice = input("\n请选择查询 (1-10): ").strip()
                if query_choice in queries:
                    print(f"\n执行查询: {queries[query_choice]['description']}")
                    print(f"SQL: {queries[query_choice]['sql']}")
                    print("-" * 50)
                    execute_query(conn, queries[query_choice]['sql'])
                else:
                    print("无效选项")
                    
            elif choice == '3':
                # 显示所有表的结构
                tables_query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
                cursor = conn.execute(tables_query)
                tables = cursor.fetchall()
                
                print("\n=== 数据库表结构 ===")
                for table in tables:
                    table_name = table[0]
                    print(f"\n表名: {table_name}")
                    structure_query = f"PRAGMA table_info({table_name});"
                    cursor = conn.execute(structure_query)
                    columns = cursor.fetchall()
                    
                    headers = ['序号', '字段名', '类型', '非空', '默认值', '主键']
                    data = []
                    for col in columns:
                        data.append([
                            col[0],  # cid
                            col[1],  # name
                            col[2],  # type
                            '是' if col[3] else '否',  # notnull
                            col[4] if col[4] else '',  # default
                            '是' if col[5] else '否'   # pk
                        ])
                    
                    print(tabulate(data, headers=headers, tablefmt='grid'))
                    
            elif choice == '4':
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
    # 检查是否安装了tabulate库
    try:
        import tabulate
    except ImportError:
        print("警告: 未安装 tabulate 库，表格显示可能不够美观")
        print("可以通过以下命令安装: pip install tabulate")
        print("")
        
        # 如果没有tabulate，使用简单的表格显示
        def simple_tabulate(data, headers, tablefmt='grid'):
            if not data:
                return ""
            
            # 计算每列的最大宽度
            col_widths = [len(str(h)) for h in headers]
            for row in data:
                for i, cell in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
            
            # 创建分隔线
            separator = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"
            
            # 构建表格
            result = [separator]
            
            # 表头
            header_row = "|" + "|".join([f" {str(h):<{col_widths[i]}} " for i, h in enumerate(headers)]) + "|"
            result.append(header_row)
            result.append(separator)
            
            # 数据行
            for row in data:
                data_row = "|" + "|".join([f" {str(cell):<{col_widths[i]}} " for i, cell in enumerate(row)]) + "|"
                result.append(data_row)
            
            result.append(separator)
            return "\n".join(result)
        
        # 替换tabulate函数
        tabulate = simple_tabulate
    
    main()