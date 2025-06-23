# MÉTHODES FONCTIONNELLES POUR ORANGE AUTO GUI
# À ajouter à orange_auto_gui.py

def auto_connect(self):
    """Auto-connect to database and modem"""
    self.log("Connexion automatique en cours...")
    
    # Connect database
    threading.Thread(target=self._connect_db_thread, daemon=True).start()
    
    # Connect modem
    threading.Thread(target=self._connect_modem_thread, daemon=True).start()

def _connect_db_thread(self):
    """Database connection thread"""
    try:
        if self.db_conn:
            try:
                self.db_conn.close()
            except:
                pass
        
        self.db_conn = pymysql.connect(
            host=self.db_server,
            database=self.db_name,
            user=self.db_user,
            password=self.db_password,
            autocommit=True
        )
        
        self.root.after(0, lambda: self.db_indicator.config(
            text="🟢 Base de données", fg='#00ff00'))
        self.root.after(0, lambda: self.log("Base de données connectée", "SUCCESS"))
        self.root.after(0, self.refresh_pending)
        
    except Exception as e:
        self.root.after(0, lambda: self.db_indicator.config(
            text="🔴 Base de données", fg='#ff3333'))
        self.root.after(0, lambda: self.log(f"Erreur DB: {e}", "ERROR"))

def _connect_modem_thread(self):
    """Modem connection thread"""
    try:
        # Close existing
        if self.modem:
            try:
                self.modem.close()
            except:
                pass
            self.modem = None
        
        # Find modem
        ports = ["COM9", "COM8", "COM7", "COM6", "COM5"]
        
        for port in ports:
            if self._test_modem_port(port):
                self.modem = serial.Serial(port, 115200, timeout=3)
                self.root.after(0, lambda: self.modem_indicator.config(
                    text=f"🟢 Modem {port}", fg='#00ff00'))
                self.root.after(0, lambda: self.log(f"Modem connecté: {port}", "SUCCESS"))
                return
        
        self.root.after(0, lambda: self.modem_indicator.config(
            text="🔴 Modem", fg='#ff3333'))
        self.root.after(0, lambda: self.log("Aucun modem trouvé", "ERROR"))
        
    except Exception as e:
        self.root.after(0, lambda: self.log(f"Erreur modem: {e}", "ERROR"))

def _test_modem_port(self, port):
    """Test modem on specific port"""
    try:
        # Test AT
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

def toggle_auto_processing(self):
    """Toggle automatic processing"""
    if not self.auto_running:
        # Start auto processing
        if not self.db_conn:
            messagebox.showerror("Erreur", "Base de données non connectée")
            return
        if not self.modem:
            messagebox.showerror("Erreur", "Modem non connecté")
            return
        
        self.auto_running = True
        self.auto_btn.config(text="⏸ ARRÊTER AUTO", bg='#aa0000')
        self.auto_status.config(text="▶ Système automatique EN MARCHE", fg='#00ff00')
        
        # Start monitoring thread
        threading.Thread(target=self._auto_monitoring_loop, daemon=True).start()
        self.log("Système automatique démarré", "SUCCESS")
        
    else:
        # Stop auto processing
        self.auto_running = False
        self.auto_btn.config(text="▶ DÉMARRER AUTO", bg='#00aa00')
        self.auto_status.config(text="⏹ Système automatique arrêté", fg='#888')
        self.log("Système automatique arrêté", "INFO")

def _auto_monitoring_loop(self):
    """Auto monitoring loop"""
    while self.auto_running:
        try:
            if not self.db_conn:
                time.sleep(10)
                continue
            
            # Get pending records
            pending = self._get_pending_records()
            
            if pending:
                self.root.after(0, lambda: self.log(f"Traitement de {len(pending)} enregistrement(s)", "WORK"))
                
                for record in pending:
                    if not self.auto_running:
                        break
                    
                    self.stats['total'] += 1
                    success = self._process_record_auto(record)
                    
                    if success:
                        self.stats['success'] += 1
                    else:
                        self.stats['errors'] += 1
                    
                    # Update stats display
                    self.root.after(0, self._update_stats_display)
                    
                    time.sleep(3)  # Wait between records
            else:
                time.sleep(5)  # Wait for new records
                
        except Exception as e:
            self.root.after(0, lambda: self.log(f"Erreur monitoring: {e}", "ERROR"))
            time.sleep(10)

