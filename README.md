# �� Orange Manager Pro ULTRA-SIMPLE - Version Finale

**Système automatique de traitement USSD avec interface épurée et suppression automatique SMS**

## 🚀 Démarrage Rapide

```bash
# Lancer l'interface principale
launch_simple.bat
```

## 📋 Fonctionnalités Principales

### ⚙️ **Traitement Automatique**
- ✅ **USSD automatique** : `*555*1*nd*1*puk*nom*cin#`
- ✅ **Reprend TOUJOURS depuis A-0** : Même les enregistrements déjà traités qui redeviennent "En Traitement"
- ✅ **Délai professionnel** : 25 secondes entre chaque traitement
- ✅ **Auto-refresh** : Base de données rafraîchie toutes les 2 secondes
- ✅ **Logique simple** : Toute réponse USSD → statut "Traité" + stockage dans sms(9)

### 📱 **SMS Monitoring Renforcé**
- ✅ **Suppression automatique** : SMS supprimés immédiatement après affichage
- ✅ **Vidage SIM au démarrage** : `AT+CMGD=1,4` pour éviter saturation
- ✅ **Lecture forcée** : Scan SMS toutes les 5 secondes
- ✅ **Alertes visuelles** : 🚨 Fenêtre clignote rouge pour nouveaux SMS
- ✅ **Configuration agressive** : `AT+CNMI=2,2,0,1,0` pour réception immédiate

### 🎨 **Interface ULTRA-ÉPURÉE**
- ✅ **Design moderne** : Orange #ff6b35, bleu #3742fa, vert #2ed573
- ✅ **Une seule fenêtre 900x600** : Header simple + contrôles + zone unique
- ✅ **Zone d'affichage unique** : USSD + SMS + logs dans un seul ScrolledText
- ✅ **Contrôles simplifiés** : 2 lignes de boutons essentiels
- ✅ **Stats compactes** : "Total: X | Succès: Y | Erreurs: Z" en une ligne
- ✅ **Statut simple** : "💾 DB: 🟢 | 📡 Modem: 🟢 COM9 | ⚙️ Auto: ▶ EN MARCHE"

## 🗄️ Configuration Base de Données

### **Serveur**
- **Host** : 192.168.3.250
- **Base** : main_raqmicash
- **Table** : identification
- **User** : rwsUserMA

### **Structure Table**
```sql
id(0), date(1), posCode(2), operator(3), nd(4), puk(5), nom(6), cin(7), etats(8), sms(9)
```

### **États**
- `"En Traitement"` → Sera traité automatiquement
- `"Traité"` → Traitement terminé avec réponse stockée

## 📡 Configuration Modem

### **Modem X602D**
- **IMSI autorisé** : 604000944298560
- **Ports prioritaires** : COM9, COM8, COM7, COM6, COM5
- **Baudrate** : 115200
- **Auto-détection** : Scan automatique des ports avec vérification IMSI

### **Commandes AT**
```
AT+CMEE=1          # Mode erreur étendu
AT+CMGF=1          # Mode SMS texte
AT+CNMI=2,2,0,1,0  # Notification SMS immédiate
AT+CMGD=1,4        # Suppression tous SMS au démarrage
```

## 🔧 Fichiers du Projet

### **Fichiers Core**
- `orange_professional_gui.py` - **Interface principale** (50KB)
- `orange_auto_processor.py` - **Processeur automatique** (23KB) 
- `orange_gui_methods.py` - **Méthodes GUI** (21KB)

### **Fichiers Support**
- `launch_simple.bat` - **Lanceur** avec vérification dépendances
- `kill_all.bat` - **Nettoyage complet** (arrêt + libération ports)
- `requirements.txt` - **Dépendances Python**
- `Pilotes Modem X602D/` - **Drivers modem**

## 🛠️ Dépendances

```txt
PyMySQL
pyserial
```

Installation automatique via `launch_simple.bat`

## 🎮 Utilisation

### **Interface Principale**
1. Lancer `launch_simple.bat`
2. Connexion auto DB + Modem
3. Cliquer "DÉMARRER AUTO" 
4. Le système traite automatiquement tous les "En Traitement"

### **Contrôles Interface**
```
Ligne 1: [DÉMARRER AUTO] [Reconnecter] [*555# Solde]
Ligne 2: [Monitor SMS] [Lire SMS] [Vider SIM] [Stats]
```

### **Zone Unique**
- Réponses USSD en temps réel
- SMS reçus avec alertes visuelles
- Logs système
- File d'attente de traitement

## 🚨 Correction Bug Majeur

**PROBLÈME RÉSOLU** : Le système reprenait pas les enregistrements qui redevenaient "En Traitement"

**AVANT** : 
```python
self.processed_records = set()  # Gardait les IDs traités
if record_id not in self.processed_records:  # Ignorait les re-traitements
```

**APRÈS** :
```python
# Plus de filtrage - TOUS les "En Traitement" sont traités
return records  # Reprend TOUJOURS depuis A-0
```

## 🛑 Arrêt du Système

### **Arrêt Normal**
- Bouton "ARRÊTER" dans l'interface
- Fermeture de fenêtre

### **Arrêt Forcé**
```bash
# Arrêt complet + nettoyage
kill_all.bat
```

## 📊 Monitoring

### **Logs en Temps Réel**
- Connexions DB/Modem
- Traitements USSD 
- SMS reçus/envoyés
- Erreurs système

### **Statistiques**
- Total traité
- Taux de succès
- Durée de fonctionnement
- Erreurs rencontrées

## 🔐 Sécurité

- **IMSI fixe** : Seul le modem 604000944298560 est autorisé
- **Vérification automatique** : Contrôle IMSI à chaque connexion
- **Blocage modems non autorisés** : Message d'erreur si mauvais IMSI

## 💡 Fonctionnalités Avancées

- **Countdown timer** : "⏳ Prochain traitement dans 00:25"
- **Auto-reconnexion** : DB et modem en cas de déconnexion
- **Gestion erreurs** : Retry automatique et logs détaillés
- **Interface responsive** : Refresh temps réel sans blocage
- **Suppression SMS auto** : Évite saturation de la SIM

---
**Orange Manager Pro** - Système professionnel de traitement automatique USSD avec interface ultra-épurée et gestion SMS renforcée.