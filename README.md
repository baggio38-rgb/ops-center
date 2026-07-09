# 亿兆智能决策平台 YEIP

Yizhao Enterprise Intelligence Platform

> 让数据成为决策，而不是报表。

## Current Stable Baseline

- V5.3: Data Foundation + Auto Refresh Architecture
- V6.0: Operation Overview prototype
- Next: V6.1 Enterprise UI

## Recommended Branches

- `main`: stable production branch
- `develop`: integration branch
- `feature/v6.1-enterprise-ui`: V6.1 UI refactor
- `feature/member360`: Member 360 module
- `feature/risk-center`: Risk Center module

## Core Principle

1. BigQuery is the single source of truth.
2. Dashboard only displays data, never performs core business calculations.
3. All metrics must be traceable to an Aggregate table.
