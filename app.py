from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, date
import sqlite3
import os
import csv
import io
from apscheduler.schedulers.background import BackgroundScheduler
from email_service import send_reminder_email, check_and_send_reminders, send_manual_reminder
from database import init_db, get_db_connection

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# 初始化Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录访问此页面'

class User(UserMixin):
    """用户类，用于Flask-Login"""
    def __init__(self, id, username, email, name, is_admin=False):
        self.id = id
        self.username = username
        self.email = email
        self.name = name
        self.is_admin = is_admin

@login_manager.user_loader
def load_user(user_id):
    """加载用户信息"""
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return User(user['id'], user['username'], user['email'], user['name'], user['is_admin'])
    return None

@app.route('/')
def index():
    """首页重定向到登录页"""
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            user_obj = User(user['id'], user['username'], user['email'], user['name'], user['is_admin'])
            login_user(user_obj)
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """用户仪表盘"""
    today = date.today().strftime('%Y-%m-%d')
    
    conn = get_db_connection()
    # 获取今日提交的反馈数量
    feedback_count = conn.execute(
        'SELECT COUNT(*) as count FROM feedback WHERE user_id = ? AND DATE(created_at) = ?',
        (current_user.id, today)
    ).fetchone()['count']
    
    # 获取最近的反馈记录
    recent_feedback_raw = conn.execute(
        'SELECT * FROM feedback WHERE user_id = ? ORDER BY created_at DESC LIMIT 5',
        (current_user.id,)
    ).fetchall()
    
    # 转换数据格式，处理datetime字段
    recent_feedback = []
    for feedback in recent_feedback_raw:
        feedback_dict = dict(feedback)
        # 将字符串格式的datetime转换为datetime对象
        if feedback_dict['created_at']:
            try:
                feedback_dict['created_at'] = datetime.fromisoformat(feedback_dict['created_at'].replace('Z', '+00:00'))
            except:
                feedback_dict['created_at'] = datetime.strptime(feedback_dict['created_at'], '%Y-%m-%d %H:%M:%S')
        if feedback_dict['updated_at']:
            try:
                feedback_dict['updated_at'] = datetime.fromisoformat(feedback_dict['updated_at'].replace('Z', '+00:00'))
            except:
                feedback_dict['updated_at'] = datetime.strptime(feedback_dict['updated_at'], '%Y-%m-%d %H:%M:%S')
        recent_feedback.append(feedback_dict)
    
    conn.close()
    
    return render_template('dashboard.html', 
                         feedback_count=feedback_count, 
                         recent_feedback=recent_feedback)

@app.route('/submit_feedback', methods=['GET', 'POST'])
@login_required
def submit_feedback():
    """提交问题反馈"""
    if request.method == 'POST':
        today = date.today().strftime('%Y-%m-%d')
        
        conn = get_db_connection()
        # 检查今日已提交数量
        current_count = conn.execute(
            'SELECT COUNT(*) as count FROM feedback WHERE user_id = ? AND DATE(created_at) = ?',
            (current_user.id, today)
        ).fetchone()['count']
        
        if current_count >= 3:
            flash('今日已提交3个问题，无法继续提交')
            conn.close()
            return redirect(url_for('dashboard'))
        
        content = request.form['content']
        has_answer = request.form.get('has_answer') == 'on'
        answer = request.form.get('answer', '').strip() if has_answer else None
        
        if not content.strip():
            flash('问题内容不能为空')
            conn.close()
            return render_template('submit_feedback.html')
        
        if has_answer and not answer:
            flash('您选择了有答案，但未填写答案内容')
            conn.close()
            return render_template('submit_feedback.html')
        
        # 生成编号
        sequence = current_count + 1
        feedback_id = f"{today.replace('-', '')}-{current_user.username}-{sequence}"
        
        # 插入反馈记录
        conn.execute(
            'INSERT INTO feedback (id, user_id, content, has_answer, answer, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (feedback_id, current_user.id, content, has_answer, answer, '新问题', datetime.now())
        )
        conn.commit()
        conn.close()
        
        flash('问题提交成功')
        return redirect(url_for('dashboard'))
    
    return render_template('submit_feedback.html')