def _get_pending_records(self):
    """Get pending records from database"""
    try:
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT * FROM identification WHERE etats = 'En Traitement' AND operator = 'Orange'")
        records = cursor.fetchall()
        cursor.close()
        
        # Filter already processed
        return [r for r in records if r[0] not in self.processed_ids]
    except:
        return []

def _process_record_auto(self, record):
    """Process single record automatically"""
    try:
        record_id = record[0]
        # CORRECTION: structure DB réelle avec "nd"
        nd = record[4] if len(record) > 4 and record[4] else "000000000000000"   # nd à l'index 4
        puk = record[5] if len(record) > 5 and record[5] else "00000000"          # puk à l'index 5
        nom = record[6] if len(record) > 6 and record[6] else "CLIENT"            # nom à l'index 6
        cin = record[7] if len(record) > 7 and record[7] else "XXXXXX"            # cin à l'index 7
        sms_number = record[9] if len(record) > 9 and record[9] else None         # sms à l'index 9
        
        self.root.after(0, lambda: self.log(f"Traitement: {nom} (ID: {record_id})", "WORK"))
        
        # Build and send USSD - LOGIQUE CORRECTE
        ussd = f"*555*1*{nd}*1*{puk}*{nom}*{cin}#"
        ussd_response = self._send_ussd_auto(ussd)
        
        if ussd_response:
            # LOGIQUE SIMPLIFIÉE: Toute réponse = TRAITÉ
            # Send SMS
            if sms_number:
                sms_text = f"Reponse Orange:\n{ussd_response}\n\nClient: {nom}\nCIN: {cin}"
                self._send_sms_auto(sms_number, sms_text)
            
            # Update status + store response in SMS column
            if self._update_record_with_response(record_id, "Traité", ussd_response):
                self.processed_ids.add(record_id)
                self.root.after(0, lambda: self.log(f"Record {record_id} traité avec succès", "SUCCESS"))
                return True
        
        return False
    except:
        return False

def _send_ussd_auto(self, code):
    """Send USSD automatically"""
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
                new_data = self.modem.read(self.modem.in_waiting).decode('utf-8', errors='ignore')
                resp += new_data
            
            if '+CUSD:' in resp:
                match = re.search(r'\+CUSD:\s*\d+,"([^"]+)"', resp)
                if match:
                    return match.group(1).replace('\\n', '\n')
            
            time.sleep(0.2)
        
        return None
    except:
        return None

def _send_sms_auto(self, phone, message):
    """Send SMS automatically"""
    if not self.modem or not phone:
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

def _update_record_status(self, record_id, status):
    """Update record status"""
    try:
        cursor = self.db_conn.cursor()
        cursor.execute("UPDATE identification SET etats = %s WHERE id = %s", (status, record_id))
        cursor.close()
        return True
    except:
        return False

def _update_record_with_response(self, record_id, status, ussd_response):
    """Update record status and store USSD response in SMS column"""
    try:
        cursor = self.db_conn.cursor()
        cursor.execute("""
            UPDATE identification 
            SET etats = %s, sms = %s
            WHERE id = %s
        """, (status, ussd_response, record_id))
        cursor.close()
        return True
    except:
        return False

def _update_stats_display(self):
    """Update statistics display"""
    self.total_label.config(text=str(self.stats['total']))
    self.success_label.config(text=str(self.stats['success']))
    self.errors_label.config(text=str(self.stats['errors']))
    
    if self.stats['total'] > 0:
        rate = (self.stats['success'] / self.stats['total']) * 100
        self.rate_label.config(text=f"{rate:.1f}%")

def send_ussd_manual(self, code):
    """Send USSD manually"""
    if not self.modem:
        messagebox.showerror("Erreur", "Modem non connecté")
        return
    
    self.log(f"Envoi USSD: {code}", "WORK")
    
    def ussd_thread():
        response = self._send_ussd_auto(code)
        if response:
            self.root.after(0, lambda: self.ussd_response.insert(tk.END, f"\n{code}:\n{response}\n" + "="*50 + "\n"))
            self.root.after(0, lambda: self.ussd_response.see(tk.END))
            self.root.after(0, lambda: self.log("Réponse USSD reçue", "SUCCESS"))
        else:
            self.root.after(0, lambda: self.log("Échec USSD", "ERROR"))
    
    threading.Thread(target=ussd_thread, daemon=True).start()

