"""Finance results feature pages.

V6.2 moves the finance-result render implementations out of core.legacy.
Shared helpers and constants are still provided by core.legacy during this
transition step, so behavior stays identical while the file layout improves.
"""

from __future__ import annotations

import core.legacy as _legacy

# Import every legacy helper, including private helpers used inside these pages.
globals().update({k: getattr(_legacy, k) for k in dir(_legacy) if not k.startswith("__")})

def render_recent_trend():
    hero("近期走势（日报）",
         "直接读每日「运营日报」谷歌表——自己拉日期看每日走势、选两段时间对比（如赛前 vs 世界杯）。"
         "数据来源：日报机器人每天自动收集；月度汇总请看「经营总览」。",
         source_badge='数据源：运营日报谷歌表（自动）',
         basis='每日「运营日报」谷歌表的「平台报表」分页（程序每日 10:00 自动写入）',
         detail=(
             '**分析范围**：每日经营走势（注册／首存／投注／公司输赢／存取款等）与两段时间对比。\n\n'
             '**数据来源**：运营日报谷歌表「平台报表」分页，自动读取近三个月。\n\n'
             '**更新方式**：程序每日 10:00 自动写入，本页约 10 分钟缓存，刷新即为最新，无需人工。\n\n'
             '**名词解释**见下方「名词说明」。完整数据来源对照见「数据说明」页。'
         ))
    import datetime as _dt
    try:
        df = load_daily_ops(_recent_month_labels(3))
    except Exception as e:
        st.error(f"读日报谷歌表失败：{str(e)[:150]}")
        return
    if df is None or df.empty:
        st.info("📭 暂时读不到日报数据（谷歌表「平台报表」分页为空，或服务账号没被授权读这份表）。")
        return
    df["_d"] = pd.to_datetime(df["日期"], errors="coerce")
    df = df[df["_d"].notna()].copy()
    min_d, max_d = df["_d"].min().date(), df["_d"].max().date()
    METRICS = [m for m in ["注册数", "首存人数", "投注人数", "有效投注额", "公司输赢",
                           "存款额", "取款额", "存提差", "公司净收入"] if m in df.columns]

    section_header("选日期范围", f"日报数据现有 {min_d} ~ {max_d}")
    c1, c2 = st.columns(2)
    with c1:
        start = st.date_input("开始日期", value=max(min_d, max_d - _dt.timedelta(days=13)),
                              min_value=min_d, max_value=max_d, key="rt_start")
    with c2:
        end = st.date_input("结束日期", value=max_d, min_value=min_d, max_value=max_d, key="rt_end")
    if start > end:
        start, end = end, start
    sel = df[(df["_d"] >= pd.Timestamp(start)) & (df["_d"] <= pd.Timestamp(end))].copy()
    st.caption(f"📅 当前显示 {start} ~ {end}，共 {len(sel)} 天。")

    def _s(c):
        return float(sel[c].sum()) if c in sel.columns and len(sel) else 0.0
    n = len(sel)
    reg, fd = _s("注册数"), _s("首存人数")
    vbet, win = _s("有效投注额"), _s("公司输赢")
    dep, wdr, net = _s("存款额"), _s("取款额"), _s("存提差")
    bonus, rebate = _s("红利"), _s("返水")
    netinc = _s("公司净收入")
    conv = (fd / reg) if reg else 0
    hold = (win / vbet) if vbet else 0

    section_header("区间总览", "合计（除标注外）")
    with st.expander("📖 名词说明（看不懂点这）"):
        st.markdown(
            "- **有效投注额**：客户实际有效的下注总额（已去掉对冲、取消、走盘那些不算的）。\n"
            "- **公司输赢**：平台对客户的输赢——客户输多少 = 公司赢多少。**正数 = 平台赢**。这是「还没扣成本」的毛赢（红利/返水/佣金/场馆费另算）。\n"
            "- **Hold%（杀率）**：公司输赢 ÷ 有效投注 = 平台从客户投注里实际赢走的比例，越高越赚。业界叫 Hold 或杀率。\n"
            "- **首存转化率**：首存人数 ÷ 新注册 = 新注册里有多少人真的存了第一笔钱。\n"
            "- **存提差（净流入）**：实际存款 − 实际取款 = 这段时间客户净流入平台多少钱。\n"
            "- **提存率**：取款 ÷ 存款，越高代表提款压力越大。\n"
            "- **公司净收入**：公司输赢扣掉红利/返水/代理佣金/场馆费等之后（口径以后台字段为准）。")
    r1 = st.columns(4)
    show_metric(r1[0], "天数", fmt_num(n))
    show_metric(r1[1], "新注册", f"{fmt_num(int(reg))}（日均 {reg/n:.0f}）" if n else "—")
    show_metric(r1[2], "首存人数", fmt_num(int(fd)))
    show_metric(r1[3], "首存转化率", fmt_pct(conv), help_text="首存人数 ÷ 新注册：新注册里多少人真的存了款", tone="accent")
    r2 = st.columns(4)
    show_metric(r2[0], "有效投注额", fmt_num(round(vbet)), help_text="客户有效下注总额（去掉对冲/取消/走盘）")
    show_metric(r2[1], "公司输赢", fmt_num(round(win)), tone=tone_by_sign(win),
                help_text="平台对客户的输赢，客户输=公司赢；正数=平台赢。未扣红利/返水/佣金/场馆费的毛赢")
    show_metric(r2[2], "Hold%（杀率）", f"{hold*100:.2f}%",
                help_text="公司输赢 ÷ 有效投注 = 平台从客户投注里实际赢走的比例，越高平台越赚（业界叫 Hold / 杀率）",
                tone="accent")
    show_metric(r2[3], "实际存款", fmt_num(round(dep)))
    r3 = st.columns(4)
    show_metric(r3[0], "存提差（净流入）", fmt_num(round(net)), tone=tone_by_sign(net),
                help_text="实际存款 − 实际取款 = 客户净流入平台的钱")
    show_metric(r3[1], "红利成本", fmt_num(round(bonus)), tone="warn")
    show_metric(r3[2], "返水成本", fmt_num(round(rebate)), tone="warn")
    show_metric(r3[3], "公司净收入", fmt_num(round(netinc)), tone=tone_by_sign(netinc),
                help_text="公司输赢扣掉红利/返水/佣金/场馆费等之后（口径以后台为准）")

    # 自动小结
    if n and "注册数" in sel.columns:
        peak_reg = sel.loc[sel["注册数"].idxmax()]
        line = (f"这 {n} 天：新注册 **{int(reg)}** 人（日均 {reg/n:.0f}）、首存 **{int(fd)}** 人（转化 **{conv*100:.1f}%**）；"
                f"有效投注 **{fmt_num(round(vbet))}**、公司输赢 **{fmt_num(round(win))}**（Hold **{hold*100:.2f}%**）；"
                f"实际存款 **{fmt_num(round(dep))}**、存提差 **{fmt_num(round(net))}**。"
                f"注册最高是 **{peak_reg['日期']}（{int(peak_reg['注册数'])} 人）**。")
        if "公司输赢" in sel.columns:
            pw, lw = sel.loc[sel["公司输赢"].idxmax()], sel.loc[sel["公司输赢"].idxmin()]
            line += f"公司输赢最高 {pw['日期']}（{fmt_num(round(pw['公司输赢']))}）、最低 {lw['日期']}（{fmt_num(round(lw['公司输赢']))}）。"
        st.info(line)

    # 关键比率每日走势
    section_header("关键比率走势", "首存转化率 / Hold% / 提存率 逐日看。")
    rate = sel.copy()
    if {"首存人数", "注册数"}.issubset(rate.columns):
        rate["首存转化率"] = (rate["首存人数"] / rate["注册数"].replace(0, pd.NA) * 100).round(1)
    if {"公司输赢", "有效投注额"}.issubset(rate.columns):
        rate["Hold%"] = (rate["公司输赢"] / rate["有效投注额"].replace(0, pd.NA) * 100).round(2)
    if {"取款额", "存款额"}.issubset(rate.columns):
        rate["提存率%"] = (rate["取款额"] / rate["存款额"].replace(0, pd.NA) * 100).round(1)
    ratecols = [c for c in ["首存转化率", "Hold%", "提存率%"] if c in rate.columns]
    if ratecols:
        rfig = go.Figure()
        for c in ratecols:
            rfig.add_trace(go.Scatter(x=rate["日期"], y=rate[c], mode="lines+markers", name=c))
        rfig.update_layout(height=300, template=TEMPLATE, margin=dict(l=10, r=10, t=10, b=10),
                           legend=dict(orientation="h", y=1.12), xaxis_title=None)
        st.plotly_chart(rfig, use_container_width=True)

    section_header("每日走势", "选要看的指标。")
    pick = st.multiselect("指标", METRICS,
                          default=[m for m in ["注册数", "投注人数", "公司输赢"] if m in METRICS],
                          key="rt_metrics")
    for m in pick:
        fig = px.bar(sel, x="日期", y=m, template=TEMPLATE, title=m, color_discrete_sequence=[BLUE])
        fig.update_layout(height=240, margin=dict(l=10, r=10, t=34, b=10), xaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)

    section_header("两段时间对比", "选 A、B 两段，看日均差异（例如赛前 vs 世界杯）。")
    cc = st.columns(4)
    with cc[0]:
        a1 = st.date_input("A 开始", value=min_d, min_value=min_d, max_value=max_d, key="rt_a1")
    with cc[1]:
        a2 = st.date_input("A 结束", value=min(max_d, min_d + _dt.timedelta(days=6)),
                           min_value=min_d, max_value=max_d, key="rt_a2")
    with cc[2]:
        b1 = st.date_input("B 开始", value=max(min_d, max_d - _dt.timedelta(days=6)),
                           min_value=min_d, max_value=max_d, key="rt_b1")
    with cc[3]:
        b2 = st.date_input("B 结束", value=max_d, min_value=min_d, max_value=max_d, key="rt_b2")
    segA = df[(df["_d"] >= pd.Timestamp(a1)) & (df["_d"] <= pd.Timestamp(a2))]
    segB = df[(df["_d"] >= pd.Timestamp(b1)) & (df["_d"] <= pd.Timestamp(b2))]
    rows = []
    for m in METRICS:
        av = segA[m].mean() if len(segA) else 0
        bv = segB[m].mean() if len(segB) else 0
        chg = f"{(bv/av-1)*100:+.0f}%" if av else "—"
        rows.append({"指标": m, f"A日均({a1}~{a2})": round(av, 1),
                     f"B日均({b1}~{b2})": round(bv, 1), "变化": chg})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption("A、B 两段的日均对比；变化 = (B−A)/A。想比「赛前 vs 世界杯」：A 设 6/1~6/11、B 设 6/12 至今。")