@app.route('/history')
@login_required
def history():
    """历史反馈记录"""
    conn = get_db_connection()
    feedback_list_raw = conn.execute(
        'SELECT * FROM feedback WHERE user_id = ? ORDER BY created_at DESC',
        (current_user.id,)
    ).fetchall()
    
    # 转换数据格式，处理datetime字段
    feedback_list = []
    for feedback in feedback_list_raw:
        feedback_dict = dict(feedback)
        # 将字符串格式的datetime转换为datetime对象
        if feedback_dict['created_at']:
            try:
                feedback_dict['created_at'] = datetime.fromisoformat(feedback_dict['created_at'].replace('Z', '+00:00'))
            except:
                feedback_dict['created_at'] = datetime.strptime(feedback_dict['created_at'], '%Y-%m-%d %H:%M:%S')
        if feedback_dict['updated_at']:
            try:
                feedback_dict['updated_at'] = datetime.fromisoformat(feedback_dict['updated_at'].replace('Z', '+00:00'))
            except:
                feedback_dict['updated_at'] = datetime.strptime(feedback_dict['updated_at'], '%Y-%m-%d %H:%M:%S')
        feedback_list.append(feedback_dict)
    
    conn.close()
    
    return render_template('history.html', feedback_list=feedback_list)

@app.route('/edit_user_feedback', methods=['POST'])
@login_required
def edit_user_feedback():
    """用户编辑自己的问题"""
    feedback_id = request.form.get('feedback_id')
    content = request.form.get('content')
    has_answer = 1 if request.form.get('has_answer') else 0
    answer = request.form.get('answer', '')
    
    if not feedback_id or not content:
        flash('问题内容不能为空')
        return redirect(url_for('history'))
    
    conn = get_db_connection()
    
    # 检查问题是否属于当前用户且状态为"新问题"
    feedback = conn.execute(
        'SELECT * FROM feedback WHERE id = ? AND user_id = ?',
        (feedback_id, current_user.id)
    ).fetchone()
    
    if not feedback:
        flash('问题不存在或无权限编辑')
        conn.close()
        return redirect(url_for('history'))
    
    if feedback['status'] != '新问题':
        flash('只能编辑状态为"新问题"的问题')
        conn.close()
        return redirect(url_for('history'))
    
    # 更新问题
    try:
        conn.execute('''
            UPDATE feedback 
            SET content = ?, has_answer = ?, answer = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        ''', (content, has_answer, answer, feedback_id, current_user.id))
        
        conn.commit()
        flash('问题修改成功')
        
    except Exception as e:
        conn.rollback()
        flash(f'修改失败: {str(e)}')
        
    finally:
        conn.close()
    
    return redirect(url_for('history'))

@app.route('/admin')
@login_required
def admin_panel():
    """管理员面板"""
    if not current_user.is_admin:
        flash('权限不足')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    
    # 获取所有用户今日提交状态
    today = date.today().strftime('%Y-%m-%d')
    users_status = conn.execute('''
        SELECT u.id, u.username, u.email, u.backup_email, u.name,
               COALESCE(f.feedback_count, 0) as feedback_count
        FROM users u
        LEFT JOIN (
            SELECT user_id, COUNT(*) as feedback_count
            FROM feedback
            WHERE DATE(created_at) = ?
            GROUP BY user_id
        ) f ON u.id = f.user_id
        WHERE u.is_admin = 0
        ORDER BY u.name
    ''', (today,)).fetchall()
    
    # 获取所有待处理的反馈
    pending_feedback_raw = conn.execute(
        'SELECT f.*, u.username, u.name FROM feedback f JOIN users u ON f.user_id = u.id WHERE f.status != "已解决" ORDER BY f.created_at DESC'
    ).fetchall()
    
    # 获取所有已解决的反馈
    resolved_feedback_raw = conn.execute(
        'SELECT f.*, u.username, u.name FROM feedback f JOIN users u ON f.user_id = u.id WHERE f.status = "已解决" ORDER BY f.updated_at DESC'
    ).fetchall()
    
    # 转换待处理反馈数据格式，处理datetime字段
    pending_feedback = []
    for feedback in pending_feedback_raw:
        feedback_dict = dict(feedback)
        # 将字符串格式的datetime转换为datetime对象
        if feedback_dict['created_at']:
            try:
                feedback_dict['created_at'] = datetime.fromisoformat(feedback_dict['created_at'].replace('Z', '+00:00'))
            except:
                feedback_dict['created_at'] = datetime.strptime(feedback_dict['created_at'], '%Y-%m-%d %H:%M:%S')
        if feedback_dict['updated_at']:
            try:
                feedback_dict['updated_at'] = datetime.fromisoformat(feedback_dict['updated_at'].replace('Z', '+00:00'))
            except:
                feedback_dict['updated_at'] = datetime.strptime(feedback_dict['updated_at'], '%Y-%m-%d %H:%M:%S')
        pending_feedback.append(feedback_dict)
    
    # 转换已解决反馈数据格式，处理datetime字段
    resolved_feedback = []
    for feedback in resolved_feedback_raw:
        feedback_dict = dict(feedback)
        # 将字符串格式的datetime转换为datetime对象
        if feedback_dict['created_at']:
            try:
                feedback_dict['created_at'] = datetime.fromisoformat(feedback_dict['created_at'].replace('Z', '+00:00'))
            except:
                feedback_dict['created_at'] = datetime.strptime(feedback_dict['created_at'], '%Y-%m-%d %H:%M:%S')
        if feedback_dict['updated_at']:
            try:
                feedback_dict['updated_at'] = datetime.fromisoformat(feedback_dict['updated_at'].replace('Z', '+00:00'))
            except:
                feedback_dict['updated_at'] = datetime.strptime(feedback_dict['updated_at'], '%Y-%m-%d %H:%M:%S')
        resolved_feedback.append(feedback_dict)
    
    conn.close()
    
    return render_template('admin.html', 
                         users_status=users_status, 
                         pending_feedback=pending_feedback,
                         resolved_feedback=resolved_feedback)

