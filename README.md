# ICC挖矿奖励监控

一个简单的GUI应用程序，用于监控您在iccloud.io平台上的挖矿奖励。

![image](https://github.com/user-attachments/assets/72d09533-b9b1-4f97-94ed-9aef8f9b094b)


## 功能特点

- 支持多账户管理和监控
- 显示每个账户的当前余额/挖矿奖励
- 显示每日和总收益统计数据
- **查看每个账户的单次奖励详细记录**
- 每分钟自动刷新数据
- 简洁美观的界面

## 系统要求

- Python 3.6 或更高版本
- 所需Python包:
  - tkinter (通常随Python一起安装)
  - requests

## 安装方法

1. 确保您的系统已安装Python
2. 安装所需的依赖包:

```
pip install requests
```

## 使用方法

1. 运行应用程序:

```
python ICC-Account-monitoring.py
```

2. 添加账户:
   - 输入账户名称（任意名称）
   - 输入您的access token (从iccloud.io网站获取)

![image](https://github.com/user-attachments/assets/ff80bf40-4b2d-4f82-921d-6a13de5fab7b)


   - 点击"保存账户"

2. 账户数据将自动每分钟刷新一次，您也可以手动点击"刷新数据"按钮

3. 查看单次奖励记录:
   - 在主界面的账户表格中点击操作列的"查看奖励记录"按钮
   - 系统会弹出新窗口，展示该账户的所有单次挖矿奖励记录

## 说明

- Access token可以从您登录iccloud.io平台后的浏览器网络请求中获取
- 您可以添加多个账户进行同时监控
- 账户信息将保存在本地文件中，下次启动程序时自动加载
- 自动刷新默认已启用，间隔为1分钟
- 奖励记录窗口可以随时刷新获取最新数据 
