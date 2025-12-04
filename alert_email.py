import requests
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

# ==================================================
#                  配置区 (请务必修改以下信息)
# ==================================================
SENDER_EMAIL = 'xyl565293491@qq.com'      # 📢 你的 QQ 邮箱地址
RECEIVER_EMAIL = 'x18358108192@gmail.com' # 📢 接收警报的邮箱地址
SMTP_SERVER = 'smtp.qq.com'              # QQ邮箱 SMTP 服务器地址
SMTP_PORT = 465                          # QQ邮箱推荐使用 465 端口 (SSL)
SMTP_PASSWORD = 'evnkciakugkddaae'         # 📢 你的 QQ 邮箱授权码
TARGET_PRICE = 92000                     # 📢 设置你的目标价格
CHECK_INTERVAL = 60                      # 检查间隔（秒）

# ==================================================

def send_email_alert(current_price):
    """发送邮件警报的函数"""
    try:
        # 构造邮件内容
        msg = MIMEText(f'比特币价格已突破目标 {TARGET_PRICE} 美元！当前价格：${current_price:,}', 'plain', 'utf-8')
        
        # 使用 formataddr 确保邮件头格式符合协议要求 (解决了 550 格式错误)
        msg['From'] = formataddr(("加密货币警报器", SENDER_EMAIL))
        msg['To'] = formataddr(("收件人", RECEIVER_EMAIL))
        msg['Subject'] = Header("⚡️【重要警报】比特币价格已触发！", 'utf-8')

        # 连接到SMTP服务器并发送邮件 (SSL 方式连接 Port 465)
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        
        print(f"DEBUG: 尝试用邮箱 {SENDER_EMAIL} 登录...")
        
        server.login(SENDER_EMAIL, SMTP_PASSWORD) # 使用授权码登录
        server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], msg.as_string())
        server.quit()
        
        print("✅ 邮件警报发送成功！")

    except Exception as e:
        # 如果是授权码或配置错误，会在这里捕获
        print(f"❌ 邮件发送失败，请检查配置和授权码。错误: {e}")


# ==================================================
#                     主循环逻辑
# ==================================================
has_alerted = False # 增加标志，防止价格在目标之上时重复发送邮件

while True:
    try:
        # 1. 获取价格 (CoinGecko API)
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        response = requests.get(url)
        response.raise_for_status() 
        data = response.json()
        current_price = data['bitcoin']['usd']

        # 2. 状态报告
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] 当前价格: ${current_price:,}. 目标价格: ${TARGET_PRICE:,}")

        # 3. 核心判断逻辑
        if current_price >= TARGET_PRICE:
            if not has_alerted:
                # 触发警报，并发送邮件
                send_email_alert(current_price) 
                has_alerted = True # 标记为已发送
            else:
                print("警报已发送，等待价格回落...")
        
        else:
            # 价格低于目标，重置警报标志
            has_alerted = False
            print("继续监控...")

    except requests.exceptions.RequestException as e:
        # 优雅地处理网络失败，程序不会崩溃
        print(f"⚠️ 网络请求失败，等待下一次重试。错误信息: {e}")
        
    finally:
        # 4. 暂停
        print("-" * 30)
        time.sleep(CHECK_INTERVAL)