def render_overview():
    platform = load_table('raw_platform_report')
    finance = load_table('raw_finance_report')
    hero('经营总览', '以平台报表与财务报表为主，查看经营结果、资金流与成本结构。', latest_imported_at(platform, finance),
         basis='经营报表＋财务报表（＋红利记录、代理结算）｜净利润＝公司输赢−红利/返水/代理佣金/集团分成',
         detail=(
             '**分析范围**：平台整体经营结果、资金流（存款／取款／净流入）、成本结构与真实净利润。\n\n'
             '**数据来源（后台导出 → 上传）**：\n'
             '- 经营报表（报表中心→经营报表）：公司输赢／注册／首存／存取款／有效投注\n'
             '- 财务报表（报表中心→财务报表）：红利／返水／代理佣金／集团分成\n'
             '- 红利记录（会员管理→VIP记录管理→红利记录）：红利构成拆分\n'
             '- 代理结算月报（客服主管提供）：实际佣金派发\n\n'
             '**计算口径**：真实平台净盈利 ＝ 公司输赢 ＋ 提前结算 ＋ 帐户调整 − 红利 − 返水 − 代理佣金 − 集团分成。\n\n'
             '**更新方式**：手动上传（每月导出后于「数据上传」页上传）。完整数据来源对照见「数据说明」页。'
         ))

    headline_slot = st.container()  # 顶部核心结论横幅：数值在页面下方算齐后回填到这里

    platform, start, end, month = date_range_picker(platform, '日期', 'ov', default_last_days=None)
    if month and '时间' in finance.columns:
        finance['时间'] = to_datetime_safe(finance['时间'])
        finance = finance[finance['时间'].dt.strftime('%Y-%m') == month].copy()
    elif '时间' in finance.columns and start is not None and end is not None:
        finance['时间'] = to_datetime_safe(finance['时间'])
        finance = finance[(finance['时间'] >= start) & (finance['时间'] < end + pd.Timedelta(days=1))].copy()

    if platform.empty:
        st.warning('当前筛选条件下无数据。')
        return

    kpi_winloss = safe_sum(platform, '公司输赢')
    kpi_diff = safe_sum(platform, '存提差')
    cols = st.columns(6)
    show_metric(cols[0], '公司输赢', fmt_num(kpi_winloss), help_text=tooltip_text('公司输赢'),
                tone=tone_by_sign(kpi_winloss))
    show_metric(cols[1], '有效投注额', fmt_num(safe_sum(platform, '有效投注额')), help_text=tooltip_text('有效投注额'))
    show_metric(cols[2], '实际总存款', fmt_num(safe_sum(finance, '实际总存款')), help_text=tooltip_text('实际总存款'))
    show_metric(cols[3], '存提差', fmt_num(kpi_diff), help_text=tooltip_text('存提差'),
                tone=tone_by_sign(kpi_diff))
    show_metric(cols[4], '注册数', fmt_num(safe_sum(platform, '注册数')))
    show_metric(cols[5], '首存转化率', fmt_pct(safe_sum(platform, '首存人数') / safe_sum(platform, '注册数') if safe_sum(platform, '注册数') else None), help_text=tooltip_text('首存转化率'),
                tone='accent')

    # ── 扣除代理红利后的调整净收入 ──
    agent_activities = st.session_state.get('agent_bonus_activities', [])
    if agent_activities and '公司净收入' in platform.columns:
        # 加载红利数据并计算代理相关红利
        bonus_for_adj = load_table('raw_bonus_report')
        if not bonus_for_adj.empty and '活动名称' in bonus_for_adj.columns and '红利金额' in bonus_for_adj.columns:
            # 对齐日期筛选
            if '申请时间' in bonus_for_adj.columns:
                bonus_for_adj['申请时间'] = to_datetime_safe(bonus_for_adj['申请时间'])
                if month:
                    bonus_for_adj = bonus_for_adj[bonus_for_adj['申请时间'].dt.strftime('%Y-%m') == month].copy()
                elif start is not None and end is not None:
                    bonus_for_adj = bonus_for_adj[
                        (bonus_for_adj['申请时间'] >= start) &
                        (bonus_for_adj['申请时间'] < end + pd.Timedelta(days=1))
                    ].copy()

            agent_mask = bonus_for_adj['活动名称'].astype(str).isin(agent_activities)
            agent_bonus_amt = float(bonus_for_adj.loc[agent_mask, '红利金额'].sum())
            total_bonus_amt = float(bonus_for_adj['红利金额'].sum())
            real_member_bonus = total_bonus_amt - agent_bonus_amt
            net_income = safe_sum(platform, '公司净收入')

            section_header('红利构成拆分', '根据红利分析页选定的代理相关活动，拆分红利支出构成。')
            adj_cols = st.columns(4)
            show_metric(adj_cols[0], '红利总支出', fmt_num(total_bonus_amt))
            show_metric(adj_cols[1], '代理相关红利', fmt_num(agent_bonus_amt),
                        help_text=f'来自 {len(agent_activities)} 个代理相关活动', tone='warn')
            show_metric(adj_cols[2], '真实会员活动红利', fmt_num(real_member_bonus),
                        help_text='红利总支出 - 代理相关红利')
            show_metric(adj_cols[3], '代理红利占比', fmt_pct(agent_bonus_amt / total_bonus_amt if total_bonus_amt else None),
                        tone='warn')

    # ── 真实平台净盈利计算 ──
    section_header('真实平台净盈利', '综合系统数据与手动输入的财务数据，还原真实盈亏。')

    # 从BQ自动读取的项目
    company_winloss = safe_sum(platform, '公司输赢')
    early_settle = safe_sum(platform, '提前结算')
    account_adjust = safe_sum(platform, '账户调整')
    rebate = safe_sum(platform, '返水')
    bonus_total = safe_sum(platform, '红利')
    tips = safe_sum(platform, '打赏收入')
    group_share = safe_sum(platform, '集团分成')
    agent_comm_sys = safe_sum(platform, '代理佣金')

    st.markdown('**系统自动读取（来自平台报表）：**')
    auto_cols = st.columns(4)
    show_metric(auto_cols[0], '公司输赢', fmt_num(company_winloss))
    show_metric(auto_cols[1], '提前结算（计营利）', fmt_num(early_settle))
    show_metric(auto_cols[2], '帐户调整（计营利）', fmt_num(account_adjust))
    show_metric(auto_cols[3], '集团分成（系统费）', fmt_num(group_share))

    auto_cols2 = st.columns(4)
    show_metric(auto_cols2[0], '红利', fmt_num(bonus_total))
    show_metric(auto_cols2[1], '返水', fmt_num(rebate))
    show_metric(auto_cols2[2], '打赏收入', fmt_num(tips))
    show_metric(auto_cols2[3], '代理佣金（系统）', fmt_num(agent_comm_sys))

    # 自动从 raw_agent_settlement_summary 拉「实际佣金派发总额」(总计发放) 当默认值
    auto_commission_default = 0.0
    settle_month_key = None
    try:
        _settle_summary = load_table('raw_agent_settlement_summary')
        if not _settle_summary.empty and '月份' in _settle_summary.columns and month:
            _sub = _settle_summary[_settle_summary['月份'].astype(str) == month]
            if not _sub.empty:
                settle_month_key = month
                # 项目 含 "总计发放" 之 row,取 abs(金额) 当默认
                _proj = _sub['项目'].astype(str).str.replace('⭐️', '', regex=False).str.strip()
                _total_row = _sub[_proj == '总计发放']
                if not _total_row.empty:
                    auto_commission_default = abs(float(_total_row['金额'].iloc[0]))
    except Exception:
        pass

    # 手动输入的项目（部分可由客服主管月报自动填）
    st.markdown('**手动输入 / 自动填入（清空则不计入）：**')
    if settle_month_key:
        st.caption(f'📌 「实际佣金派发总额」已从 raw_agent_settlement_summary（{settle_month_key} 总计发放）自动带入 {fmt_num(auto_commission_default)}。可手动覆盖。')

    manual_cols = st.columns(4)
    with manual_cols[0]:
        channel_fee = st.number_input('通道手续费（正数）', min_value=0.0, value=0.0, step=10000.0, key=f'channel_fee_{month or "all"}', help='存取款支付通道费用，填正数（目前无 BQ 来源，需手填）')
    with manual_cols[1]:
        project_adjust = st.number_input('项目调整-财务承担', value=0.0, step=10000.0, key=f'project_adjust_{month or "all"}', help='正数=平台收入，负数=平台支出（目前无 BQ 来源，需手填）')
    with manual_cols[2]:
        real_commission = st.number_input(
            '实际佣金派发总额（正数）',
            min_value=0.0, value=auto_commission_default, step=10000.0,
            key=f'real_commission_{month or "all"}',
            help='含平台直发+兑台预派的佣金总额，填正数。已从客服主管月报「总计发放」自动带入,可手动覆盖。',
        )
    with manual_cols[3]:
        agent_refund = st.number_input('代理回帐', min_value=0.0, value=0.0, step=10000.0, key=f'agent_refund_{month or "all"}', help='代理退回的金额，填正数。口径与客服主管月报存在差异（仅部分笔回款入帐），目前仍需手填')

    # 计算真实净盈利
    # 如果填了实际佣金且选了代理相关活动，红利用真实会员红利（扣掉代理红利）避免重复计算
    agent_activities = st.session_state.get('agent_bonus_activities', [])
    if real_commission > 0 and agent_activities:
        # 有选代理活动 + 有填实际佣金 → 用真实会员红利
        bonus_for_calc = load_table('raw_bonus_report')
        if not bonus_for_calc.empty and '活动名称' in bonus_for_calc.columns and '红利金额' in bonus_for_calc.columns:
            if '申请时间' in bonus_for_calc.columns:
                bonus_for_calc['申请时间'] = to_datetime_safe(bonus_for_calc['申请时间'])
                if month:
                    bonus_for_calc = bonus_for_calc[bonus_for_calc['申请时间'].dt.strftime('%Y-%m') == month].copy()
                elif start is not None and end is not None:
                    bonus_for_calc = bonus_for_calc[
                        (bonus_for_calc['申请时间'] >= start) &
                        (bonus_for_calc['申请时间'] < end + pd.Timedelta(days=1))
                    ].copy()
            agent_mask = bonus_for_calc['活动名称'].astype(str).isin(agent_activities)
            agent_bonus_in_calc = float(bonus_for_calc.loc[agent_mask, '红利金额'].sum())
            real_bonus = bonus_total - agent_bonus_in_calc
        else:
            real_bonus = bonus_total
        bonus_note = f'真实会员红利（已扣除代理红利 {fmt_num(agent_bonus_in_calc)}）'
    else:
        real_bonus = bonus_total
        bonus_note = '红利（含代理红利，建议在红利分析页选择代理活动+填入实际佣金以避免重复计算）'

    gross_income = company_winloss + early_settle + account_adjust + tips
    costs = real_bonus + rebate + group_share + channel_fee - project_adjust
    commission_total = real_commission if real_commission > 0 else agent_comm_sys
    refund = agent_refund

    real_profit = gross_income - costs - commission_total + refund

    st.markdown('---')
    result_cols = st.columns(3)
    show_metric(result_cols[0], '毛收入', fmt_num(gross_income),
                help_text='公司输赢 + 提前结算 + 帐户调整 + 打赏',
                tone=tone_by_sign(gross_income))
    show_metric(result_cols[1], '总成本', fmt_num(costs + commission_total - refund),
                help_text=bonus_note + ' + 返水 + 集团分成 + 通道手续费 - 项目调整 + 佣金 - 代理回帐',
                tone='warn')
    show_metric(result_cols[2], '真实平台净盈利', fmt_num(real_profit),
                help_text='毛收入 - 总成本',
                tone=tone_by_sign(real_profit))
    if real_commission > 0 and agent_activities:
        st.caption('✅ 已使用实际佣金 + 扣除代理红利，避免重复计算')
    elif real_commission > 0:
        st.caption('⚠️ 已使用实际佣金，但未选择代理相关活动，红利可能含代理部分导致重复扣除。请到红利分析页选择代理活动。')
    else:
        st.caption('⚠️ 佣金使用系统数据（可能偏低），建议填入实际佣金派发总额以获得准确结果')

    # ── 经营摘要：净利瀑布 + 业务线盈利贡献 + 月环比 + 摘要 ──
    valid_bet = safe_sum(platform, '有效投注额')
    fx = st.number_input('兑台汇率（人民币→台币）', min_value=0.0, value=4.35, step=0.01,
                         key=f'fx_rate_{month or "all"}', help='把人民币净利换算成台币，仅展示用')
    net_rmb = real_profit
    net_twd = net_rmb * fx
    hold = (company_winloss / valid_bet) if valid_bet else None

    section_header('经营摘要', '本期净利润、损益结构与业务线盈利贡献。')
    bcols = st.columns(4)
    show_metric(bcols[0], '平台净盈利（人民币）', fmt_num(net_rmb), help_text='即上方「真实平台净盈利」',
                tone=tone_by_sign(net_rmb))
    show_metric(bcols[1], f'平台净盈利（台币 @{fx:g}）', fmt_num(net_twd),
                tone=tone_by_sign(net_twd))
    show_metric(bcols[2], '有效投注额（流水）', fmt_num(valid_bet))
    show_metric(bcols[3], '整体盈余比例', fmt_pct(hold),
                help_text='公司输赢 ÷ 有效投注额（Hold %）',
                tone='accent')

    other_rev = early_settle + account_adjust + tips + project_adjust
    promo = real_bonus + rebate
    sys_chan = group_share + channel_fee
    agent_net = commission_total - refund

    with st.container(border=True):
        section_header('损益瀑布分析', '绿色为收入项，红色为成本项，蓝色为净利润。')
        wf = go.Figure(go.Waterfall(
            orientation='v',
            measure=['relative', 'relative', 'relative', 'relative', 'relative', 'total'],
            x=['公司输赢', '其他营收', '优惠成本<br>(红利+返水)', '平台费用<br>(系统费+通道费)', '代理佣金<br>(净额)', '净利润'],
            y=[company_winloss, other_rev, -promo, -sys_chan, -agent_net, net_rmb],
            text=[fmt_num(company_winloss), fmt_num(other_rev), fmt_num(-promo),
                  fmt_num(-sys_chan), fmt_num(-agent_net), fmt_num(net_rmb)],
            textposition='outside',
            textfont=dict(size=12),
            connector={'line': {'color': 'rgba(150,170,210,0.30)', 'width': 1}},
            increasing={'marker': {'color': GREEN}},
            decreasing={'marker': {'color': RED}},
            totals={'marker': {'color': BLUE}},
        ))
        wf.update_layout(height=430, template=TEMPLATE, showlegend=False, yaxis_title='金额')
        st.plotly_chart(wf, width='stretch')

    # 哪块业务在赚（BQ 场馆报表，仅在选定单一月份时显示）
    cat = pd.DataFrame()
    if month:
        try:
            vsql = (
                "SELECT `场馆名称` AS venue, "
                "SUM(SAFE_CAST(REPLACE(REPLACE(`公司输赢`,'=\"',''),'\"','') AS FLOAT64)) AS win "
                f"FROM `{BQ_PREFIX}.raw_game_report_venue` "
                f"WHERE `时间` LIKE '{month}%' GROUP BY venue"
            )
            vdf = get_bq_client().query(vsql).to_dataframe()
            if not vdf.empty:
                vdf['类别'] = vdf['venue'].map(_venue_category)
                cat = vdf.groupby('类别', as_index=False)['win'].sum().sort_values('win', ascending=False)
        except Exception:
            cat = pd.DataFrame()

    if not cat.empty:
        with st.container(border=True):
            section_header('业务线盈利贡献', '各场馆类别本期公司输赢（场馆报表口径）。')
            figcat = go.Figure(go.Bar(
                x=cat['类别'], y=cat['win'],
                marker_color=[GREEN if v >= 0 else RED for v in cat['win']],
                text=[fmt_num(v) for v in cat['win']], textposition='outside',
                textfont=dict(size=12),
            ))
            figcat.update_layout(height=360, template=TEMPLATE, showlegend=False, yaxis_title='公司输赢')
            st.plotly_chart(figcat, width='stretch')

    # 月环比（BQ 平台报表）：流水 + 公司输赢
    mom_txt = ''
    bet_mom_pct = None
    win_mom_pct = None
    if month:
        try:
            yy, mm = int(month[:4]), int(month[5:7])
            py, pm = (yy, mm - 1) if mm > 1 else (yy - 1, 12)
            prev_ym = f'{py}-{pm:02d}'
            psql = (
                "SELECT SUBSTR(`日期`,1,7) AS ym, "
                "SUM(SAFE_CAST(REPLACE(REPLACE(`有效投注额`,'=\"',''),'\"','') AS FLOAT64)) AS bet, "
                "SUM(SAFE_CAST(REPLACE(REPLACE(`公司输赢`,'=\"',''),'\"','') AS FLOAT64)) AS win "
                f"FROM `{BQ_PREFIX}.raw_platform_report` "
                f"WHERE SUBSTR(`日期`,1,7) IN ('{month}','{prev_ym}') GROUP BY ym"
            )
            mdf = get_bq_client().query(psql).to_dataframe()
            if len(mdf) == 2:
                mdf = mdf.set_index('ym')
                cb, pb = float(mdf.loc[month, 'bet']), float(mdf.loc[prev_ym, 'bet'])
                if pb:
                    bet_mom_pct = (cb - pb) / pb * 100
                    mom_txt = f' 有效投注额较上月（{prev_ym}）{"▲" if bet_mom_pct >= 0 else "▼"} {abs(bet_mom_pct):.1f}%。'
                cw, pw = float(mdf.loc[month, 'win']), float(mdf.loc[prev_ym, 'win'])
                if pw:
                    win_mom_pct = (cw - pw) / abs(pw) * 100
        except Exception:
            mom_txt = ''

    # 回填顶部核心结论横幅（口径 = 真实平台净盈利，含手动输入项）
    with headline_slot:
        def _kb_delta(p):
            cls = 'kb-up' if p >= 0 else 'kb-down'
            return f'<span class="{cls}">{"▲" if p >= 0 else "▼"} {abs(p):.1f}%</span>'
        _net_color = GREEN if net_rmb >= 0 else RED
        items = [
            f'<span class="kb-main" style="color:{_net_color};">'
            f'{escape(month) if month else "当前范围"} 平台净利润 {fmt_num(net_rmb)}</span>',
            f'<span class="kb-item">约合台币 {fmt_num(net_twd)}</span>',
        ]
        if hold is not None:
            items.append(f'<span class="kb-item">盈余率 {fmt_pct(hold)}</span>')
        if win_mom_pct is not None:
            items.append(f'<span class="kb-item">公司输赢环比 {_kb_delta(win_mom_pct)}</span>')
        if bet_mom_pct is not None:
            items.append(f'<span class="kb-item">流水环比 {_kb_delta(bet_mom_pct)}</span>')
        st.markdown(f'<div class="kpi-banner">{"".join(items)}</div>', unsafe_allow_html=True)

    def _hl(text, color=None):
        style = f'color:{color};font-weight:600;' if color else 'font-weight:600;'
        return f'<span style="{style}">{escape(str(text))}</span>'

    big3 = sorted([('代理佣金', abs(agent_net)), ('红利+返水', abs(promo)),
                   ('系统费+通道费', abs(sys_chan))], key=lambda x: -x[1])
    big3_txt = '、'.join([f'{n} {fmt_num(v)}' for n, v in big3])
    s_scale = (f'本期有效投注额 {_hl(fmt_num(valid_bet))}，公司输赢 {_hl(fmt_num(company_winloss))}'
               + (f'（盈余率 {hold*100:.2f}%）' if hold is not None else '') + '。' + mom_txt)
    s_net = f'扣除各项成本后，平台净利润 {_hl(fmt_num(net_rmb), GREEN)}（约合台币 {_hl(fmt_num(net_twd), GREEN)}）。'
    s_cost = f'主要成本项：{big3_txt}。'
    cat_txt = ''
    if not cat.empty:
        top2 = cat.head(2)
        tot_win = cat['win'].sum()
        if tot_win:
            share = top2['win'].sum() / tot_win
            cat_txt = f'盈利贡献集中于 {_hl("、".join(top2["类别"].tolist()))}，合计约占 {_hl(f"{share*100:.0f}%")}。'
    st.markdown(
        '<div class="hero-card" style="padding:1.1rem 1.4rem;line-height:2.05;">'
        f'<div>{s_scale}</div>'
        f'<div>{s_net}</div>'
        f'<div style="margin-top:0.35rem;color:#9fb0d0;">{s_cost}{(" " + cat_txt) if cat_txt else ""}</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            section_header('经营结果趋势', '公司输赢与公司净收入分开经营规模字段显示，避免量级混在一起。')
            trend_cols = [c for c in ['公司输赢', '公司净收入'] if c in platform.columns]
            if trend_cols and '日期' in platform.columns:
                daily = platform[['日期'] + trend_cols].copy()
                daily['日期'] = to_datetime_safe(daily['日期'])
                daily = daily[daily['日期'].notna()].sort_values('日期')
                daily = daily.groupby('日期', as_index=False)[trend_cols].sum()
                fig = go.Figure()
                if '公司输赢' in daily.columns:
                    fig.add_trace(go.Bar(x=daily['日期'], y=daily['公司输赢'], name='公司输赢', marker_color=BLUE, opacity=0.55))
                if '公司净收入' in daily.columns:
                    fig.add_trace(go.Scatter(x=daily['日期'], y=daily['公司净收入'], name='公司净收入', mode='lines+markers',
                                             line=dict(color=GREEN, width=2.5, shape='spline', smoothing=0.6), marker=dict(size=5)))
                fig.update_layout(
                    height=380,
                    template=TEMPLATE,
                    barmode='overlay',
                    legend=dict(orientation='h', y=-0.18),
                    hovermode='x unified',
                    xaxis_title=None,
                    yaxis_title='金额'
                )
                st.plotly_chart(fig, width='stretch')
    with c2:
        with st.container(border=True):
            section_header('资金流趋势', '字段使用财务报表原始字段。')
            if not finance.empty and '时间' in finance.columns:
                fin = finance.copy()
                fin['时间'] = to_datetime_safe(fin['时间'])
                fin = fin[fin['时间'].notna()].sort_values('时间')
                value_cols = [c for c in ['实际总存款', '实际总提款', '存提差'] if c in fin.columns]
                if value_cols:
                    melted = fin.melt(id_vars='时间', value_vars=value_cols, var_name='指标', value_name='值')
                    fig = px.bar(melted, x='时间', y='值', color='指标', barmode='group', template=TEMPLATE,
                                 color_discrete_sequence=[GREEN, RED, BLUE])
                    fig.update_layout(height=380, legend=dict(orientation='h', y=-0.18), hovermode='x unified',
                                      xaxis_title=None)
                    st.plotly_chart(fig, width='stretch')

    if '有效投注额' in platform.columns and '日期' in platform.columns:
        with st.container(border=True):
            section_header('经营规模趋势', '有效投注额单独显示，避免与经营结果共用一张图。')
            scale_df = platform[['日期', '有效投注额']].copy()
            scale_df['日期'] = to_datetime_safe(scale_df['日期'])
            scale_df = scale_df[scale_df['日期'].notna()].sort_values('日期')
            scale_df = scale_df.groupby('日期', as_index=False)['有效投注额'].sum()
            fig_scale = px.area(scale_df, x='日期', y='有效投注额', template=TEMPLATE)
            fig_scale.update_traces(line_color=CYAN, line_shape='spline', line_smoothing=0.6,
                                    fillcolor='rgba(34,211,238,0.16)')
            fig_scale.update_layout(height=300, hovermode='x unified', showlegend=False, xaxis_title=None, yaxis_title='金额')
            st.plotly_chart(fig_scale, width='stretch')

    c3, c4 = st.columns([1.1, 0.9])
    with c3:
        with st.container(border=True):
            section_header('核心日报明细')
            table_cols = [c for c in ['日期', '公司输赢', '公司净收入', '有效投注额', '注册数', '首存人数'] if c in platform.columns]
            st.dataframe(platform[table_cols].sort_values('日期', ascending=False), width='stretch', hide_index=True)
    with c4:
        with st.container(border=True):
            section_header('成本结构')
            cost_cols = [c for c in ['红利', '返水', '代理佣金'] if c in platform.columns]
            if cost_cols:
                cost_df = pd.DataFrame({'项目': cost_cols, '金额': [safe_sum(platform, c) for c in cost_cols]})
                cost_sum_total = float(cost_df['金额'].sum())
                fig = px.pie(cost_df, names='项目', values='金额', hole=0.58, template=TEMPLATE,
                             color_discrete_sequence=[BLUE, CYAN, PURPLE])
                fig.update_traces(textinfo='percent', textfont_size=12,
                                  marker=dict(line=dict(color='rgba(7,15,30,0.9)', width=2)))
                fig.update_layout(
                    height=310,
                    legend=dict(orientation='h', y=-0.12),
                    annotations=[dict(text=f'总成本<br><b>{fmt_num(cost_sum_total)}</b>',
                                      x=0.5, y=0.5, showarrow=False,
                                      font=dict(size=14, color='#f0f5ff'))],
                )
                st.plotly_chart(fig, width='stretch')
            summary = []
            if '公司输赢' in platform.columns:
                summary.append(f"• 公司输赢：{fmt_num(safe_sum(platform, '公司输赢'))}")
            if '存提差' in platform.columns:
                summary.append(f"• 存提差：{fmt_num(safe_sum(platform, '存提差'))}")
            if '首存人数' in platform.columns and '注册数' in platform.columns and safe_sum(platform, '注册数'):
                summary.append(f"• 首存转化率：{fmt_pct(safe_sum(platform, '首存人数')/safe_sum(platform, '注册数'))}")
            if cost_cols and safe_sum(platform, '公司输赢'):
                cost_total = sum(safe_sum(platform, c) for c in cost_cols)
                summary.append(f"• 成本 / 公司输赢占比：{fmt_pct(cost_total / safe_sum(platform, '公司输赢'))}")
            st.markdown('<div style="color:#aebcd9; line-height:1.9; padding:0.2rem 0.2rem 0.6rem;">' + '<br>'.join(summary) + '</div>', unsafe_allow_html=True)

    render_metric_explainer(['公司输赢', '有效投注额', '实际总存款', '存提差', '首存转化率'])



def render_bonus_analysis():
    bonus = load_table('raw_bonus_report')
    hero('红利分析', '按活动名称、红利类型分析红利发放情况。', latest_imported_at(bonus),
         basis='红利记录（会员管理→VIP记录管理→红利记录·上传）',
         detail=(
             '**分析范围**：红利按活动名称、类型的发放分布、每日趋势与 TOP 领取会员。\n\n'
             '**数据来源**：红利记录（会员管理→VIP记录管理→红利记录，状态＝成功）。\n\n'
             '**计算口径**：区分「代理相关红利」与「真实会员活动红利」。\n\n'
             '**更新方式**：手动上传（按订单号去重，只补新订单）。完整对照见「数据说明」页。'
         ))

    if bonus.empty:
        st.warning('暂无红利数据')
        return

    # Date filter
    if '申请时间' in bonus.columns:
        bonus['申请时间'] = to_datetime_safe(bonus['申请时间'])
        bonus['日期'] = bonus['申请时间'].dt.date

    bonus, start, end, month = date_range_picker(bonus, '申请时间', 'bn', default_last_days=None)

    # 口径与「红利ROI / 代理质量」页一致：只算发放成功的红利（失败/驳回不是成本）
    if '状态' in bonus.columns:
        _before_n = len(bonus)
        bonus = bonus[bonus['状态'].astype(str).str.strip() == '成功'].copy()
        _excluded = _before_n - len(bonus)
        if _excluded:
            st.caption(f'已排除 {_excluded} 笔非「成功」状态的红利（与红利ROI页口径一致，只统计成功发放）。')

    # ── 代理相关红利分类 ──
    all_activity_names = []
    if '活动名称' in bonus.columns:
        all_activity_names = sorted(bonus['活动名称'].dropna().astype(str).unique().tolist())
        all_activity_names = [n for n in all_activity_names if n not in ('', 'nan', 'None')]

    if 'agent_bonus_activities' not in st.session_state:
        st.session_state['agent_bonus_activities'] = []

    # 安全过滤：确保 default 中的值都在当前 options 内
    safe_default = [n for n in st.session_state['agent_bonus_activities'] if n in all_activity_names]

    section_header('代理相关红利分类', '选择属于代理相关的活动名称，用于拆分红利归属并调整经营总览净收入。')
    selected_agent_activities = st.multiselect(
        '选择代理相关红利活动',
        options=all_activity_names,
        default=safe_default,
        key='agent_bonus_activities_select',
        help='选中的活动将被归类为"代理相关红利"，其余为"真实会员活动红利"',
    )
    st.session_state['agent_bonus_activities'] = selected_agent_activities

    # 计算拆分金额
    if selected_agent_activities and '活动名称' in bonus.columns:
        agent_mask = bonus['活动名称'].astype(str).isin(selected_agent_activities)
        agent_bonus_total = float(bonus.loc[agent_mask, '红利金额'].sum()) if '红利金额' in bonus.columns else 0.0
    else:
        agent_bonus_total = 0.0

    # KPIs
    cols = st.columns(4)
    total_amount = safe_sum(bonus, '红利金额')
    total_count = len(bonus)
    unique_members = member_count(bonus)
    avg_per_member = total_amount / unique_members if unique_members else 0
    show_metric(cols[0], '红利总金额', fmt_num(total_amount), tone='warn',
                help_text='成本项，重点监控')
    show_metric(cols[1], '红利笔数', fmt_num(total_count))
    show_metric(cols[2], '领取会员数', fmt_num(unique_members))
    show_metric(cols[3], '人均红利', fmt_num(avg_per_member), tone='accent')

    # 代理 vs 真实会员红利拆分
    if selected_agent_activities:
        real_member_bonus_total = total_amount - agent_bonus_total
        split_cols = st.columns(3)
        show_metric(split_cols[0], '代理相关红利', fmt_num(agent_bonus_total),
                    help_text=f'来自 {len(selected_agent_activities)} 个代理相关活动', tone='warn')
        show_metric(split_cols[1], '真实会员活动红利', fmt_num(real_member_bonus_total),
                    help_text='红利总金额 - 代理相关红利', tone='good')
        if total_amount:
            show_metric(split_cols[2], '代理红利占比', fmt_pct(agent_bonus_total / total_amount),
                        help_text='代理相关红利 / 红利总金额', tone='warn')

    # By activity name
    with st.container(border=True):
        section_header('按活动名称统计')
        if '活动名称' in bonus.columns and '红利金额' in bonus.columns:
            by_activity = bonus.groupby('活动名称', as_index=False).agg(
                红利金额=('红利金额', 'sum'),
                笔数=('红利金额', 'count')
            ).sort_values('红利金额', ascending=False)

            fig = px.bar(by_activity.head(20), x='活动名称', y='红利金额', text='笔数',
                         template=TEMPLATE, color='红利金额', color_continuous_scale='Oranges')
            fig.update_layout(height=420, xaxis_tickangle=-45, coloraxis_showscale=False, xaxis_title=None)
            fig.update_traces(textposition='outside', textfont_size=10)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(by_activity, use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        # By type
        with st.container(border=True):
            section_header('按红利类型分布')
            if '红利类型' in bonus.columns:
                by_type = bonus.groupby('红利类型', as_index=False).agg(
                    红利金额=('红利金额', 'sum'),
                    笔数=('红利金额', 'count')
                ).sort_values('红利金额', ascending=False)
                fig = px.pie(by_type, names='红利类型', values='红利金额', hole=0.58,
                             template=TEMPLATE, color_discrete_sequence=[AMBER, BLUE, PURPLE, CYAN, GREEN, RED])
                fig.update_traces(textinfo='percent', textfont_size=12,
                                  marker=dict(line=dict(color='rgba(7,15,30,0.9)', width=2)))
                fig.update_layout(
                    height=360,
                    legend=dict(orientation='h', y=-0.12),
                    annotations=[dict(text=f'红利<br><b>{fmt_num(float(by_type["红利金额"].sum()))}</b>',
                                      x=0.5, y=0.5, showarrow=False,
                                      font=dict(size=14, color='#f0f5ff'))],
                )
                st.plotly_chart(fig, use_container_width=True)

    with c2:
        # By date trend
        with st.container(border=True):
            section_header('每日红利趋势')
            if '日期' in bonus.columns:
                by_date = bonus.groupby('日期', as_index=False).agg(红利金额=('红利金额', 'sum'))
                by_date = by_date.sort_values('日期')
                fig = px.area(by_date, x='日期', y='红利金额', template=TEMPLATE)
                fig.update_traces(line_color=AMBER, line_shape='spline', line_smoothing=0.6,
                                  fillcolor='rgba(251,191,36,0.14)')
                fig.update_layout(height=360, hovermode='x unified', xaxis_title=None)
                st.plotly_chart(fig, use_container_width=True)

    # TOP members
    with st.container(border=True):
        section_header('TOP 领取会员')
        if '会员账号' in bonus.columns and '红利金额' in bonus.columns:
            top_members = bonus.groupby('会员账号', as_index=False).agg(
                红利金额=('红利金额', 'sum'),
                笔数=('红利金额', 'count'),
                会员等级=('会员等级', 'first')
            ).sort_values('红利金额', ascending=False).head(20)
            st.dataframe(top_members, use_container_width=True, hide_index=True)

    with st.expander('本页指标口径说明', expanded=False):
        st.write('数据来源：raw_bonus_report（红利记录导出）')
        st.write('活动名称：红利标题为空时，自动取用申请备注')
        st.write('仅统计状态=成功的记录')



def render_agent_commission():
    """代理佣金深度分析 — 基于代理佣金单线版 + 团队版两张 BigQuery 表"""
    hero(
        '代理佣金深度分析',
        '基于后台的代理佣金报表（单线版 + 团队版），分析代理产值、赤字分布、手续费净成本与代理层级结构。',
        '',
        basis='代理佣金单线＋团队（代理管理→佣金管理→发放佣金）＋代理结算月报（客服主管提供）',
        detail=(
            '**分析范围**：代理产值与赤字、手续费净成本、代理层级结构，及客服主管月报的结算明细与退成。\n\n'
            '**数据来源**：\n'
            '- 代理佣金（代理管理→佣金管理→发放佣金，切单线／团队，设「佣金月份」，导出 Csv）\n'
            '- 代理结算月报（客服主管提供「X月代理帐.xlsx」，现可拖数据上传页自助入库）\n\n'
            '**更新方式**：佣金按佣金月份手动上传；结算月报拖上传页选月份入库。市代月度见独立「市代月度结算」页。完整对照见「数据说明」页。'
        )
    )
    source_note(
        '后台 <b>代理管理 → 佣金管理 → 发放佣金</b>，切换「<b>单线佣金 / 团队佣金</b>」，'
        '把「佣金月份」选到目标月份 → 按「<b>导出 Csv</b>」下载（单线、团队各导一份）。每月导一次。'
        '<br>导出后**直接拖进面板顶部「🗂 数据上传」页**即可入库（自动识别单线/团队、按月刷新当月、保留其他月，密码 zip 也行）。'
        '<br>对应 BigQuery 表：<code>raw_agent_commission_single</code>（单线）/ '
        '<code>raw_agent_commission_team</code>（团队）。'
    )

    try:
        single = load_table('raw_agent_commission_single')
        team = load_table('raw_agent_commission_team')
    except Exception as e:
        st.error(f'代理佣金数据尚未导入 BigQuery。错误：{e}')
        st.info('运行 `import_agent_commission.py` 导入最新月份数据后再查看此页面。')
        return

    if single.empty:
        st.warning('尚无代理佣金单线版数据')
        return

    months = []
    if '佣金月份' in single.columns:
        months = sorted(single['佣金月份'].dropna().astype(str).unique().tolist())
    month_label = months[-1] if months else '未知'

    # 月份选择器（始终显示，即使只有一个月）
    month_options = months if months else ['未知']
    col_m1, col_m2 = st.columns([1, 4])
    with col_m1:
        sel_month = st.selectbox(
            '📅 佣金月份',
            month_options,
            index=len(month_options) - 1,
            key='ac_month',
            disabled=(len(month_options) <= 1 and month_options[0] == '未知'),
        )
    with col_m2:
        st.markdown(
            f'<div style="padding-top:1.8rem;color:#b6c5e1;">'
            f'当前查看：<b>{sel_month}</b> | 本页共有数据月份：<b>{", ".join(months) if months else "尚未导入"}</b>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.caption('📊 本页上半部（手续费 / 产值赤字 / 层级 / 代理明细）全部用「**代理佣金 单线·团队**」数据，'
               '跟着上面的「佣金月份」走。下半部「客服主管月报」是平哥手动结算（另一份、自己的月份）。'
               '「市代月度」已独立成 🅲 代理/渠道 →「市代月度结算」页。')

    # 月份过滤
    if months and sel_month in months:
        single = single[single['佣金月份'].astype(str) == sel_month].copy()
        team = team[team['佣金月份'].astype(str) == sel_month].copy()
    month_label = sel_month

    st.info(
        f'📌 **重要提示**：此报表的「佣金」字段仅记录系统派发部分；红利派发、兑台等其他派发方式不在内。'
        f'所以"佣金"列常为 0，但"冲正后净输赢"、"上月结余（赤字）"、"手续费基数"等字段是真实数据。'
    )

    # ── 顶部 KPI ─────────────────────────────
    total_agents = len(single)
    active_agents = int((single['冲正后净输赢'].fillna(0) != 0).sum()) if '冲正后净输赢' in single.columns else 0
    total_net = safe_sum(single, '冲正后净输赢')
    deficit_mask = (single['上月结余'].fillna(0) < 0) if '上月结余' in single.columns else None
    deficit_agents = int(deficit_mask.sum()) if deficit_mask is not None else 0
    total_deficit = float(single.loc[deficit_mask, '上月结余'].sum()) if deficit_mask is not None else 0.0
    dep_base = safe_sum(single, '存款手续费基数')
    wd_base = safe_sum(single, '提款手续费基数')
    total_base = dep_base + wd_base
    charged_to_agent = total_base * 0.015
    paid_to_yabo = total_base * 0.016
    platform_extra = total_base * 0.001

    cols = st.columns(4)
    show_metric(cols[0], '代理总数', fmt_num(total_agents), f'活跃 {active_agents}')
    show_metric(cols[1], '冲正后净输赢（总）', fmt_num(total_net), help_text='正值=平台盈利，负值=平台亏损',
                tone=tone_by_sign(total_net))
    show_metric(cols[2], '赤字代理数', fmt_num(deficit_agents), f'合计欠 {fmt_num(total_deficit)}',
                help_text='上月结余 < 0 的代理数量',
                tone='bad' if deficit_agents else None, delta_tone='down' if deficit_agents else 'flat')
    show_metric(cols[3], '手续费净差额（0.1%）', fmt_num(platform_extra),
                f'代理端 {fmt_num(charged_to_agent)} / 系统方 {fmt_num(paid_to_yabo)}',
                help_text='代理手续费 1.5%，系统方手续费 1.6%，差额 0.1%', tone='warn')

    # ── 手续费结构图 ─────────────────────────────
    section_header('手续费结构分析')
    c1, c2 = st.columns([1, 1])
    with c1:
        with st.container(border=True):
            fee_df = pd.DataFrame({
                '类别': ['存款手续费基数', '提款手续费基数'],
                '金额(万)': [dep_base / 10000, wd_base / 10000],
            })
            fig = px.bar(fee_df, x='类别', y='金额(万)', template=TEMPLATE,
                         color='类别', color_discrete_sequence=[BLUE, CYAN])
            fig.update_traces(hovertemplate='%{x}<br>%{y:,.2f} 万<extra></extra>')
            fig.update_yaxes(title_text='金额（万元）')
            fig.update_layout(height=320, showlegend=False, title='存提款手续费基数', xaxis_title=None)
            st.plotly_chart(fig, width='stretch')
    with c2:
        with st.container(border=True):
            compare_df = pd.DataFrame({
                '方向': ['代理端 1.5%', '系统方 1.6%', '差额 0.1%'],
                '金额(万)': [charged_to_agent / 10000, paid_to_yabo / 10000, platform_extra / 10000],
                'color': ['代理端', '系统方', '差额'],
            })
            fig = px.bar(compare_df, x='方向', y='金额(万)', template=TEMPLATE,
                         color='color', color_discrete_map={'代理端': GREEN, '系统方': BLUE, '差额': AMBER})
            fig.update_traces(hovertemplate='%{x}<br>%{y:,.2f} 万<extra></extra>')
            fig.update_yaxes(title_text='金额（万元）')
            fig.update_layout(height=320, showlegend=False, title='手续费结构对比', xaxis_title=None)
            st.plotly_chart(fig, width='stretch')

    st.markdown(
        f'<div class="hero-card" style="margin-top:0.5rem;">'
        f'<div class="hero-title">{month_label} 手续费结构摘要</div>'
        f'<div class="hero-subtitle">'
        f'存提款总基数 <b>{fmt_num(total_base)}</b>；代理端手续费 <b>{fmt_num(charged_to_agent)}</b>，'
        f'系统方手续费 <b>{fmt_num(paid_to_yabo)}</b>，<b style="color:{AMBER}">差额 {fmt_num(platform_extra)}</b>。'
        f'按此速率年化约 <b>{fmt_num(platform_extra * 12)}</b>。'
        f'</div></div>',
        unsafe_allow_html=True
    )

    # ── 代理产值 & 赤字排行 ─────────────────────────────
    section_header('代理产值 vs 赤字排行')
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown('**Top 20 产值代理（按冲正后净输赢，正值=平台盈利）**')
            if {'代理账号', '冲正后净输赢'}.issubset(single.columns):
                pos = single[single['冲正后净输赢'].fillna(0) > 0].copy()
                top = pos.nlargest(20, '冲正后净输赢')[['代理账号', '冲正后净输赢', '下级人数']].sort_values('冲正后净输赢')
                top['净输赢(万)'] = top['冲正后净输赢'] / 10000
                fig = px.bar(top, y='代理账号', x='净输赢(万)', orientation='h', template=TEMPLATE,
                             color='净输赢(万)', color_continuous_scale='Greens',
                             hover_data=['下级人数'])
                fig.update_traces(hovertemplate='代理：%{y}<br>净输赢：%{x:,.2f} 万<extra></extra>')
                fig.update_xaxes(title_text='净输赢（万元）')
                fig.update_layout(height=520, coloraxis_showscale=False)
                st.plotly_chart(fig, width='stretch')
    with c2:
        with st.container(border=True):
            st.markdown('**Top 20 赤字代理（按上月结余欠款）**')
            if {'代理账号', '上月结余'}.issubset(single.columns):
                neg = single[single['上月结余'].fillna(0) < 0].copy()
                worst = neg.nsmallest(20, '上月结余')[['代理账号', '上月结余', '冲正后净输赢']].sort_values('上月结余', ascending=False)
                worst['结余(万)'] = worst['上月结余'] / 10000
                fig = px.bar(worst, y='代理账号', x='结余(万)', orientation='h', template=TEMPLATE,
                             color='结余(万)', color_continuous_scale='Reds_r',
                             hover_data=['冲正后净输赢'])
                fig.update_traces(hovertemplate='代理：%{y}<br>上月结余：%{x:,.2f} 万<extra></extra>')
                fig.update_xaxes(title_text='上月结余（万元）')
                fig.update_layout(height=520, coloraxis_showscale=False)
                st.plotly_chart(fig, width='stretch')

    # ── 赤字分布直方图 ─────────────────────────────
    section_header('赤字代理分布（大客户专账方案的关键数据）')
    c1, c2 = st.columns([2, 1])
    with c1:
        with st.container(border=True):
            if '上月结余' in single.columns:
                neg = single[single['上月结余'].fillna(0) < 0].copy()
                neg['赤字金额(万)'] = -neg['上月结余'] / 10000
                fig = px.histogram(neg, x='赤字金额(万)', nbins=30, template=TEMPLATE,
                                   color_discrete_sequence=[RED])
                fig.update_traces(hovertemplate='赤字区间：%{x} 万<br>代理数：%{y}<extra></extra>')
                fig.update_xaxes(title_text='赤字金额（万元）')
                fig.update_yaxes(title_text='代理数')
                fig.update_layout(height=380, title='赤字金额分布直方图')
                st.plotly_chart(fig, width='stretch')
    with c2:
        with st.container(border=True):
            if '上月结余' in single.columns:
                neg = single[single['上月结余'].fillna(0) < 0].copy()
                bins = [
                    ('< 1w', neg[neg['上月结余'] > -10000]),
                    ('1w-5w', neg[(neg['上月结余'] <= -10000) & (neg['上月结余'] > -50000)]),
                    ('5w-10w', neg[(neg['上月结余'] <= -50000) & (neg['上月结余'] > -100000)]),
                    ('10w+', neg[neg['上月结余'] <= -100000]),
                ]
                bin_df = pd.DataFrame([
                    {'区间': name, '代理数': len(d), '赤字合计': float(d['上月结余'].sum())}
                    for name, d in bins
                ])
                st.markdown('**按赤字规模分区**')
                for _, row in bin_df.iterrows():
                    st.markdown(
                        f'<div style="padding:0.4rem 0.6rem;background:var(--bad-soft);'
                        f'border-left:3px solid var(--bad);margin-bottom:0.4rem;border-radius:4px;">'
                        f'<b>{row["区间"]}</b>：{int(row["代理数"])} 个代理，合计 {fmt_num(row["赤字合计"])}'
                        f'</div>',
                        unsafe_allow_html=True
                    )

    # ── 赤字代理完整名单（可排序 / 搜索 / 下载）─────────────────────────────
    section_header('赤字代理完整名单',
                   '上月结余 < 0 的全部代理。点列头可排序，悬停右上角可搜索 / 下载 CSV。')
    if {'代理账号', '上月结余'}.issubset(single.columns):
        neg = single[single['上月结余'].fillna(0) < 0].copy()
        show_cols = [c for c in ['代理账号', '上月结余', '冲正后净输赢', '下级人数', '活跃人数']
                     if c in neg.columns]
        detail = neg[show_cols].sort_values('上月结余').reset_index(drop=True)
        st.dataframe(detail, width='stretch', hide_index=True)
        st.caption(
            f'共 {len(detail)} 个赤字代理（{month_label}）。默认按欠款最多排在最前；'
            f'点任意列头可改排序，悬停表格右上角的图标可搜索或下载。')
    else:
        st.info('此月份数据缺「代理账号」或「上月结余」字段，无法列出名单。')

    # ── 主副线结构（团队版数据） ─────────────────────────────
    if not team.empty and '线别' in team.columns:
        section_header('代理层级结构（来自团队版数据）')
        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                line_stats = team.groupby('线别').agg(
                    代理数=('代理账号', 'count'),
                    总净输赢=('冲正后净输赢', lambda x: float(x.sum())),
                    总赤字=('上月结余', lambda x: float(x[x < 0].sum())),
                ).reset_index()
                fig = px.bar(line_stats, x='线别', y='代理数', template=TEMPLATE,
                             color='线别', color_discrete_map={'主线': BLUE, '副线': CYAN},
                             title='主线 vs 副线 代理数量')
                fig.update_layout(height=320, xaxis_title=None)
                st.plotly_chart(fig, width='stretch')
        with c2:
            with st.container(border=True):
                line_stats['总净输赢(万)'] = line_stats['总净输赢'] / 10000
                fig = px.bar(line_stats, x='线别', y='总净输赢(万)', template=TEMPLATE,
                             color='线别', color_discrete_map={'主线': BLUE, '副线': CYAN},
                             title='主线 vs 副线 净输赢对比')
                fig.update_traces(hovertemplate='%{x}<br>净输赢：%{y:,.2f} 万<extra></extra>')
                fig.update_yaxes(title_text='净输赢（万元）')
                fig.update_layout(height=320, xaxis_title=None)
                st.plotly_chart(fig, width='stretch')

        if '团队名称' in team.columns:
            with st.container(border=True):
                section_header('Top 10 团队（按净输赢合计）')
                team_agg = team.groupby('团队名称', as_index=False).agg(
                    代理数=('代理账号', 'count'),
                    净输赢=('冲正后净输赢', 'sum'),
                    赤字=('上月结余', lambda x: float(x[x < 0].sum())),
                ).sort_values('净输赢', ascending=False).head(10)
                st.dataframe(team_agg, width='stretch', hide_index=True)

    # ── 代理活跃度分析 ─────────────────────────────
    section_header('代理活跃度分布')
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            if '活跃人数' in single.columns:
                active_dist = single['活跃人数'].fillna(0).astype(int)
                bins = [
                    ('0 人（无活跃）', int((active_dist == 0).sum())),
                    ('1-5 人', int(((active_dist >= 1) & (active_dist <= 5)).sum())),
                    ('6-20 人', int(((active_dist >= 6) & (active_dist <= 20)).sum())),
                    ('21-100 人', int(((active_dist >= 21) & (active_dist <= 100)).sum())),
                    ('100+ 人', int((active_dist > 100).sum())),
                ]
                bin_df = pd.DataFrame(bins, columns=['活跃会员区间', '代理数'])
                fig = px.bar(bin_df, x='活跃会员区间', y='代理数', template=TEMPLATE,
                             color='活跃会员区间', color_discrete_sequence=px.colors.sequential.Tealgrn)
                fig.update_layout(height=320, showlegend=False, title='按名下活跃会员数分档', xaxis_title=None)
                st.plotly_chart(fig, width='stretch')
    with c2:
        with st.container(border=True):
            if '代理类型' in single.columns:
                type_dist = single['代理类型'].value_counts().reset_index()
                type_dist.columns = ['代理类型', '代理数']
                fig = px.pie(type_dist, names='代理类型', values='代理数', template=TEMPLATE,
                             hole=0.55, title='代理类型构成')
                fig.update_traces(textinfo='percent', marker=dict(line=dict(color='rgba(7,15,30,0.9)', width=2)))
                fig.update_layout(height=320)
                st.plotly_chart(fig, width='stretch')
    with c3:
        with st.container(border=True):
            if '是否在团队' in single.columns:
                in_team = single['是否在团队'].astype(str).value_counts().reset_index()
                in_team.columns = ['是否在团队', '代理数']
                fig = px.pie(in_team, names='是否在团队', values='代理数', template=TEMPLATE,
                             hole=0.55, title='是否在团队（散户识别）')
                fig.update_traces(textinfo='percent', marker=dict(line=dict(color='rgba(7,15,30,0.9)', width=2)))
                fig.update_layout(height=320)
                st.plotly_chart(fig, width='stretch')

    # ── 明细表 ─────────────────────────────
    section_header('代理明细（可筛选、可下载）')
    with st.expander('筛选器', expanded=False):
        f1, f2, f3 = st.columns(3)
        df_filter = single.copy()
        with f1:
            if '代理类型' in df_filter.columns:
                df_filter = apply_multiselect(df_filter, '代理类型', '代理类型', 'ac_type')
        with f2:
            if '是否在团队' in df_filter.columns:
                df_filter = apply_multiselect(df_filter, '是否在团队', '是否在团队', 'ac_in_team')
        with f3:
            kw = st.text_input('搜索代理账号或备注', key='ac_kw')
            if kw:
                mask = pd.Series(False, index=df_filter.index)
                for col in ['代理账号', '备注']:
                    if col in df_filter.columns:
                        mask = mask | df_filter[col].astype(str).str.contains(kw, case=False, na=False)
                df_filter = df_filter[mask]

    show_cols = [c for c in [
        '代理账号', '代理类型', '上级账号', '下级人数', '活跃人数', '存款金额', '提款金额',
        '冲正后净输赢', '上月结余', '存款手续费基数', '提款手续费基数', '佣金比例',
        '是否在团队', '是否为主线', '发展人', '备注',
    ] if c in df_filter.columns]

    display_df = df_filter[show_cols].copy()
    if '冲正后净输赢' in display_df.columns:
        display_df = display_df.sort_values('冲正后净输赢', ascending=False)
    st.dataframe(display_df, width='stretch', hide_index=True, height=400)

    csv = display_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button('📥 下载当前筛选结果（CSV）', csv,
                       file_name=f'agent_commission_{month_label}.csv',
                       mime='text/csv')

    # ── 客服主管月报（代理结算手动汇整）─────────────────
    st.markdown('---')
    section_header('客服主管月报 · 代理结算明细',
                   '由客服主管平哥手动汇整，按 8 种适用待遇分类。含累计挂帐、本月发放、退成明细等系统报表外的细节。')

    try:
        settle_summary = load_table('raw_agent_settlement_summary')
        settle_detail = load_table('raw_agent_settlement_detail')
    except Exception as e:
        st.info(f'尚无代理结算手动月报数据。请运行 `import_agent_settlement.py <代理帐.xlsx> <YYYY-MM>` 导入。错误：{e}')
    else:
        if settle_summary.empty and settle_detail.empty:
            st.info('代理结算手动月报：暂无数据。')
        else:
            settle_months = sorted(set(
                settle_summary['月份'].dropna().astype(str).unique().tolist() +
                settle_detail['月份'].dropna().astype(str).unique().tolist()
            ))
            st.caption(f'📌 数据来源：客服主管月报（手动汇整 xlsx 导入），目前涵盖月份：{", ".join(settle_months) if settle_months else "无"}')
            sel_set_month = st.selectbox(
                '📅 代理结算月份',
                settle_months if settle_months else ['无'],
                index=(len(settle_months) - 1) if settle_months else 0,
                key='settle_month',
            )
            sub_sum = settle_summary[settle_summary['月份'].astype(str) == sel_set_month].copy() if not settle_summary.empty else pd.DataFrame()
            sub_det = settle_detail[settle_detail['月份'].astype(str) == sel_set_month].copy() if not settle_detail.empty else pd.DataFrame()

            # 摘要 KPI
            if not sub_sum.empty:
                summary_map = dict(zip(
                    sub_sum['项目'].astype(str).str.replace('⭐️', '', regex=False).str.strip(),
                    sub_sum['金额']
                ))
                ks = st.columns(4)
                show_metric(ks[0], '累计挂帐金额', fmt_num(summary_map.get('累计挂帐金额')),
                            help_text='截至本月底之累计代理挂帐余额（含历史滚结）', tone='warn')
                show_metric(ks[1], '本月新增挂帐', fmt_num(summary_map.get('本月新增挂帐')), tone='warn')
                show_metric(ks[2], '红利佣金派发', fmt_num(summary_map.get('红利佣金派发')))
                show_metric(ks[3], '总计发放', fmt_num(summary_map.get('总计发放')),
                            help_text='本月平台向代理实际派发之佣金 + 红利合计（红利佣金派发 + 佣金派发）',
                            tone='accent')

            # 按 8 种待遇 拆分
            if not sub_det.empty and '适用待遇' in sub_det.columns:
                section_header('按适用待遇分类（笔数 + 实际佣金）')
                by_treatment = sub_det.groupby('适用待遇', as_index=False).agg(
                    笔数=('实际佣金', 'count'),
                    实际佣金=('实际佣金', lambda x: float(pd.to_numeric(x, errors='coerce').fillna(0).sum())),
                ).sort_values('实际佣金', ascending=False)
                c_t1, c_t2 = st.columns([1.2, 1])
                with c_t1:
                    with st.container(border=True):
                        fig = px.bar(by_treatment, x='适用待遇', y='实际佣金',
                                     text='实际佣金', template=TEMPLATE,
                                     color='实际佣金', color_continuous_scale='Tealgrn',
                                     hover_data={'笔数': True, '实际佣金': ':,.0f'})
                        fig.update_layout(height=360, coloraxis_showscale=False, xaxis_tickangle=-15, xaxis_title=None)
                        fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                        st.plotly_chart(fig, width='stretch')
                with c_t2:
                    with st.container(border=True):
                        st.dataframe(by_treatment, width='stretch', hide_index=True)

                # 退成 明细
                rebate = sub_det[sub_det['适用待遇'].astype(str).str.contains('退成', na=False)].copy()
                if not rebate.empty:
                    section_header(f'退成（介绍人佣金分成）明细 — {len(rebate)} 笔',
                                   '详细的引荐关系 / 比例 / 实际派发金额。退成口径见下方「本页指标口径说明」。')
                    rebate_disp = rebate[['名称', '总代账号', '业绩总计', '比例', '实际佣金']].copy()
                    rebate_disp = rebate_disp.sort_values('实际佣金', ascending=False)
                    st.dataframe(
                        rebate_disp, width='stretch', hide_index=True,
                        column_config={
                            '业绩总计': st.column_config.NumberColumn(format='%.2f'),
                            '比例': st.column_config.NumberColumn(format='%.2%'),
                            '实际佣金': st.column_config.NumberColumn(format='%.0f'),
                        },
                    )

            render_metric_explainer(['退成（介绍人佣金分成）'])

    # 市代月度结算已独立成「市代月度结算」页（🅲 代理 / 渠道），本页不再重复。

    with st.expander('本页指标口径说明', expanded=False):
        st.markdown('''
- **数据来源**：`raw_agent_commission_single`（单线版）+ `raw_agent_commission_team`（团队版）+ `raw_agent_settlement_summary` / `raw_agent_settlement_detail`（客服主管手动月报）
- **冲正后净输赢**：代理名下所有会员的净盈亏，**正值=平台盈利，负值=平台亏损**
- **上月结余**：从上月滚下来的赤字/盈余，**负值=代理端尚有赤字待抵扣**
- **手续费 0.1% 净支出**：存款/提款手续费基数 × (1.6% 付系统方 − 1.5% 收代理) 的结构性差额
- **佣金字段限制**：此报表的「佣金」仅含系统派发部分，**不含红利派发/兑台等其他渠道**
- **大客户专账方案**：赤字分布数据直接用于校准 v2 方案的门槛金额
- **客服主管月报**：客服主管平哥手动汇整之 xlsx，含累计挂帐、退成、新代理特殊安排等系统外的细节；月度更新，需手动 import
''')




def render_bonus_roi_agent_quality():
    """红利 ROI & 代理质量 — 6/4 新增 (Miru 决策面板:砍 / 升活动 + 代理筛选)"""
    bonus = load_table('raw_bonus_report')
    agent = load_table('raw_agent_report')

    hero('红利 ROI & 代理质量', '红利成本效率与代理质量分析，支持活动调整与代理管理决策。',
         latest_imported_at(bonus, agent),
         basis='红利记录＋代理报表（后台导出·每月上传）',
         detail=(
             '**分析范围**：红利成本效率（ROI）与代理质量（拉新、首存转化、红利依赖、亏损识别）。\n\n'
             '**数据来源（后台导出 → 上传）**：\n'
             '- 红利记录（会员管理→VIP记录管理→红利记录）\n'
             '- 代理报表（报表中心→代理报表）\n\n'
             '**更新方式**：手动上传。完整对照见「数据说明」页。'
         ))

    if bonus.empty or agent.empty:
        st.warning('暂无 红利 或 代理 数据')
        return

    # 准备数据
    bonus['申请时间'] = to_datetime_safe(bonus['申请时间'])
    bonus['日期'] = bonus['申请时间'].dt.date
    if '状态' in bonus.columns:
        bonus_succ = bonus[bonus['状态'].astype(str) == '成功'].copy()
    else:
        bonus_succ = bonus.copy()
    agent['日期'] = to_datetime_safe(agent['日期']).dt.date

    tabs = st.tabs(['🎯 红利 ROI', '👥 代理质量'])

    # ━━━━━━━━ Tab A: 红利 ROI ━━━━━━━━
    with tabs[0]:
        b_filt, b_start, b_end, _ = date_range_picker(bonus_succ, '申请时间', 'bn_roi', default_last_days=30)
        if b_filt.empty:
            st.info('该范围无红利数据')
        else:
            # KPI
            total_amt = safe_sum(b_filt, '红利金额')
            total_cnt = len(b_filt)
            unique_mem = member_count(b_filt)
            avg_per_mem = total_amt / unique_mem if unique_mem else 0

            # 同日期范围 agent 公司输赢
            if b_start and b_end:
                a_range = agent[(agent['日期'] >= b_start.date()) & (agent['日期'] <= b_end.date())]
            else:
                a_range = agent
            co_winloss = safe_sum(a_range, '公司输赢')
            bonus_share = (total_amt / abs(co_winloss) * 100) if co_winloss else 0
            co_income = safe_sum(a_range, '公司收入')

            c1, c2, c3, c4 = st.columns(4)
            show_metric(c1, '红利总成本', fmt_num(total_amt), tone='warn')
            show_metric(c2, '红利笔数', fmt_num(total_cnt))
            show_metric(c3, '涉及会员数', fmt_num(unique_mem))
            show_metric(c4, '人均红利', fmt_num(avg_per_mem), tone='accent')

            c5, c6 = st.columns(2)
            show_metric(c5, '同期公司输赢', fmt_num(co_winloss),
                        help_text='代理报表口径，正值=平台盈利，负值=平台亏损',
                        tone=tone_by_sign(co_winloss))
            show_metric(c6, '同期公司收入(净)', fmt_num(co_income),
                        help_text='扣除红利/返水/佣金后的净收入',
                        tone=tone_by_sign(co_income))

            # 时间趋势
            with st.container(border=True):
                section_header('每日红利成本 vs 公司收入', '红利成本与净收入的相对趋势。')
                daily_bn = b_filt.groupby('日期', as_index=False)['红利金额'].sum().rename(columns={'红利金额': '红利成本'})
                daily_co = a_range.groupby('日期', as_index=False)['公司收入'].sum().rename(columns={'公司收入': '公司收入(净)'})
                merged = pd.merge(daily_bn, daily_co, on='日期', how='outer').fillna(0).sort_values('日期')
                if not merged.empty:
                    fig = make_subplots(specs=[[{'secondary_y': True}]])
                    fig.add_trace(go.Bar(x=merged['日期'], y=merged['红利成本'], name='红利成本',
                                  marker_color=RED, opacity=0.65), secondary_y=False)
                    fig.add_trace(go.Scatter(x=merged['日期'], y=merged['公司收入(净)'], name='公司收入(净)',
                                  line=dict(color=CYAN, width=2.5, shape='spline', smoothing=0.6),
                                  mode='lines+markers'), secondary_y=True)
                    fig.update_layout(height=400, hovermode='x unified', xaxis_title=None, template=TEMPLATE,
                                      margin=dict(l=40, r=40, t=30, b=40))
                    fig.update_yaxes(title_text='红利成本 (元)', secondary_y=False)
                    fig.update_yaxes(title_text='公司收入 (元)', secondary_y=True)
                    st.plotly_chart(fig, use_container_width=True)

            # 红利类型分布
            if '红利类型' in b_filt.columns:
                section_header('红利类型分布', '按类型分组,看各类成本占比')
                type_grp = b_filt.groupby('红利类型').agg(
                    笔数=('红利金额', 'count'),
                    总金额=('红利金额', 'sum'),
                    会员数=('会员账号', 'nunique')
                ).sort_values('总金额', ascending=False).reset_index()
                type_grp['总金额占比'] = (type_grp['总金额'] / total_amt * 100).round(2).astype(str) + '%'
                type_grp['总金额'] = type_grp['总金额'].round(0)
                st.dataframe(type_grp, use_container_width=True, hide_index=True)

            # 红利标题 Top 30
            if '红利标题' in b_filt.columns:
                section_header('红利标题 Top 30 排行', '按总成本排序，用于识别高成本、低回报的活动。')
                title_grp = b_filt.groupby('红利标题').agg(
                    笔数=('红利金额', 'count'),
                    总金额=('红利金额', 'sum'),
                    平均金额=('红利金额', 'mean'),
                    涉及会员=('会员账号', 'nunique'),
                ).sort_values('总金额', ascending=False).head(30).reset_index()
                title_grp['总金额'] = title_grp['总金额'].round(0)
                title_grp['平均金额'] = title_grp['平均金额'].round(2)
                title_grp['人均红利'] = (title_grp['总金额'] / title_grp['涉及会员'].replace(0, 1)).round(0)
                st.dataframe(title_grp, use_container_width=True, hide_index=True,
                             column_config={
                                 '总金额': st.column_config.NumberColumn(format='%d'),
                                 '平均金额': st.column_config.NumberColumn(format='%.2f'),
                             })

            # 高频领取监测
            section_header('高频领取监测', '单日领取 ≥3 笔的会员（按累计红利降序），可作为流水门槛与风控名单的参考。')
            if '会员账号' in b_filt.columns:
                mem_daily = b_filt.groupby(['会员账号', '日期']).agg(
                    单日笔数=('红利金额', 'count'),
                    单日总额=('红利金额', 'sum')
                ).reset_index()
                multi = mem_daily[mem_daily['单日笔数'] >= 3]
                if multi.empty:
                    st.info('该范围内无单日 >=3 笔的会员')
                else:
                    multi_mem = multi.groupby('会员账号').agg(
                        高频天数=('日期', 'nunique'),
                        累积笔数=('单日笔数', 'sum'),
                        累积红利=('单日总额', 'sum'),
                        最高单日笔数=('单日笔数', 'max'),
                        最高单日金额=('单日总额', 'max')
                    ).sort_values('累积红利', ascending=False).head(30).reset_index()
                    multi_mem['累积红利'] = multi_mem['累积红利'].round(0)
                    multi_mem['最高单日金额'] = multi_mem['最高单日金额'].round(0)
                    st.dataframe(multi_mem, use_container_width=True, hide_index=True)

            # 流水门槛分析
            if '是否需要流水' in b_filt.columns and '流水倍数' in b_filt.columns:
                section_header('流水门槛分析', '识别无流水要求或低流水倍数的红利，评估套利风险敞口。')
                wr_grp = b_filt.groupby(['是否需要流水', '流水倍数']).agg(
                    笔数=('红利金额', 'count'),
                    总金额=('红利金额', 'sum'),
                    平均金额=('红利金额', 'mean')
                ).reset_index().sort_values('总金额', ascending=False).head(25)
                wr_grp['总金额'] = wr_grp['总金额'].round(0)
                wr_grp['平均金额'] = wr_grp['平均金额'].round(2)
                st.dataframe(wr_grp, use_container_width=True, hide_index=True)

            # VIP 等级 × 红利成本
            if '会员等级' in b_filt.columns:
                section_header('VIP 等级 × 红利成本', '各 VIP 等级的红利成本分布。')
                vip_grp = b_filt.groupby('会员等级').agg(
                    笔数=('红利金额', 'count'),
                    总金额=('红利金额', 'sum'),
                    会员数=('会员账号', 'nunique')
                ).reset_index().sort_values('总金额', ascending=False)
                vip_grp['人均红利'] = (vip_grp['总金额'] / vip_grp['会员数'].replace(0, 1)).round(0)
                vip_grp['总金额'] = vip_grp['总金额'].round(0)
                with st.container(border=True):
                    fig = px.bar(vip_grp, x='会员等级', y='总金额',
                                 text='总金额', hover_data=['笔数', '会员数', '人均红利'],
                                 color='总金额', color_continuous_scale='Reds')
                    fig.update_layout(height=380, showlegend=False, margin=dict(l=40, r=20, t=20, b=40), xaxis_title=None)
                    fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                    st.plotly_chart(fig, use_container_width=True)
                st.dataframe(vip_grp, use_container_width=True, hide_index=True)

    # ━━━━━━━━ Tab B: 代理质量 ━━━━━━━━
    with tabs[1]:
        a_filt, a_start, a_end, _ = date_range_picker(agent, '日期', 'ag_q', default_last_days=30)
        if a_filt.empty:
            st.info('该范围无代理数据')
        else:
            # KPI
            total_agents = safe_nunique(a_filt, '代理编号')
            agents_with_signup = a_filt[a_filt['注册人数'] > 0]['代理编号'].nunique() if '注册人数' in a_filt.columns else 0
            total_bonus = safe_sum(a_filt, '红利')
            total_co_income = safe_sum(a_filt, '公司收入')
            total_signup = safe_sum(a_filt, '注册人数')
            total_ftd = safe_sum(a_filt, '首存人数')

            c1, c2, c3, c4 = st.columns(4)
            show_metric(c1, '活跃代理数', fmt_num(total_agents))
            show_metric(c2, '有拉新代理', fmt_num(agents_with_signup))
            show_metric(c3, '累积拉新', fmt_num(total_signup))
            show_metric(c4, '累积首存', fmt_num(total_ftd))

            c5, c6, c7 = st.columns(3)
            show_metric(c5, '代理口径红利成本', fmt_num(total_bonus), tone='warn')
            show_metric(c6, '公司净收入', fmt_num(total_co_income), tone=tone_by_sign(total_co_income))
            cv = total_ftd / total_signup * 100 if total_signup else 0
            show_metric(c7, '注册→首存转化', f'{cv:.1f}%', tone='accent')

            # 代理类型分布
            if '代理类型' in a_filt.columns:
                section_header('代理类型分布', '看各类代理对收入的贡献占比')
                type_grp = a_filt.groupby('代理类型').agg(
                    代理数=('代理编号', 'nunique'),
                    累积注册=('注册人数', 'sum'),
                    累积红利=('红利', 'sum'),
                    累积公司收入=('公司收入', 'sum'),
                ).reset_index().sort_values('累积公司收入', ascending=False)
                st.dataframe(type_grp, use_container_width=True, hide_index=True)

            # 代理聚合 (per 代理)
            if '代理编号' in a_filt.columns:
                group_cols = ['代理编号']
                if '代理名称' in a_filt.columns: group_cols.append('代理名称')
                if '代理类型' in a_filt.columns: group_cols.append('代理类型')
                agg_per_agent = a_filt.groupby(group_cols).agg(
                    累积注册=('注册人数', 'sum'),
                    累积首存=('首存人数', 'sum'),
                    累积投注=('有效投注额', 'sum'),
                    累积红利=('红利', 'sum'),
                    累积返水=('返水', 'sum'),
                    累积公司收入=('公司收入', 'sum'),
                ).reset_index()

                # 红利依赖度 = 红利 / 有效投注
                agg_per_agent['红利依赖度'] = (
                    agg_per_agent['累积红利'] / agg_per_agent['累积投注'].replace(0, 1)
                ).clip(upper=1).round(4)
                active = agg_per_agent[(agg_per_agent['累积注册'] > 0) | (agg_per_agent['累积投注'] > 0)].copy()

                # 散点图: 拉新 vs 公司收入 × 红利依赖度
                if not active.empty:
                    with st.container(border=True):
                        section_header('代理质量散点图', 'X=累积拉新 / Y=累积公司收入 / 颜色=红利依赖度（越红依赖度越高）')
                        scatter_df = active[active['累积注册'] > 0].copy()  # 只画有拉新的
                        if not scatter_df.empty:
                            hover = ['累积首存', '累积投注', '累积红利', '红利依赖度']
                            if '代理名称' in scatter_df.columns: hover.insert(0, '代理名称')
                            fig = px.scatter(
                                scatter_df, x='累积注册', y='累积公司收入',
                                color='红利依赖度',
                                color_continuous_scale='RdYlGn_r',
                                hover_data=hover,
                                height=500
                            )
                            fig.add_hline(y=0, line_dash='dot', line_color='rgba(150,170,210,0.5)')
                            fig.update_layout(margin=dict(l=40, r=40, t=20, b=40))
                            st.plotly_chart(fig, use_container_width=True)

                # 优质代理 Top 20
                section_header('优质代理 Top 20', '按公司净收入降序')
                top_q = active.sort_values('累积公司收入', ascending=False).head(20).copy()
                for c in ['累积投注', '累积红利', '累积返水', '累积公司收入']:
                    if c in top_q.columns:
                        top_q[c] = top_q[c].round(0)
                st.dataframe(top_q, use_container_width=True, hide_index=True)

                # 高红利依赖代理识别
                section_header('高红利依赖代理识别',
                              '红利依赖度 > 0.5（红利金额/投注金额）且 累积公司收入 ≤ 0，建议重点审视。')
                bonus_eaters = active[
                    (active['红利依赖度'] > 0.5) & (active['累积公司收入'] <= 0)
                ].sort_values('累积红利', ascending=False).head(30).copy()
                if bonus_eaters.empty:
                    st.info('未发现高红利依赖代理（标准：红利/投注 > 50% 且 公司收入 ≤ 0）')
                else:
                    for c in ['累积投注', '累积红利', '累积返水', '累积公司收入']:
                        if c in bonus_eaters.columns:
                            bonus_eaters[c] = bonus_eaters[c].round(0)
                    st.dataframe(bonus_eaters, use_container_width=True, hide_index=True)

                # 倒数 20: 公司收入最差代理
                section_header('亏损代理 Bottom 20', '按公司收入升序，亏损额最大的代理。')
                bottom = active.sort_values('累积公司收入').head(20).copy()
                for c in ['累积投注', '累积红利', '累积返水', '累积公司收入']:
                    if c in bottom.columns:
                        bottom[c] = bottom[c].round(0)
                st.dataframe(bottom, use_container_width=True, hide_index=True)

    st.markdown('---')
    with st.expander('ℹ️ 字段说明 / 计算口径'):
        st.markdown('''
- **红利总成本**: 仅含「状态=成功」的红利,失败 / 拒绝不算
- **同期公司收入(净)**: 来自 代理报表 (`raw_agent_report`),已扣红利/返水/佣金后的净收入
- **红利依赖度** = 累积红利 / 累积有效投注额 (越高代表代理拉来的会员靠红利,不靠真投注)
- **高红利依赖代理**: 红利依赖度 > 50% **AND** 公司收入 ≤ 0 (双条件,避免误判高产代理)
- **高频领取会员**: 单日领 >= 3 笔的会员 (按累积红利降序)
- **代理报表** = 每个代理每日 KPIs,这里按选定时间累加
- **数据范围**: 默认显示近 30 天,可在筛选器调整 / 切月
''')



def render_finance_channel():
    hero('存取款分析',
         '充值 / 提款各渠道的成功率、掉单率、平均处理时间。数据存数据库、这页从库里读——'
         '要更新去顶部「数据上传」把后台「存款管理 / 提款管理 历史记录」Csv 拖进去（以后接日报机器人自动更新）。',
         basis='存款/提款历史记录订单（程序每日 11:00 自动抓取）',
         detail=(
             '**分析范围**：充值／提款各渠道的成功率、掉单率、平均处理时间与慢单。\n\n'
             '**数据来源**：财务管理→存款管理／提款管理→历史记录。\n\n'
             '**计算口径**：按「完成时间」统计；处理时长＝完成时间−订单时间（存）／申请时间（提）。\n\n'
             '**更新方式**：程序每日 11:00 自动抓取；亦可于「数据上传」页拖入历史记录 Csv 手动补。完整对照见「数据说明」页。'
         ))
    try:
        dep = load_table('raw_finance_deposit')
    except Exception:
        dep = None
    try:
        wd = load_table('raw_finance_withdraw')
    except Exception:
        wd = None
    if (dep is None or dep.empty) and (wd is None or wd.empty):
        st.info('📭 数据库里还没有存取款数据。\n\n去顶部「数据上传」，把后台「存款管理 / 提款管理 → 历史记录」导出的 Csv 拖进去存一下，再回这页就能看。')
        return
    tab1, tab2 = st.tabs(['💰 充值（存款）', '🏧 提款（取款）'])
    with tab1:
        _fin_deposit_view(dep)
    with tab2:
        _fin_withdraw_view(wd)


