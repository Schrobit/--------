import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect('feedback_system.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库"""
    conn = get_db_connection()
    
    # 创建用户表
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            name TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建反馈表
    conn.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            status TEXT DEFAULT '新提案',
            revised_proposal TEXT,
            admin_comment TEXT,
            handler TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # 创建提醒日志表
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reminder_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            status TEXT NOT NULL,
            error_message TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # 创建操作日志表
    conn.execute('''
        CREATE TABLE IF NOT EXISTS operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feedback_id TEXT NOT NULL,
            operator_id INTEGER NOT NULL,
            operation_type TEXT NOT NULL,
            old_content TEXT,
            new_content TEXT,
            old_status TEXT,
            new_status TEXT,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (feedback_id) REFERENCES feedback (id),
            FOREIGN KEY (operator_id) REFERENCES users (id)
        )
    ''')
    
    # 创建通知日志表
    conn.execute('''
        CREATE TABLE IF NOT EXISTS notification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feedback_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            notification_type TEXT NOT NULL,
            old_status TEXT,
            new_status TEXT,
            status TEXT NOT NULL,
            error_message TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            handler_name TEXT,
            FOREIGN KEY (feedback_id) REFERENCES feedback (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # 预置用户数据
    users_data = [
        ('admin', 'admin123', 'admin@ei-power.tech', '管理员', True),
        ('yuanshanzhang', 'user123', 'yuanshanzhang@ei-power.tech', '曹彩月', False),
        ('tongjiahao', 'user123', 'tongjiahao@ei-power.tech', '童佳豪', False),
        ('iiio', 'user123', 'iiio@ei-power.tech', '陈佳欣', False),
        ('xiaoxue', 'user123', 'xiaoxue@ei-power.tech', '姜赐雪', False),
        ('chuaner', 'user123', 'chuaner@ei-power.tech', '倪杨钊', False),
        ('xiaoyuaishuijiao', 'user123', 'xiaoyuaishuijiao@ei-power.tech', '王星月', False),
        ('misa', 'user123', 'misa@ei-power.tech', '吴俊豪', False),
        ('sandishousibushousi', 'user123', 'sandishousibushousi@ei-power.tech', '徐茹雯', False),
        ('noname', 'user123', 'noname@ei-power.tech', '叶邱静怡', False),
        ('wuyigexiaolingcheng', 'user123', 'wuyigexiaolingcheng@ei-power.tech', '张彤', False)
    ]
    
    # 首先检查是否需要添加name字段
    try:
        conn.execute('SELECT name FROM users LIMIT 1')
    except sqlite3.OperationalError:
        # name字段不存在，添加该字段
        conn.execute('ALTER TABLE users ADD COLUMN name TEXT')
        print("已添加name字段到users表")
    
    for username, password, email, name, is_admin in users_data:
        # 检查用户是否已存在
        existing_user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if not existing_user:
            # 使用提供的密码
            password_hash = generate_password_hash(password)
            conn.execute(
                'INSERT INTO users (username, password, email, name, is_admin) VALUES (?, ?, ?, ?, ?)',
                (username, password_hash, email, name, is_admin)
            )
        else:
            # 更新现有用户的中文姓名
            conn.execute(
                'UPDATE users SET name = ? WHERE username = ?',
                (name, username)
            )
    
    conn.commit()
    conn.close()
    print("数据库初始化完成")

if __name__ == '__main__':
    init_db()