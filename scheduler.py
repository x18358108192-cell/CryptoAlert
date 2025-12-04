# -*- coding: utf-8 -*-
import requests
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from web_app import app, db, Alert 
from apscheduler.schedulers.background import BackgroundScheduler

# ==================================================
#                  邮件配置区 (QQ 邮箱配置)
# !!! 请替换为你的真实 QQ 邮箱信息和授权码 !!!
# ==================================================
SENDER_EMAIL = 'xyl565293491@qq.com'      # 📢 你的 QQ 邮箱地址
SMTP_SERVER = 'smtp.qq.com'              # QQ 邮箱 SMTP 服务器
SMTP_PORT = 465                          # QQ 邮箱推荐端口
SMTP_PASSWORD = 'ppndfjqcdjbndbij'         # 📢 你的 QQ 邮箱授权码
# ==================================================


def send_email_alert(recipient_email, current_price, target_price):
    """发送邮件警报的函数，这次是给特定用户发送"""
    global SENDER_EMAIL, SMTP_SERVER, SMTP_PORT, SMTP_PASSWORD 
    
    try:
        # 构造邮件内容 (恢复中文)
        target_str = f'目标价格: ${target_price:,}'
        current_str = f'当前价格: ${current_price:,}'
        
        subject = f"⚡️【重要警报】比特币价格已达标！"
        body = f'恭喜！您设置的比特币 {target_str} 已达到或超过！\n{current_str}'
        
        # 明确指定内容使用 utf-8 编码
        msg = MIMEText(body, 'plain', 'utf-8')
        
        # 恢复中文发件人昵称 (依赖 UTF-8 文件保存和 msg.as_bytes())
        msg['From'] = formataddr(("加密货币警报服务", SENDER_EMAIL)) # 👈 恢复中文昵称
        msg['To'] = formataddr(("", recipient_email)) 
        msg['Subject'] = Header(subject, 'utf-8')

        # 连接服务器并发送 (使用 msg.as_bytes() 是解决编码冲突的关键)
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SMTP_PASSWORD)
        server.sendmail(SENDER_EMAIL, [recipient_email], msg.as_bytes()) # 👈 关键修复
        server.quit()
        
        print(f"✅ 邮件警报发送成功给: {recipient_email}")

    except Exception as e:
        print(f"❌ 邮件发送失败给 {recipient_email}. 错误: {e}")


def check_prices():
    """调度器的主任务：获取当前价格，检查所有用户警报，并发送邮件。"""
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] 任务开始：检查所有用户警报...")
    
    # 1. 获取当前比特币价格
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
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
#                     启动调度器
# ==================================================

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_prices, 'interval', seconds=60)
    scheduler.start()
    print("🔔 后台任务调度器已启动，每 60 秒检查一次价格...")

    try:
        # Keep the main thread alive
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("调度器已关闭。")