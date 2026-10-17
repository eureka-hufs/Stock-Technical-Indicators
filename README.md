## 股票数据调取与分析
### 技术指标说明
**MA5 / MA10 / MA20**：**移动平均线**（Moving Average），是根据一段时间内（5日内 / 10日内 / 20日内）的收盘价计算出来的平均值，反映了一段时间内的平均成交价格。代码如下
```
df['MA5'] = df['close'].rolling(window=5).mean()
df['MA10'] = df['close'].rolling(window=10).mean()
df['MA20'] = df['close'].rolling(window=20).mean()
```

**EMA**：**指数移动平均线**（Exponential Moving Average）是一个趋势跟踪指标。相较于 MA 线，EMA 对近期数据更加敏感，给予最近的价格数据更高的权重，因此对市场变化的响应更显著。

首先考虑平滑系数：

$$
\alpha = \frac{2}{N+1}
$$

其中 N 是计算的时间周期（如 EMA12 就是取 N=12 的计算结果），然后根据递推公式：

$$
\mathrm{EMA}_{t} = \alpha P + (1-\alpha)\,\mathrm{EMA}_{t-1}
$$

计算每期 EMA。其中 EMA 是当期指数移动平均数，P 是当期收盘价，α 是平滑系数。递推公式可以展开成通项公式，不加赘述。

- 当价格位于 EMA 之上，且 EMA 本身呈上升趋势，标明市场处于上涨阶段。当价格位于 EMA 之下，且 EMA 本身呈下降趋势，标明市场处于下跌阶段。
- **金叉（买入信号）**：当短期 EMA（如 12 日）由下向上突破长期 EMA（如 26 日）时，表明市场可能进入**上涨趋势**，即为**买入信号**。
- **死叉（卖出信号）**：当短期 EMA 由上向下跌破长期 EMA 时，表明市场可能进入**下跌趋势**，即为**卖出信号**。
- 代码如下（利用 pandas 库中提供的 ewm 函数计算 EMA）
```
import pandas as pd
df['EMA12'] = df['close'].ewm(span=12, adjust=False).mean()
df['EMA26'] = df['close'].ewm(span=26, adjust=False).mean()
df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()
df['EMA200'] = df['close'].ewm(span=200, adjust=False).mean()
```

**MACD**：异同移动平均线（Moving Average Convergence / Divergence）由两条线（DIF & DEA）和由此计算得到的柱状图构成。
- **DIF**：**差离值**（Difference）或常称"快线"，短期 EMA 和长期 EMA 之差，一般是 EMA12 - EMA26.
- **DEA**：实际上就是 DIF 的 9 日指数移动平均线，我们称为对 DIF 的平滑处理。

$$
\mathrm{DEA}_{t} = \frac{\mathrm{DIF}_{t}\times 2 + \mathrm{DEA}_{t-1}\times 8}{9}
$$

- DIF 大于 0：短期 EMA 在长期 EMA 上方，代表多头趋势，数值越大，短期上涨动能越强；DIF 小于 0：短期 EMA 在长期 EMA 下方，代表空头趋势，数值越小，短期下跌动能越强。
- DIF 由下向上穿过 0 线：由空转多，是潜在的买入信号；DIF 由上向下穿过 0 线：由多转空，是潜在的卖出信号。
- 金叉：DIF 由下向上穿过 DEA 是买入信号；死叉：DIF 由上向下穿过 DEA 是卖出信号。
- **红绿柱（BAR）**：两倍处理放大波动，方便观察。

$$
\mathrm{BAR} = 2 \times (\mathrm{DIF} - \mathrm{DEA})
$$

- 代码如下：
```
def calculate_macd(self, df, fast_period=12, slow_period=26, signal_period=9):
        df['EMA12'] = df['close'].ewm(span=fast_period, adjust=False).mean()
        df['EMA26'] = df['close'].ewm(span=slow_period, adjust=False).mean()
        df['DIF'] = df['EMA12'] - df['EMA26']
        df['DEA'] = df['DIF'].ewm(span=signal_period, adjust=False).mean()
        df['MACD'] = (df['DIF'] - df['DEA']) * 2
        return df
```

