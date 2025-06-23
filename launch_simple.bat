@echo off
title 🍊 Orange Professional Manager - Lanceur
color 0E

echo ===============================================
echo         🍊 ORANGE PROFESSIONAL MANAGER
echo ===============================================
echo.
echo 💻 Interface professionnelle avec toutes les fonctionnalités:
echo ✅ Système automatique de traitement
echo ✅ Affichage en temps réel des réponses USSD
echo ✅ Monitoring automatique des SMS reçus
echo ✅ 6 boutons USSD rapides (Solde, Crédit, etc.)
echo ✅ Gestion SMS complète (envoi, lecture, suppression)
echo ✅ Monitoring base de données en temps réel
echo ✅ Statistiques détaillées avec taux de succès
echo ✅ Design Orange professionnel moderne
echo ✅ Sécurité IMSI (604000944298560) 
echo.

:: Fermer toutes les applications Python en cours
echo 🔄 Fermeture des applications Python existantes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1

:: Attendre un peu pour que les ports se libèrent
echo 📡 Libération des ports COM...
timeout /t 3 /nobreak >nul

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installé !
    echo Veuillez installer Python depuis python.org
    pause
    exit /b 1
)

:: Check and install dependencies
echo 📋 Vérification des dépendances...

REM Vérifier PyMySQL
python -c "import pymysql" 2>nul
if errorlevel 1 (
    echo ❌ PyMySQL manquant - Installation...
    pip install PyMySQL
    echo ✅ PyMySQL installé
) else (
    echo ✅ PyMySQL OK
)

REM Vérifier pyserial
python -c "import serial" 2>nul
if errorlevel 1 (
    echo ❌ pyserial manquant - Installation...
    pip install pyserial
    echo ✅ pyserial installé
) else (
    echo ✅ pyserial OK
)

:: Launch the professional interface
echo.
echo 🚀 Lancement de l'interface professionnelle...
echo - Connexion auto à la base de données (192.168.3.250)
echo - Détection auto du modem X602D (COM9, COM8, COM7...)
echo - Vérification IMSI de sécurité
echo - Interface 3 panneaux: Auto + USSD + SMS
echo - Affichage professionnel des réponses
echo.

python orange_professional_gui.py

:: Keep window open if error
if errorlevel 1 (
    echo.
    echo [ERREUR] L'application s'est fermée avec une erreur
    echo 💡 Vérifiez:
    echo    - Que le modem X602D est branché
    echo    - Que la SIM avec IMSI 604000944298560 est insérée
    echo    - Que le serveur 192.168.3.250 est accessible
    pause
) else (
    echo.
    echo ✅ Interface fermée normalement
) 