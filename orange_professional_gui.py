#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ORANGE PROFESSIONAL GUI - Interface Professionnelle
Système automatique + Interface moderne + Affichage SMS/USSD en temps réel
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import serial
import serial.tools.list_ports
import re
from datetime import datetime

# Database import
try:
    import pymysql
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

class OrangeProfessionalGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🍊 Orange Professional Manager")
        self.root.geometry("1100x800")
        self.root.configure(bg='#0a0a0a')
        self.root.resizable(True, True)
        
        # Configuration
        self.db_server = "192.168.3.250"
        self.db_name = "main_raqmicash"
        self.db_user = "rwsUserMA"
        self.db_password = "oF90mS@8203e"
        self.fixed_imsi = "604000944298560"
        
        # Variables
        self.db_conn = None
        self.modem = None
        self.auto_running = False
        self.sms_monitoring = False
        self.processed_ids = set()
        
        # Stats
        self.stats = {'total': 0, 'success': 0, 'errors': 0, 'start_time': datetime.now()}
        
        # Create UI
        self.create_interface()
        
        # Auto-connect
        self.root.after(1000, self.auto_connect)
        
        # Auto-refresh every 2 seconds
        self.start_auto_refresh()
        
    def create_interface(self):
        """Create professional interface"""
        # Main container
        main_frame = tk.Frame(self.root, bg='#0a0a0a')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Orange title
        title_frame = tk.Frame(main_frame, bg='#ff6600', height=50)
        title_frame.pack(fill='x', pady=(0, 10))
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="🍊 ORANGE PROFESSIONAL MANAGER", 
                bg='#ff6600', fg='white', 
                font=('Arial', 16, 'bold')).pack(expand=True)
        
        # Connection status
        self.create_connection_panel(main_frame)
        
        # Main content - 3 columns
        content_frame = tk.Frame(main_frame, bg='#0a0a0a')
        content_frame.pack(fill='both', expand=True)
        
        # Left: Auto System
        left_frame = tk.Frame(content_frame, bg='#0a0a0a', width=350)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        self.create_auto_panel(left_frame)
        
        # Center: USSD Professional
        center_frame = tk.Frame(content_frame, bg='#0a0a0a', width=400)
        center_frame.pack(side='left', fill='both', expand=True, padx=5)
        self.create_ussd_professional_panel(center_frame)
        
        # Right: SMS Professional
        right_frame = tk.Frame(content_frame, bg='#0a0a0a', width=350)
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        self.create_sms_professional_panel(right_frame)
        
        # Status bar
        self.create_status_bar(main_frame)
        
    def create_connection_panel(self, parent):
        """Create professional connection panel"""
        conn_frame = tk.LabelFrame(parent, text="🔗 État des Connexions", 
                                 bg='#1a1a1a', fg='#ff6600', 
                                 font=('Arial', 11, 'bold'))
        conn_frame.pack(fill='x', pady=(0, 10))
        
        conn_grid = tk.Frame(conn_frame, bg='#1a1a1a')
        conn_grid.pack(fill='x', padx=10, pady=8)
        
        # Status indicators
        self.db_status = tk.Label(conn_grid, text="🔴 Base de données", 
                                bg='#1a1a1a', fg='#ff3333', 
                                font=('Arial', 10, 'bold'))
        self.db_status.pack(side='left', padx=10)
        
        self.modem_status = tk.Label(conn_grid, text="🔴 Modem", 
                                   bg='#1a1a1a', fg='#ff3333', 
                                   font=('Arial', 10, 'bold'))
        self.modem_status.pack(side='left', padx=10)
        
        self.auto_status = tk.Label(conn_grid, text="⏹ Système arrêté", 
                                  bg='#1a1a1a', fg='#888', 
                                  font=('Arial', 10, 'bold'))
        self.auto_status.pack(side='left', padx=20)
        
        # Control buttons
        btn_frame = tk.Frame(conn_grid, bg='#1a1a1a')
        btn_frame.pack(side='right')
        
        tk.Button(btn_frame, text="🔄 Reconnecter", 
                 bg='#ff6600', fg='white', 
                 font=('Arial', 9, 'bold'),
                 command=self.auto_connect).pack(side='left', padx=5)
        
        self.auto_btn = tk.Button(btn_frame, text="▶ DÉMARRER AUTO", 
                                bg='#00aa00', fg='white', 
                                font=('Arial', 9, 'bold'),
                                command=self.toggle_auto_processing)
        self.auto_btn.pack(side='left', padx=5)
        
    def create_auto_panel(self, parent):
        """Create auto system panel"""
        # Stats
        stats_frame = tk.LabelFrame(parent, text="📊 Statistiques Auto", 
                                  bg='#1a1a1a', fg='#ff6600', 
                                  font=('Arial', 11, 'bold'))
        stats_frame.pack(fill='x', pady=(0, 10))
        
        stats_grid = tk.Frame(stats_frame, bg='#1a1a1a')
        stats_grid.pack(fill='x', padx=10, pady=10)
        
        # Create stats display
        self.create_stat_display(stats_grid, "Total:", "0", 0, 0, 'total_label')
        self.create_stat_display(stats_grid, "Succès:", "0", 0, 1, 'success_label')
        self.create_stat_display(stats_grid, "Erreurs:", "0", 1, 0, 'errors_label')
        self.create_stat_display(stats_grid, "Taux:", "0%", 1, 1, 'rate_label')
        
        # Pending records
        pending_frame = tk.LabelFrame(parent, text="📋 En Attente de Traitement", 
                                    bg='#1a1a1a', fg='#ff6600', 
                                    font=('Arial', 11, 'bold'))
        pending_frame.pack(fill='both', expand=True)
        
        # Control buttons for pending
        control_frame = tk.Frame(pending_frame, bg='#1a1a1a')
        control_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Button(control_frame, text="🔄 Actualiser", 
                 bg='#666', fg='white', 
                 font=('Arial', 8),
                 command=self.refresh_pending).pack(side='left', padx=2)
        
        # Auto-refresh indicator
        self.auto_refresh_indicator = tk.Label(control_frame, text="🟢 Auto 2s", 
                                             bg='#1a1a1a', fg='#00ff00', 
                                             font=('Arial', 8))
        self.auto_refresh_indicator.pack(side='right')
        
        self.pending_display = scrolledtext.ScrolledText(pending_frame, 
                                                       bg='#0a0a0a', fg='#00ff00',
                                                       font=('Consolas', 9),
                                                       height=15)
        self.pending_display.pack(fill='both', expand=True, padx=10, pady=10)
        
    def create_ussd_professional_panel(self, parent):
        """Create professional USSD panel"""
        ussd_frame = tk.LabelFrame(parent, text="📡 USSD Professional", 
                                 bg='#1a1a1a', fg='#ff6600', 
                                 font=('Arial', 11, 'bold'))
        ussd_frame.pack(fill='both', expand=True)
        
        # Quick buttons
        btn_frame = tk.Frame(ussd_frame, bg='#1a1a1a')
        btn_frame.pack(fill='x', padx=10, pady=10)
        
        buttons = [
            ("💰 Solde", "*555#", '#00aa00'),
            ("📊 Crédit", "*100#", '#0066cc'),
            ("📞 Minutes", "*121#", '#aa6600'),
            ("📱 Forfait", "*123#", '#aa0066'),
            ("ℹ️ Info", "*111#", '#666666'),
            ("🎁 Bonus", "*144#", '#cc6600')
        ]
        
        for i, (text, code, color) in enumerate(buttons):
            row = i // 3
            col = i % 3
            btn = tk.Button(btn_frame, text=text, bg=color, fg='white', 
                           font=('Arial', 8, 'bold'),
                           command=lambda c=code: self.send_ussd_manual(c))
            btn.grid(row=row, column=col, padx=2, pady=2, sticky='ew')
        
        for i in range(3):
            btn_frame.columnconfigure(i, weight=1)
        
        # Custom USSD
        custom_frame = tk.Frame(ussd_frame, bg='#1a1a1a')
        custom_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(custom_frame, text="Code USSD:", bg='#1a1a1a', fg='white', 
                font=('Arial', 9)).pack(side='left')
        
        self.ussd_entry = tk.Entry(custom_frame, bg='#2a2a2a', fg='white', 
                                 font=('Arial', 9))
        self.ussd_entry.pack(side='left', fill='x', expand=True, padx=10)
        
        tk.Button(custom_frame, text="📤 Envoyer", 
                 bg='#ff6600', fg='white', 
                 font=('Arial', 9, 'bold'),
                 command=self.send_custom_ussd).pack(side='right')
        
        # USSD Response Display
        response_label = tk.Label(ussd_frame, text="📥 Réponses USSD:", 
                                bg='#1a1a1a', fg='#ff6600', 
                                font=('Arial', 10, 'bold'))
        response_label.pack(anchor='w', padx=10, pady=(10, 5))
        
        self.ussd_display = scrolledtext.ScrolledText(ussd_frame, 
                                                     bg='#0a0a0a', fg='#00ff00',
                                                     font=('Consolas', 9),
                                                     height=12)
        self.ussd_display.pack(fill='both', expand=True, padx=10, pady=10)
        
    def create_sms_professional_panel(self, parent):
        """Create professional SMS panel"""
        sms_frame = tk.LabelFrame(parent, text="📱 SMS Professional", 
                                bg='#1a1a1a', fg='#ff6600', 
                                font=('Arial', 11, 'bold'))
        sms_frame.pack(fill='both', expand=True)
        
        # SMS Controls
        ctrl_frame = tk.Frame(sms_frame, bg='#1a1a1a')
        ctrl_frame.pack(fill='x', padx=10, pady=10)
        
        self.sms_monitor_btn = tk.Button(ctrl_frame, text="▶ Monitor SMS", 
                                       bg='#00aa00', fg='white', 
                                       font=('Arial', 9, 'bold'),
                                       command=self.toggle_sms_monitoring)
        self.sms_monitor_btn.pack(side='left', padx=2)
        
        tk.Button(ctrl_frame, text="📧 Lire Tous", 
                 bg='#0066cc', fg='white', 
                 font=('Arial', 9, 'bold'),
                 command=self.read_all_sms).pack(side='left', padx=2)
        
        tk.Button(ctrl_frame, text="🗑 Supprimer", 
                 bg='#cc3300', fg='white', 
                 font=('Arial', 9, 'bold'),
                 command=self.delete_all_sms).pack(side='left', padx=2)
        
        tk.Button(ctrl_frame, text="🔍 Force Lecture", 
                 bg='#ff6600', fg='white', 
                 font=('Arial', 9, 'bold'),
                 command=self._force_read_all_sms).pack(side='left', padx=2)
        
        # SMS Send
        send_frame = tk.Frame(sms_frame, bg='#1a1a1a')
        send_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(send_frame, text="Numéro:", bg='#1a1a1a', fg='white', 
                font=('Arial', 9)).pack(side='left')
        
        self.phone_entry = tk.Entry(send_frame, bg='#2a2a2a', fg='white', 
                                   font=('Arial', 9), width=15)
        self.phone_entry.pack(side='left', padx=5)
        
        tk.Button(send_frame, text="📤 Envoyer", 
                 bg='#ff6600', fg='white', 
                 font=('Arial', 9, 'bold'),
                 command=self.send_manual_sms).pack(side='right')
        
        # Message text
        self.sms_text = tk.Text(sms_frame, bg='#2a2a2a', fg='white', 
                               font=('Arial', 9), height=3)
        self.sms_text.pack(fill='x', padx=10, pady=5)
        
        # SMS Display
        display_label = tk.Label(sms_frame, text="📥 SMS Reçus & Envoyés:", 
                               bg='#1a1a1a', fg='#ff6600', 
                               font=('Arial', 10, 'bold'))
        display_label.pack(anchor='w', padx=10, pady=(10, 5))
        
        self.sms_display = scrolledtext.ScrolledText(sms_frame, 
                                                   bg='#0a0a0a', fg='#00ff00',
                                                   font=('Consolas', 9),
                                                   height=10)
        self.sms_display.pack(fill='both', expand=True, padx=10, pady=10)
        
    def create_status_bar(self, parent):
        """Create status bar"""
        status_frame = tk.Frame(parent, bg='#1a1a1a', height=25)
        status_frame.pack(fill='x', pady=(10, 0))
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(status_frame, text="🔍 Initialisation...", 
                                   bg='#1a1a1a', fg='#888', 
                                   font=('Arial', 9))
        self.status_label.pack(side='left', padx=10, pady=3)
        
        self.time_label = tk.Label(status_frame, text="", 
                                 bg='#1a1a1a', fg='#888', 
                                 font=('Arial', 9))
        self.time_label.pack(side='right', padx=10, pady=3)
        
        self.update_time()
        
    def create_stat_display(self, parent, label, value, row, col, ref_name):
        """Create stat display item"""
        frame = tk.Frame(parent, bg='#2a2a2a')
        frame.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
        
        tk.Label(frame, text=label, bg='#2a2a2a', fg='#888', 
                font=('Arial', 8)).pack()
        
        value_label = tk.Label(frame, text=value, bg='#2a2a2a', fg='#ff6600', 
                             font=('Arial', 11, 'bold'))
        value_label.pack()
        
        setattr(self, ref_name, value_label)
        parent.columnconfigure(col, weight=1)
        
    def update_time(self):
        """Update time display"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)
        
    def log_message(self, message, msg_type="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WORK": "⚙️", "SMS": "📱", "USSD": "📡"}
        icon = icons.get(msg_type, "ℹ️")
        
        formatted_msg = f"[{timestamp}] {icon} {message}"
        
        # Update status
        self.status_label.config(text=formatted_msg)
        
        # Add to appropriate display
        if msg_type == "SMS":
            self.sms_display.insert(tk.END, f"\n{formatted_msg}\n")
            self.sms_display.see(tk.END)
        elif msg_type == "USSD":
            self.ussd_display.insert(tk.END, f"\n{formatted_msg}\n")
            self.ussd_display.see(tk.END)
        
        self.root.update_idletasks()
        
    # Connection methods (simplified)
    def auto_connect(self):
        """Auto-connect to database and modem"""
        self.log_message("Connexion automatique en cours...")
        threading.Thread(target=self._connect_db, daemon=True).start()
        threading.Thread(target=self._connect_modem, daemon=True).start()

    def _connect_db(self):
        """Connect to database"""
        try:
            if self.db_conn:
                self.db_conn.close()
            
            self.db_conn = pymysql.connect(
                host=self.db_server,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                autocommit=True
            )
            
            self.root.after(0, lambda: self.db_status.config(
                text="🟢 Base de données", fg='#00ff00'))
            self.root.after(0, lambda: self.log_message("Base de données connectée", "SUCCESS"))
            self.root.after(0, self.refresh_pending)
            
        except Exception as e:
            self.root.after(0, lambda: self.db_status.config(
                text="🔴 Base de données", fg='#ff3333'))
            self.root.after(0, lambda: self.log_message(f"Erreur DB: {e}", "ERROR"))

    def _connect_modem(self):
        """Connect to modem"""
        try:
            if self.modem:
                self.modem.close()
                self.modem = None
            
            ports = ["COM9", "COM8", "COM7", "COM6", "COM5"]
            
            for port in ports:
                if self._test_modem_port(port):
                    self.modem = serial.Serial(port, 115200, timeout=3)
                    self.root.after(0, lambda: self.modem_status.config(
                        text=f"🟢 Modem {port}", fg='#00ff00'))
                    self.root.after(0, lambda: self.log_message(f"Modem connecté: {port}", "SUCCESS"))
                    
                    # Start background SMS monitoring automatiquement
                    self.sms_monitoring = True
                    self.sms_monitor_btn.config(text="■ Stop Monitor", bg='#aa0000')
                    
                    # Configurer le modem pour notification SMS
                    try:
                        self.modem.write(b'AT+CNMI=1,2,0,1,0\r\n')
                        time.sleep(0.5)
                    except:
                        pass
                    
                    # Start SMS monitoring automatically
                    self.sms_monitoring = True
                    self.sms_monitor_btn.config(text="■ Stop Monitor", bg='#aa0000')
                    
                    # Configure SMS reception
                    try:
                        self.modem.write(b'AT+CMGF=1\r\n')  # Text mode
                        time.sleep(0.5)
                        self.modem.write(b'AT+CNMI=2,2,0,1,0\r\n')  # Enhanced notifications
                        time.sleep(0.5)
                    except:
                        pass
                    
                    threading.Thread(target=self._sms_background_monitor, daemon=True).start()
                    self.root.after(0, lambda: self.log_message("📱 Monitoring SMS automatique activé", "SMS"))
                    
                    # Force read existing SMS immediately
                    self.root.after(2000, self._force_read_all_sms)  # After 2 seconds
                    
                    return
            
            self.root.after(0, lambda: self.modem_status.config(
                text="🔴 Modem", fg='#ff3333'))
            self.root.after(0, lambda: self.log_message("Aucun modem autorisé trouvé", "ERROR"))
            
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"Erreur modem: {e}", "ERROR"))

    def _test_modem_port(self, port):
        """Test modem port with IMSI verification"""
        try:
            test = serial.Serial(port, 115200, timeout=1)
            test.write(b'AT\r\n')
            time.sleep(0.5)
            resp = test.read(test.in_waiting).decode('utf-8', errors='ignore')
            test.close()
            
            if 'OK' not in resp:
                return False
            
            # Test IMSI
            test = serial.Serial(port, 115200, timeout=2)
            test.write(b'AT+CIMI\r\n')
            time.sleep(1)
            resp = test.read(test.in_waiting).decode('utf-8', errors='ignore')
            test.close()
            
            imsi = re.search(r'\d{15}', resp)
            return imsi and imsi.group() == self.fixed_imsi
            
        except:
            return False

    # Auto processing methods
    def toggle_auto_processing(self):
        """Toggle auto processing"""
        if not self.auto_running:
            if not self.db_conn or not self.modem:
                messagebox.showerror("Erreur", "Connexions requises!")
                return
            
            self.auto_running = True
            self.auto_btn.config(text="⏸ ARRÊTER", bg='#aa0000')
            self.auto_status.config(text="▶ Système EN MARCHE", fg='#00ff00')
            
            threading.Thread(target=self._auto_loop, daemon=True).start()
            self.log_message("Système automatique démarré", "SUCCESS")
        else:
            self.auto_running = False
            self.auto_btn.config(text="▶ DÉMARRER AUTO", bg='#00aa00')
            self.auto_status.config(text="⏹ Système arrêté", fg='#888')
            self.log_message("Système automatique arrêté", "INFO")

    def _auto_loop(self):
        """Main auto processing loop"""
        while self.auto_running:
            try:
                if self.db_conn:
                    cursor = self.db_conn.cursor()
                    cursor.execute("SELECT * FROM identification WHERE etats = 'En Traitement' AND operator = 'Orange'")
                    records = cursor.fetchall()
                    cursor.close()
                    
                    new_records = [r for r in records if r[0] not in self.processed_ids]
                    
                    if new_records:
                        self.root.after(0, lambda: self.log_message(f"Traitement de {len(new_records)} enregistrement(s)", "WORK"))
                        
                        for i, record in enumerate(new_records):
                            if not self.auto_running:
                                break
                            
                            # Professional processing with countdown
                            record_id = record[0]
                            nom = record[6] if len(record) > 6 and record[6] else f"Record {record_id}"
                            
                            success = self._process_record(record)
                            self.stats['total'] += 1
                            
                            if success:
                                self.stats['success'] += 1
                                self.processed_ids.add(record[0])
                            else:
                                self.stats['errors'] += 1
                            
                            self.root.after(0, self._update_stats)
                            
                            # Professional delay with countdown (except for last record)
                            if i < len(new_records) - 1:
                                next_record = new_records[i + 1]
                                next_nom = next_record[6] if len(next_record) > 6 and next_record[6] else f"Record {next_record[0]}"
                                self.root.after(0, lambda: self.add_professional_countdown(25, next_nom))
                                time.sleep(25)  # Délai professionnel de 25 secondes entre records
                
                time.sleep(5)
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"Erreur auto: {e}", "ERROR"))
                time.sleep(10)

    def _process_record(self, record):
        """Process single record - NE CHANGE L'ÉTAT QUE SI TOUT RÉUSSIT"""
        try:
            record_id = record[0]
            # CORRECTION: Structure DB réelle avec colonne "nd"
            nd = record[4] if len(record) > 4 and record[4] else "000000000000000"   # nd à l'index 4
            puk = record[5] if len(record) > 5 and record[5] else "00000000"         # puk à l'index 5  
            nom = record[6] if len(record) > 6 and record[6] else "CLIENT"           # nom à l'index 6
            cin = record[7] if len(record) > 7 and record[7] else "XXXXXX"           # cin à l'index 7
            sms_number = record[9] if len(record) > 9 and record[9] else None        # colonne "sms" à l'index 9
            
            self.root.after(0, lambda: self.log_message(f"🔄 Début traitement: {nom} (ID: {record_id})", "WORK"))
            
            # Build USSD code - LOGIQUE CORRECTE
            ussd_code = f"*555*1*{nd}*1*{puk}*{nom}*{cin}#"
            self.root.after(0, lambda: self.log_message(f"📡 Envoi USSD: {ussd_code}", "USSD"))
            
            # Send USSD and get response
            ussd_response = self._send_ussd(ussd_code)
            
            if not ussd_response:
                # ÉCHEC USSD - NE PAS CHANGER L'ÉTAT
                self.root.after(0, lambda: self.log_message(f"❌ USSD ÉCHEC pour {nom} - État non modifié", "ERROR"))
                return False
            
            # USSD réussi - ANALYSER LA RÉPONSE POUR DÉCIDER L'ÉTAT
            self.root.after(0, lambda: self.log_message(f"✅ USSD reçu pour {nom}: {ussd_response[:50]}...", "USSD"))
            
            # Afficher dans le panneau USSD aussi
            self.root.after(0, lambda: self.ussd_display.insert(tk.END, f"\n🤖 AUTO USSD pour {nom}:\n📡 Code: {ussd_code}\n📥 Réponse: {ussd_response}\n" + "="*60 + "\n"))
            self.root.after(0, lambda: self.ussd_display.see(tk.END))
            
            # LOGIQUE SIMPLIFIÉE: Toute réponse USSD = TRAITÉ
            self.root.after(0, lambda: self.log_message(f"✅ Réponse USSD reçue pour {nom} - Passage à 'Traité'", "SUCCESS"))
            
            # Essayer d'envoyer SMS si numéro disponible
            if sms_number:
                sms_text = f"Reponse Orange:\n{ussd_response}\n\nClient: {nom}\nCIN: {cin}"
                sms_sent = self._send_sms(sms_number, sms_text)
                
                if sms_sent:
                    self.root.after(0, lambda: self.log_message(f"✅ SMS envoyé à {sms_number}", "SMS"))
                    # Afficher SMS envoyé dans le panneau SMS
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    self.root.after(0, lambda: self.sms_display.insert(tk.END, f"\n📤 [{timestamp}] SMS AUTO envoyé à {sms_number}:\n💬 {sms_text}\n" + "-"*50 + "\n"))
                    self.root.after(0, lambda: self.sms_display.see(tk.END))
                else:
                    self.root.after(0, lambda: self.log_message(f"⚠️ SMS ÉCHEC vers {sms_number} - Mais traité quand même", "ERROR"))
            else:
                self.root.after(0, lambda: self.log_message(f"ℹ️ Pas de numéro SMS pour {nom} - Traité quand même", "INFO"))
            
            # STOCKER LA RÉPONSE DANS LA COLONNE SMS + CHANGER VERS "TRAITÉ"
            try:
                cursor = self.db_conn.cursor()
                
                # Stocker la réponse dans la colonne SMS + mettre "Traité"
                cursor.execute("""
                    UPDATE identification 
                    SET etats = %s, sms = %s
                    WHERE id = %s
                """, ("Traité", ussd_response, record_id))
                
                rows_affected = cursor.rowcount
                cursor.close()
                
                if rows_affected > 0:
                    self.root.after(0, lambda: self.log_message(f"✅ État changé: ID {record_id} → 'Traité'", "SUCCESS"))
                    self.root.after(0, lambda: self.log_message(f"💾 Réponse stockée dans colonne SMS", "SUCCESS"))
                    self.root.after(0, lambda: self.log_message(f"🎉 Record {record_id} TRAITÉ avec succès", "SUCCESS"))
                    return True
                else:
                    self.root.after(0, lambda: self.log_message(f"⚠️ Aucune ligne mise à jour pour ID {record_id}", "ERROR"))
                    return False
                    
            except Exception as db_error:
                self.root.after(0, lambda: self.log_message(f"❌ Erreur DB update: {db_error}", "ERROR"))
                return False
            
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"❌ Erreur traitement record {record_id}: {e}", "ERROR"))
            return False

    def _send_ussd(self, code):
        """Send USSD and return response"""
        if not self.modem:
            return None
        
        try:
            self.modem.reset_input_buffer()
            self.modem.write(b'AT+CUSD=1\r\n')
            time.sleep(0.5)
            
            self.modem.reset_input_buffer()
            self.modem.write(f'AT+CUSD=1,"{code}",15\r\n'.encode())
            
            resp = ""
            start = time.time()
            while time.time() - start < 30:
                if self.modem.in_waiting:
                    resp += self.modem.read(self.modem.in_waiting).decode('utf-8', errors='ignore')
                
                if '+CUSD:' in resp:
                    match = re.search(r'\+CUSD:\s*\d+,"([^"]+)"', resp)
                    if match:
                        return match.group(1).replace('\\n', '\n')
                
                time.sleep(0.2)
            
            return None
        except:
            return None

    def _send_sms(self, phone, message):
        """Send SMS"""
        if not self.modem:
            return False
        
        try:
            self.modem.reset_input_buffer()
            self.modem.write(b'AT+CMGF=1\r\n')
            time.sleep(0.5)
            
            self.modem.write(f'AT+CMGS="{phone}"\r\n'.encode())
            time.sleep(1)
            
            self.modem.write((message + '\x1A').encode())
            time.sleep(3)
            
            resp = ""
            start = time.time()
            while time.time() - start < 10:
                if self.modem.in_waiting:
                    resp += self.modem.read(self.modem.in_waiting).decode('utf-8', errors='ignore')
                
                if '+CMGS:' in resp or 'OK' in resp:
                    return True
                
                time.sleep(0.5)
            
            return False
        except:
            return False

    def _update_stats(self):
        """Update statistics display"""
        self.total_label.config(text=str(self.stats['total']))
        self.success_label.config(text=str(self.stats['success']))
        self.errors_label.config(text=str(self.stats['errors']))
        
        if self.stats['total'] > 0:
            rate = (self.stats['success'] / self.stats['total']) * 100
            self.rate_label.config(text=f"{rate:.1f}%")

    def start_auto_refresh(self):
        """Start automatic refresh every 2 seconds"""
        self.auto_refresh_pending()
        self.root.after(2000, self.start_auto_refresh)  # Schedule next refresh in 2 seconds
    
    def auto_refresh_pending(self):
        """Auto refresh pending records and stats"""
        if self.db_conn:
            try:
                # Update pending records count
                cursor = self.db_conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM identification WHERE etats = 'En Traitement' AND operator = 'Orange'")
                pending_count = cursor.fetchone()[0]
                
                # Update processed count  
                cursor.execute("SELECT COUNT(*) FROM identification WHERE etats = 'Traité' AND operator = 'Orange'")
                treated_count = cursor.fetchone()[0]
                
                cursor.close()
                
                # Update status bar with real-time info
                current_time = datetime.now().strftime("%H:%M:%S")
                status_text = f"🔄 Actualisation auto - {current_time} | 📋 En attente: {pending_count} | ✅ Traités: {treated_count}"
                self.status_label.config(text=status_text)
                
                # Auto-refresh pending list if not running auto processing
                if not self.auto_running:
                    self.refresh_pending()
                
            except Exception as e:
                current_time = datetime.now().strftime("%H:%M:%S")
                self.status_label.config(text=f"❌ Erreur actualisation - {current_time}")
        else:
            # No DB connection - show status
            current_time = datetime.now().strftime("%H:%M:%S")
            self.status_label.config(text=f"🔴 Base déconnectée - {current_time}")

    def add_professional_countdown(self, seconds_remaining, record_name):
        """Add professional countdown display"""
        if seconds_remaining > 0:
            mins = seconds_remaining // 60
            secs = seconds_remaining % 60
            countdown_text = f"⏳ Prochain traitement dans {mins:02d}:{secs:02d} (Après: {record_name})"
            self.status_label.config(text=countdown_text)
            self.root.after(1000, lambda: self.add_professional_countdown(seconds_remaining - 1, record_name))

    # Manual USSD methods
    def send_ussd_manual(self, code):
        """Send USSD manually"""
        if not self.modem:
            messagebox.showerror("Erreur", "Modem non connecté")
            return
        
        self.log_message(f"Envoi USSD: {code}", "USSD")
        
        def ussd_thread():
            response = self._send_ussd(code)
            if response:
                self.root.after(0, lambda: self.ussd_display.insert(tk.END, f"\n📡 {code}:\n{response}\n" + "="*50 + "\n"))
                self.root.after(0, lambda: self.ussd_display.see(tk.END))
                self.root.after(0, lambda: self.log_message(f"Réponse USSD reçue: {response[:30]}...", "USSD"))
            else:
                self.root.after(0, lambda: self.log_message("Échec USSD - Pas de réponse", "ERROR"))
        
        threading.Thread(target=ussd_thread, daemon=True).start()

    def send_custom_ussd(self):
        """Send custom USSD"""
        code = self.ussd_entry.get().strip()
        if code:
            self.send_ussd_manual(code)
            self.ussd_entry.delete(0, tk.END)

    # SMS methods
    def toggle_sms_monitoring(self):
        """Toggle SMS monitoring"""
        if not self.sms_monitoring:
            if not self.modem:
                messagebox.showerror("Erreur", "Modem non connecté")
                return
                
            self.sms_monitoring = True
            self.sms_monitor_btn.config(text="■ Stop Monitor", bg='#aa0000')
            
            # Configure modem for SMS reception - IMPROVED
            try:
                # Configuration optimale pour réception SMS
                self.modem.write(b'AT+CMGF=1\r\n')  # Mode texte
                time.sleep(0.5)
                self.modem.write(b'AT+CNMI=2,2,0,1,0\r\n')  # Notifications améliorées
                time.sleep(0.5)
                self.log_message("📱 Configuration SMS améliorée", "SMS")
            except Exception as e:
                self.log_message(f"⚠️ Erreur config SMS: {e}", "ERROR")
            
            # Start background monitoring
            threading.Thread(target=self._sms_background_monitor, daemon=True).start()
            self.log_message("Monitoring SMS activé", "SMS")
        else:
            self.sms_monitoring = False
            self.sms_monitor_btn.config(text="▶ Monitor SMS", bg='#00aa00')
            self.log_message("Monitoring SMS désactivé", "SMS")

    def _sms_background_monitor(self):
        """Background SMS monitoring - AFFICHAGE AUTOMATIQUE COMPLET"""
        self.root.after(0, lambda: self.log_message("🔄 Monitoring SMS en arrière-plan démarré", "SMS"))
        
        while self.sms_monitoring and self.modem:
            try:
                # Vérifier les données reçues
                if self.modem.in_waiting > 0:
                    data = self.modem.read(self.modem.in_waiting).decode('utf-8', errors='ignore')
                    
                    # Afficher tout ce qui arrive
                    if data.strip():
                        self.root.after(0, lambda: self.log_message(f"📥 Données reçues: {data.strip()}", "SMS"))
                    
                    # Check for incoming SMS notification
                    if '+CMTI:' in data:
                        self.root.after(0, lambda: self.log_message("🔔 NOUVEAU SMS DÉTECTÉ!", "SMS"))
                        self.root.after(0, lambda: self._read_new_sms())
                    
                    # Check for direct SMS content
                    if '+CMT:' in data:
                        self.root.after(0, lambda: self._process_direct_sms(data))
                
                # Lecture périodique FORCÉE des SMS - PLUS AGRESSIVE
                if hasattr(self, '_last_sms_check'):
                    if time.time() - self._last_sms_check > 5:  # Vérifier toutes les 5 secondes
                        self.root.after(0, lambda: self._force_read_all_sms())
                        self._last_sms_check = time.time()
                else:
                    self._last_sms_check = time.time()
                
                time.sleep(1)
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"❌ Erreur monitoring SMS: {e}", "ERROR"))
                time.sleep(5)
                break

    def _read_new_sms(self):
        """Read new SMS - AFFICHAGE AUTOMATIQUE"""
        try:
            self.modem.write(b'AT+CMGL="UNREAD"\r\n')
            time.sleep(2)
            
            if self.modem.in_waiting > 0:
                resp = self.modem.read(self.modem.in_waiting).decode('utf-8', errors='ignore')
                
                if '+CMGL:' in resp:
                    self.log_message("📋 Lecture SMS non lus...", "SMS")
                    lines = resp.split('\n')
                    sms_count = 0
                    
                    for i, line in enumerate(lines):
                        if '+CMGL:' in line:
                            match = re.search(r'\+CMGL: (\d+),"([^"]+)","([^"]+)"', line)
                            if match and i + 1 < len(lines):
                                idx, status, sender = match.groups()
                                message = lines[i + 1].strip()
                                
                                # Affichage immédiat et détaillé
                                timestamp = datetime.now().strftime("%H:%M:%S")
                                sms_entry = f"📥 [{timestamp}] SMS #{idx} de {sender}:\n💬 {message}\n" + "-"*50 + "\n"
                                self.sms_display.insert(tk.END, sms_entry)
                                self.sms_display.see(tk.END)
                                
                                # Log aussi
                                self.log_message(f"📥 SMS reçu de {sender}: {message[:30]}...", "SMS")
                                sms_count += 1
                    
                    if sms_count > 0:
                        self.log_message(f"✅ {sms_count} SMS affiché(s)", "SMS")
                else:
                    self.log_message("📭 Aucun SMS non lu", "SMS")
        except Exception as e:
            self.log_message(f"❌ Erreur lecture SMS: {e}", "ERROR")

    def _process_direct_sms(self, data):
        """Process direct SMS from modem data"""
        try:
            # Traiter les SMS qui arrivent directement
            lines = data.split('\n')
            for i, line in enumerate(lines):
                if '+CMT:' in line:
                    # Format: +CMT: "sender","","date","time"
                    match = re.search(r'\+CMT:\s*"([^"]+)"', line)
                    if match and i + 1 < len(lines):
                        sender = match.group(1)
                        message = lines[i + 1].strip()
                        
                        # Affichage immédiat
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        sms_entry = f"📱 [{timestamp}] SMS DIRECT de {sender}:\n💬 {message}\n" + "-"*50 + "\n"
                        self.sms_display.insert(tk.END, sms_entry)
                        self.sms_display.see(tk.END)
                        
                        # Log
                        self.log_message(f"📱 SMS DIRECT de {sender}: {message[:30]}...", "SMS")
        except Exception as e:
            self.log_message(f"❌ Erreur traitement SMS direct: {e}", "ERROR")

    def _check_unread_sms(self):
        """Check for unread SMS periodically"""
        try:
            self.modem.write(b'AT+CMGL="UNREAD"\r\n')
            time.sleep(1)
            
            if self.modem.in_waiting > 0:
                resp = self.modem.read(self.modem.in_waiting).decode('utf-8', errors='ignore')
                
                if '+CMGL:' in resp and resp.count('+CMGL:') > 0:
                    count = resp.count('+CMGL:')
                    self.log_message(f"🔍 Vérification: {count} SMS non lu(s) détecté(s)", "SMS")
                    self._read_new_sms()
        except:
            pass

    def _force_read_all_sms(self):
        """Force read ALL SMS from SIM card - AGGRESSIVE METHOD"""
        if not self.modem:
            return
            
        try:
            # Lecture FORCÉE de tous les SMS (même anciens)
            self.modem.reset_input_buffer()
            self.modem.write(b'AT+CMGL="ALL"\r\n')
            time.sleep(2)
            
            resp = ""
            if self.modem.in_waiting > 0:
                resp = self.modem.read(self.modem.in_waiting).decode('utf-8', errors='ignore')
            
            if '+CMGL:' in resp:
                lines = resp.split('\n')
                sms_found = 0
                
                for i, line in enumerate(lines):
                    if '+CMGL:' in line:
                        # Parser: +CMGL: index,"status","sender","","date","time"
                        parts = line.split(',')
                        if len(parts) >= 3:
                            try:
                                index = parts[0].split(':')[1].strip()
                                status = parts[1].strip('"')
                                sender = parts[2].strip('"')
                                
                                # Message sur la ligne suivante
                                if i + 1 < len(lines):
                                    message = lines[i + 1].strip()
                                    
                                    if message:  # Ignorer les messages vides
                                        timestamp = datetime.now().strftime("%H:%M:%S")
                                        
                                        # Affichage amélioré avec statut
                                        status_icon = "📬" if status == "REC UNREAD" else "📭"
                                        sms_entry = f"\n{status_icon} [{timestamp}] SMS #{index} ({status})\n"
                                        sms_entry += f"📱 De: {sender}\n"
                                        sms_entry += f"💬 Message: {message}\n"
                                        sms_entry += "-" * 60 + "\n"
                                        
                                        self.sms_display.insert(tk.END, sms_entry)
                                        self.sms_display.see(tk.END)
                                        
                                        # ALERTE VISUELLE pour nouveaux SMS
                                        if status == "REC UNREAD":
                                            self.root.after(0, lambda: self._flash_sms_alert())
                                        
                                        sms_found += 1
                                        
                            except Exception as parse_error:
                                self.log_message(f"⚠️ Erreur parsing SMS: {parse_error}", "ERROR")
                
                if sms_found > 0:
                    self.log_message(f"📥 {sms_found} SMS récupéré(s) depuis la SIM", "SMS")
                else:
                    # Même si pas de nouveaux SMS, on affiche qu'on a vérifié
                    current_time = datetime.now().strftime("%H:%M:%S")
                    self.log_message(f"🔍 [{current_time}] Vérification SIM - Aucun nouveau SMS", "SMS")
            else:
                # Aucune réponse SMS
                self.log_message("📭 Aucun SMS sur la SIM", "SMS")
                
        except Exception as e:
            self.log_message(f"❌ Erreur lecture forcée SMS: {e}", "ERROR")

    def _flash_sms_alert(self):
        """Flash visual alert for new SMS"""
        try:
            # Faire clignoter le titre de la fenêtre
            original_title = self.root.title()
            
            # Clignotement de la fenêtre
            for i in range(6):  # 3 cycles de clignotement
                if i % 2 == 0:
                    self.root.title("🚨 NOUVEAU SMS REÇU! 🚨")
                    self.root.configure(bg='#ff3333')  # Rouge
                else:
                    self.root.title("📱 SMS REÇU!")
                    self.root.configure(bg='#0a0a0a')  # Normal
                self.root.update()
                time.sleep(0.3)
            
            # Restaurer titre normal
            self.root.title(original_title)
            self.root.configure(bg='#0a0a0a')
            
            # Log d'alerte
            self.log_message("🚨 NOUVEAU SMS DÉTECTÉ sur la SIM!", "SMS")
            
        except Exception as e:
            self.log_message(f"❌ Erreur alerte SMS: {e}", "ERROR")

    def send_manual_sms(self):
        """Send manual SMS"""
        phone = self.phone_entry.get().strip()
        message = self.sms_text.get(1.0, tk.END).strip()
        
        if not phone or not message:
            messagebox.showwarning("Champs requis", "Numéro et message requis")
            return
        
        if not self.modem:
            messagebox.showerror("Erreur", "Modem non connecté")
            return
        
        self.log_message(f"Envoi SMS vers {phone}", "SMS")
        
        def sms_thread():
            success = self._send_sms(phone, message)
            if success:
                self.root.after(0, lambda: self.sms_display.insert(tk.END, f"\n📤 SMS envoyé à {phone}:\n{message}\n" + "-"*40 + "\n"))
                self.root.after(0, lambda: self.sms_display.see(tk.END))
                self.root.after(0, lambda: self.log_message("SMS envoyé avec succès", "SMS"))
                self.root.after(0, lambda: self.phone_entry.delete(0, tk.END))
                self.root.after(0, lambda: self.sms_text.delete(1.0, tk.END))
            else:
                self.root.after(0, lambda: self.log_message("Échec envoi SMS", "ERROR"))
        
        threading.Thread(target=sms_thread, daemon=True).start()

    def read_all_sms(self):
        """Read all SMS"""
        if not self.modem:
            messagebox.showerror("Erreur", "Modem non connecté")
            return
        
        self.log_message("Lecture de tous les SMS...", "SMS")
        
        def read_thread():
            try:
                self.modem.write(b'AT+CMGL="ALL"\r\n')
                time.sleep(2)
                
                if self.modem.in_waiting > 0:
                    resp = self.modem.read(self.modem.in_waiting).decode('utf-8', errors='ignore')
                    
                    if '+CMGL:' in resp:
                        self.root.after(0, lambda: self.sms_display.insert(tk.END, f"\n📋 TOUS LES SMS:\n{resp}\n" + "="*50 + "\n"))
                        self.root.after(0, lambda: self.sms_display.see(tk.END))
                        self.root.after(0, lambda: self.log_message("SMS lus avec succès", "SMS"))
                    else:
                        self.root.after(0, lambda: self.log_message("Aucun SMS trouvé", "SMS"))
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"Erreur lecture SMS: {e}", "ERROR"))
        
        threading.Thread(target=read_thread, daemon=True).start()

    def delete_all_sms(self):
        """Delete all SMS"""
        if not self.modem:
            messagebox.showerror("Erreur", "Modem non connecté")
            return
        
        if messagebox.askyesno("Confirmation", "Supprimer tous les SMS?"):
            self.log_message("Suppression de tous les SMS...", "SMS")
            
            def delete_thread():
                try:
                    self.modem.write(b'AT+CMGD=0,4\r\n')
                    time.sleep(3)
                    self.root.after(0, lambda: self.log_message("Tous les SMS supprimés", "SMS"))
                except Exception as e:
                    self.root.after(0, lambda: self.log_message(f"Erreur suppression: {e}", "ERROR"))
            
            threading.Thread(target=delete_thread, daemon=True).start()

    def refresh_pending(self):
        """Refresh pending records"""
        if not self.db_conn:
            return
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT * FROM identification WHERE etats = 'En Traitement' AND operator = 'Orange' LIMIT 20")
            records = cursor.fetchall()
            cursor.close()
            
            self.pending_display.delete(1.0, tk.END)
            
            if records:
                self.pending_display.insert(tk.END, "📋 ENREGISTREMENTS EN ATTENTE:\n")
                self.pending_display.insert(tk.END, "="*50 + "\n")
                
                for record in records:
                    record_id = record[0] if len(record) > 0 else "N/A"
                    nom = record[6] if len(record) > 6 else "N/A"        # nom à l'index 6
                    cin = record[7] if len(record) > 7 else "N/A"        # cin à l'index 7
                    sms_number = record[9] if len(record) > 9 else "N/A" # sms à l'index 9
                    
                    entry = f"ID: {record_id} | {nom} | CIN: {cin} | SMS: {sms_number}\n"
                    self.pending_display.insert(tk.END, entry)
                
                self.pending_display.insert(tk.END, "\n" + "="*50)
            else:
                self.pending_display.insert(tk.END, "Aucun enregistrement en attente")
                
        except Exception as e:
            self.log_message(f"Erreur actualisation: {e}", "ERROR")

def main():
    """Main function"""
    if not MYSQL_AVAILABLE:
        print("❌ PyMySQL non installé")
        print("💡 Installez avec: pip install PyMySQL")
        input("Appuyez sur Entrée...")
        return
    
    try:
        app = OrangeProfessionalGUI()
        app.root.mainloop()
    except Exception as e:
        print(f"Erreur: {e}")
        input("Appuyez sur Entrée...")

if __name__ == "__main__":
    main() 