@echo off
rem Traudi - Einrichtung fuer Entwickler (Windows).
rem
rem Windows verbietet das Ausfuehren von PowerShell-Skripten standardmaessig
rem (ExecutionPolicy "Restricted"). Diese Datei umgeht das nur fuer diesen einen
rem Aufruf, ohne eine Systemeinstellung dauerhaft zu aendern.
rem
rem   setup.bat            CPU-Variante
rem   setup.bat -Cuda      mit CUDA 12.8
rem   setup.bat -NoModels  ohne Modell-Download

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1" %*
exit /b %ERRORLEVEL%
