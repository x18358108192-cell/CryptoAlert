import os
import smtplib
from email.mime.text import MIMEText
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import requests

# ==================================================
#                  邮件配置区 (Gmail 配置)
# ==================================================
# 🚨 注意：请在 Render 环境变量中设置这些值，此处仅作代码示例
# SENDER_EMAIL = os.environ.get('SENDER_EMAIL') 
# SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD') 
SENDER_EMAIL = 'zhihu507@gmail.com'  
SMTP_SERVER = 'smtp.gmail.com'              
SMTP_PORT = 465                          
SMTP_PASSWORD = 'thelrccgzcmxnmxu'      
RECEIVER_EMAIL = '你的收件邮箱@example.com' 
# ==================================================

app = Flask(__name__)

# PostgreSQL 配置 (使用环境变量读取 Neon URL)
# Render 的内部链接格式是 postgres://，但 SQLAlchemy 需要 postgresql://
database_url = os.environ.get('DATABASE_URL')
if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace("postgres://", "postgresql://")
else:
    # 🚨 警告：本地测试或未设置环境变量时会失败
    print("⚠️ 警告: DATABASE_URL 环境变量未设置！")
    # 可以设置为一个无效的 URL 来提醒本地运行时需要配置
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@host/db_name_placeholder'
    
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Alert(db.Model):
    """数据库模型：存储用户的警报设置"""
    id = db.Column(db.Integer, primary_key=True)
    target_price = db.Column(db.Float, nullable=False)
    is_triggered = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Alert {self.id}: ${self.target_price}>'

# 确保在第一次运行时创建数据库表
with app.app_context():
    db.create_all()

def send_alert_email(price, target):
    """发送邮件通知警报触发"""
    msg = MIMEText(f"🚨 加密货币警报触发！\n\n当前价格: ${price:,.0f}\n目标价格: ${target:,.0f}\n\n请尽快检查市场!", 'plain', 'utf-8')
    msg['Subject'] = f'价格警报触发：达到 ${target:,.0f}'
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print(f"✅ 邮件警报发送成功给: {RECEIVER_EMAIL}")
        return True
    except Exception as e:
        print(f"❌ 邮件发送失败，请检查SMTP配置: {e}")
        return False

def check_prices():
    """从 Binance API 获取价格并检查所有警报。"""
    
    # 🎯 使用币安价格API 🎯
    url = "https://api.binance.com/api/v3/ticker/price"
    params = {'symbol': 'BTCUSDT'}

    current_price = None
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status() 
        data = response.json()
        
        # 币安返回的 JSON 结构: {"symbol": "BTCUSDT", "price": "65000.00"}
        current_price = float(data['price'])
        
        formatted_price = f"${current_price:,.0f}"
        print(f"当前价格获取成功: {formatted_price}")

    except requests.exceptions.RequestException as e:
        print(f"⚠️ 网络请求失败，跳过本次检查。错误: {e}")
        return
    except Exception as e:
        print(f"⚠️ 解析Binance数据失败。错误: {e}")
        return


    # --- 警报检查逻辑 ---
    print("任务开始：检查所有用户警报...")
    # ⚠️ 注意：这里使用 app_context 是因为 Cron job 是在外部调用的
    with app.app_context():
        alerts = Alert.query.filter_by(is_triggered=False).all()
        print(f"从数据库中找到 {len(alerts)} 个未触发警报设置。")

        for alert in alerts:
            if current_price <= alert.target_price:
                print(f"🚨 警报触发！当前价格 ${current_price:,.0f} 达到目标 ${alert.target_price:,.0f}")
                
                if send_alert_email(current_price, alert.target_price):
                    alert.is_triggered = True  # 标记为已触发
                    db.session.commit()
                else:
                    # 如果邮件发送失败，则不标记为已触发，下次继续尝试
                    pass


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            target_price = float(request.form['target_price'])
            # 始终只保留一个警报，或者创建新的
            with app.app_context():
                # 清空旧警报并设置新警报
                db.session.query(Alert).delete()
                new_alert = Alert(target_price=target_price, is_triggered=False)
                db.session.add(new_alert)
                db.session.commit()
                print(f"🎉 成功设置新警报: ${target_price:,.0f}")
            return redirect(url_for('index'))
        except ValueError:
            return "无效的输入，请确保价格是数字。", 400
        
    # GET 请求：显示当前设置
    current_alert = Alert.query.first()
    return render_template('index.html', current_alert=current_alert)


@app.route('/check_alerts')
def check_alerts_route():
    """供Cron-Job.org调用的API路由"""
    check_prices()
    return "Alert check completed", 200

# 这是一个调试用的路由，可以手动清除警报
@app.route('/clear_alerts')
def clear_alerts():
    with app.app_context():
        db.session.query(Alert).delete()
        db.session.commit()
        print("所有警报已清除。")
    return "All alerts cleared.", 200

if __name__ == '__main__':
    # 确保在本地运行时也创建数据库表
    with app.app_context():
        db.create_all()
    # 在 Render 上运行时 Gunicorn 会管理端口，本地可以设置为 5000
    app.run(debug=True)