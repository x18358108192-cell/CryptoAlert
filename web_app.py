from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

# 实例化 Flask 应用
app = Flask(__name__)

# 配置数据库 (使用 SQLite 数据库文件)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alerts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# =========================================================
# 数据库模型：定义我们要存储的用户数据结构
# =========================================================
class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    target_price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='BTC')

    def __repr__(self):
        return f'<Alert {self.email} @ {self.target_price}>'

# =========================================================
# 路由（Route）：处理用户的访问请求
# =========================================================

# 当用户访问主页 '/' 时，执行这个函数
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 1. 如果用户提交了表单 (POST 请求)
        user_email = request.form['email']
        target = float(request.form['price'])
        
        # 2. 存储到数据库
        new_alert = Alert(email=user_email, target_price=target)
        try:
            db.session.add(new_alert)
            db.session.commit()
            return '警报设置成功！我们将向您的邮箱发送确认邮件。'
        except:
            # 如果邮箱已经存在，数据库会报错
            return '警报设置失败或该邮箱已设置过警报。'

    # 3. 如果用户只是访问页面 (GET 请求)
    return render_template('index.html')


# =========================================================
# 启动和初始化
# =========================================================

if __name__ == '__main__':
    # 在应用启动前，创建数据库文件（如果不存在）
    with app.app_context():
        db.create_all()
    
    # 启动 Web 服务器，让它监听你的电脑 IP:5000 端口
    app.run(debug=True)