def send_custom_ussd(self):
    """Send custom USSD"""
    code = self.ussd_entry.get().strip()
    if code:
        self.send_ussd_manual(code)
        self.ussd_entry.delete(0, tk.END)

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
    
    self.log(f"Envoi SMS vers {phone}", "WORK")
    
    def sms_thread():
        success = self._send_sms_auto(phone, message)
        if success:
            self.root.after(0, lambda: self.log("SMS envoyé avec succès", "SUCCESS"))
            self.root.after(0, lambda: self.phone_entry.delete(0, tk.END))
            self.root.after(0, lambda: self.sms_text.delete(1.0, tk.END))
        else:
            self.root.after(0, lambda: self.log("Échec envoi SMS", "ERROR"))
    
    threading.Thread(target=sms_thread, daemon=True).start()

def read_sms(self):
    """Read SMS messages"""
    if not self.modem:
        messagebox.showerror("Erreur", "Modem non connecté")
        return
    
    self.log("Lecture des SMS...", "WORK")
    
    def read_thread():
        try:
            self.modem.write(b'AT+CMGL="ALL"\r\n')
            time.sleep(2)
            
            resp = ""
            if self.modem.in_waiting:
                resp = self.modem.read(self.modem.in_waiting).decode('utf-8', errors='ignore')
            
            if '+CMGL:' in resp:
                self.root.after(0, lambda: self.log("SMS trouvés", "SUCCESS"))
                # Parse and display SMS here
            else:
                self.root.after(0, lambda: self.log("Aucun SMS", "INFO"))
        except Exception as e:
            self.root.after(0, lambda: self.log(f"Erreur lecture SMS: {e}", "ERROR"))
    
    threading.Thread(target=read_thread, daemon=True).start()

def delete_sms(self):
    """Delete all SMS"""
    if not self.modem:
        messagebox.showerror("Erreur", "Modem non connecté")
        return
    
    if messagebox.askyesno("Confirmation", "Supprimer tous les SMS?"):
        self.log("Suppression SMS...", "WORK")
        
        def delete_thread():
            try:
                self.modem.write(b'AT+CMGD=0,4\r\n')
                time.sleep(3)
                self.root.after(0, lambda: self.log("SMS supprimés", "SUCCESS"))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Erreur suppression: {e}", "ERROR"))
        
        threading.Thread(target=delete_thread, daemon=True).start()

def test_sms(self):
    """Test SMS functionality"""
    test_msg = f"Test SMS Orange Auto Manager - {datetime.now().strftime('%H:%M:%S')}"
    self.phone_entry.delete(0, tk.END)
    self.phone_entry.insert(0, "+212600000000")  # Default test number
    self.sms_text.delete(1.0, tk.END)
    self.sms_text.insert(1.0, test_msg)

def refresh_pending(self):
    """Refresh pending records display"""
    if not self.db_conn:
        return
    
            try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT * FROM identification WHERE etats = 'En Traitement' AND operator = 'Orange' LIMIT 20")
            records = cursor.fetchall()
            cursor.close()
        
        # Clear and update display
        self.pending_scroll.delete(1.0, tk.END)
        
        if records:
            for record in records:
                record_id = record[0] if len(record) > 0 else "N/A"
                nom = record[3] if len(record) > 3 else "N/A"
                cin = record[4] if len(record) > 4 else "N/A"
                phone = record[5] if len(record) > 5 else "N/A"
                etat = record[6] if len(record) > 6 else "En Traitement"
                
                line = f"{record_id:<8} {nom:<15} {cin:<12} {phone:<15} {etat}\n"
                self.pending_scroll.insert(tk.END, line)
        else:
            self.pending_scroll.insert(tk.END, "Aucun enregistrement en attente\n")
            
    except Exception as e:
        self.log(f"Erreur actualisation: {e}", "ERROR")

def show_detailed_stats(self):
    """Show detailed statistics"""
    runtime = datetime.now() - self.stats['start_time']
    
    stats_text = f"""
📊 STATISTIQUES DÉTAILLÉES

⏱️ Durée de fonctionnement: {runtime}
📈 Total traité: {self.stats['total']}
✅ Succès: {self.stats['success']}
❌ Erreurs: {self.stats['errors']}

"""
    
    if self.stats['total'] > 0:
        rate = (self.stats['success'] / self.stats['total']) * 100
        stats_text += f"📊 Taux de succès: {rate:.1f}%\n"
        avg_time = runtime.total_seconds() / self.stats['total']
        stats_text += f"⚡ Temps moyen par traitement: {avg_time:.1f}s\n"
    
    messagebox.showinfo("Statistiques Détaillées", stats_text)

