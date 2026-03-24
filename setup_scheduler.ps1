# KAIRI-SIO-SATELITAL - Setup Windows Task Scheduler
# Ejecutar como Administrador

$ProjectPath = "C:\kairi-sio-satelital"
$PipelineBAT = "$ProjectPath\run_pipeline.bat"
$MonitorBAT  = "$ProjectPath\run_precip_monitor.bat"

Write-Host ""
Write-Host "KAIRI-SIO-SATELITAL - Setup Task Scheduler" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $PipelineBAT)) {
    Write-Host "ERROR: No se encuentra $PipelineBAT" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $MonitorBAT)) {
    Write-Host "ERROR: No se encuentra $MonitorBAT" -ForegroundColor Red
    exit 1
}

$LogsPath = "$ProjectPath\logs"
if (-not (Test-Path $LogsPath)) {
    New-Item -ItemType Directory -Path $LogsPath | Out-Null
    Write-Host "Carpeta logs/ creada" -ForegroundColor Green
}

# Duracion valida para Task Scheduler (10 anos)
$DuracionLarga = (New-TimeSpan -Days 3650)

# TAREA 1 - Pipeline SAR cada 6 dias
Write-Host "Creando tarea: KAIRI-Pipeline-SAR..." -ForegroundColor Yellow

$existe = Get-ScheduledTask -TaskName "KAIRI-Pipeline-SAR" -ErrorAction SilentlyContinue
if ($existe) {
    Unregister-ScheduledTask -TaskName "KAIRI-Pipeline-SAR" -Confirm:$false
}

$ActionPipeline = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$PipelineBAT`"" `
    -WorkingDirectory $ProjectPath

$StartPipeline = (Get-Date).Date.AddDays(1).AddHours(3)
$TriggerPipeline = New-ScheduledTaskTrigger `
    -Once `
    -At $StartPipeline `
    -RepetitionInterval (New-TimeSpan -Days 6) `
    -RepetitionDuration $DuracionLarga

$SettingsPipeline = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 30) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

Register-ScheduledTask `
    -TaskName    "KAIRI-Pipeline-SAR" `
    -Description "KAIRI-SIO-SATELITAL: Ingesta SAR+GPM+NDVI cada 6 dias" `
    -Action      $ActionPipeline `
    -Trigger     $TriggerPipeline `
    -Settings    $SettingsPipeline `
    -RunLevel    Highest | Out-Null

Write-Host "KAIRI-Pipeline-SAR creada OK" -ForegroundColor Green
Write-Host "Proxima ejecucion: $($StartPipeline.ToString('dd/MM/yyyy HH:mm'))" -ForegroundColor Gray

# TAREA 2 - Monitor precipitacion cada 1 hora
Write-Host ""
Write-Host "Creando tarea: KAIRI-Precip-Monitor..." -ForegroundColor Yellow

$existe2 = Get-ScheduledTask -TaskName "KAIRI-Precip-Monitor" -ErrorAction SilentlyContinue
if ($existe2) {
    Unregister-ScheduledTask -TaskName "KAIRI-Precip-Monitor" -Confirm:$false
}

$ActionMonitor = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$MonitorBAT`"" `
    -WorkingDirectory $ProjectPath

$NextHour = (Get-Date).Date.AddHours((Get-Date).Hour + 1)
$TriggerMonitor = New-ScheduledTaskTrigger `
    -Once `
    -At $NextHour `
    -RepetitionInterval (New-TimeSpan -Hours 1) `
    -RepetitionDuration $DuracionLarga

$SettingsMonitor = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

Register-ScheduledTask `
    -TaskName    "KAIRI-Precip-Monitor" `
    -Description "KAIRI-SIO-SATELITAL: Monitor precipitacion GPM cada hora" `
    -Action      $ActionMonitor `
    -Trigger     $TriggerMonitor `
    -Settings    $SettingsMonitor `
    -RunLevel    Highest | Out-Null

Write-Host "KAIRI-Precip-Monitor creada OK" -ForegroundColor Green
Write-Host "Proxima ejecucion: $($NextHour.ToString('dd/MM/yyyy HH:mm'))" -ForegroundColor Gray

# Verificacion
Write-Host ""
Write-Host "Verificacion:" -ForegroundColor Cyan

foreach ($nombre in @("KAIRI-Pipeline-SAR", "KAIRI-Precip-Monitor")) {
    $t = Get-ScheduledTask -TaskName $nombre -ErrorAction SilentlyContinue
    if ($t) {
        $info = Get-ScheduledTaskInfo -TaskName $nombre
        Write-Host "  $nombre" -ForegroundColor Green
        Write-Host "    Estado:  $($t.State)" -ForegroundColor White
        Write-Host "    Proxima: $($info.NextRunTime)" -ForegroundColor White
    } else {
        Write-Host "  $nombre - ERROR no encontrada" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Setup completado." -ForegroundColor Cyan
Write-Host "Para probar ahora mismo:" -ForegroundColor White
Write-Host "  Start-ScheduledTask -TaskName 'KAIRI-Precip-Monitor'" -ForegroundColor Gray
Write-Host ""