**RSI**：**相对强弱指标**（Relative Strength Index），衡量市场买卖力量的强弱对比，为短线交易中判断进场时机提供参考。首先考虑**相对强弱**（Relative Strength，**RS**）：

$$
\mathrm{RS} = \frac{\text{一定时间内收盘价的平均涨幅}}{\text{一定时间内收盘价的平均跌幅}}
$$

然后计算：

$$
\mathrm{RSI} = 100 - \frac{100}{1 + \mathrm{RS}}
$$

- RSI 趋于 100，意味着较大的下跌风险；RSI 趋于 0，意味着较大的上涨机会。
- 一般考虑两个参考值：RSI 大于等于 70（超买线），意味着市场情绪亢奋，此时不宜盲目追高。RSI 小于等于 30（超卖线），意味着市场普遍恐慌，此时应寻找左侧建仓机会，争取超跌反弹。
- **顶背离**：股价上涨而 RSI 乏力，意味着买盘逐渐无力，大跌即将到来；
- **底背离**：股价下跌而 RSI 抬高，意味着卖盘逐渐无力，反弹即将到来。
- RSI 在遇到极端行情时容易失效（钝化）。因此，实际量化投资策略是需要参考多种指标的。
- 代码如下：
```
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
```

**BOLL**：**布林带**（Bollinger Bands）或**保利加通道**由三条线组成。其中**中轨**就是 **MA20**。计算过去 20 日收盘价的标准差：

$$
\mathrm{SD} = \sqrt{\frac{\displaystyle\sum_{i=1}^{20}\left(P_{t-i+1}-\mathrm{MA}_{20}\right)}{20}}
$$

进而计算**上轨**：

$$
\mathrm{UB} = \mathrm{MA}_{20} + 2\times \mathrm{SD}
$$

和**下轨**：

$$
\mathrm{LB} = \mathrm{MA}_{20} - 2\times \mathrm{SD}
$$

- 布林带上下轨夹成**通道**，股价在通道内外的波动情况给出了参考投资信号：
- **上轨**也被称为**压力线**。当股价穿越上轨且上轨向上发散，意味着多头趋势启动，股价大概率延续上涨，可视为买入信号；
- **下轨**也称为**支撑线**，当股价穿越下轨且下轨向下发散，意味着空头趋势启动，股价大概率延续下跌，可视为卖出信号。
- 布林带无明显趋势或明显收敛，而股价突破上轨且短期内连续在上方运行，意味着成交量萎缩，即超买信号，是股价回落信号；股价突破下轨且短期内持续在下方运行，即超卖信号，大概率出现反弹。
- 通过同时考虑布林带情况和 RSI 背离，可以更准确地确认反弹信号。
- 代码如下：
```
def calculate_bollinger_bands(self, df, window=20, num_std=2):
        df['BB_Middle'] = df['close'].rolling(window=window).mean()
        bb_std = df['close'].rolling(window=window).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * num_std)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * num_std)
        return df
```

![[Pasted image 20251130194141.png]]

**KDJ**：随机指标（Stochastic Indicator）。首先考虑**未成熟随机值（RSV）**：

$$
\mathrm{RSV} = \frac{C - L_{n}}{H_{n} - L_{n}}\times 100
$$

其中 C 是当天收盘价，L_n 是前 n 日最低价，H_n 是前 n 日最高价。分别规定某一天的 K，D，J 值如下：

$$
K_{i} = \frac{2}{3}K_{i-1} + \frac{1}{3}\mathrm{RSV}_{i}
$$

$$
D_{i} = \frac{2}{3}D_{i-1} + \frac{1}{3}K_{i}
$$

$$
J_{i} = 3K_{i-1} + 2D_{i}
$$