def refresh_db_info(self):
    """Refresh database information"""
    if not self.db_conn:
        self.db_info.delete(1.0, tk.END)
        self.db_info.insert(tk.END, "Base de données non connectée")
        return
    
    try:
        cursor = self.db_conn.cursor()
        
        # Get table info
        cursor.execute("SELECT COUNT(*) FROM identification")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM identification WHERE etats = 'En Traitement' AND operator = 'Orange'")
        pending = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM identification WHERE etats = 'Traité' AND operator = 'Orange'")
        processed = cursor.fetchone()[0]
        
        cursor.close()
        
        info_text = f"""
Table: identification
Total enregistrements: {total}
En traitement: {pending}
Traités: {processed}

Dernière mise à jour: {datetime.now().strftime('%H:%M:%S')}
"""
        
        self.db_info.delete(1.0, tk.END)
        self.db_info.insert(tk.END, info_text)
        
    except Exception as e:
        self.db_info.delete(1.0, tk.END)
        self.db_info.insert(tk.END, f"Erreur: {e}")

def analyze_table(self):
    """Analyze identification table"""
    if not self.db_conn:
        messagebox.showerror("Erreur", "Base de données non connectée")
        return
    
    try:
        cursor = self.db_conn.cursor()
        
        # Get detailed stats
        cursor.execute("SELECT etats, COUNT(*) FROM identification GROUP BY etats")
        states = cursor.fetchall()
        
        cursor.execute("DESCRIBE identification")
        columns = cursor.fetchall()
        
        cursor.close()
        
        analysis = "📊 ANALYSE TABLE IDENTIFICATION\n\n"
        analysis += "Structure:\n"
        for col in columns:
            analysis += f"  • {col[0]} ({col[1]})\n"
        
        analysis += "\nRépartition par état:\n"
        for state in states:
            analysis += f"  • {state[0]}: {state[1]} enregistrements\n"
        
        messagebox.showinfo("Analyse Table", analysis)
        
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur analyse: {e}")

def cleanup_processed(self):
    """Cleanup processed records"""
    if not self.db_conn:
        messagebox.showerror("Erreur", "Base de données non connectée")
        return
    
    if messagebox.askyesno("Confirmation", "Supprimer les enregistrements 'Traité'?"):
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("DELETE FROM identification WHERE etats = 'Traité'")
            affected = cursor.rowcount
            cursor.close()
            
            messagebox.showinfo("Succès", f"{affected} enregistrements supprimés")
            self.refresh_db_info()
            self.refresh_pending()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur suppression: {e}")

def execute_sql(self):
    """Execute custom SQL query"""
    query = self.sql_entry.get().strip()
    if not query:
        messagebox.showwarning("Requête vide", "Entrez une requête SQL")
        return
    
    if not self.db_conn:
        messagebox.showerror("Erreur", "Base de données non connectée")
        return
    
    try:
        cursor = self.db_conn.cursor()
        cursor.execute(query)
        
        if query.strip().upper().startswith(('SELECT', 'SHOW', 'DESCRIBE')):
            results = cursor.fetchall()
            
            result_text = f"Requête: {query}\n"
            result_text += f"Résultats ({len(results)} lignes):\n"
            result_text += "=" * 50 + "\n"
            
            for i, row in enumerate(results[:50], 1):
                result_text += f"{i}: {row}\n"
            
            if len(results) > 50:
                result_text += f"... et {len(results) - 50} autres lignes\n"
        else:
            affected = cursor.rowcount
            result_text = f"Requête exécutée: {affected} ligne(s) affectée(s)"
        
        cursor.close()
        
        self.sql_result.delete(1.0, tk.END)
        self.sql_result.insert(tk.END, result_text)
        
    except Exception as e:
        self.sql_result.delete(1.0, tk.END)
        self.sql_result.insert(tk.END, f"Erreur SQL: {e}")

def clear_log(self):
    """Clear activity log"""
    self.activity_log.delete(1.0, tk.END)
    self.log("Journal effacé", "INFO") 