@app.route('/admin/export_resolved', methods=['GET'])
@login_required
def export_resolved_feedback():
    """导出已解决问题为CSV格式"""
    if not current_user.is_admin:
        flash('权限不足', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    
    # 获取所有已解决的反馈，包含管理员修正的问题内容
    resolved_feedback = conn.execute('''
        SELECT f.id, f.content, f.revised_proposal, f.answer, f.updated_at, u.name
        FROM feedback f 
        JOIN users u ON f.user_id = u.id 
        WHERE f.status = "已解决" 
        ORDER BY f.updated_at DESC
    ''').fetchall()
    
    conn.close()
    
    # 创建CSV内容
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入标题行
    writer.writerow(['序号', '问题', '答案', '时间'])
    
    # 写入数据行
    for i, feedback in enumerate(resolved_feedback, 1):
        # 使用管理员修正的问题内容，如果没有则使用原始内容
        problem_content = feedback['revised_proposal'] if feedback['revised_proposal'] else feedback['content']
        answer_content = feedback['answer'] if feedback['answer'] else '无答案'
        
        # 处理时间格式
        if feedback['updated_at']:
            try:
                updated_time = datetime.fromisoformat(feedback['updated_at'].replace('Z', '+00:00'))
                time_str = updated_time.strftime('%Y-%m-%d %H:%M:%S')
            except:
                try:
                    updated_time = datetime.strptime(feedback['updated_at'], '%Y-%m-%d %H:%M:%S')
                    time_str = updated_time.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    time_str = feedback['updated_at']
        else:
            time_str = '未知时间'
        
        writer.writerow([i, problem_content, answer_content, time_str])
    
    # 创建响应
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    # 使用英文文件名避免编码问题
    filename = f'resolved_issues_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

@app.route('/admin/update_feedback', methods=['POST'])
@login_required
def update_feedback():
    """管理员更新问题状态"""
    if not current_user.is_admin:
        return jsonify({'error': '权限不足'}), 403
    
    feedback_id = request.form.get('feedback_id')
    status = request.form.get('status')
    revised_proposal = request.form.get('revised_proposal', '')
    admin_comment = request.form.get('admin_comment', '')
    has_answer = 1 if request.form.get('has_answer') else 0
    answer = request.form.get('answer', '')
    
    conn = get_db_connection()
    
    # 获取原始问题信息
    original_feedback = conn.execute(
        'SELECT * FROM feedback WHERE id = ?', (feedback_id,)
    ).fetchone()
    
    if not original_feedback:
        flash('问题不存在')
        conn.close()
        return redirect(url_for('admin_panel'))
    
    # 记录操作日志
    operation_type = '状态更新'
    new_content = original_feedback['content']
    
    # 如果有修正内容且状态为已解决，则更新问题内容
    if revised_proposal.strip() and status == '已解决':
        new_content = revised_proposal.strip()
        operation_type = '修正问题'
        
        # 记录修正问题的操作日志
        conn.execute(
            'INSERT INTO operation_logs (feedback_id, operator_id, operation_type, old_content, new_content, old_status, new_status, comment) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (feedback_id, current_user.id, operation_type, original_feedback['content'], new_content, original_feedback['status'], status, admin_comment)
        )
        
        # 更新问题内容和状态
        conn.execute(
            'UPDATE feedback SET content = ?, status = ?, revised_proposal = ?, admin_comment = ?, has_answer = ?, answer = ?, handler = ?, updated_at = ? WHERE id = ?',
            (new_content, status, revised_proposal, admin_comment, has_answer, answer, current_user.name, datetime.now(), feedback_id)
        )
        
        flash('问题已修正并标记为已解决')
    else:
        # 只更新状态和意见
        conn.execute(
            'INSERT INTO operation_logs (feedback_id, operator_id, operation_type, old_status, new_status, comment) VALUES (?, ?, ?, ?, ?, ?)',
            (feedback_id, current_user.id, operation_type, original_feedback['status'], status, admin_comment)
        )
        
        conn.execute(
            'UPDATE feedback SET status = ?, revised_proposal = ?, admin_comment = ?, has_answer = ?, answer = ?, handler = ?, updated_at = ? WHERE id = ?',
            (status, revised_proposal, admin_comment, has_answer, answer, current_user.name, datetime.now(), feedback_id)
        )
        
        flash('问题状态更新成功')
    
    conn.commit()
    conn.close()
    
    # 发送状态更新通知邮件
    try:
        from email_service import send_status_update_notification
        send_status_update_notification(
            feedback_id=feedback_id,
            old_status=original_feedback['status'],
            new_status=status,
            admin_comment=admin_comment,
            revised_proposal=revised_proposal if revised_proposal.strip() else '',
            handler_name=current_user.name
        )
    except Exception as e:
        print(f"邮件通知发送失败: {str(e)}")
        # 邮件发送失败不影响主要功能，只记录错误
    
    return redirect(url_for('admin_panel'))

@app.route('/api/today_status')
@login_required
def api_today_status():
    """API: 获取当前用户今日提交状态"""
    today = date.today().strftime('%Y-%m-%d')
    
    conn = get_db_connection()
    feedback_count = conn.execute(
        'SELECT COUNT(*) as count FROM feedback WHERE user_id = ? AND DATE(created_at) = ?',
        (current_user.id, today)
    ).fetchone()['count']
    conn.close()
    
    return jsonify({
        'success': True,
        'feedback_count': feedback_count,
        'remaining': 3 - feedback_count
    })

@app.route('/send_manual_reminder', methods=['POST'])
@login_required
def send_manual_reminder_route():
    """手动发送邮件提醒"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '需要管理员权限'})
    
    data = request.get_json()
    target_user = data.get('user_identifier')  # 可以是用户ID或用户名
    target_email = data.get('target_email')  # 指定的目标邮箱
    
    if not target_user:
        return jsonify({'success': False, 'message': '请提供用户ID或用户名'})
    
    try:
        result = send_manual_reminder(target_user, target_email)
        if result['success']:
            return jsonify({'success': True, 'message': f'提醒邮件已发送给 {result["username"]}'})
        else:
            return jsonify({'success': False, 'message': result['message']})
    except Exception as e:
        return jsonify({'success': False, 'message': f'发送失败: {str(e)}'})

@app.route('/proposals')
@login_required
def all_proposals():
    """所有问题页面 - 所有人可见"""
    conn = get_db_connection()
    
    # 获取筛选参数
    status_filter = request.args.get('status', 'all')
    search_query = request.args.get('search', '')
    
    # 构建查询条件
    where_conditions = []
    params = []
    
    if status_filter != 'all':
        where_conditions.append('f.status = ?')
        params.append(status_filter)
    
    if search_query:
        where_conditions.append('f.content LIKE ?')
        params.append(f'%{search_query}%')
    
    where_clause = ' AND '.join(where_conditions)
    if where_clause:
        where_clause = 'WHERE ' + where_clause
    
    # 获取所有问题
    proposals_raw = conn.execute(f'''
        SELECT f.*, u.username, u.name,
               handler_user.name as handler_name
        FROM feedback f 
        JOIN users u ON f.user_id = u.id
        LEFT JOIN users handler_user ON f.handler = handler_user.name
        {where_clause}
        ORDER BY f.created_at DESC
    ''', params).fetchall()
    
    # 转换数据格式，处理datetime字段
    proposals = []
    for proposal in proposals_raw:
        proposal_dict = dict(proposal)
        # 将字符串格式的datetime转换为datetime对象
        if proposal_dict['created_at']:
            try:
                proposal_dict['created_at'] = datetime.fromisoformat(proposal_dict['created_at'].replace('Z', '+00:00'))
            except:
                proposal_dict['created_at'] = datetime.strptime(proposal_dict['created_at'], '%Y-%m-%d %H:%M:%S')
        if proposal_dict['updated_at']:
            try:
                proposal_dict['updated_at'] = datetime.fromisoformat(proposal_dict['updated_at'].replace('Z', '+00:00'))
            except:
                proposal_dict['updated_at'] = datetime.strptime(proposal_dict['updated_at'], '%Y-%m-%d %H:%M:%S')
        proposals.append(proposal_dict)
    
    # 获取统计信息
    stats = conn.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = '新问题' THEN 1 ELSE 0 END) as new_count,
            SUM(CASE WHEN status = '处理中' THEN 1 ELSE 0 END) as processing_count,
            SUM(CASE WHEN status = '已解决' THEN 1 ELSE 0 END) as resolved_count
        FROM feedback
    ''').fetchone()
    
    conn.close()
    
    return render_template('proposals.html', 
                         proposals=proposals, 
                         stats=dict(stats),
                         current_status=status_filter,
                         search_query=search_query)

# check_and_send_reminders 函数已移至 email_service.py

@app.route('/notification_logs')
@login_required
def notification_logs():
    """通知日志管理页面（仅管理员可访问）"""
    if not current_user.is_admin:
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    
    # 获取通知日志
    logs = conn.execute('''
        SELECT nl.*, u.name as user_name
        FROM notification_logs nl
        LEFT JOIN users u ON nl.user_id = u.id
        ORDER BY nl.sent_at DESC
        LIMIT 500
    ''').fetchall()
    
    # 获取统计信息
    total_notifications = conn.execute('SELECT COUNT(*) as count FROM notification_logs').fetchone()['count']
    success_notifications = conn.execute('SELECT COUNT(*) as count FROM notification_logs WHERE status = "成功"').fetchone()['count']
    failed_notifications = conn.execute('SELECT COUNT(*) as count FROM notification_logs WHERE status = "失败"').fetchone()['count']
    today_notifications = conn.execute('''
        SELECT COUNT(*) as count FROM notification_logs 
        WHERE date(sent_at) = date('now')
    ''').fetchone()['count']
    
    conn.close()
    
    return render_template('notification_logs.html',
                         notification_logs=[dict(log) for log in logs],
                         total_notifications=total_notifications,
                         success_notifications=success_notifications,
                         failed_notifications=failed_notifications,
                         today_notifications=today_notifications)

@app.route('/api/notification_log/<int:log_id>')
@login_required
def get_notification_log(log_id):
    """获取通知日志详情API"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'})
    
    conn = get_db_connection()
    log = conn.execute('''
        SELECT nl.*, u.name as user_name
        FROM notification_logs nl
        LEFT JOIN users u ON nl.user_id = u.id
        WHERE nl.id = ?
    ''', (log_id,)).fetchone()
    conn.close()
    
    if log:
        return jsonify({'success': True, 'log': dict(log)})
    else:
        return jsonify({'success': False, 'message': '日志不存在'})

@app.route('/api/resend_notification/<int:feedback_id>', methods=['POST'])
@login_required
def resend_notification(feedback_id):
    """重新发送通知API"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'})
    
    try:
        conn = get_db_connection()
        
        # 获取问题信息
        feedback = conn.execute('''
            SELECT f.*, u.email, u.name as user_name
            FROM feedback f
            JOIN users u ON f.user_id = u.id
            WHERE f.id = ?
        ''', (feedback_id,)).fetchone()
        
        if not feedback:
            conn.close()
            return jsonify({'success': False, 'message': '问题不存在'})
        
        # 获取最新的状态更新记录
        latest_log = conn.execute('''
            SELECT * FROM operation_logs 
            WHERE feedback_id = ? AND action LIKE '%状态更新%'
            ORDER BY created_at DESC LIMIT 1
        ''', (feedback_id,)).fetchone()
        
        conn.close()
        
        # 重新发送通知
        from email_service import send_status_update_notification
        
        old_status = latest_log['details'].split('→')[0].strip() if latest_log and '→' in latest_log['details'] else '未知'
        new_status = feedback['status']
        
        send_status_update_notification(
            feedback_id=feedback_id,
            user_id=feedback['user_id'],
            user_email=feedback['email'],
            old_status=old_status,
            new_status=new_status,
            handler_name=current_user.name,
            admin_comment=feedback.get('admin_comment', ''),
            corrected_proposal=feedback.get('corrected_proposal', '')
        )
        
        return jsonify({'success': True, 'message': '通知邮件重新发送成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'重新发送失败: {str(e)}'})

@app.route('/api/clear_old_logs', methods=['POST'])
@login_required
def clear_old_logs():
    """清理旧日志API"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'})
    
    try:
        conn = get_db_connection()
        
        # 删除30天前的日志
        result = conn.execute('''
            DELETE FROM notification_logs 
            WHERE date(sent_at) < date('now', '-30 days')
        ''')
        
        deleted_count = result.rowcount
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'成功清理了 {deleted_count} 条旧日志',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'清理失败: {str(e)}'})

