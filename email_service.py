import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from database import get_db_connection

# 邮件配置（需要根据实际情况修改）
SMTP_SERVER = 'smtp.exmail.qq.com'  # 企业邮箱SMTP服务器
SMTP_PORT = 465
SENDER_EMAIL = 'administrator@ei-power.tech'  # 发送方邮箱
SENDER_PASSWORD = 't4pFYxV98myHCQqt'  # 邮箱授权码
SYSTEM_URL = 'https://ei-power.tjh666.cn'  # 系统访问地址

def get_user_email_for_sending(user_id):
    """获取用户的发送邮箱（交替使用主邮箱和备份邮箱）"""
    conn = get_db_connection()
    
    # 获取用户的邮箱信息
    user = conn.execute('SELECT email, backup_email FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        conn.close()
        return None
    
    # 获取该用户最近一次发送邮件使用的邮箱
    last_email = conn.execute(
        'SELECT email FROM reminder_logs WHERE user_id = ? ORDER BY sent_at DESC LIMIT 1',
        (user_id,)
    ).fetchone()
    
    conn.close()
    
    # 如果有备份邮箱，则交替使用
    if user['backup_email']:
        if last_email and last_email['email'] == user['email']:
            # 上次用的是主邮箱，这次用备份邮箱
            return user['backup_email']
        else:
            # 上次用的是备份邮箱或者是第一次发送，这次用主邮箱
            return user['email']
    else:
        # 没有备份邮箱，使用主邮箱
        return user['email']

def send_reminder_email(recipient_email, username, remaining_count):
    """发送提醒邮件"""
    print(f"📧 [邮件服务] 开始发送提醒邮件给 {username} ({recipient_email})")
    
    try:
        # 创建邮件对象
        msg = MIMEMultipart()
        msg['From'] = Header(f'EI Power反馈系统 <{SENDER_EMAIL}>', 'utf-8')
        msg['To'] = Header(recipient_email, 'utf-8')
        msg['Subject'] = Header('[行动要求] 今日反馈未提交', 'utf-8')
        
        # 邮件正文
        body = f"""
亲爱的 {username}，

您好！

系统检测到您今日还需要提交 {remaining_count} 个问题反馈。

请及时登录系统完成提交：
{SYSTEM_URL}

提交截止时间：今日24:00

如有疑问，请联系admin@ei-power.tech。

此邮件为系统自动发送，请勿回复。

EI Power 反馈管理系统
        """.strip()
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        print(f"📧 [邮件服务] 正在连接SMTP服务器 {SMTP_SERVER}:{SMTP_PORT}")
        
        # 连接SMTP服务器并发送邮件 - 使用SSL连接
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        
        print(f"📧 [邮件服务] 正在进行身份验证...")
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        print(f"📧 [邮件服务] 正在发送邮件...")
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, recipient_email, text)
        server.quit()
        
        print(f"✅ [邮件服务] 提醒邮件发送成功: {username} ({recipient_email})")
        return True
        
    except Exception as e:
        print(f"❌ [邮件服务] 发送邮件失败: {str(e)}")
        print(f"❌ [邮件服务] 收件人: {username} ({recipient_email})")
        raise e

def test_email_config():
    """测试邮件配置"""
    print("🔧 [邮件服务] 开始测试邮件配置...")
    try:
        print(f"🔧 [邮件服务] 连接SMTP服务器: {SMTP_SERVER}:{SMTP_PORT}")
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        
        print(f"🔧 [邮件服务] 验证邮箱账户: {SENDER_EMAIL}")
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.quit()
        
        print("✅ [邮件服务] 邮件配置测试成功")
        return True
    except Exception as e:
        print(f"❌ [邮件服务] 邮件配置测试失败: {str(e)}")
        return False

