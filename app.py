from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, date
import sqlite3
import os
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
    """提交反馈"""
    if request.method == 'POST':
        today = date.today().strftime('%Y-%m-%d')
        
        conn = get_db_connection()
        # 检查今日已提交数量
        current_count = conn.execute(
            'SELECT COUNT(*) as count FROM feedback WHERE user_id = ? AND DATE(created_at) = ?',
            (current_user.id, today)
        ).fetchone()['count']
        
        if current_count >= 3:
            flash('今日已提交3个反馈，无法继续提交')
            conn.close()
            return redirect(url_for('dashboard'))
        
        content = request.form['content']
        if not content.strip():
            flash('反馈内容不能为空')
            conn.close()
            return render_template('submit_feedback.html')
        
        # 生成编号
        sequence = current_count + 1
        feedback_id = f"{today.replace('-', '')}-{current_user.username}-{sequence}"
        
        # 插入反馈记录
        conn.execute(
            'INSERT INTO feedback (id, user_id, content, status, created_at) VALUES (?, ?, ?, ?, ?)',
            (feedback_id, current_user.id, content, '新提案', datetime.now())
        )
        conn.commit()
        conn.close()
        
        flash('反馈提交成功')
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
        SELECT u.id, u.username, u.email, u.name,
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
    
    # 转换数据格式，处理datetime字段
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
    
    conn.close()
    
    return render_template('admin.html', 
                         users_status=users_status, 
                         pending_feedback=pending_feedback)

@app.route('/admin/update_feedback', methods=['POST'])
@login_required
def update_feedback():
    """管理员更新提案状态"""
    if not current_user.is_admin:
        return jsonify({'error': '权限不足'}), 403
    
    feedback_id = request.form['feedback_id']
    status = request.form['status']
    revised_proposal = request.form.get('revised_proposal', '')
    admin_comment = request.form.get('admin_comment', '')
    
    conn = get_db_connection()
    
    # 获取原始提案信息
    original_feedback = conn.execute(
        'SELECT * FROM feedback WHERE id = ?', (feedback_id,)
    ).fetchone()
    
    if not original_feedback:
        flash('提案不存在')
        conn.close()
        return redirect(url_for('admin_panel'))
    
    # 记录操作日志
    operation_type = '状态更新'
    new_content = original_feedback['content']
    
    # 如果有修正提案且状态为已解决，则更新提案内容
    if revised_proposal.strip() and status == '已解决':
        new_content = revised_proposal.strip()
        operation_type = '修正提案'
        
        # 记录修正提案的操作日志
        conn.execute(
            'INSERT INTO operation_logs (feedback_id, operator_id, operation_type, old_content, new_content, old_status, new_status, comment) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (feedback_id, current_user.id, operation_type, original_feedback['content'], new_content, original_feedback['status'], status, admin_comment)
        )
        
        # 更新提案内容和状态
        conn.execute(
            'UPDATE feedback SET content = ?, status = ?, revised_proposal = ?, admin_comment = ?, handler = ?, updated_at = ? WHERE id = ?',
            (new_content, status, revised_proposal, admin_comment, current_user.name, datetime.now(), feedback_id)
        )
        
        flash('提案已修正并标记为已解决')
    else:
        # 只更新状态和意见
        conn.execute(
            'INSERT INTO operation_logs (feedback_id, operator_id, operation_type, old_status, new_status, comment) VALUES (?, ?, ?, ?, ?, ?)',
            (feedback_id, current_user.id, operation_type, original_feedback['status'], status, admin_comment)
        )
        
        conn.execute(
            'UPDATE feedback SET status = ?, revised_proposal = ?, admin_comment = ?, handler = ?, updated_at = ? WHERE id = ?',
            (status, revised_proposal, admin_comment, current_user.name, datetime.now(), feedback_id)
        )
        
        flash('提案状态更新成功')
    
    conn.commit()
    conn.close()
    
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
    
    if not target_user:
        return jsonify({'success': False, 'message': '请提供用户ID或用户名'})
    
    try:
        result = send_manual_reminder(target_user)
        if result['success']:
            return jsonify({'success': True, 'message': f'提醒邮件已发送给 {result["username"]}'})
        else:
            return jsonify({'success': False, 'message': result['message']})
    except Exception as e:
        return jsonify({'success': False, 'message': f'发送失败: {str(e)}'})

@app.route('/proposals')
@login_required
def all_proposals():
    """所有提案页面 - 所有人可见"""
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
    
    # 获取所有提案
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
            SUM(CASE WHEN status = '新提案' THEN 1 ELSE 0 END) as new_count,
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

if __name__ == '__main__':
    # 初始化数据库
    init_db()
    
    # 设置定时任务
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=check_and_send_reminders,
        trigger="cron",
        hour=16,
        minute=0,
        id='daily_reminder'
    )
    scheduler.start()
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5001)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()