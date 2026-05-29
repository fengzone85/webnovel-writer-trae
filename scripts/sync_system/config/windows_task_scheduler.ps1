# Windows 任务计划程序配置
# 使用方法:
# 1. 以管理员身份打开 PowerShell
# 2. 运行: schtasks /create /tn "WebnovelWriterSync" /tr "python.exe E:\小说\.trae\skills\webnovel-writer\scripts\sync_system\sync_system.py run" /sc daily /st 03:00 /f
# 3. 或使用下面的 PowerShell 脚本创建任务

# =============================================================================
# 任务计划程序 - 创建每日同步任务
# =============================================================================

$taskName = "WebnovelWriterSync"
$pythonExe = "python.exe"
$scriptPath = "E:\小说\.trae\skills\webnovel-writer\scripts\sync_system\sync_system.py"
$workingDir = "E:\小说\.trae\skills\webnovel-writer\scripts\sync_system"
$time = "03:00"

# 创建每周任务 (每周一 03:00)
schtasks /create /tn $taskName /tr "$pythonExe `"$scriptPath`" run" /sc weekly /d Monday /st $time /f

Write-Host "任务 '$taskName' 已创建" -ForegroundColor Green
Write-Host "每天 $time 执行同步" -ForegroundColor Cyan

# =============================================================================
# 任务计划程序 - 创建每周同步任务 (可选)
# =============================================================================

$weeklyTaskName = "WebnovelWriterSyncWeekly"
$dayOfWeek = "Sunday"

# 创建每周任务
schtasks /create /tn $weeklyTaskName /tr "$pythonExe `"$scriptPath`" run --force" /sc weekly /d $dayOfWeek /st $time /f

Write-Host "每周任务 '$weeklyTaskName' 已创建" -ForegroundColor Green

# =============================================================================
# 查看任务列表
# =============================================================================

Write-Host "`n当前任务列表:" -ForegroundColor Yellow
schtasks /query /fo LIST /tn $taskName

# =============================================================================
# 删除任务 (如需删除)
# =============================================================================

# schtasks /delete /tn $taskName /f
# schtasks /delete /tn $weeklyTaskName /f
