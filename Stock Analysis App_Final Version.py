import tushare as ts
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
import plotly.graph_objects as go
import plotly.io as pio
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
from scipy import stats  
import re
from datetime import datetime
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  
plt.rcParams['axes.unicode_minus'] = False

# 设置matplotlib黑色主题
plt.style.use('dark_background')

# 设置plotly黑色主题
pio.templates["custom_dark"] = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor='black',
        plot_bgcolor='black',
        font=dict(color='white'),
        xaxis=dict(
            gridcolor='rgba(128,128,128,0.2)',
            linecolor='rgba(128,128,128,0.5)',
            zerolinecolor='rgba(128,128,128,0.3)'
        ),
        yaxis=dict(
            gridcolor='rgba(128,128,128,0.2)',
            linecolor='rgba(128,128,128,0.5)',
            zerolinecolor='rgba(128,128,128,0.3)'
        )
    )
)
pio.templates.default = "custom_dark"

# 初始化Tushare
TOKEN = 'your_tushare_token'  # 替换为你的token
ts.set_token(TOKEN)
pro = ts.pro_api()

class StockAnalysisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("股票技术分析工具")
        self.root.geometry("500x800")
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="股票技术分析工具", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # 分析模式选择
        mode_frame = ttk.Frame(main_frame)
        mode_frame.pack(pady=10, fill=tk.X)
        
        ttk.Label(mode_frame, text="分析模式:", font=("Arial", 12)).grid(row=0, column=0, padx=5, sticky=tk.W)
        self.analysis_mode = tk.StringVar(value="single")
        single_mode = ttk.Radiobutton(mode_frame, text="单股票分析", variable=self.analysis_mode, value="single", command=self.toggle_input_fields)
        single_mode.grid(row=0, column=1, padx=5)
        compare_mode = ttk.Radiobutton(mode_frame, text="双股票相关性分析", variable=self.analysis_mode, value="compare", command=self.toggle_input_fields)
        compare_mode.grid(row=0, column=2, padx=5)
        
        # 输入框架 - 单股票模式
        self.single_input_frame = ttk.Frame(main_frame)
        self.single_input_frame.pack(pady=10, fill=tk.X)
        
        ttk.Label(self.single_input_frame, text="股票代码:", font=("Arial", 12)).grid(row=0, column=0, padx=5, sticky=tk.W)
        self.stock_code_entry = ttk.Entry(self.single_input_frame, width=20, font=("Arial", 12))
        self.stock_code_entry.grid(row=0, column=1, padx=5)
        self.stock_code_entry.insert(0, "000001.SZ")  # 默认代码
        
        # 输入框架 - 双股票模式
        self.compare_input_frame = ttk.Frame(main_frame)
        
        ttk.Label(self.compare_input_frame, text="股票代码 1:", font=("Arial", 12)).grid(row=0, column=0, padx=5, sticky=tk.W)
        self.stock1_code_entry = ttk.Entry(self.compare_input_frame, width=20, font=("Arial", 12))
        self.stock1_code_entry.grid(row=0, column=1, padx=5)
        self.stock1_code_entry.insert(0, "000001.SZ")
        
        ttk.Label(self.compare_input_frame, text="股票代码 2:", font=("Arial", 12)).grid(row=0, column=2, padx=5, sticky=tk.W)
        self.stock2_code_entry = ttk.Entry(self.compare_input_frame, width=20, font=("Arial", 12))
        self.stock2_code_entry.grid(row=0, column=3, padx=5)
        self.stock2_code_entry.insert(0, "000001.SZ")
        
        # 日期选择框架 - 调整字号为12（与股票代码一致）
        date_frame = ttk.Frame(main_frame)
        date_frame.pack(pady=10, fill=tk.X)
        
        ttk.Label(date_frame, text="开始日期:", font=("Arial", 12)).grid(row=0, column=0, padx=5, sticky=tk.W)
        self.start_date_entry = ttk.Entry(date_frame, width=12, font=("Arial", 12))
        self.start_date_entry.grid(row=0, column=1, padx=5)
        self.start_date_entry.insert(0, "20241125")
        
        ttk.Label(date_frame, text="结束日期:", font=("Arial", 12)).grid(row=0, column=2, padx=5, sticky=tk.W)
        self.end_date_entry = ttk.Entry(date_frame, width=12, font=("Arial", 12))
        self.end_date_entry.grid(row=0, column=3, padx=5)
        self.end_date_entry.insert(0, "20251024")
        
        # ========== 技术指标选择UI ==========
        indicators_frame = ttk.LabelFrame(main_frame, text="技术指标选择", padding="10")
        indicators_frame.pack(pady=10, fill=tk.X)
        
        # 创建技术指标选择变量
        self.bb_var = tk.BooleanVar(value=False)
        self.kdj_var = tk.BooleanVar(value=False)
        self.obv_var = tk.BooleanVar(value=False)
        self.atr_var = tk.BooleanVar(value=False)
        
        # 技术指标选择复选框
        ttk.Checkbutton(indicators_frame, text="BOLL布林带", variable=self.bb_var).grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Checkbutton(indicators_frame, text="KDJ随机指标", variable=self.kdj_var).grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Checkbutton(indicators_frame, text="OBV能量潮", variable=self.obv_var).grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Checkbutton(indicators_frame, text="ATR平均波幅", variable=self.atr_var).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        self.analyze_button = ttk.Button(button_frame, text="开始分析", command=self.start_analysis)
        self.analyze_button.pack(side=tk.LEFT, padx=10)
        
        self.clear_button = ttk.Button(button_frame, text="清空", command=self.clear_input)
        self.clear_button.pack(side=tk.LEFT, padx=10)
        
        # 状态标签
        self.status_label = ttk.Label(main_frame, text="请选择分析模式并输入股票代码", font=("Arial", 10))
        self.status_label.pack(pady=10)
        
        # 进度条
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        
        # ========== 新增：在主窗口下方添加报告显示区域 ==========
        report_frame = ttk.LabelFrame(main_frame, text="技术分析与风险评估报告", padding="10")
        report_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        self.report_text = scrolledtext.ScrolledText(report_frame, wrap=tk.WORD, width=80, height=15,
                                                   font=("Courier New", 9))
        self.report_text.pack(fill=tk.BOTH, expand=True)
        self.report_text.insert(tk.END, "分析报告将显示在这里...")
        self.report_text.config(state=tk.DISABLED)
        
        # 报告操作按钮
        report_buttons_frame = ttk.Frame(report_frame)
        report_buttons_frame.pack(pady=5)
        
        self.save_report_button = ttk.Button(report_buttons_frame, text="保存报告", 
                                           command=self.save_current_report)
        self.save_report_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_report_button = ttk.Button(report_buttons_frame, text="清空报告", 
                                            command=self.clear_report)
        self.clear_report_button.pack(side=tk.LEFT, padx=5)
        
        # ========== 新增：数据导出按钮 ==========
        self.export_data_button = ttk.Button(report_buttons_frame, text="导出收盘价数据(CSV)", 
                                           command=self.export_close_price_data)
        self.export_data_button.pack(side=tk.LEFT, padx=5)
        
        # 初始化输入框显示状态
        self.toggle_input_fields()
        
        # 存储当前报告内容
        self.current_report = ""
        self.current_stock_code = ""
        self.current_stock_data = None  # 新增：存储当前股票数据
        
        # 设置关闭窗口事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def on_closing(self):
        # 确保完全退出
        self.root.quit()
        self.root.destroy()
        
    def toggle_input_fields(self):
        # 根据选择的模式显示/隐藏相应的输入框
        if self.analysis_mode.get() == "single":
            self.single_input_frame.pack(pady=10, fill=tk.X)
            self.compare_input_frame.pack_forget()
        else:
            self.single_input_frame.pack_forget()
            self.compare_input_frame.pack(pady=10, fill=tk.X)
        
    def clear_input(self):
        self.stock_code_entry.delete(0, tk.END)
        self.stock1_code_entry.delete(0, tk.END)
        self.stock2_code_entry.delete(0, tk.END)
        self.start_date_entry.delete(0, tk.END)
        self.end_date_entry.delete(0, tk.END)
        self.status_label.config(text="已清空输入框")
        
    def validate_inputs(self):
        """验证输入参数"""
        # 验证日期格式
        start_date = self.start_date_entry.get().strip()
        end_date = self.end_date_entry.get().strip()
        
        if not start_date or not end_date:
            return False, "请输入开始日期和结束日期"
            
        # 验证日期格式是否为YYYYMMDD
        date_pattern = r'^\d{8}$'
        if not re.match(date_pattern, start_date) or not re.match(date_pattern, end_date):
            return False, "日期格式错误，请使用YYYYMMDD格式"
            
        # 验证开始日期是否早于结束日期
        try:
            start_dt = datetime.strptime(start_date, '%Y%m%d')
            end_dt = datetime.strptime(end_date, '%Y%m%d')
            if start_dt >= end_dt:
                return False, "开始日期必须早于结束日期"
        except ValueError:
            return False, "日期格式错误，请使用有效的YYYYMMDD格式"
        
        # 验证股票代码
        if self.analysis_mode.get() == "single":
            stock_code = self.stock_code_entry.get().strip()
            if not stock_code:
                return False, "请输入股票代码"
            if not self.validate_stock_code(stock_code):
                return False, "股票代码格式错误，请使用类似000001.SZ的格式"
        else:
            stock1_code = self.stock1_code_entry.get().strip()
            stock2_code = self.stock2_code_entry.get().strip()
            if not stock1_code or not stock2_code:
                return False, "请输入两只股票的代码"
            if not self.validate_stock_code(stock1_code) or not self.validate_stock_code(stock2_code):
                return False, "股票代码格式错误，请使用类似000001.SZ的格式"
                
        return True, "输入验证通过"
    
    def validate_stock_code(self, code):
        """验证股票代码格式"""
        # 简单的股票代码格式验证
        pattern = r'^\d{6}\.(SZ|SH)$'
        return re.match(pattern, code) is not None
        
    def start_analysis(self):
        # 先验证输入
        is_valid, message = self.validate_inputs()
        if not is_valid:
            messagebox.showerror("输入错误", message)
            return
            
        start_date = self.start_date_entry.get().strip()
        end_date = self.end_date_entry.get().strip()
        
        if self.analysis_mode.get() == "single":
            stock_code = self.stock_code_entry.get().strip()
                
            # 禁用按钮并显示进度条
            self.analyze_button.config(state=tk.DISABLED)
            self.progress.pack(pady=10)
            self.progress.start()
            self.status_label.config(text="正在获取数据并生成图表...")
            
            # 在新线程中执行分析
            analysis_thread = threading.Thread(
                target=self.perform_single_analysis, 
                args=(stock_code, start_date, end_date)
            )
            analysis_thread.daemon = True
            analysis_thread.start()
            
        else:  # 双股票比较模式
            stock1_code = self.stock1_code_entry.get().strip()
            stock2_code = self.stock2_code_entry.get().strip()
                
            # 禁用按钮并显示进度条
            self.analyze_button.config(state=tk.DISABLED)
            self.progress.pack(pady=10)
            self.progress.start()
            self.status_label.config(text="正在获取数据并分析相关性...")
            
            # 在新线程中执行分析
            analysis_thread = threading.Thread(
                target=self.perform_compare_analysis, 
                args=(stock1_code, stock2_code, start_date, end_date)
            )
            analysis_thread.daemon = True
            analysis_thread.start()
    
    def perform_single_analysis(self, stock_code, start_date, end_date):
        try:
            # 获取股票数据
            df_stock = pro.daily(ts_code=stock_code, start_date=start_date, end_date=end_date)
            
            if df_stock.empty:
                self.show_error("未找到该股票代码的数据，请检查代码是否正确")
                return
                
            # 预处理数据
            df_stock = self.preprocess_data(df_stock, stock_code)
            
            # 检查数据是否足够
            if len(df_stock) < 20:
                self.show_error(f"数据不足（仅{len(df_stock)}条），至少需要20个交易日数据")
                return
            
            # 存储当前股票数据（用于导出）
            self.current_stock_data = df_stock.copy()
                
            # 计算技术指标
            df_stock = self.calculate_indicators(df_stock)
            
            # 计算风险指标
            risk_metrics = self.calculate_risk_metrics(df_stock)
            
            # 生成分析报告
            analysis_report = self.generate_analysis_report(df_stock, stock_code, risk_metrics)
            
            # 在主线程中显示图表和报告
            self.root.after(0, lambda: self.display_single_charts(df_stock, stock_code, risk_metrics, analysis_report))
            
        except Exception as e:
            self.show_error(f"分析过程中出现错误: {str(e)}")
    
    def perform_compare_analysis(self, stock1_code, stock2_code, start_date, end_date):
        try:
            # 获取两只股票的数据
            df_stock1 = pro.daily(ts_code=stock1_code, start_date=start_date, end_date=end_date)
            df_stock2 = pro.daily(ts_code=stock2_code, start_date=start_date, end_date=end_date)
            
            if df_stock1.empty or df_stock2.empty:
                self.show_error("未找到股票数据，请检查股票代码是否正确")
                return
                
            # 预处理数据
            df_stock1 = self.preprocess_data(df_stock1, stock1_code)
            df_stock2 = self.preprocess_data(df_stock2, stock2_code)
            
            # 合并数据，确保日期对齐
            df_merged = self.merge_stock_data(df_stock1, df_stock2, stock1_code, stock2_code)
            
            if df_merged is None or len(df_merged) < 5:
                self.show_error("数据不足或日期不匹配，无法进行相关性分析")
                return
                
            # 在主线程中显示相关性图表
            self.root.after(0, lambda: self.display_correlation_charts(df_merged, stock1_code, stock2_code))
            
        except Exception as e:
            self.show_error(f"分析过程中出现错误: {str(e)}")
    
    def preprocess_data(self, df, name):
        # 按日期排序
        df = df.sort_values('trade_date')
        df = df.reset_index(drop=True)
        
        # 转换日期格式
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        
        # 计算日收益率
        if 'close' in df.columns:
            df['return'] = df['close'].pct_change()
            print(f"{name}数据预处理完成，共{len(df)}条记录")
        
        return df
    
    def merge_stock_data(self, df1, df2, name1, name2):
        """合并两只股票的数据，确保日期对齐"""
        # 选择需要的列并重命名
        df1_clean = df1[['trade_date', 'close']].rename(columns={'close': f'{name1}_close'})
        df2_clean = df2[['trade_date', 'close']].rename(columns={'close': f'{name2}_close'})
        
        # 合并数据，使用内连接确保日期对齐
        df_merged = pd.merge(df1_clean, df2_clean, on='trade_date', how='inner')
        
        if df_merged.empty:
            return None
            
        # 计算收益率
        df_merged[f'{name1}_return'] = df_merged[f'{name1}_close'].pct_change()
        df_merged[f'{name2}_return'] = df_merged[f'{name2}_close'].pct_change()
        
        # 删除NaN值
        df_merged = df_merged.dropna()
        
        print(f"合并后数据: {len(df_merged)}条记录")
        return df_merged
    
    def calculate_indicators(self, df):
        # 计算均线
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA10'] = df['close'].rolling(window=10).mean()
        df['MA20'] = df['close'].rolling(window=20).mean()

        # 计算MACD（内含EMA12/EMA26）
        df = self.calculate_macd(df)
        
        # 计算RSI
        df = self.calculate_rsi(df)
        
        # 计算常用EMA（12/26/50/200）- 新增用于Plotly显示
        df['EMA12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['close'].ewm(span=26, adjust=False).mean()
        df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['EMA200'] = df['close'].ewm(span=200, adjust=False).mean()
        
        # 根据用户选择计算额外技术指标
        if self.bb_var.get():
            df = self.calculate_bollinger_bands(df)
            
        if self.kdj_var.get():
            df = self.calculate_stochastic_oscillator(df)
            
        if self.obv_var.get():
            df = self.calculate_obv(df)
            
        if self.atr_var.get():
            df = self.calculate_atr(df)
        
        return df
    
    def calculate_macd(self, df, fast_period=12, slow_period=26, signal_period=9):
        df['EMA12'] = df['close'].ewm(span=fast_period, adjust=False).mean()
        df['EMA26'] = df['close'].ewm(span=slow_period, adjust=False).mean()
        df['DIF'] = df['EMA12'] - df['EMA26']
        df['DEA'] = df['DIF'].ewm(span=signal_period, adjust=False).mean()
        df['MACD'] = (df['DIF'] - df['DEA']) * 2
        return df

    def calculate_rsi(self, df, window=14):
        delta = df['close'].diff(1)
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        avg_loss = avg_loss.replace(0, 1e-10)
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df
        
    def calculate_bollinger_bands(self, df, window=20, num_std=2):
        """计算布林带"""
        df['BB_Middle'] = df['close'].rolling(window=window).mean()
        bb_std = df['close'].rolling(window=window).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * num_std)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * num_std)
        return df
        
    def calculate_stochastic_oscillator(self, df, window=14):
        """计算随机指标KDJ"""
        df['L14'] = df['low'].rolling(window=window).min()
        df['H14'] = df['high'].rolling(window=window).max()
        df['%K'] = 100 * ((df['close'] - df['L14']) / (df['H14'] - df['L14']))
        df['%D'] = df['%K'].rolling(window=3).mean()
        df['%J'] = 3 * df['%K'] - 2 * df['%D']
        return df
        
    def calculate_obv(self, df):
        """计算能量潮指标"""
        df['OBV'] = (np.sign(df['close'].diff()) * df['vol']).fillna(0).cumsum()
        return df
        
    def calculate_atr(self, df, window=14):
        """计算平均真实波幅"""
        df['TR'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift()),
                abs(df['low'] - df['close'].shift())
            )
        )
        df['ATR'] = df['TR'].rolling(window=window).mean()
        return df
    
    def calculate_risk_metrics(self, df, risk_free_rate=0.02):
        """计算风险指标"""
        if 'return' not in df.columns or len(df) < 2:
            return {}
            
        returns = df['return'].dropna()
        if len(returns) < 2:
            return {}
        
        metrics = {}
        
        # 基础统计
        metrics['total_return'] = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]
        metrics['total_periods'] = len(df)
        
        # 收益率统计
        metrics['avg_daily_return'] = returns.mean()
        metrics['daily_volatility'] = returns.std()
        
        # 年化指标（假设252个交易日）
        metrics['annual_return'] = metrics['avg_daily_return'] * 252
        metrics['annual_volatility'] = metrics['daily_volatility'] * np.sqrt(252)
        
        # 夏普比率（假设无风险利率为0）
        if metrics['annual_volatility'] > 0:
            metrics['sharpe_ratio'] = (metrics['annual_return'] - risk_free_rate) / metrics['annual_volatility']
        else:
            metrics['sharpe_ratio'] = 0
        
        # 最大回撤
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        metrics['max_drawdown'] = drawdown.min()
        metrics['max_drawdown_period'] = drawdown.idxmin() if not drawdown.empty else 0
        
        # VaR (95%)
        if len(returns) >= 5:
            metrics['var_95'] = np.percentile(returns, 5)
        else:
            metrics['var_95'] = 0
            
        # 价格统计
        metrics['highest_price'] = df['high'].max()
        metrics['lowest_price'] = df['low'].min()
        metrics['avg_price'] = df['close'].mean()
        
        return metrics
    
    def generate_analysis_report(self, df, stock_code, risk_metrics):
        """生成分析报告"""
        if not risk_metrics:
            return "无法生成报告：风险指标计算失败"
            
        # ========== 新增：获取最近5个交易日的收盘价 ==========
        recent_dates = df['trade_date'].tail(5).tolist()
        recent_closes = df['close'].tail(5).tolist()
        recent_data = list(zip(recent_dates, recent_closes))
        recent_data.reverse()  # 按日期从近到远排序
        
        # 构建最近交易日数据字符串
        recent_closes_str = ""
        for date, close_price in recent_data:
            recent_closes_str += f"  {date.strftime('%Y-%m-%d')}: {close_price:.2f}元\n"
            
        report = f"""
{'='*60}
股票分析报告 - {stock_code}
{'='*60}

【基本信息】
分析期间: {df['trade_date'].min().strftime('%Y-%m-%d')} 至 {df['trade_date'].max().strftime('%Y-%m-%d')}
数据点数: {len(df)} 个交易日
最新收盘价: {df['close'].iloc[-1]:.2f} 元

【价格统计】
期间最高价: {risk_metrics['highest_price']:.2f} 元
期间最低价: {risk_metrics['lowest_price']:.2f} 元
平均价格: {risk_metrics['avg_price']:.2f} 元
总收益率: {risk_metrics['total_return']*100:.2f}%

【最近5个交易日收盘价】
{recent_closes_str}
【风险指标】
年化收益率: {risk_metrics['annual_return']*100:.2f}%
年化波动率: {risk_metrics['annual_volatility']*100:.2f}%
夏普比率: {risk_metrics['sharpe_ratio']:.2f}
最大回撤: {risk_metrics['max_drawdown']*100:.2f}%
VaR(95%): {risk_metrics['var_95']*100:.2f}%

【技术指标状态】"""
        
        # 添加技术指标状态
        if 'RSI' in df.columns:
            current_rsi = df['RSI'].iloc[-1]
            rsi_status = "超买" if current_rsi > 70 else "超卖" if current_rsi < 30 else "正常"
            report += f"\nRSI(14): {current_rsi:.2f} - {rsi_status}"
            
        if 'DIF' in df.columns and 'DEA' in df.columns:
            dif = df['DIF'].iloc[-1]
            dea = df['DEA'].iloc[-1]
            macd_status = "金叉" if dif > dea and df['DIF'].iloc[-2] <= df['DEA'].iloc[-2] else \
                         "死叉" if dif < dea and df['DIF'].iloc[-2] >= df['DEA'].iloc[-2] else "震荡"
            report += f"\nMACD: {macd_status}"
            
        if 'BB_Upper' in df.columns and 'BB_Lower' in df.columns:
            current_close = df['close'].iloc[-1]
            bb_upper = df['BB_Upper'].iloc[-1]
            bb_lower = df['BB_Lower'].iloc[-1]
            bb_status = "上轨压力" if current_close > bb_upper else \
                       "下轨支撑" if current_close < bb_lower else "通道内"
            report += f"\n布林带: {bb_status}"
            
        report += f"\n\n【数据导出】"
        report += f"\n完整收盘价数据可通过'导出收盘价数据(CSV)'按钮保存"
        report += f"\n\n【分析时间】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        report += f"\n{'='*60}"
        
        return report
    
    def display_single_charts(self, df_stock, stock_code, risk_metrics, analysis_report):
        # 停止进度条并恢复按钮
        self.progress.stop()
        self.progress.pack_forget()
        self.analyze_button.config(state=tk.NORMAL)
        self.status_label.config(text="图表生成完成!")
        
        # 存储当前报告
        self.current_report = analysis_report
        self.current_stock_code = stock_code
        
        # 在主窗口显示报告
        self.show_report_in_main_window(analysis_report)
        
        # 显示matplotlib图表（已移除价格子图）
        self.show_matplotlib_charts(df_stock, stock_code)
        
        # 显示plotly交互式图表（新增EMA线）
        self.show_plotly_chart(df_stock, stock_code)
    
    def display_correlation_charts(self, df_merged, stock1_code, stock2_code):
        # 停止进度条并恢复按钮
        self.progress.stop()
        self.progress.pack_forget()
        self.analyze_button.config(state=tk.NORMAL)
        self.status_label.config(text="相关性分析完成!")
        
        # 显示相关性图表
        self.show_correlation_charts(df_merged, stock1_code, stock2_code)
    
    def show_matplotlib_charts(self, df_stock, stock_code):
        # 创建新窗口显示图表
        chart_window = tk.Toplevel(self.root)
        chart_window.title(f"{stock_code} 技术分析图表")
        chart_window.geometry("1200x900")
        
        # 根据选择的指标确定子图数量（移除价格子图后重新计算）
        base_subplots = 3  # 成交量、MACD、RSI
        extra_subplots = 0
        
        if self.kdj_var.get():
            extra_subplots += 1
        if self.obv_var.get():
            extra_subplots += 1
        if self.atr_var.get():
            extra_subplots += 1
            
        total_subplots = base_subplots + extra_subplots
        
        # 创建matplotlib图表 - 使用黑色背景
        fig = plt.figure(figsize=(17, 3.0*total_subplots), facecolor='black')
        
        # 动态调整子图高度比例
        height_ratios = [1.5] * total_subplots  # 移除价格图后统一高度
            
        gs = GridSpec(total_subplots, 1, height_ratios=height_ratios, hspace=0.3)

        subplot_index = 0

        # 子图1：成交量 - 红涨绿跌（原第二个子图，现第一个）
        if 'vol' in df_stock.columns and 'change' in df_stock.columns:
            ax2 = fig.add_subplot(gs[subplot_index])
            subplot_index += 1
            ax2.set_facecolor('black')
            # 使用红涨绿跌的颜色方案
            colors = ['red' if change > 0 else 'green' for change in df_stock['change']]
            ax2.bar(df_stock['trade_date'], df_stock['vol'], color=colors, alpha=0.7)
            ax2.set_ylabel('成交量', fontsize=12, color='white')
            ax2.set_title(f'{stock_code} 技术指标分析', fontsize=16, color='white')
            ax2.grid(alpha=0.3, color='gray')
            ax2.tick_params(colors='white')
            # 隐藏x轴标签 - 只在最下面的图表显示
            plt.setp(ax2.get_xticklabels(), visible=False)

        # 子图2：MACD（原第三个子图，现第二个）
        ax3 = fig.add_subplot(gs[subplot_index], sharex=ax2)
        subplot_index += 1
        ax3.set_facecolor('black')
        ax3.plot(df_stock['trade_date'], df_stock['DIF'], color='white', label='DIF')
        ax3.plot(df_stock['trade_date'], df_stock['DEA'], color='yellow', label='DEA')
        # MACD柱状图使用红绿颜色
        macd_colors = ['red' if x > 0 else 'green' for x in df_stock['MACD']]
        ax3.bar(df_stock['trade_date'], df_stock['MACD'], color=macd_colors, alpha=0.5, label='MACD')
        ax3.axhline(0, color='white', linestyle='--', alpha=0.5)
        ax3.set_ylabel('MACD', fontsize=12, color='white')
        
        # 优化MACD图例位置 - 移到左侧外部
        ax3.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=11, framealpha=0.7)
        
        ax3.grid(alpha=0.3, color='gray')
        ax3.tick_params(colors='white')
        # 隐藏x轴标签 - 只在最下面的图表显示
        plt.setp(ax3.get_xticklabels(), visible=False)

        # 子图3：RSI（原第四个子图，现第三个）
        ax4 = fig.add_subplot(gs[subplot_index], sharex=ax2)
        subplot_index += 1
        ax4.set_facecolor('black')
        ax4.plot(df_stock['trade_date'], df_stock['RSI'], color='white', label='RSI(14)')
        ax4.axhline(70, color='red', linestyle='--', alpha=0.7, label='超买线(70)')
        ax4.axhline(30, color='green', linestyle='--', alpha=0.7, label='超卖线(30)')
        ax4.set_ylabel('RSI', fontsize=12, color='white')
        
        # 优化RSI图例位置 - 移到左侧外部
        ax4.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=11, framealpha=0.7)
        
        ax4.grid(alpha=0.3, color='gray')
        ax4.tick_params(colors='white')
        # 隐藏x轴标签 - 只在最下面的图表显示
        plt.setp(ax4.get_xticklabels(), visible=False)
        
        # 动态添加额外技术指标子图
        if self.kdj_var.get() and '%K' in df_stock.columns:
            ax_kdj = fig.add_subplot(gs[subplot_index], sharex=ax2)
            subplot_index += 1
            ax_kdj.set_facecolor('black')
            ax_kdj.plot(df_stock['trade_date'], df_stock['%K'], color='cyan', label='%K')
            ax_kdj.plot(df_stock['trade_date'], df_stock['%D'], color='yellow', label='%D')
            ax_kdj.plot(df_stock['trade_date'], df_stock['%J'], color='magenta', label='%J')
            ax_kdj.set_ylabel('KDJ', fontsize=12, color='white')
            
            # 优化KDJ图例位置 - 移到左侧外部
            ax_kdj.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=11, framealpha=0.7)
            
            ax_kdj.grid(alpha=0.3, color='gray')
            ax_kdj.tick_params(colors='white')
            # 隐藏x轴标签 - 只在最下面的图表显示
            plt.setp(ax_kdj.get_xticklabels(), visible=False)
            
        if self.obv_var.get() and 'OBV' in df_stock.columns:
            ax_obv = fig.add_subplot(gs[subplot_index], sharex=ax2)
            subplot_index += 1
            ax_obv.set_facecolor('black')
            ax_obv.plot(df_stock['trade_date'], df_stock['OBV'], color='white', label='OBV')
            ax_obv.set_ylabel('OBV', fontsize=12, color='white')
            
            # 优化OBV图例位置 - 移到左侧外部
            ax_obv.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=11, framealpha=0.7)
            
            ax_obv.grid(alpha=0.3, color='gray')
            ax_obv.tick_params(colors='white')
            # 隐藏x轴标签 - 只在最下面的图表显示
            plt.setp(ax_obv.get_xticklabels(), visible=False)
            
        if self.atr_var.get() and 'ATR' in df_stock.columns:
            ax_atr = fig.add_subplot(gs[subplot_index], sharex=ax2)
            subplot_index += 1
            ax_atr.set_facecolor('black')
            ax_atr.plot(df_stock['trade_date'], df_stock['ATR'], color='white', label='ATR')
            ax_atr.set_ylabel('ATR', fontsize=12, color='white')
            
            # 优化ATR图例位置 - 移到左侧外部
            ax_atr.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=11, framealpha=0.7)
            
            ax_atr.grid(alpha=0.3, color='gray')
            ax_atr.tick_params(colors='white')
            # 隐藏x轴标签 - 只在最下面的图表显示
            plt.setp(ax_atr.get_xticklabels(), visible=False)

        # 最后一个子图显示x轴标签 - 确保总是在最下方子图显示日期
        bottom_ax = fig.get_axes()[-1]  # 获取最后一个子图
        plt.setp(bottom_ax.get_xticklabels(), visible=True)
        bottom_ax.set_xlabel('日期', fontsize=12, color='white')
        
        # 设置日期格式和密度
        date_format = mdates.DateFormatter('%Y-%m-%d')
        bottom_ax.xaxis.set_major_formatter(date_format)
        
        # 根据数据量调整日期刻度密度
        if len(df_stock) > 100:
            # 数据较多时，每月显示一个刻度
            bottom_ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        elif len(df_stock) > 50:
            # 数据中等时，每两周显示一个刻度
            bottom_ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        else:
            # 数据较少时，每周显示一个刻度
            bottom_ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
            
        plt.setp(bottom_ax.get_xticklabels(), rotation=45, ha='right')

        # 调整布局，为外部图例留出空间
        plt.tight_layout()
        plt.subplots_adjust(right=0.80)  # 为右侧图例留出空间
        
        # 将matplotlib图表嵌入到Tkinter窗口
        canvas = FigureCanvasTkAgg(fig, chart_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 添加关闭按钮
        close_button = ttk.Button(chart_window, text="关闭", command=chart_window.destroy)
        close_button.pack(pady=10)
    
    def show_plotly_chart(self, df_stock, stock_code):
        if all(col in df_stock.columns for col in ['open', 'high', 'low', 'close']):
            kline_data = df_stock.sort_values('trade_date')
            
            # 创建K线图 - 使用黑色背景和交易软件常用颜色
            fig_kline = go.Figure(data=[go.Candlestick(
                x=kline_data['trade_date'],
                open=kline_data['open'],
                high=kline_data['high'],
                low=kline_data['low'],
                close=kline_data['close'],
                name='K线',
                increasing_line_color='red',  # 阳线红色
                decreasing_line_color='green'  # 阴线绿色
            )])

            # 添加MA均线 - 保留原MA线
            fig_kline.add_trace(go.Scatter(
                x=kline_data['trade_date'],
                y=kline_data['MA5'],
                mode='lines',
                line=dict(color='yellow', width=1.5),
                name='MA5'
            ))
            fig_kline.add_trace(go.Scatter(
                x=kline_data['trade_date'],
                y=kline_data['MA10'],
                mode='lines',
                line=dict(color='magenta', width=1.5),
                name='MA10'
            ))
            fig_kline.add_trace(go.Scatter(
                x=kline_data['trade_date'],
                y=kline_data['MA20'],
                mode='lines',
                line=dict(color='cyan', width=1.5),
                name='MA20'
            ))
            
            # 新增：添加常用EMA线（12/26/50/200）
            fig_kline.add_trace(go.Scatter(
                x=kline_data['trade_date'],
                y=kline_data['EMA12'],
                mode='lines',
                line=dict(color='orange', width=1.8, dash='dot'),
                name='EMA12'
            ))
            fig_kline.add_trace(go.Scatter(
                x=kline_data['trade_date'],
                y=kline_data['EMA26'],
                mode='lines',
                line=dict(color='purple', width=1.8, dash='dot'),
                name='EMA26'
            ))
            fig_kline.add_trace(go.Scatter(
                x=kline_data['trade_date'],
                y=kline_data['EMA50'],
                mode='lines',
                line=dict(color='lime', width=1.8, dash='dash'),
                name='EMA50'
            ))
            fig_kline.add_trace(go.Scatter(
                x=kline_data['trade_date'],
                y=kline_data['EMA200'],
                mode='lines',
                line=dict(color='blue', width=1.8, dash='dash'),
                name='EMA200'
            ))
            
            # 如果选择了布林带，添加到图表
            if self.bb_var.get() and 'BB_Upper' in kline_data.columns:
                fig_kline.add_trace(go.Scatter(
                    x=kline_data['trade_date'],
                    y=kline_data['BB_Upper'],
                    mode='lines',
                    line=dict(color='orange', width=1, dash='dash'),
                    name='BB上轨'
                ))
                fig_kline.add_trace(go.Scatter(
                    x=kline_data['trade_date'],
                    y=kline_data['BB_Middle'],
                    mode='lines',
                    line=dict(color='gray', width=1, dash='dash'),
                    name='BB中轨'
                ))
                fig_kline.add_trace(go.Scatter(
                    x=kline_data['trade_date'],
                    y=kline_data['BB_Lower'],
                    mode='lines',
                    line=dict(color='orange', width=1, dash='dash'),
                    name='BB下轨',
                    fill='tonexty',
                    fillcolor='rgba(255,165,0,0.1)'
                ))

            fig_kline.update_layout(
                title=f'{stock_code} 交互式K线图',
                xaxis_title='日期',
                yaxis_title='价格（元）',
                xaxis_rangeslider_visible=False,
                hovermode='x unified',
                template='custom_dark',  # 使用自定义黑色主题
                font=dict(color='white'),
                paper_bgcolor='black',
                plot_bgcolor='black',
                # 添加图例布局设置，防止重叠
                legend=dict(
                    orientation="h",  # 水平排列
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # 显示图表
            fig_kline.show()
        else:
            messagebox.showwarning("警告", "缺少K线图所需数据，无法绘制交互式K线图")
    
    # ========== 新增：在主窗口显示报告 ==========
    def show_report_in_main_window(self, report):
        """在主窗口显示分析报告"""
        self.report_text.config(state=tk.NORMAL)
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, report)
        self.report_text.config(state=tk.DISABLED)
        self.report_text.see(1.0)  # 滚动到顶部
    
    def save_current_report(self):
        """保存当前分析报告"""
        if not self.current_report:
            messagebox.showwarning("警告", "没有可保存的报告")
            return
            
        filename = f"{self.current_stock_code}_分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.current_report)
            messagebox.showinfo("保存成功", f"报告已保存为: {filename}")
        except Exception as e:
            messagebox.showerror("保存失败", f"保存报告时出错: {str(e)}")
    
    def clear_report(self):
        """清空报告显示区域"""
        self.report_text.config(state=tk.NORMAL)
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, "分析报告将显示在这里...")
        self.report_text.config(state=tk.DISABLED)
        self.current_report = ""
        self.current_stock_code = ""
    
    # ========== 新增：导出收盘价数据功能 ==========
    def export_close_price_data(self):
        """导出收盘价数据为CSV文件"""
        if self.current_stock_data is None:
            messagebox.showwarning("警告", "没有可导出的数据，请先进行股票分析")
            return
        
        # 选择保存路径
        default_filename = f"{self.current_stock_code}_收盘价_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            initialfile=default_filename
        )
        
        if not file_path:
            return  # 用户取消了保存
        
        try:
            # 提取收盘价相关数据
            export_data = self.current_stock_data[['trade_date', 'open', 'high', 'low', 'close', 'vol']].copy()
            
            # 按日期排序（从早到晚）
            export_data = export_data.sort_values('trade_date')
            
            # 添加日收益率和涨跌幅
            export_data['日收益率'] = export_data['close'].pct_change()
            export_data['涨跌幅'] = (export_data['close'] - export_data['close'].shift(1)) / export_data['close'].shift(1) * 100
            
            # 格式化日期
            export_data['trade_date'] = export_data['trade_date'].dt.strftime('%Y-%m-%d')
            
            # 保存为CSV
            export_data.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            messagebox.showinfo("导出成功", f"收盘价数据已导出到:\n{file_path}\n\n包含字段:\n- 交易日期\n- 开盘价\n- 最高价\n- 最低价\n- 收盘价\n- 成交量\n- 日收益率\n- 涨跌幅(%)")
            
        except Exception as e:
            messagebox.showerror("导出失败", f"导出数据时出错: {str(e)}")
    
    def show_correlation_charts(self, df_merged, stock1_code, stock2_code):
        # 创建新窗口显示相关性图表
        chart_window = tk.Toplevel(self.root)
        chart_window.title(f"{stock1_code} vs {stock2_code} 相关性分析")
        chart_window.geometry("1000x800")
        
        # 创建matplotlib图表 - 使用黑色背景
        fig = plt.figure(figsize=(14, 10), facecolor='black')
        gs = GridSpec(2, 2, height_ratios=[2, 1])
        
        # 提取股票收益率数据
        stock1_returns = df_merged[f'{stock1_code}_return']
        stock2_returns = df_merged[f'{stock2_code}_return']
        stock1_prices = df_merged[f'{stock1_code}_close']
        stock2_prices = df_merged[f'{stock2_code}_close']
        
        # 计算相关性指标
        correlation = np.corrcoef(stock1_returns, stock2_returns)[0, 1]
        covariance = np.cov(stock1_returns, stock2_returns)[0, 1]
        
        # 子图1：收益率散点图与线性拟合
        ax1 = fig.add_subplot(gs[0, :])
        ax1.set_facecolor('black')
        
        # 绘制散点图
        scatter = ax1.scatter(stock1_returns, stock2_returns, 
                             c=range(len(stock1_returns)), cmap='viridis', 
                             alpha=0.7, s=30)
        
        # 线性回归拟合
        slope, intercept, r_value, p_value, std_err = stats.linregress(stock1_returns, stock2_returns)
        line_x = np.linspace(stock1_returns.min(), stock1_returns.max(), 100)
        line_y = slope * line_x + intercept
        
        # 绘制拟合线 - 修复R^2显示问题
        ax1.plot(line_x, line_y, color='red', linewidth=2, 
                label=f'线性拟合: y = {slope:.4f}x + {intercept:.4f}\nR^2 = {r_value**2:.4f}')
        
        ax1.set_xlabel(f'{stock1_code} 日收益率', fontsize=12, color='white')
        ax1.set_ylabel(f'{stock2_code} 日收益率', fontsize=12, color='white')
        ax1.set_title(f'{stock1_code} vs {stock2_code} 收益率相关性分析', fontsize=16, color='white')
        ax1.legend(loc='upper left', fontsize=10)
        ax1.grid(alpha=0.3, color='gray')
        ax1.tick_params(colors='white')
        
        # 添加颜色条
        cbar = plt.colorbar(scatter, ax=ax1)
        cbar.set_label('时间序列', color='white')
        cbar.ax.yaxis.set_tick_params(color='white')
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
        
        # 子图2：价格走势对比
        ax2 = fig.add_subplot(gs[1, 0])
        ax2.set_facecolor('black')
        
        # 归一化价格（以起始点为1）
        norm_stock1 = stock1_prices / stock1_prices.iloc[0]
        norm_stock2 = stock2_prices / stock2_prices.iloc[0]
        
        ax2.plot(df_merged['trade_date'], norm_stock1, color='cyan', linewidth=2, label=f'{stock1_code}')
        ax2.plot(df_merged['trade_date'], norm_stock2, color='yellow', linewidth=2, label=f'{stock2_code}')
        ax2.set_xlabel('日期', fontsize=10, color='white')
        ax2.set_ylabel('归一化价格', fontsize=10, color='white')
        ax2.set_title('价格走势对比', fontsize=12, color='white')
        ax2.legend(loc='upper left')
        ax2.grid(alpha=0.3, color='gray')
        ax2.tick_params(colors='white')
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.xticks(rotation=45)
        
        # 子图3：统计信息
        ax3 = fig.add_subplot(gs[1, 1])
        ax3.set_facecolor('black')
        ax3.axis('off')
        
        # 显示统计信息 - 修复R^2显示问题
        stats_text = f"""
        相关性统计信息:
        
        相关系数: {correlation:.4f}
        协方差: {covariance:.6f}
        决定系数 R^2: {r_value**2:.4f} 
        样本数量: {len(df_merged)}
        时间范围: {df_merged['trade_date'].min().strftime('%Y-%m-%d')} 至 {df_merged['trade_date'].max().strftime('%Y-%m-%d')}
        
        {stock1_code}:
          平均收益率: {stock1_returns.mean():.4f}
          收益率标准差: {stock1_returns.std():.4f}
        
        {stock2_code}:
          平均收益率: {stock2_returns.mean():.4f}
          收益率标准差: {stock2_returns.std():.4f}
        """
        
        ax3.text(0.05, 0.95, stats_text, transform=ax3.transAxes, fontsize=11, 
                color='white', verticalalignment='top', linespacing=1.5)
        
        plt.tight_layout()
        
        # 将matplotlib图表嵌入到Tkinter窗口
        canvas = FigureCanvasTkAgg(fig, chart_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 添加关闭按钮
        close_button = ttk.Button(chart_window, text="关闭", command=chart_window.destroy)
        close_button.pack(pady=10)
        
        # 同时显示交互式plotly图表
        self.show_plotly_correlation(df_merged, stock1_code, stock2_code)
    
    def show_plotly_correlation(self, df_merged, stock1_code, stock2_code):
        """显示交互式相关性图表"""
        # 提取数据
        stock1_returns = df_merged[f'{stock1_code}_return']
        stock2_returns = df_merged[f'{stock2_code}_return']
        
        # 线性回归
        slope, intercept, r_value, p_value, std_err = stats.linregress(stock1_returns, stock2_returns)
        
        # 创建散点图
        fig = go.Figure()
        
        # 添加散点
        fig.add_trace(go.Scatter(
            x=stock1_returns,
            y=stock2_returns,
            mode='markers',
            marker=dict(
                size=8,
                color=list(range(len(stock1_returns))),
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="时间序列")
            ),
            name='收益率散点',
            hovertemplate=f'{stock1_code}: %{{x:.4f}}<br>{stock2_code}: %{{y:.4f}}<extra></extra>'
        ))
        
        # 添加拟合线
        x_range = [stock1_returns.min(), stock1_returns.max()]
        y_range = [slope * x + intercept for x in x_range]

        fig.add_trace(go.Scatter(
            x=x_range,
            y=y_range,
            mode='lines',
            line=dict(color='red', width=3),
            name=f'线性拟合 (R^2 = {r_value**2:.4f})'
        ))
        
        fig.update_layout(
            title=f'{stock1_code} vs {stock2_code} 收益率相关性分析',
            xaxis_title=f'{stock1_code} 日收益率',
            yaxis_title=f'{stock2_code} 日收益率',
            template='custom_dark',
            font=dict(color='white'),
            paper_bgcolor='black',
            plot_bgcolor='black',
            hovermode='closest',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(0,0,0,0.8)"
            )
        )
        
        fig.show()
    
    def show_error(self, message):
        self.root.after(0, lambda: self.handle_error(message))
    
    def handle_error(self, message):
        self.progress.stop()
        self.progress.pack_forget()
        self.analyze_button.config(state=tk.NORMAL)
        self.status_label.config(text="分析失败")
        messagebox.showerror("错误", message)

if __name__ == "__main__":
    root = tk.Tk()
    app = StockAnalysisApp(root)
    root.mainloop()