@app.route('/api/delete_feedback/<feedback_id>', methods=['DELETE'])
@login_required
def delete_feedback(feedback_id):
    """删除问题API - 仅管理员可用"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'})
    
    try:
        conn = get_db_connection()
        
        # 首先检查问题是否存在，并获取用户邮箱信息
        feedback = conn.execute('''
            SELECT f.*, u.username, u.name, u.email, u.backup_email
            FROM feedback f
            JOIN users u ON f.user_id = u.id
            WHERE f.id = ?
        ''', (feedback_id,)).fetchone()
        
        if not feedback:
            conn.close()
            return jsonify({'success': False, 'message': '问题不存在'})
        
        # 获取删除原因（可选参数）
        deletion_reason = request.json.get('reason', '') if request.is_json else ''
        
        # 记录操作日志
        conn.execute('''
            INSERT INTO operation_logs (feedback_id, operator_id, operation_type, comment, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        ''', (
            feedback_id,
            current_user.id,
            '删除问题',
            f'管理员删除了用户 {feedback["username"]} 的问题: {feedback["content"][:50]}...'
        ))
        
        # 删除相关的通知日志
        conn.execute('DELETE FROM notification_logs WHERE feedback_id = ?', (feedback_id,))
        
        # 删除问题
        conn.execute('DELETE FROM feedback WHERE id = ?', (feedback_id,))
        
        conn.commit()
        conn.close()
        
        # 发送删除通知邮件
        try:
            from email_service import send_deletion_notification_email, get_user_email_for_sending
            
            # 获取要发送的邮箱地址（交替使用主邮箱和备份邮箱）
            target_email = get_user_email_for_sending(feedback['user_id'])
            if target_email:
                send_deletion_notification_email(
                    recipient_email=target_email,
                    username=feedback['name'] or feedback['username'],
                    feedback_content=feedback['content'],
                    admin_name=current_user.name,
                    deletion_reason=deletion_reason
                )
                
                # 记录邮件发送日志
                conn = get_db_connection()
                conn.execute('''
                    INSERT INTO notification_logs (user_id, feedback_id, email, notification_type, status, error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    feedback['user_id'],
                    feedback_id,
                    target_email,
                    'delete_notification',
                    '成功',
                    None
                ))
                conn.commit()
                conn.close()
                
                print(f"✅ [删除通知] 已向用户 {feedback['username']} 发送删除通知邮件")
            else:
                print(f"⚠️ [删除通知] 用户 {feedback['username']} 没有有效邮箱地址")
                
        except Exception as email_error:
            print(f"❌ [删除通知] 发送邮件失败: {str(email_error)}")
            # 记录邮件发送失败日志
            try:
                conn = get_db_connection()
                conn.execute('''
                    INSERT INTO notification_logs (user_id, feedback_id, email, notification_type, status, error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    feedback['user_id'],
                    feedback_id,
                    feedback['email'],
                    'delete_notification',
                    '失败',
                    str(email_error)
                ))
                conn.commit()
                conn.close()
            except:
                pass
        
        return jsonify({
            'success': True, 
            'message': f'成功删除问题 #{feedback_id}，已通知提议人'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'})

if __name__ == '__main__':
    # 初始化数据库
    init_db()
    
    # 设置定时任务 - 每天4点和6点发送提醒
    scheduler = BackgroundScheduler()
    
    # 早上4点提醒
    scheduler.add_job(
        func=check_and_send_reminders,
        trigger="cron",
        hour=16,
        minute=0,
        id='morning_reminder_4pm'
    )
    
    # 早上6点提醒
    scheduler.add_job(
        func=check_and_send_reminders,
        trigger="cron",
        hour=18,
        minute=0,
        id='morning_reminder_6pm'
    )
    
    scheduler.start()
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5008)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()