- 这些式子里的系数（权重）在规定条件下可以根据实际需要选取。这里我们选取的系数是常用的配置。
- KDJ 指标可以帮助人们判断股票中短期的走势。通常来说，K 线涨过 D 线（金叉）是买入信号，K 线跌破 D 线（死叉）是卖出信号。J 值大于 100 为超买，小于 0 为超卖。
- 股价新高而 KD 值未新高或 KD 值新高而股价未新高，称为顶背离，是卖出信号；股价新低而 KD 值未新低或 KD 值新低而股价未新低，称为底背离，是买入信号。
- 代码如下（这里取 14 日的 KDJ 指标计算，适用于中线交易）：
```
def calculate_stochastic_oscillator(self, df, window=14):
        df['L14'] = df['low'].rolling(window=window).min()
        df['H14'] = df['high'].rolling(window=window).max()
        df['%K'] = 100 * ((df['close'] - df['L14']) / (df['H14'] - df['L14']))
        df['%D'] = df['%K'].rolling(window=3).mean()
        df['%J'] = 3 * df['%K'] - 2 * df['%D']
        return df
```

**OBV**：**能量潮**（On Balance Volume）或**平衡成交量**是一种基于成交量衡量市场买卖压力的指标。它的计算仅仅是简单的交易量累加：

$$
\mathrm{OBV}_{t} = \mathrm{OBV}_{t-1} + \begin{cases}
\ \ \mathrm{vol}, & P_t > P_{t-1} \\
\ 0, & P_t = P_{t-1} \\
-\mathrm{vol}, & P_t < P_{t-1}
\end{cases}
$$

其中 P_t 是当日收盘价。

- 也即每天的总成交量会根据当天价格的涨跌被赋予正值或负值。收盘价越高，当天成交量越高；收盘价越低，成交量越低。当 OBV 位于高位时，说明当前市场的成交量较大，市场上涨的买盘力量很强，可能会出现买盘逐步消耗，市场出现调整的可能性也会增加。当 OBV 位于低位时，说明当前市场的成交量较小，市场下跌的卖盘力量很强，可能会出现卖盘逐步消耗，市场反弹的可能性也会增加。
- 实际投资分析也考虑 OBV 的"背离"，此处不加赘述。
- 代码如下：
```
def calculate_obv(self, df):
        df['OBV'] = (np.sign(df['close'].diff()) * df['vol']).fillna(0).cumsum()
        return df
```

**ATR**：**平均真实波幅**（Average true range）或**真实区间**用以衡量市场价格的波动性。它是以下三个波动幅度的最大值：当天最高点与最低点间的距离、前一天收盘价和当天最高价间的距离、前一天收盘价和当天最低价间的距离（距离即作差后取绝对值）。
- 波动幅度的概念表示可以显示出交易者的期望和热情。大幅的或增加中的波动幅度表示交易者在当天可能准备持续买进或卖出股票。波动幅度的减少则表示交易者对股市没有太大的兴趣。
- 因此，观察股票的 ATR 有助于投资者初步选股，或为调整投资策略提供参考。
- 代码如下：
```
def calculate_atr(self, df, window=14):
        df['TR'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift()),
                abs(df['low'] - df['close'].shift())
            )
        )
        df['ATR'] = df['TR'].rolling(window=window).mean()
        return df
```


以下几个指标都用于股票的**风险分析**参考：
- **年化收益率**：程序中采用单利计算的简单年化收益率 = 日平均收益率 $\times$ 252个交易日。
- **年化波动率**：日波动率 $\times$ 252 的平方根（即 $\sqrt{252}$）。
- **Sharpe 比率**：夏普比率，即超额收益率与总风险的比值。其中，**超额收益**指超过无风险利率的收益，总风险则以年化波动率衡量。

$$
\text{Sharpe Ratio} = \frac{E(R_P) - R_f}{\sigma_{P}}
$$

