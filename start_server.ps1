$ErrorActionPreference = "Stop"

# Edit this only once if your SQL Server details are different.
$env:MSSQL_SERVER = "LAPTOP-SBFLV5MC\SQLEXPRESS"
$env:MSSQL_DATABASE = "AttendancePro"
$env:MSSQL_USER = "sa"
$env:MSSQL_PASSWORD = "Amrendra@12345"

Set-Location "E:\AttendancePro\face_server"

if ($env:MSSQL_PASSWORD -eq "CHANGE_SQL_PASSWORD_HERE") {
    Write-Host "Please open E:\AttendancePro\face_server\start_server.ps1 and replace CHANGE_SQL_PASSWORD_HERE with your SQL Server password." -ForegroundColor Yellow
    Write-Host "Server will start, but MSSQL sync will fail until password is changed." -ForegroundColor Yellow
}

.\venv\Scripts\python.exe main.py
