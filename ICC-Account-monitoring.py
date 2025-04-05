import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import threading
import time
from datetime import datetime
import os

class RewardsDetailWindow:
    """奖励详情窗口类"""
    def __init__(self, parent, account_name, token):
        self.top = tk.Toplevel(parent)
        self.top.title(f"{account_name} - 单次奖励记录")
        self.top.geometry("900x500")
        self.top.resizable(True, True)
        self.top.transient(parent)  # 设置为父窗口的临时窗口
        
        self.account_name = account_name
        self.token = token
        
        self.create_widgets()
        self.fetch_rewards_data()
        
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.top, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题标签
        title_label = ttk.Label(main_frame, text=f"{self.account_name} 的单次奖励记录", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("正在加载数据...")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="gray")
        status_label.pack(fill=tk.X, pady=5)
        
        # 创建表格
        self.create_rewards_table(main_frame)
        
        # 底部按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.refresh_btn = ttk.Button(button_frame, text="刷新数据", command=self.fetch_rewards_data)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        close_btn = ttk.Button(button_frame, text="关闭窗口", command=self.top.destroy)
        close_btn.pack(side=tk.RIGHT, padx=5)
    
    def create_rewards_table(self, parent):
        """创建奖励记录表格"""
        # 创建容器框架
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 定义列
        columns = ('id', 'amount', 'time', 'type', 'title')
        self.rewards_table = ttk.Treeview(frame, columns=columns, show='headings')
        
        # 设置列标题
        self.rewards_table.heading('id', text='ID')
        self.rewards_table.heading('amount', text='奖励数量')
        self.rewards_table.heading('time', text='时间')
        self.rewards_table.heading('type', text='类型')
        self.rewards_table.heading('title', text='标题')
        
        # 设置列宽
        self.rewards_table.column('id', width=80)
        self.rewards_table.column('amount', width=100)
        self.rewards_table.column('time', width=120)
        self.rewards_table.column('type', width=200)
        self.rewards_table.column('title', width=150)
        
        # 添加滚动条
        scrollbar_y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.rewards_table.yview)
        self.rewards_table.configure(yscrollcommand=scrollbar_y.set)
        
        scrollbar_x = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=self.rewards_table.xview)
        self.rewards_table.configure(xscrollcommand=scrollbar_x.set)
        
        # 布局
        self.rewards_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
    
    def fetch_rewards_data(self):
        """获取单次奖励数据"""
        self.status_var.set("正在获取奖励记录...")
        self.refresh_btn.config(state=tk.DISABLED)
        
        # 清空现有数据
        for item in self.rewards_table.get_children():
            self.rewards_table.delete(item)
        
        # 创建线程进行API请求
        thread = threading.Thread(target=self._fetch_rewards_task)
        thread.daemon = True
        thread.start()
    
    def _fetch_rewards_task(self):
        """后台任务：请求单次奖励数据"""
        try:
            url = "https://iccloud.io/api/v1/scc_site/user/asset/record"
            headers = {
                "access-token": self.token,
                "Content-Type": "application/json",
                "locale": "en_US"
            }
            payload = {
                "assetType": 1,
                "queryType": 0,
                "pIndex": 1,
                "pSize": 100
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    rewards_list = data.get("data", {}).get("list", [])
                    total_count = data.get("data", {}).get("total", 0)
                    
                    # 更新表格数据
                    for reward in rewards_list:
                        self.rewards_table.insert('', tk.END, values=(
                            reward.get('id', ''),
                            f"{reward.get('amount', 0):.4f}",
                            reward.get('createTime', ''),
                            reward.get('billTypeDesc', ''),
                            reward.get('title', '')
                        ))
                    
                    self.status_var.set(f"已加载 {len(rewards_list)} 条奖励记录，共 {total_count} 条")
                else:
                    error_msg = data.get('msg', '未知错误')
                    self.status_var.set(f"获取奖励记录失败: {error_msg}")
            else:
                self.status_var.set(f"获取奖励记录失败: HTTP {response.status_code}")
        
        except Exception as e:
            self.status_var.set(f"获取奖励记录失败: {str(e)}")
        
        finally:
            # 恢复按钮状态
            if self.refresh_btn:
                self.refresh_btn.config(state=tk.NORMAL)

class MiningMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("ICC账户奖励监控   by晚风  推特（x.com/pl_wanfeng)")
        self.root.geometry("1170x600")  # 增加窗口宽度为1050px
        self.root.resizable(True, True)
        
        # 账户数据存储
        self.accounts_file = "mining_accounts.json"
        self.accounts = self.load_accounts()
        self.current_account = None
        
        # 数据变量
        self.refresh_interval = 60  # 默认1分钟
        self.auto_refresh = True
        self.refresh_thread = None
        
        self.create_widgets()
        
        # 启动自动刷新
        self.toggle_auto_refresh()
        
    def load_accounts(self):
        """加载保存的账户"""
        if os.path.exists(self.accounts_file):
            try:
                with open(self.accounts_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载账户文件失败: {e}")
        return {}
    
    def save_accounts(self):
        """保存账户到文件"""
        try:
            with open(self.accounts_file, 'w', encoding='utf-8') as f:
                json.dump(self.accounts, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.status_var.set(f"保存账户失败: {e}")
    
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧账户管理面板
        accounts_frame = ttk.LabelFrame(main_frame, text="账户管理", padding=10, width=250)
        accounts_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        accounts_frame.pack_propagate(False)
        
        # 添加账户区域
        add_account_frame = ttk.Frame(accounts_frame)
        add_account_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(add_account_frame, text="账户名称:").pack(anchor=tk.W, pady=2)
        self.account_name_entry = ttk.Entry(add_account_frame, width=25)
        self.account_name_entry.pack(fill=tk.X, pady=2)
        
        ttk.Label(add_account_frame, text="Access Token:").pack(anchor=tk.W, pady=2)
        self.token_entry = ttk.Entry(add_account_frame, width=25)
        self.token_entry.pack(fill=tk.X, pady=2)
        
        button_frame = ttk.Frame(add_account_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.save_btn = ttk.Button(button_frame, text="保存账户", command=self.save_account)
        self.save_btn.pack(side=tk.LEFT, padx=2)
        
        self.delete_btn = ttk.Button(button_frame, text="删除账户", command=self.delete_account)
        self.delete_btn.pack(side=tk.LEFT, padx=2)
        
        # 账户列表
        ttk.Label(accounts_frame, text="已保存账户:").pack(anchor=tk.W, pady=5)
        accounts_list_frame = ttk.Frame(accounts_frame)
        accounts_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.accounts_listbox = tk.Listbox(accounts_list_frame)
        self.accounts_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        accounts_scrollbar = ttk.Scrollbar(accounts_list_frame, orient=tk.VERTICAL, command=self.accounts_listbox.yview)
        accounts_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.accounts_listbox.config(yscrollcommand=accounts_scrollbar.set)
        
        self.accounts_listbox.bind('<<ListboxSelect>>', self.on_account_select)
        
        # 更新账户列表
        self.update_accounts_list()
        
        # 控制区域
        control_frame = ttk.Frame(accounts_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        self.refresh_btn = ttk.Button(control_frame, text="刷新数据", command=self.refresh_all_accounts)
        self.refresh_btn.pack(side=tk.LEFT, padx=2)
        
        self.auto_refresh_var = tk.BooleanVar(value=True)  # 默认启用自动刷新
        self.auto_refresh_check = ttk.Checkbutton(
            control_frame, 
            text="自动刷新", 
            variable=self.auto_refresh_var,
            command=self.toggle_auto_refresh
        )
        self.auto_refresh_check.pack(side=tk.LEFT, padx=5)
        
        # 右侧数据显示区域
        data_area = ttk.Frame(main_frame)
        data_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪。请添加或选择账户。")
        status_label = ttk.Label(data_area, textvariable=self.status_var, foreground="gray")
        status_label.pack(fill=tk.X, pady=5)
        
        # 账户数据表格 (直接在主界面显示，不使用标签页)
        accounts_table_frame = ttk.LabelFrame(data_area, text="所有账户", padding=10)
        accounts_table_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建账户数据表格
        self.create_accounts_table(accounts_table_frame)
        
    def create_accounts_table(self, parent):
        """创建账户数据表格"""
        columns = ('account', 'balance', 'profit_today', 'profit_total', 'last_update', 'actions')
        self.accounts_table = ttk.Treeview(parent, columns=columns, show='headings')
        
        # 定义列
        self.accounts_table.heading('account', text='账户名称')
        self.accounts_table.heading('balance', text='当前余额')
        self.accounts_table.heading('profit_today', text='今日收益')
        self.accounts_table.heading('profit_total', text='总收益')
        self.accounts_table.heading('last_update', text='最后更新时间')
        self.accounts_table.heading('actions', text='操作')
        
        # 设置列宽 - 增加宽度以显示更多内容
        self.accounts_table.column('account', width=140)
        self.accounts_table.column('balance', width=140)
        self.accounts_table.column('profit_today', width=140)
        self.accounts_table.column('profit_total', width=140)
        self.accounts_table.column('last_update', width=170)
        self.accounts_table.column('actions', width=100)
        
        # 添加滚动条
        table_scroll = ttk.Scrollbar(parent, orient="vertical", command=self.accounts_table.yview)
        self.accounts_table.configure(yscrollcommand=table_scroll.set)
        
        # 添加水平滚动条，以便在窗口宽度不够时可以滚动查看
        h_scroll = ttk.Scrollbar(parent, orient="horizontal", command=self.accounts_table.xview)
        self.accounts_table.configure(xscrollcommand=h_scroll.set)
        
        # 布局
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.accounts_table.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        table_scroll.pack(fill=tk.Y, side=tk.RIGHT)
        
        # 绑定点击事件
        self.accounts_table.bind('<ButtonRelease-1>', self.on_table_click)
    
    def on_table_click(self, event):
        """处理表格点击事件"""
        region = self.accounts_table.identify_region(event.x, event.y)
        if region != "cell":
            return
            
        column = self.accounts_table.identify_column(event.x)
        column_index = int(column.replace('#', ''))
        
        # 如果点击的是操作列（第6列）
        if column_index == 6:  # 第6列是操作列
            item_id = self.accounts_table.identify_row(event.y)
            if item_id:
                # 获取该行的账户名称
                values = self.accounts_table.item(item_id, 'values')
                account_name = values[0]
                
                # 显示奖励详情窗口
                self.show_rewards_detail(account_name)
    
    def show_rewards_detail(self, account_name):
        """显示单次奖励详情窗口"""
        if account_name not in self.accounts:
            return
            
        token = self.accounts[account_name]['token']
        RewardsDetailWindow(self.root, account_name, token)
    
    def update_accounts_list(self):
        """更新账户列表显示"""
        self.accounts_listbox.delete(0, tk.END)
        for account_name in self.accounts:
            self.accounts_listbox.insert(tk.END, account_name)
    
    def save_account(self):
        """保存账户信息"""
        account_name = self.account_name_entry.get().strip()
        token = self.token_entry.get().strip()
        
        if not account_name:
            messagebox.showerror("错误", "请输入账户名称")
            return
            
        if not token:
            messagebox.showerror("错误", "请输入Access Token")
            return
        
        # 保存账户
        self.accounts[account_name] = {
            'token': token,
            'balance': 0,
            'profit_today': 0,
            'profit_total': 0,
            'last_updated': '从未'
        }
        
        self.save_accounts()
        self.update_accounts_list()
        
        # 清空输入框
        self.account_name_entry.delete(0, tk.END)
        self.token_entry.delete(0, tk.END)
        
        self.status_var.set(f"账户 '{account_name}' 已保存")
        
        # 立即刷新该账户数据
        self.refresh_account_data(account_name)
    
    def delete_account(self):
        """删除选中的账户"""
        selection = self.accounts_listbox.curselection()
        if not selection:
            messagebox.showerror("错误", "请先选择要删除的账户")
            return
            
        account_name = self.accounts_listbox.get(selection[0])
        
        if messagebox.askyesno("确认删除", f"确定要删除账户 '{account_name}' 吗?"):
            # 删除账户数据
            if account_name in self.accounts:
                del self.accounts[account_name]
                
            # 更新账户列表和表格
            self.save_accounts()
            self.update_accounts_list()
            self.update_accounts_table()
            
            self.status_var.set(f"账户 '{account_name}' 已删除")
    
    def on_account_select(self, event):
        """处理账户选择事件"""
        selection = self.accounts_listbox.curselection()
        if not selection:
            return
            
        account_name = self.accounts_listbox.get(selection[0])
        self.current_account = account_name
        
        # 填充编辑区域
        self.account_name_entry.delete(0, tk.END)
        self.account_name_entry.insert(0, account_name)
        
        self.token_entry.delete(0, tk.END)
        if account_name in self.accounts:
            self.token_entry.insert(0, self.accounts[account_name]['token'])
    
    def refresh_account_data(self, account_name):
        """刷新单个账户的数据"""
        if account_name not in self.accounts:
            return
            
        account = self.accounts[account_name]
        token = account['token']
        
        try:
            # API请求
            url = "https://iccloud.io/api/v1/scc_site/user/asset/info"
            headers = {
                "access-token": token,
                "Content-Type": "application/json",
                "locale": "en_US"
            }
            payload = {"assetType": 1}
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    asset_data = data.get("data", {})
                    
                    # 更新账户数据
                    account['balance'] = asset_data.get("balance", 0)
                    account['profit_today'] = asset_data.get("profitToday", 0)
                    account['profit_total'] = asset_data.get("profitTotal", 0)
                    account['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 更新表格
                    self.update_accounts_table()
                    
                    return True
                else:
                    error_msg = data.get('msg', '未知错误')
                    self.status_var.set(f"账户 '{account_name}' 刷新失败: {error_msg}")
            else:
                self.status_var.set(f"账户 '{account_name}' 刷新失败: HTTP {response.status_code}")
        
        except Exception as e:
            self.status_var.set(f"账户 '{account_name}' 刷新失败: {str(e)}")
        
        return False
    
    def refresh_all_accounts(self):
        """刷新所有账户的数据"""
        if not self.accounts:
            self.status_var.set("没有保存的账户")
            return
            
        self.status_var.set("正在刷新所有账户数据...")
        self.refresh_btn.config(state=tk.DISABLED)
        
        success_count = 0
        for account_name in self.accounts:
            if self.refresh_account_data(account_name):
                success_count += 1
        
        # 保存账户数据
        self.save_accounts()
        
        self.status_var.set(f"已刷新 {success_count}/{len(self.accounts)} 个账户")
        self.refresh_btn.config(state=tk.NORMAL)
    
    def update_accounts_table(self):
        """更新账户表格数据"""
        # 清空表格
        for item in self.accounts_table.get_children():
            self.accounts_table.delete(item)
            
        # 添加账户数据
        for account_name, account in self.accounts.items():
            self.accounts_table.insert('', tk.END, values=(
                account_name,
                f"{account.get('balance', 0):.8f}",
                f"{account.get('profit_today', 0):.8f}",
                f"{account.get('profit_total', 0):.8f}",
                account.get('last_updated', '从未'),
                "查看奖励记录"  # 操作按钮文本
            ))
    
    def auto_refresh_task(self):
        """自动刷新任务"""
        while self.auto_refresh:
            self.refresh_all_accounts()
            time.sleep(self.refresh_interval)
    
    def toggle_auto_refresh(self):
        """切换自动刷新功能"""
        self.auto_refresh = self.auto_refresh_var.get()
        
        if self.auto_refresh:
            self.refresh_interval = 60  # 固定为1分钟
            
            self.status_var.set(f"已启用自动刷新 (每{self.refresh_interval}秒)")
            self.refresh_thread = threading.Thread(target=self.auto_refresh_task, daemon=True)
            self.refresh_thread.start()
        else:
            self.status_var.set("已禁用自动刷新")

if __name__ == "__main__":
    root = tk.Tk()
    app = MiningMonitor(root)
    root.mainloop() 