def check_and_send_reminders():
    """检查并发送提醒邮件"""
    from datetime import date
    
    print("📅 [邮件提醒] 开始检查今日未提交反馈的用户...")
    today = date.today().strftime('%Y-%m-%d')
    
    conn = get_db_connection()
    # 查找今日未提交满3个反馈的用户
    users_to_remind = conn.execute('''
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
    
    print(f"📊 [邮件提醒] 找到 {len(users_to_remind)} 个用户需要发送提醒")
    
    success_count = 0
    fail_count = 0
    
    for user in users_to_remind:
        remaining = 3 - user['feedback_count']
        print(f"👤 [邮件提醒] 处理用户: {user['username']} (已提交: {user['feedback_count']}, 剩余: {remaining})")
        
        # 获取要发送的邮箱地址（交替使用主邮箱和备份邮箱）
        target_email = get_user_email_for_sending(user['id'])
        if not target_email:
            print(f"⚠️ [邮件提醒] 用户 {user['username']} 没有可用的邮箱地址")
            continue
            
        print(f"📧 [邮件提醒] 发送到邮箱: {target_email}")
        
        try:
            send_reminder_email(target_email, user['username'], remaining)
            # 记录提醒日志
            conn.execute(
                'INSERT INTO reminder_logs (user_id, email, status, sent_at) VALUES (?, ?, ?, ?)',
                (user['id'], target_email, '成功', datetime.now())
            )
            success_count += 1
        except Exception as e:
            # 记录失败日志
            conn.execute(
                'INSERT INTO reminder_logs (user_id, email, status, sent_at, error_message) VALUES (?, ?, ?, ?, ?)',
                (user['id'], target_email, '失败', datetime.now(), str(e))
            )
            fail_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"📈 [邮件提醒] 提醒完成 - 成功: {success_count}, 失败: {fail_count}")
    return success_count, fail_count

def send_manual_reminder(user_identifier):
    """手动发送邮件提醒 - 为Web API优化的版本"""
    from datetime import date
    
    print("🔧 [手动提醒] 开始手动发送邮件提醒...")
    today = date.today().strftime('%Y-%m-%d')
    
    conn = get_db_connection()
    
    # 判断是用户ID还是用户名
    if user_identifier.isdigit():
        where_clause = "AND u.id = ?"
        params = (today, int(user_identifier))
        print(f"🎯 [手动提醒] 目标用户ID: {user_identifier}")
    else:
        where_clause = "AND u.username = ?"
        params = (today, user_identifier)
        print(f"🎯 [手动提醒] 目标用户名: {user_identifier}")
    
    # 查找用户
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
        print("ℹ️ [手动提醒] 没有找到需要提醒的用户")
        conn.close()
        return {'success': False, 'message': '用户不存在或已完成今日反馈'}
    
    user = users_to_remind[0]  # 应该只有一个用户
    remaining = 3 - user['feedback_count']
    print(f"👤 [手动提醒] 处理用户: {user['username']} (已提交: {user['feedback_count']}, 剩余: {remaining})")
    
    # 获取要发送的邮箱地址（交替使用主邮箱和备份邮箱）
    target_email = get_user_email_for_sending(user['id'])
    if not target_email:
        conn.close()
        return {'success': False, 'message': f'用户 {user["username"]} 没有可用的邮箱地址'}
        
    print(f"📧 [手动提醒] 发送到邮箱: {target_email}")
    
    try:
        send_reminder_email(target_email, user['username'], remaining)
        # 记录提醒日志
        conn.execute(
            'INSERT INTO reminder_logs (user_id, email, status, sent_at) VALUES (?, ?, ?, ?)',
            (user['id'], target_email, '手动成功', datetime.now())
        )
        conn.commit()
        conn.close()
        
        print(f"✅ [手动提醒] 手动提醒发送成功: {user['username']} ({target_email})")
        return {'success': True, 'username': user['username'], 'message': f'提醒邮件已发送给 {user["username"]} ({target_email})'}
        
    except Exception as e:
        # 记录失败日志
        conn.execute(
            'INSERT INTO reminder_logs (user_id, email, status, sent_at, error_message) VALUES (?, ?, ?, ?, ?)',
            (user['id'], target_email, '手动失败', datetime.now(), str(e))
        )
        conn.commit()
        conn.close()
        
        print(f"❌ [手动提醒] 手动提醒发送失败: {user['username']} - {str(e)}")
        return {'success': False, 'username': user['username'], 'message': f'发送失败: {str(e)}'}

def send_manual_reminder_batch(user_id=None, username=None):
    """批量手动发送邮件提醒 - 为命令行使用"""
    from datetime import date
    
    print("🔧 [手动提醒] 开始手动发送邮件提醒...")
    today = date.today().strftime('%Y-%m-%d')
    
    conn = get_db_connection()
    
    # 构建查询条件
    if user_id:
        where_clause = "AND u.id = ?"
        params = (today, user_id)
        print(f"🎯 [手动提醒] 目标用户ID: {user_id}")
    elif username:
        where_clause = "AND u.username = ?"
        params = (today, username)
        print(f"🎯 [手动提醒] 目标用户名: {username}")
    else:
        where_clause = ""
        params = (today,)
        print(f"🎯 [手动提醒] 目标: 所有未完成用户")
    
    # 查找用户
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
        print("ℹ️ [手动提醒] 没有找到需要提醒的用户")
        conn.close()
        return 0, 0
    
    print(f"📊 [手动提醒] 找到 {len(users_to_remind)} 个用户需要发送提醒")
    
    success_count = 0
    fail_count = 0
    
    for user in users_to_remind:
        remaining = 3 - user['feedback_count']
        print(f"👤 [手动提醒] 处理用户: {user['username']} (已提交: {user['feedback_count']}, 剩余: {remaining})")
        
        try:
            send_reminder_email(user['email'], user['username'], remaining)
            # 记录提醒日志
            conn.execute(
                'INSERT INTO reminder_logs (user_id, email, status, sent_at) VALUES (?, ?, ?, ?)',
                (user['id'], user['email'], '手动成功', datetime.now())
            )
            success_count += 1
        except Exception as e:
            # 记录失败日志
            conn.execute(
                'INSERT INTO reminder_logs (user_id, email, status, sent_at, error_message) VALUES (?, ?, ?, ?, ?)',
                (user['id'], user['email'], '手动失败', datetime.now(), str(e))
            )
            fail_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"📈 [手动提醒] 手动提醒完成 - 成功: {success_count}, 失败: {fail_count}")
    return success_count, fail_count

def send_status_update_notification(feedback_id, old_status, new_status, admin_comment='', revised_proposal='', handler_name=''):
    """发送提案状态更新通知邮件给提议人"""
    print(f"📧 [状态通知] 开始发送状态更新通知邮件 - 提案ID: {feedback_id}")
    
    try:
        conn = get_db_connection()
        
        # 获取提案和用户信息
        feedback_info = conn.execute('''
            SELECT f.id, f.content, f.status, f.created_at, u.username, u.email, u.name
            FROM feedback f
            JOIN users u ON f.user_id = u.id
            WHERE f.id = ?
        ''', (feedback_id,)).fetchone()
        
        if not feedback_info:
            print(f"❌ [状态通知] 未找到提案信息: {feedback_id}")
            return False
        
        # 状态中文映射
        status_map = {
            '新提案': '新提案',
            '处理中': '处理中', 
            '已解决': '已解决',
            '已关闭': '已关闭'
        }
        
        old_status_cn = status_map.get(old_status, old_status)
        new_status_cn = status_map.get(new_status, new_status)
        
        # 创建邮件对象
        msg = MIMEMultipart()
        msg['From'] = Header(f'EI Power 提案管理系统 <{SENDER_EMAIL}>', 'utf-8')
        msg['To'] = Header(feedback_info['email'], 'utf-8')
        msg['Subject'] = Header(f'[提案状态更新] 您的提案 #{feedback_id} 状态已更新', 'utf-8')
        
        # 构建邮件正文
        body_parts = [
            f"亲爱的 {feedback_info['name'] or feedback_info['username']}，",
            "",
            "您好！",
            "",
            f"您提交的提案 #{feedback_id} 状态已更新：",
            "",
            f"提案内容：{feedback_info['content'][:100]}{'...' if len(feedback_info['content']) > 100 else ''}",
            f"状态变更：{old_status_cn} → {new_status_cn}",
            f"处理人员：{handler_name}" if handler_name else "",
        ]
        
        if admin_comment:
            body_parts.extend([
                "",
                "处理意见：",
                admin_comment
            ])
        
        if revised_proposal:
            body_parts.extend([
                "",
                "修正后的提案：",
                revised_proposal
            ])
        
        body_parts.extend([
            "",
            f"您可以登录系统查看详细信息：{SYSTEM_URL}",
            "",
            "如有疑问，请联系管理员。",
            "",
            "此邮件为系统自动发送，请勿回复。",
            "",
            "EI Power 提案管理系统"
        ])
        
        body = "\n".join(filter(None, body_parts))
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        print(f"📧 [状态通知] 正在连接SMTP服务器 {SMTP_SERVER}:{SMTP_PORT}")
        
        # 发送邮件
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, feedback_info['email'], text)
        server.quit()
        
        # 记录通知日志
        conn.execute('''
            INSERT INTO notification_logs (feedback_id, user_id, email, notification_type, 
                                         old_status, new_status, status, sent_at, handler_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            feedback_id, feedback_info['id'], feedback_info['email'], '状态更新',
            old_status, new_status, '成功', datetime.now(), handler_name
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ [状态通知] 状态更新通知发送成功: {feedback_info['username']} ({feedback_info['email']})")
        return True
        
    except Exception as e:
        print(f"❌ [状态通知] 发送状态更新通知失败: {str(e)}")
        
        # 记录失败日志
        try:
            conn = get_db_connection()
            user_info = conn.execute('SELECT user_id FROM feedback WHERE id = ?', (feedback_id,)).fetchone()
            if user_info:
                conn.execute('''
                    INSERT INTO notification_logs (feedback_id, user_id, notification_type, 
                                                 old_status, new_status, status, sent_at, error_message, handler_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    feedback_id, user_info['user_id'], '状态更新',
                    old_status, new_status, '失败', datetime.now(), str(e), handler_name
                ))
                conn.commit()
            conn.close()
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