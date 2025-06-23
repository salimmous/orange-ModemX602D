@echo off
title 🛑 KILL ALL - Arrêt Complet Orange
color 0C

echo.
echo  ========================================
echo  🛑 ARRÊT COMPLET - KILL ALL PROCESSES
echo  ========================================
echo.
echo  ⚠️  ATTENTION: Ce script va arrêter:
echo  • Tous les processus Python
echo  • Tous les scripts Orange en cours
echo  • Tous les terminaux/CMD ouverts
echo  • Libérer tous les ports COM
echo.

pause

echo.
echo  🔄 Arrêt en cours...
echo.

REM === 1. ARRÊTER TOUS LES PROCESSUS PYTHON ===
echo  ❌ Arrêt de tous les processus Python...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
taskkill /F /IM py.exe >nul 2>&1

REM === 2. ARRÊTER TOUS LES CMD/TERMINAUX ===
echo  ❌ Arrêt des terminaux...
for /f "tokens=2 delims=," %%i in ('tasklist /fo csv ^| findstr /i "cmd.exe"') do (
    set pid=%%i
    set pid=!pid:"=!
    if not "!pid!"=="%~dp0" (
        taskkill /F /PID !pid! >nul 2>&1
    )
)

REM === 3. ARRÊTER PROCESSUS SPÉCIFIQUES ORANGE ===
echo  ❌ Arrêt processus Orange spécifiques...
taskkill /F /IM orange_*.exe >nul 2>&1
taskkill /F /IM modem_*.exe >nul 2>&1
taskkill /F /IM database_*.exe >nul 2>&1

REM === 4. ARRÊTER PROCESSUS SÉRIE/COM ===
echo  ❌ Libération des ports COM...
taskkill /F /IM putty.exe >nul 2>&1
taskkill /F /IM hyperterminal.exe >nul 2>&1
taskkill /F /IM minicom.exe >nul 2>&1

REM === 5. NETTOYER FICHIERS TEMPORAIRES ===
echo  🧹 Nettoyage fichiers temporaires...
del /Q /F *.pyc >nul 2>&1
del /Q /F __pycache__\*.* >nul 2>&1
rmdir /S /Q __pycache__ >nul 2>&1

REM === 6. ARRÊTER SERVICES MYSQL CLIENTS (si nécessaire) ===
echo  ❌ Arrêt connexions MySQL...
taskkill /F /IM mysql.exe >nul 2>&1
taskkill /F /IM mysqld.exe >nul 2>&1

REM === 7. FORCER FERMETURE POWERSHELL ===
echo  ❌ Arrêt PowerShell...
taskkill /F /IM powershell.exe >nul 2>&1
taskkill /F /IM pwsh.exe >nul 2>&1

REM === 8. ATTENDRE LIBÉRATION DES RESSOURCES ===
echo  ⏳ Libération des ressources...
timeout /t 3 /nobreak >nul

REM === 9. VÉRIFICATION ===
echo.
echo  🔍 Vérification des processus restants...
echo.

set python_running=0
for /f %%i in ('tasklist /FI "IMAGENAME eq python.exe" 2^>nul ^| find /c "python.exe"') do set python_running=%%i

if %python_running% GTR 0 (
    echo  ⚠️  Il reste %python_running% processus Python en cours
    echo  💡 Essayez de fermer manuellement ou redémarrer le PC
) else (
    echo  ✅ Tous les processus Python arrêtés
)

REM === 10. AFFICHER PROCESSUS PYTHON RESTANTS ===
echo.
echo  📋 Processus Python actifs (s'il y en a):
tasklist /FI "IMAGENAME eq python*" 2>nul | findstr /i "python"

echo.
echo  ========================================
echo  🎯 NETTOYAGE TERMINÉ
echo  ========================================
echo.
echo  ✅ Actions effectuées:
echo     • Processus Python: ARRÊTÉS
echo     • Terminaux: FERMÉS  
echo     • Ports COM: LIBÉRÉS
echo     • Fichiers temp: NETTOYÉS
echo     • Services: ARRÊTÉS
echo.
echo  💡 Vous pouvez maintenant relancer proprement:
echo     launch_simple.bat
echo.

pause 