import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect('feedback_system.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_tables(conn):
    """创建所有数据库表"""
    # 创建用户表
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            backup_email TEXT,
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
            has_answer BOOLEAN DEFAULT 0,
            answer TEXT,
            status TEXT DEFAULT '新问题',
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

def insert_initial_users(conn):
    """插入初始用户数据"""
    # 预置用户数据 (username, password, email, backup_email, name, is_admin)
    users_data = [
        ('admin', 'tjh123', 'admin@ei-power.tech', None, '管理员', True),
        ('tongjiahao', '@ei-power.tech', 'tongjiahao@ei-power.tech', 'admin@tjh666.cn', '童佳豪', False),
        ('wujunhao', '@ei-power.tech', 'misa@ei-power.tech', 'wjhlxynb666@163.com', '吴俊豪', False),
        ('caocaiyue', '@ei-power.tech', 'yuanshanzhang@ei-power.tech', '1447091509@qq.com', '曹彩月', False),
        ('yeqiujingyi', '@ei-power.tech', 'noname@ei-power.tech', '1473886876@qq.com', '叶邱静怡', False),
        ('chenjiaxin', '@ei-power.tech', 'chenjiaxin@ei-power.tech', '2174874621@qq.com', '陈佳欣', False),
        ('zhangtong', '@ei-power.tech', 'wuyigexiaolingcheng@ei-power.tech', '3512059073@qq.com', '张彤', False),
        ('wangxingyue', '@ei-power.tech', 'xiaoyuaishuijiao@ei-power.tech', '2563442458@qq.com', '王星月', False),
        ('niyangzhao', '@ei-power.tech', 'chuaner@ei-power.tech', '807597677@qq.com', '倪杨钊', False),
        ('xuruwen', '@ei-power.tech', 'sandishousibushousi@ei-power.tech', '3151247853@qq.com', '徐茹雯', False),
        ('jiangcixue', '@ei-power.tech', 'xiaoxue@ei-power.tech', '2757186656@qq.com', '姜赐雪', False)
    ]
    
    for username, password, email, backup_email, name, is_admin in users_data:
        # 检查用户是否已存在
        existing_user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if not existing_user:
            # 生成密码哈希
            password_hash = generate_password_hash(password)
            conn.execute(
                'INSERT INTO users (username, password, email, backup_email, name, is_admin) VALUES (?, ?, ?, ?, ?, ?)',
                (username, password_hash, email, backup_email, name, is_admin)
            )
            print(f"已创建用户: {name} ({username})")
        else:
            print(f"用户已存在: {name} ({username})")

def init_db():
    """初始化数据库"""
    print("开始初始化数据库...")
    
    conn = get_db_connection()
    
    try:
        # 创建所有表
        create_tables(conn)
        print("数据库表创建完成")
        
        # 插入初始用户数据
        insert_initial_users(conn)
        
        # 提交事务
        conn.commit()
        print("数据库初始化完成")
        
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()