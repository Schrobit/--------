import smtplib
import logging
import os
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from contextlib import contextmanager
from typing import Optional, Dict, Any, Tuple, List
from database import get_db_connection

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 邮件配置类
class EmailConfig:
    """邮件配置管理类"""
    
    def __init__(self):
        # 优先从环境变量读取配置，提高安全性
        self.SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.exmail.qq.com')
        self.SMTP_PORT = int(os.getenv('SMTP_PORT', '465'))
        self.SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'administrator@ei-power.tech')
        self.SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', 't4pFYxV98myHCQqt')
        self.SYSTEM_URL = os.getenv('SYSTEM_URL', 'https://ei-power.tjh666.cn')
        self.SENDER_NAME = os.getenv('SENDER_NAME', 'EI Power反馈系统')
        
    def validate(self) -> bool:
        """验证邮件配置是否完整"""
        required_fields = [self.SMTP_SERVER, self.SENDER_EMAIL, self.SENDER_PASSWORD]
        return all(field for field in required_fields)

# 全局配置实例
email_config = EmailConfig()

class EmailService:
    """邮件服务类 - 统一管理邮件发送逻辑"""
    
    def __init__(self, config: EmailConfig = None):
        self.config = config or email_config
        
    @contextmanager
    def get_smtp_connection(self):
        """获取SMTP连接的上下文管理器"""
        server = None
        try:
            logger.info(f"连接SMTP服务器: {self.config.SMTP_SERVER}:{self.config.SMTP_PORT}")
            server = smtplib.SMTP_SSL(self.config.SMTP_SERVER, self.config.SMTP_PORT)
            
            logger.info("进行身份验证...")
            server.login(self.config.SENDER_EMAIL, self.config.SENDER_PASSWORD)
            
            yield server
            
        except Exception as e:
            logger.error(f"SMTP连接失败: {str(e)}")
            raise
        finally:
            if server:
                try:
                    server.quit()
                except:
                    pass
    
    def create_email_message(self, recipient_email: str, subject: str, body: str) -> MIMEMultipart:
        """创建邮件消息对象"""
        msg = MIMEMultipart()
        
        # 设置From头部，符合RFC5322标准
        from_name = Header(self.config.SENDER_NAME, 'utf-8').encode()
        msg['From'] = f'{from_name} <{self.config.SENDER_EMAIL}>'
        msg['To'] = recipient_email
        msg['Subject'] = Header(subject, 'utf-8')
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        return msg
    
    def send_email(self, recipient_email: str, subject: str, body: str) -> bool:
        """发送邮件的通用方法"""
        try:
            msg = self.create_email_message(recipient_email, subject, body)
            
            with self.get_smtp_connection() as server:
                logger.info("正在发送邮件...")
                text = msg.as_string()
                server.sendmail(self.config.SENDER_EMAIL, recipient_email, text)
                
            logger.info(f"邮件发送成功: {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {recipient_email} - {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """测试邮件配置"""
        logger.info("开始测试邮件配置...")
        try:
            with self.get_smtp_connection():
                pass  # 连接成功即可
            logger.info("邮件配置测试成功")
            return True
        except Exception as e:
            logger.error(f"邮件配置测试失败: {str(e)}")
            return False

# 全局邮件服务实例
email_service = EmailService()

# 邮件模板类
class EmailTemplates:
    """邮件模板管理类"""
    
    @staticmethod
    def reminder_email(username: str, remaining_count: int, system_url: str) -> Tuple[str, str]:
        """提醒邮件模板"""
        subject = '[行动要求] 今日反馈未提交'
        body = f"""亲爱的 {username}，

您好！

系统检测到您今日还需要提交 {remaining_count} 个问题反馈。

请及时登录系统完成提交：
{system_url}

提交截止时间：今日24:00

如有疑问，请联系admin@ei-power.tech。

此邮件为系统自动发送，请勿回复。

EI Power 反馈管理系统"""
        return subject, body
    
    @staticmethod
    def deletion_notification(username: str, feedback_content: str, admin_name: str, deletion_reason: str = "") -> Tuple[str, str]:
        """删除通知邮件模板"""
        subject = '[通知] 您的问题已被删除'
        reason_text = f"\n删除原因：{deletion_reason}" if deletion_reason else ""
        
        body = f"""亲爱的 {username}，

您好！

您提交的以下问题已被管理员删除：

    问题内容：{feedback_content}
处理人员：{admin_name}{reason_text}

如对此操作有疑问，请联系管理员 admin@ei-power.tech。

此邮件为系统自动发送，请勿回复。

EI Power 反馈管理系统"""
        return subject, body
    
    @staticmethod
    def status_update_notification(username: str, feedback_id: int, feedback_content: str, 
                                 old_status: str, new_status: str, handler_name: str = "",
                                 admin_comment: str = "", revised_proposal: str = "",
                                 system_url: str = "") -> Tuple[str, str]:
        """状态更新通知邮件模板"""
        subject = f'[问题状态更新] 您的问题 #{feedback_id} 状态已更新'
        
        # 状态中文映射
        status_map = {
            '新问题': '新问题',
            '处理中': '处理中', 
            '已解决': '已解决',
            '已关闭': '已关闭'
        }
        
        old_status_cn = status_map.get(old_status, old_status)
        new_status_cn = status_map.get(new_status, new_status)
        
        body_parts = [
            f"亲爱的 {username}，",
            "",
            "您好！",
            "",
            f"您提交的问题 #{feedback_id} 状态已更新：",
            "",
            f"问题内容：{feedback_content[:100]}{'...' if len(feedback_content) > 100 else ''}",
            f"状态变更：{old_status_cn} → {new_status_cn}",
            f"处理人员：{handler_name}" if handler_name else "",
        ]
        
        if admin_comment:
            body_parts.extend(["", "处理意见：", admin_comment])
        
        if revised_proposal:
            body_parts.extend(["", "修正后的问题：", revised_proposal])
        
        body_parts.extend([
            "",
            f"您可以登录系统查看详细信息：{system_url}",
            "",
            "如有疑问，请联系管理员。",
            "",
            "此邮件为系统自动发送，请勿回复。",
            "",
            "EI Power 问题管理系统"
        ])
        
        body = "\n".join(filter(None, body_parts))
        return subject, body

# 数据库操作类
class DatabaseOperations:
    """数据库操作封装类"""
    
    @staticmethod
    def get_user_email_for_sending(user_id: int) -> Optional[str]:
        """获取用户的发送邮箱（交替使用主邮箱和备份邮箱）"""
        with get_db_connection() as conn:
            # 获取用户的邮箱信息
            user = conn.execute('SELECT email, backup_email FROM users WHERE id = ?', (user_id,)).fetchone()
            if not user:
                return None
            
            # 获取该用户最近一次发送邮件使用的邮箱
            last_email = conn.execute(
                'SELECT email FROM reminder_logs WHERE user_id = ? ORDER BY sent_at DESC LIMIT 1',
                (user_id,)
            ).fetchone()
            
            # 如果有备份邮箱，则交替使用
            if user['backup_email']:
                if last_email and last_email['email'] == user['email']:
                    return user['backup_email']  # 上次用的是主邮箱，这次用备份邮箱
                else:
                    return user['email']  # 上次用的是备份邮箱或者是第一次发送，这次用主邮箱
            else:
                return user['email']  # 没有备份邮箱，使用主邮箱
    
    @staticmethod
    def get_users_to_remind(today: str) -> List[Dict[str, Any]]:
        """获取需要提醒的用户列表"""
        with get_db_connection() as conn:
            return conn.execute('''
                SELECT u.id, u.username, u.email, u.backup_email,
                       COALESCE(f.feedback_count, 0) as feedback_count
                FROM users u
                LEFT JOIN (
                    SELECT user_id, COUNT(*) as feedback_count
                    FROM feedback
                    WHERE DATE(created_at) = ?
                    GROUP BY user_id
                ) f ON u.id = f.user_id
                WHERE u.is_admin = 0 AND COALESCE(f.feedback_count, 0) < 3
            ''', (today,)).fetchall()
    
    @staticmethod
    def log_reminder_result(user_id: int, email: str, status: str, error_message: str = None):
        """记录提醒结果"""
        with get_db_connection() as conn:
            if error_message:
                conn.execute(
                    'INSERT INTO reminder_logs (user_id, email, status, sent_at, error_message) VALUES (?, ?, ?, ?, ?)',
                    (user_id, email, status, datetime.now(), error_message)
                )
            else:
                conn.execute(
                    'INSERT INTO reminder_logs (user_id, email, status, sent_at) VALUES (?, ?, ?, ?)',
                    (user_id, email, status, datetime.now())
                )
            conn.commit()
    
    @staticmethod
    def log_notification_result(feedback_id: int, user_id: int, email: str, notification_type: str,
                              old_status: str, new_status: str, status: str, handler_name: str = "",
                              error_message: str = None):
        """记录通知结果"""
        with get_db_connection() as conn:
            if error_message:
                conn.execute('''
                    INSERT INTO notification_logs (feedback_id, user_id, email, notification_type, 
                                                 old_status, new_status, status, sent_at, error_message, handler_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    feedback_id, user_id, email, notification_type,
                    old_status, new_status, status, datetime.now(), error_message, handler_name
                ))
            else:
                conn.execute('''
                    INSERT INTO notification_logs (feedback_id, user_id, email, notification_type, 
                                                 old_status, new_status, status, sent_at, handler_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    feedback_id, user_id, email, notification_type,
                    old_status, new_status, status, datetime.now(), handler_name
                ))
            conn.commit()

# 主要功能函数
def get_user_email_for_sending(user_id: int) -> Optional[str]:
    """获取用户的发送邮箱（交替使用主邮箱和备份邮箱）"""
    return DatabaseOperations.get_user_email_for_sending(user_id)

def send_deletion_notification_email(recipient_email: str, username: str, feedback_content: str, 
                                   admin_name: str, deletion_reason: str = "") -> bool:
    """发送问题删除通知邮件"""
    logger.info(f"开始发送删除通知邮件给 {username} ({recipient_email})")
    
    try:
        subject, body = EmailTemplates.deletion_notification(username, feedback_content, admin_name, deletion_reason)
        email_service.send_email(recipient_email, subject, body)
        logger.info(f"删除通知邮件发送成功: {username} ({recipient_email})")
        return True
    except Exception as e:
        logger.error(f"发送删除通知邮件失败: {username} ({recipient_email}) - {str(e)}")
        raise

def send_reminder_email(recipient_email: str, username: str, remaining_count: int) -> bool:
    """发送提醒邮件"""
    logger.info(f"开始发送提醒邮件给 {username} ({recipient_email})")
    
    try:
        subject, body = EmailTemplates.reminder_email(username, remaining_count, email_config.SYSTEM_URL)
        email_service.send_email(recipient_email, subject, body)
        logger.info(f"提醒邮件发送成功: {username} ({recipient_email})")
        return True
    except Exception as e:
        logger.error(f"发送提醒邮件失败: {username} ({recipient_email}) - {str(e)}")
        raise

def test_email_config() -> bool:
    """测试邮件配置"""
    return email_service.test_connection()

def check_and_send_reminders() -> Tuple[int, int]:
    """检查并发送提醒邮件"""
    logger.info("开始检查今日未提交反馈的用户...")
    today = date.today().strftime('%Y-%m-%d')
    
    users_to_remind = DatabaseOperations.get_users_to_remind(today)
    logger.info(f"找到 {len(users_to_remind)} 个用户需要发送提醒")
    
    success_count = 0
    fail_count = 0
    
    import time
    
    for i, user in enumerate(users_to_remind):
        remaining = 3 - user['feedback_count']
        logger.info(f"处理用户: {user['username']} (已提交: {user['feedback_count']}, 剩余: {remaining})")
        
        # 获取要发送的邮箱地址（交替使用主邮箱和备份邮箱）
        target_email = get_user_email_for_sending(user['id'])
        if not target_email:
            logger.warning(f"用户 {user['username']} 没有可用的邮箱地址")
            continue
            
        logger.info(f"发送到邮箱: {target_email}")
        
        try:
            send_reminder_email(target_email, user['username'], remaining)
            DatabaseOperations.log_reminder_result(user['id'], target_email, '成功')
            success_count += 1
            logger.info(f"邮件发送成功: {user['username']} ({target_email})")
        except Exception as e:
            DatabaseOperations.log_reminder_result(user['id'], target_email, '失败', str(e))
            fail_count += 1
            logger.error(f"邮件发送失败: {user['username']} ({target_email}) - {str(e)}")
        
        # 如果不是最后一个用户，等待10秒再发送下一封邮件
        if i < len(users_to_remind) - 1:
            logger.info("等待10秒后发送下一封邮件...")
            time.sleep(10)
    
    logger.info(f"提醒完成 - 成功: {success_count}, 失败: {fail_count}")
    return success_count, fail_count

def send_manual_reminder(user_identifier: str, target_email: str = None) -> Dict[str, Any]:
    """手动发送邮件提醒 - 为Web API优化的版本"""
    logger.info("开始手动发送邮件提醒...")
    today = date.today().strftime('%Y-%m-%d')
    
    # 判断是用户ID还是用户名
    if user_identifier.isdigit():
        where_clause = "AND u.id = ?"
        params = (today, int(user_identifier))
        logger.info(f"目标用户ID: {user_identifier}")
    else:
        where_clause = "AND u.username = ?"
        params = (today, user_identifier)
        logger.info(f"目标用户名: {user_identifier}")
    
    # 查找用户
    with get_db_connection() as conn:
        users_to_remind = conn.execute(f'''
            SELECT u.id, u.username, u.email, u.backup_email,
                   COALESCE(f.feedback_count, 0) as feedback_count
            FROM users u
            LEFT JOIN (
                SELECT user_id, COUNT(*) as feedback_count
                FROM feedback
                WHERE DATE(created_at) = ?
                GROUP BY user_id
            ) f ON u.id = f.user_id
            WHERE u.is_admin = 0 AND COALESCE(f.feedback_count, 0) < 3 {where_clause}
        ''', params).fetchall()
    
    if not users_to_remind:
        logger.info("没有找到需要提醒的用户")
        return {'success': False, 'message': '用户不存在或已完成今日反馈'}
    
    user = users_to_remind[0]  # 应该只有一个用户
    remaining = 3 - user['feedback_count']
    logger.info(f"处理用户: {user['username']} (已提交: {user['feedback_count']}, 剩余: {remaining})")
    
    # 确定要发送的邮箱地址
    if target_email:
        # 验证指定的邮箱是否属于该用户
        if target_email not in [user['email'], user['backup_email']]:
            return {'success': False, 'message': f'指定的邮箱地址不属于用户 {user["username"]}'}
        logger.info(f"使用指定邮箱: {target_email}")
    else:
        # 自动选择邮箱（交替使用主邮箱和备份邮箱）
        target_email = get_user_email_for_sending(user['id'])
        if not target_email:
            return {'success': False, 'message': f'用户 {user["username"]} 没有可用的邮箱地址'}
        logger.info(f"自动选择邮箱: {target_email}")
    
    try:
        send_reminder_email(target_email, user['username'], remaining)
        DatabaseOperations.log_reminder_result(user['id'], target_email, '手动成功')
        
        logger.info(f"手动提醒发送成功: {user['username']} ({target_email})")
        return {
            'success': True, 
            'username': user['username'], 
            'message': f'提醒邮件已发送给 {user["username"]} ({target_email})'
        }
        
    except Exception as e:
        DatabaseOperations.log_reminder_result(user['id'], target_email, '手动失败', str(e))
        
        logger.error(f"手动提醒发送失败: {user['username']} - {str(e)}")
        return {
            'success': False, 
            'username': user['username'], 
            'message': f'发送失败: {str(e)}'
        }

def send_manual_reminder_batch(user_id: int = None, username: str = None) -> Tuple[int, int]:
    """批量手动发送邮件提醒 - 为命令行使用"""
    logger.info("开始手动发送邮件提醒...")
    today = date.today().strftime('%Y-%m-%d')
    
    # 构建查询条件
    if user_id:
        where_clause = "AND u.id = ?"
        params = (today, user_id)
        logger.info(f"目标用户ID: {user_id}")
    elif username:
        where_clause = "AND u.username = ?"
        params = (today, username)
        logger.info(f"目标用户名: {username}")
    else:
        where_clause = ""
        params = (today,)
        logger.info("目标: 所有未完成用户")
    
    # 查找用户
    with get_db_connection() as conn:
        users_to_remind = conn.execute(f'''
            SELECT u.id, u.username, u.email,
                   COALESCE(f.feedback_count, 0) as feedback_count
            FROM users u
            LEFT JOIN (
                SELECT user_id, COUNT(*) as feedback_count
                FROM feedback
                WHERE DATE(created_at) = ?
                GROUP BY user_id
            ) f ON u.id = f.user_id
            WHERE u.is_admin = 0 AND COALESCE(f.feedback_count, 0) < 3 {where_clause}
        ''', params).fetchall()
    
    if not users_to_remind:
        logger.info("没有找到需要提醒的用户")
        return 0, 0
    
    logger.info(f"找到 {len(users_to_remind)} 个用户需要发送提醒")
    
    success_count = 0
    fail_count = 0
    
    for user in users_to_remind:
        remaining = 3 - user['feedback_count']
        logger.info(f"处理用户: {user['username']} (已提交: {user['feedback_count']}, 剩余: {remaining})")
        
        try:
            send_reminder_email(user['email'], user['username'], remaining)
            DatabaseOperations.log_reminder_result(user['id'], user['email'], '手动成功')
            success_count += 1
        except Exception as e:
            DatabaseOperations.log_reminder_result(user['id'], user['email'], '手动失败', str(e))
            fail_count += 1
    
    logger.info(f"手动提醒完成 - 成功: {success_count}, 失败: {fail_count}")
    return success_count, fail_count

def send_status_update_notification(feedback_id: int, old_status: str, new_status: str, 
                                  admin_comment: str = '', revised_proposal: str = '', 
                                  handler_name: str = '') -> bool:
    """发送问题状态更新通知邮件给提议人"""
    logger.info(f"开始发送状态更新通知邮件 - 问题ID: {feedback_id}")
    
    try:
        with get_db_connection() as conn:
            # 获取问题和用户信息
            feedback_info = conn.execute('''
                SELECT f.id, f.content, f.status, f.created_at, u.id as user_id, u.username, u.email, u.name
                FROM feedback f
                JOIN users u ON f.user_id = u.id
                WHERE f.id = ?
            ''', (feedback_id,)).fetchone()
            
            if not feedback_info:
                logger.error(f"未找到问题信息: {feedback_id}")
                return False
            
            username = feedback_info['name'] or feedback_info['username']
            subject, body = EmailTemplates.status_update_notification(
                username, feedback_id, feedback_info['content'],
                old_status, new_status, handler_name,
                admin_comment, revised_proposal, email_config.SYSTEM_URL
            )
            
            # 发送邮件
            email_service.send_email(feedback_info['email'], subject, body)
            
            # 记录通知日志
            DatabaseOperations.log_notification_result(
                feedback_id, feedback_info['user_id'], feedback_info['email'], '状态更新',
                old_status, new_status, '成功', handler_name
            )
            
            logger.info(f"状态更新通知发送成功: {feedback_info['username']} ({feedback_info['email']})")
            return True
            
    except Exception as e:
        logger.error(f"发送状态更新通知失败: {str(e)}")
        
        # 记录失败日志
        try:
            with get_db_connection() as conn:
                user_info = conn.execute('SELECT user_id FROM feedback WHERE id = ?', (feedback_id,)).fetchone()
                if user_info:
                    DatabaseOperations.log_notification_result(
                        feedback_id, user_info['user_id'], '', '状态更新',
                        old_status, new_status, '失败', handler_name, str(e)
                    )
        except:
            pass
        
        return False

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'test':
            # 测试邮件配置
            test_email_config()
        elif command == 'check':
            # 检查并发送提醒
            check_and_send_reminders()
        elif command == 'manual':
            # 手动发送提醒
            if len(sys.argv) > 2:
                target = sys.argv[2]
                if target.isdigit():
                    send_manual_reminder_batch(user_id=int(target))
                else:
                    send_manual_reminder_batch(username=target)
            else:
                send_manual_reminder_batch()
        else:
            print("使用方法:")
            print("  python email_service.py test          # 测试邮件配置")
            print("  python email_service.py check         # 检查并发送提醒")
            print("  python email_service.py manual        # 手动发送所有提醒")
            print("  python email_service.py manual <用户ID>  # 手动发送给指定用户ID")
            print("  python email_service.py manual <用户名>  # 手动发送给指定用户名")
    else:
        # 默认测试邮件配置
        test_email_config()