其中 E(R_P) 表示某投资组合预期年化报酬率，R_f 是无风险年化收益率（程序中设定为 0.02），σ_P 是该投资组合年化报酬率的标准差。夏普比率表征了投资者额外承受的每一单位风险所获得的额外收益。

- **最大回撤**：最大回撤率（drawdown）是指在某段时间内，资产净值从峰值下跌至谷值的最大百分比跌幅，用于衡量投资过程中可能出现的最大亏损风险。其计算公式为：

$$
\mathrm{DD}_{\max} = \frac{\text{最低点净值} - \text{最高点净值}}{\text{最高点净值}}
$$

该指标通过反映资产价格从峰值到谷值的最大跌幅，帮助投资者评估极端亏损风险。回撤率越小代表风险控制能力越强。

- 在程序编写中，我们如此处理：先将日收益率加上 1 得到日净值增长因子，再对期内增长因子累乘得到累计净值序列，之后提取累计净值的滚动最大值；利用每日净值和历史峰值净值就可以算得每日回撤率，进而最终取得最大回撤率。
- **VaR（95%）**：风险价值（Value at Risk）是指在特定置信水平（程序中设置为 95%）下金融资产可能承受的最大潜在损失，常用于衡量投资组合的市场风险。
以上风险指标代码实现如下：
```
metrics = {}
metrics['avg_daily_return'] = returns.mean()
metrics['daily_volatility'] = returns.std()
metrics['annual_return'] = metrics['avg_daily_return'] * 252
metrics['annual_volatility'] = metrics['daily_volatility'] * np.sqrt(252)

if metrics['annual_volatility'] > 0:
        metrics['sharpe_ratio'] = metrics['annual_return'] / metrics['annual_volatility']
else:
        metrics['sharpe_ratio'] = 0
           
cumulative = (1 + returns).cumprod()
running_max = cumulative.expanding().max()
drawdown = (cumulative - running_max) / running_max
metrics['max_drawdown'] = drawdown.min()
metrics['max_drawdown_period'] = drawdown.idxmin() if not drawdown.empty else 0

if len(returns) >= 5:
        metrics['var_95'] = np.percentile(returns, 5)
else:
        metrics['var_95'] = 0
```

除了以上呈现的技术指标计算之外，程序还有股票波动相关性分析的功能。我们通过两只股票的日收益率分析它们之间的相关性，其中可以参考相关系数：

$$
r = \frac{\sum (x_{i}-\bar{x})(y_{i}-\bar{y})}{\sqrt{\sum (x_{i}-\bar{x})^{2}}\ \sqrt{\sum (y_{i}-\bar{y})^{2}}}
$$

和决定系数：

$$
R^{2} = 1 - \frac{\sum (y-\hat{y})^{2}}{\sum (y-\bar{y})^{2}}
$$

整个相关性分析功能的核心代码如下：
```
stock1_returns = df_merged[f'{stock1_code}_return']
stock2_returns = df_merged[f'{stock2_code}_return']
stock1_prices = df_merged[f'{stock1_code}_close']
stock2_prices = df_merged[f'{stock2_code}_close']

correlation = np.corrcoef(stock1_returns, stock2_returns)[0, 1]
covariance = np.cov(stock1_returns, stock2_returns)[0, 1]

# 子图1：收益率散点图与线性拟合
ax1 = fig.add_subplot(gs[0, :])
ax1.set_facecolor('black')
scatter = ax1.scatter(stock1_returns, stock2_returns, c=range(len(stock1_returns)), cmap='viridis', alpha=0.7, s=30)
slope, intercept, r_value, p_value, std_err = stats.linregress(stock1_returns, stock2_returns)
line_x = np.linspace(stock1_returns.min(), stock1_returns.max(), 100)
line_y = slope * line_x + intercept
ax1.plot(line_x, line_y, color='red', linewidth=2, label=f'线性拟合: y = {slope:.4f}x + {intercept:.4f}\nR^2 = {r_value**2:.4f}')
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
```
