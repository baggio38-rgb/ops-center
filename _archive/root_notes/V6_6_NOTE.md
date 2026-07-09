# V6.6 Realtime / Health Split

本版完成監控類頁面拆分：

- 新增 `features/realtime_health.py`
- 從 `features/member_value.py` 搬出 `render_realtime`
- 從 `features/upload_admin.py` 搬出 `render_data_health`
- 更新 `app_pages/member_value.py`、`app_pages/data_admin.py` 的路由 import
- 不改原本 UI 與計算邏輯

測試建議：

1. 會員價值 → 實時波動 & DAU
2. 數據上傳 → 數據健康
3. 其他頁面快速點一次確認導航正常
