# Windows 安裝與同步

## 1. 需要先安裝

- Git for Windows
- Python 3.11 或更新版本

安裝 Python 時請勾選 `Add Python to PATH`。

## 2. 第一次下載專案

開啟 PowerShell：

```powershell
git clone https://github.com/shou0715-Arthur/Simulation-python-dev.git
cd .\Simulation-python-dev
```

## 3. 安裝 requirements

執行：

```powershell
.\setup_windows.ps1
```

也可以直接雙擊 `setup_windows.bat`。

腳本會：

1. 建立 `.venv` 虛擬環境。
2. 更新 pip。
3. 安裝 `requirements.txt`。
4. 執行 `pip check`。

## 4. 啟動程式

```powershell
.\run_ai_stock.ps1
```

也可以雙擊 `run_ai_stock.bat`。

第一次啟動後，在 GUI 輸入 FinMind 與 Gemini API key，按「儲存 Key」。Key 只會儲存在該電腦專案資料夾內的 `api-key.txt`，不會從 GitHub 下載。

## 5. 日後同步 GitHub 更新

```powershell
.\update_from_github.ps1
```

也可以雙擊 `update_from_github.bat`。更新腳本會執行：

```powershell
git pull --ff-only
.\setup_windows.ps1
```

如果 Git 提示本機有衝突，請先備份 `watchlist.json` 並處理本機修改後再更新。

## 6. 手動安裝方式

若不使用安裝腳本：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```
