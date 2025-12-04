# -*- coding: utf-8 -*-
import requests
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

# ==================================================
#                  邮件配置区 (QQ 邮箱配置)
# !!! 请替换为你的真实 QQ 邮箱信息和授权码 !!!
# ==================================================
# 注意：线上部署时，最好使用环境变量读取这些信息，这里为了测试方便，直接写出。
SENDER_EMAIL = 'zhihu507@gmail.com'      
SMTP_SERVER = 'smtp.gmail.com'              
SMTP_PORT = 465                          
SMTP_PASSWORD = 'thelrccgzcmxnmxu'         
# ==================================================


app = Flask(__name__)

# PostgreSQL 配置 (使用环境变量读取)
# Render 的内部链接格式是 postgres://，但 SQLAlchemy 需要 postgresql://
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    target_price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Alert {self.email} - ${self.target_price}>'

# 确保数据库和表在应用启动时创建 (仅用于本地测试，Render 部署时需要手动初始化)
with app.app_context():
    db.create_all()


# ==================================================
#                 邮件发送功能 (从 scheduler.py 迁移)
# ==================================================

def send_email_alert(recipient_email, current_price, target_price):
    """发送邮件警报的函数"""
    global SENDER_EMAIL, SMTP_SERVER, SMTP_PORT, SMTP_PASSWORD 
    
    try:
        # 构造邮件内容 (恢复中文)
        target_str = f'目标价格: ${target_price:,}'
        current_str = f'当前价格: ${current_price:,}'
        
        subject = f"⚡️【重要警报】比特币价格已达标！"
        body = f'恭喜！您设置的比特币 {target_str} 已达到或超过！\n{current_str}'
        
        msg = MIMEText(body, 'plain', 'utf-8')
        
        # 恢复中文发件人昵称 (依赖 UTF-8 文件保存和 msg.as_bytes())
        msg['From'] = formataddr(("加密货币警报服务", SENDER_EMAIL))
        msg['To'] = formataddr(("", recipient_email)) 
        msg['Subject'] = Header(subject, 'utf-8')

        # 连接服务器并发送 (使用 msg.as_bytes() 是解决编码冲突的关键)
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SMTP_PASSWORD)
        server.sendmail(SENDER_EMAIL, [recipient_email], msg.as_bytes())
        server.quit()
        
        # 保持中文日志，因为你的系统现在支持了
        print(f"✅ 邮件警报发送成功给: {recipient_email}")

    except Exception as e:
        print(f"❌ 邮件发送失败给 {recipient_email}. 错误: {e}")


# ==================================================
#                 价格检查功能 (从 scheduler.py 迁移)
# ==================================================

def check_prices():
    """从 Coinbase API 获取价格并检查所有警报。"""
    
    # 🎯 切换到 Coinbase Pro 免费公共 API 🎯
    url = "https://api.pro.coinbase.com/products/BTC-USD/ticker"
    params = {} # 不需要参数

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status() 
        data = response.json()
        
        # Coinbase 返回的 JSON 结构中，价格在 'price' 字段
        # 价格是字符串，需要转换为浮点数
        current_price = float(data['price'])
        
        # 格式化价格，用于日志输出和比较
        formatted_price = f"${current_price:,.0f}"
        print(f"当前价格获取成功: {formatted_price}")

    except requests.exceptions.RequestException as e:
        print(f"⚠️ 网络请求失败，跳过本次检查。错误: {e}")
        return # 如果获取失败，则退出函数，不进行检查

    # 🚨 警报检查逻辑 (保持不变)
    # ... (这里是原有的从数据库查询警报、比较价格和发送邮件的代码)
    
    # ...
    """从币安API获取价格并检查所有警报。"""
    
    # 🎯 切换到 Binance 免费公共 API 🎯
    url = "https://api.pro.coinbase.com/products/BTC-USD/ticker"
    params = {'symbol': 'BTCUSDT'}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status() 
        data = response.json()
        
        # 币安返回的 JSON 结构: {"symbol": "BTCUSDT", "price": "60000.00"}
        # 我们需要从字符串转换为浮点数
        current_price = float(data['price'])
        
        # 格式化价格，用于日志输出和比较
        formatted_price = f"${current_price:,.0f}"
        print(f"当前价格获取成功: {formatted_price}")

    except requests.exceptions.RequestException as e:
        print(f"⚠️ 网络请求失败，跳过本次检查。错误: {e}")
        return # 如果获取失败，则退出函数，不进行检查

    # 🚨 警报检查逻辑 (保持不变)
    # ... (这里是原有的从数据库查询警报、比较价格和发送邮件的代码)
    
    # 确保在检查逻辑中，你用来比较价格的变量是 current_price
    
    # ...
    """获取当前价格，检查所有用户警报，并发送邮件。"""
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] 任务开始：检查所有用户警报...")
    
    # 1. 获取当前比特币价格
    try:
        url = "https://api.binance.com/api/v3/ticker/price"
        response = requests.get(url)
        response.raise_for_status() 
        data = response.json()
        current_price = data['bitcoin']['usd']
        print(f"当前价格获取成功: ${current_price:,}")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ 网络请求失败，跳过本次检查。错误: {e}")
        return

    # 2. 连接数据库，获取所有警报
    with app.app_context():
        alerts = Alert.query.all() 
        print(f"从数据库中找到 {len(alerts)} 个警报设置。")
        
        # 3. 循环检查每一个警报
        for alert in alerts:
            if current_price >= alert.target_price:
                print(f"🚨 警报触发！用户 {alert.email} 目标 ${alert.target_price:,}。")
                
                # 发送邮件
                send_email_alert(alert.email, current_price, alert.target_price)
                
                # 警报一旦触发，就删除或标记此警报，防止重复发送
                db.session.delete(alert)
                db.session.commit()
                print(f"✅ 警报 {alert.email} 已从数据库中删除。")


# ==================================================
#                         Web 路由
# ==================================================

# 新增路由：用于外部 Cron 调用
@app.route('/check_alerts', methods=['GET'])
def trigger_alert_check():
    """外部服务调用此路由以触发价格检查任务"""
    check_prices()
    return "Alert check initiated successfully.", 200


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email = request.form.get('email')
        target_price = request.form.get('target_price')

        if not email or not target_price:
            return render_template('index.html', message="邮箱和价格不能为空！")

        try:
            target_price = float(target_price.replace(',', ''))
        except ValueError:
            return render_template('index.html', message="价格格式错误！")

        with app.app_context():
            # 检查是否已存在此邮箱的警报
            existing_alert = Alert.query.filter_by(email=email).first()

            if existing_alert:
                # 更新警报
                existing_alert.target_price = target_price
                db.session.commit()
                message = f"警报已更新：{email}，目标价格：${target_price:,}"
            else:
                # 创建新警报
                new_alert = Alert(email=email, target_price=target_price)
                db.session.add(new_alert)
                db.session.commit()
                message = f"警报设置成功！{email}，目标价格：${target_price:,}"
            
            # 返回成功页面
            return render_template('index.html', message=message)
            
    # GET 请求时，加载页面
    return render_template('index.html')


if __name__ == '__main__':
    # 仅用于本地测试，部署时由 Gunicorn 启动
    app.run(debug=True)