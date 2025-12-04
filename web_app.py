# -*- coding: utf-8 -*-
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
SMTP_PASSWORD = '你的16位Gmail授权码'      
RECEIVER_EMAIL = 'thelrccgzcmxnmxu' 
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
    msg = MIMEText(f"🚨 加密货币警报触发！\n\n当前价格: ${price:,.0f}\n目标价格