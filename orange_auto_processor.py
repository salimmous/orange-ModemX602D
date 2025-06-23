#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ORANGE AUTO PROCESSOR - Système automatique de traitement
Surveille la base et traite automatiquement les enregistrements "En Traitement"
"""

import sys
import time
import threading
import serial
import serial.tools.list_ports
import re
from datetime import datetime

# Try PyMySQL first (more stable)
try:
    import pymysql as mysql_lib
    CONNECTION_TYPE = "PyMySQL"
    print("✅ PyMySQL disponible (version stable)")
    
    def create_connection(host, database, user, password, timeout=10):
        return mysql_lib.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            connect_timeout=timeout,
            autocommit=True
        )
        
except ImportError:
    # Fallback to mysql-connector-python
    try:
        import mysql.connector as mysql_lib
        CONNECTION_TYPE = "mysql-connector-python"
        print("✅ mysql-connector-python disponible")
        
        def create_connection(host, database, user, password, timeout=10):
            return mysql_lib.connect(
                host=host,
                database=database,
                user=user,
                password=password,
                connection_timeout=timeout,
                autocommit=True
            )
            
    except ImportError:
        print("❌ Modules MySQL non trouvés")
        print("💡 Installez: pip install PyMySQL")
        input("Appuyez sur Entrée...")
        sys.exit(1)

class OrangeAutoProcessor:
    def __init__(self):
        """Initialize Orange Auto Processor"""
        print("=" * 60)
        print("🍊 ORANGE AUTO PROCESSOR - SYSTÈME AUTOMATIQUE")
        print("=" * 60)
        print(f"🔧 Base de données: {CONNECTION_TYPE}")
        
        # Database configuration
        self.myServer = "192.168.3.250"
        self.myDB = "main_raqmicash"
        self.myUsername = "rwsUserMA"
        self.myPassword = "oF90mS@8203e"
        
        # Modem configuration
        self.FIXED_IMSI = "604000944298560"  # IMSI autorisé
        
        # Connections
        self.db_connection = None
        self.db_connected = False
        self.modem_port = None
        self.modem_connected = False
        
        # Processing
        self.processing = False
        self.status_column = None  # Auto-detected
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'success': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        
        self.show_config()
        
    def show_config(self):
        """Show configuration"""
        print("\n📋 Configuration:")
        print(f"   🗄️ Serveur DB: {self.myServer}")
        print(f"   📊 Base: {self.myDB}")
        print(f"   👤 Utilisateur: {self.myUsername}")
        print(f"   🔐 IMSI autorisé: {self.FIXED_IMSI}")
        print()
    
    def log(self, message, level="INFO"):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ️",
            "SUCCESS": "✅", 
            "ERROR": "❌",
            "WARNING": "⚠️",
            "PROCESSING": "⚙️"
        }.get(level, "ℹ️")
        
        print(f"[{timestamp}] {prefix} {message}")
    
    def connect_database(self):
        """Connect to database"""
        self.log("Connexion base de données...")
        
        try:
            if self.db_connection:
                try:
                    self.db_connection.close()
                except:
                    pass
                self.db_connection = None
            
            self.db_connection = create_connection(
                host=self.myServer,
                database=self.myDB,
                user=self.myUsername,
                password=self.myPassword,
                timeout=10
            )
            
            if self.db_connection:
                self.db_connected = True
                self.log("Base de données connectée", "SUCCESS")
                
                # Auto-detect column names
                self.detect_columns()
                return True
            else:
                self.log("Échec connexion base", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Erreur base de données: {str(e)}", "ERROR")
            self.db_connected = False
            return False
    
    def detect_columns(self):
        """Auto-detect column names"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("DESCRIBE identification")
            columns = cursor.fetchall()
            cursor.close()
            
            column_names = [col[0].lower() for col in columns]
            
            if 'etats' in column_names:
                self.status_column = 'etats'
                self.log("Colonne état détectée: 'etats'", "SUCCESS")
            elif 'etat' in column_names:
                self.status_column = 'etat'
                self.log("Colonne état détectée: 'etat'", "SUCCESS")
            else:
                self.status_column = 'etats'  # Default
                self.log("Utilisation colonne par défaut: 'etats'", "WARNING")
                
        except Exception as e:
            self.log(f"Erreur détection colonnes: {str(e)}", "ERROR")
            self.status_column = 'etats'  # Default
    
    def connect_modem(self):
        """Connect to authorized modem"""
        self.log("Recherche modem autorisé...")
        
        # Priority ports for SCD modem
        priority_ports = ["COM9", "COM8", "COM7", "COM6", "COM5"]
        
        # Get all available ports
        available_ports = []
        try:
            for port_info in serial.tools.list_ports.comports():
                available_ports.append(port_info.device)
        except:
            self.log("Erreur énumération ports", "ERROR")
            return False
        
        # Try priority ports first
        for port in priority_ports:
            if port in available_ports:
                if self.try_modem_connection(port):
                    return True
        
        # Try other ports
        for port in available_ports:
            if port not in priority_ports:
                if self.try_modem_connection(port):
                    return True
        
        self.log("Aucun modem autorisé trouvé", "ERROR")
        return False
    
    def try_modem_connection(self, port):
        """Try to connect to specific port and verify IMSI"""
        try:
            self.log(f"Test modem sur {port}...")
            
            # Quick AT test
            test_port = serial.Serial(
                port=port,
                baudrate=115200,
                timeout=1,
                write_timeout=1
            )
            
            test_port.reset_input_buffer()
            test_port.write(b'AT\r\n')
            time.sleep(0.5)
            
            response = ""
            if test_port.in_waiting > 0:
                response = test_port.read(test_port.in_waiting).decode('utf-8', errors='ignore')
            
            test_port.close()
            
            if 'OK' not in response:
                return False
            
            # Verify IMSI
            if self.verify_imsi(port):
                self.modem_port = serial.Serial(
                    port=port,
                    baudrate=115200,
                    timeout=3,
                    write_timeout=3
                )
                self.modem_connected = True
                self.log(f"Modem autorisé connecté sur {port}", "SUCCESS")
                
                # Configure modem
                self.send_at("AT+CMEE=1")
                self.send_at("AT+CMGF=1")
                
                return True
            
            return False
            
        except Exception as e:
            self.log(f"Erreur test {port}: {str(e)}", "ERROR")
            return False
    
    def verify_imsi(self, port):
        """Verify IMSI authorization"""
        try:
            temp_port = serial.Serial(
                port=port,
                baudrate=115200,
                timeout=2,
                write_timeout=2
            )
            
            temp_port.reset_input_buffer()
            temp_port.write(b'AT+CIMI\r\n')
            time.sleep(1)
            
            response = ""
            if temp_port.in_waiting > 0:
                response = temp_port.read(temp_port.in_waiting).decode('utf-8', errors='ignore')
            
            temp_port.close()
            
            imsi_match = re.search(r'\d{15}', response)
            if imsi_match:
                detected_imsi = imsi_match.group()
                if detected_imsi == self.FIXED_IMSI:
                    self.log(f"IMSI autorisé confirmé: {detected_imsi}", "SUCCESS")
                    return True
                else:
                    self.log(f"IMSI non autorisé: {detected_imsi}", "WARNING")
                    return False
            
            return False
            
        except Exception as e:
            self.log(f"Erreur vérification IMSI: {str(e)}", "ERROR")
            return False
    
    def send_at(self, command, timeout=3):
        """Send AT command to modem"""
        if not self.modem_connected or not self.modem_port:
            return None
        
        try:
            self.modem_port.reset_input_buffer()
            self.modem_port.write((command + '\r\n').encode())
            
            time.sleep(0.2)
            response = ""
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if self.modem_port.in_waiting > 0:
                    response += self.modem_port.read(self.modem_port.in_waiting).decode('utf-8', errors='ignore')
                    
                if 'OK' in response or 'ERROR' in response:
                    break
                    
                time.sleep(0.1)
            
            return response.strip()
            
        except Exception as e:
            self.log(f"Erreur AT: {str(e)}", "ERROR")
            return None
    
    def send_ussd(self, ussd_code):
        """Send USSD and get response"""
        if not self.modem_connected:
            return None
        
        try:
            self.log(f"Envoi USSD: {ussd_code}", "PROCESSING")
            
            # Configure USSD
            self.send_at("AT+CUSD=1", timeout=2)
            time.sleep(0.3)
            
            # Send USSD
            self.modem_port.reset_input_buffer()
            self.modem_port.write(f'AT+CUSD=1,"{ussd_code}",15\r\n'.encode())
            
            # Wait for response
            response = ""
            start_time = time.time()
            ussd_timeout = 30
            
            while time.time() - start_time < ussd_timeout:
                if self.modem_port.in_waiting > 0:
                    new_data = self.modem_port.read(self.modem_port.in_waiting).decode('utf-8', errors='ignore')
                    response += new_data
                
                # Check for USSD response
                if '+CUSD:' in response:
                    match = re.search(r'\+CUSD:\s*\d+,"([^"]+)"', response)
                    if match:
                        result = match.group(1)
                        result = result.replace('\\n', '\n').replace('\\r', '\r')
                        self.log(f"Réponse USSD reçue: {result[:50]}...", "SUCCESS")
                        return result
                
                if 'ERROR' in response:
                    self.log("Erreur USSD", "ERROR")
                    return None
                
                time.sleep(0.2)
            
            self.log("Timeout USSD", "WARNING")
            return None
            
        except Exception as e:
            self.log(f"Erreur USSD: {str(e)}", "ERROR")
            return None
    
    def send_sms(self, phone_number, message):
        """Send SMS"""
        if not self.modem_connected:
            return False
        
        try:
            self.log(f"Envoi SMS vers {phone_number}", "PROCESSING")
            
            # Set SMS mode
            self.send_at("AT+CMGF=1")
            time.sleep(0.5)
            
            # Set recipient
            response = self.send_at(f'AT+CMGS="{phone_number}"', timeout=5)
            if not response or 'ERROR' in response:
                self.log("Erreur destinataire SMS", "ERROR")
                return False
            
            time.sleep(1)
            
            # Send message
            self.modem_port.write((message + '\x1A').encode())
            time.sleep(3)
            
            # Check response
            response = ""
            start_time = time.time()
            while time.time() - start_time < 10:
                if self.modem_port.in_waiting > 0:
                    response += self.modem_port.read(self.modem_port.in_waiting).decode('utf-8', errors='ignore')
                
                if '+CMGS:' in response or 'OK' in response:
                    self.log("SMS envoyé avec succès", "SUCCESS")
                    return True
                
                if 'ERROR' in response:
                    break
                
                time.sleep(0.5)
            
            self.log("Échec envoi SMS", "ERROR")
            return False
            
        except Exception as e:
            self.log(f"Erreur SMS: {str(e)}", "ERROR")
            return False
    
    def get_pending_records(self):
        """Get records with status 'En Traitement'"""
        if not self.db_connected:
            return []
        
        try:
            cursor = self.db_connection.cursor()
            query = f"SELECT * FROM identification WHERE {self.status_column} = 'En Traitement' AND operator = 'Orange'"
            cursor.execute(query)
            records = cursor.fetchall()
            cursor.close()
            
            # CORRECTION: Traiter TOUS les enregistrements "En Traitement"
            # Même s'ils ont déjà été traités avant (reprendre depuis A-0)
            return records
            
        except Exception as e:
            self.log(f"Erreur lecture base: {str(e)}", "ERROR")
            return []
    
    def update_record_status(self, record_id, status):
        """Update record status in database"""
        if not self.db_connected:
            return False
        
        try:
            cursor = self.db_connection.cursor()
            query = f"UPDATE identification SET {self.status_column} = %s WHERE id = %s"
            cursor.execute(query, (status, record_id))
            cursor.close()
            
            self.log(f"Record {record_id} mis à jour: {status}", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Erreur mise à jour base: {str(e)}", "ERROR")
            return False
    
    def update_record_with_response(self, record_id, status, ussd_response):
        """Update record status and store USSD response in SMS column"""
        if not self.db_connected:
            return False
        
        try:
            cursor = self.db_connection.cursor()
            query = f"UPDATE identification SET {self.status_column} = %s, sms = %s WHERE id = %s"
            cursor.execute(query, (status, ussd_response, record_id))
            cursor.close()
            
            self.log(f"Record {record_id} mis à jour: {status} + réponse stockée", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Erreur mise à jour base: {str(e)}", "ERROR")
            return False
    
    def process_record(self, record):
        """Process a single record"""
        try:
            record_id = record[0]
            
            # Extract data - CORRECTION: structure DB réelle avec "nd"
            # Colonnes: id, date, posCode, operator, nd, puk, nom, cin, etats, sms
            if len(record) >= 8:
                nd = record[4] if record[4] else "000000000000000"    # nd à l'index 4
                puk = record[5] if record[5] else "00000000"          # puk à l'index 5
                nom = record[6] if record[6] else "CLIENT"            # nom à l'index 6
                cin = record[7] if record[7] else "XXXXXX"            # cin à l'index 7
                sms_number = record[9] if len(record) > 9 and record[9] else None  # sms à l'index 9
            else:
                self.log(f"Record {record_id}: Structure invalide", "WARNING")
                return False
            
            self.log(f"Traitement record {record_id}: {nom}", "PROCESSING")
            
            # Build USSD command - LOGIQUE CORRECTE
            ussd_command = f"*555*1*{nd}*1*{puk}*{nom}*{cin}#"
            
            # Send USSD
            ussd_response = self.send_ussd(ussd_command)
            
            if ussd_response:
                # LOGIQUE SIMPLIFIÉE: Toute réponse USSD = TRAITÉ
                self.log(f"Réponse USSD reçue pour {nom} - Passage à 'Traité'", "SUCCESS")
                
                # Send SMS if SMS number available
                if sms_number:
                    sms_message = f"Reponse Orange:\n{ussd_response}\n\nClient: {nom}\nCIN: {cin}"
                    if self.send_sms(sms_number, sms_message):
                        self.log(f"SMS envoyé pour {nom}", "SUCCESS")
                    else:
                        self.log(f"Échec SMS pour {nom} - Mais traité quand même", "WARNING")
                else:
                    self.log(f"Pas de numéro pour {nom} - Traité quand même", "WARNING")
                
                # Stocker la réponse dans colonne SMS + changer vers "Traité"
                if self.update_record_with_response(record_id, "Traité", ussd_response):
                    self.stats['success'] += 1
                    self.log(f"Record {record_id} TRAITÉ avec succès", "SUCCESS")
                    return True
                else:
                    self.log(f"Erreur mise à jour record {record_id}", "ERROR")
                    return False
            else:
                self.log(f"Échec USSD pour record {record_id}", "ERROR")
                self.stats['errors'] += 1
                return False
                
        except Exception as e:
            self.log(f"Erreur traitement record: {str(e)}", "ERROR")
            self.stats['errors'] += 1
            return False
    
    def monitoring_loop(self):
        """Main monitoring loop"""
        self.log("Démarrage monitoring automatique...", "SUCCESS")
        self.processing = True
        
        while self.processing:
            try:
                # Check database connection
                if not self.db_connected:
                    if not self.connect_database():
                        time.sleep(10)
                        continue
                
                # Check modem connection
                if not self.modem_connected:
                    if not self.connect_modem():
                        time.sleep(30)
                        continue
                
                # Get pending records
                pending_records = self.get_pending_records()
                
                if pending_records:
                    self.log(f"Traitement de {len(pending_records)} enregistrement(s)", "INFO")
                    
                    for record in pending_records:
                        if not self.processing:
                            break
                        
                        self.stats['total_processed'] += 1
                        self.process_record(record)
                        
                        # Professional delay between records
                        time.sleep(25)  # Délai professionnel de 25 secondes
                else:
                    # No pending records, wait and check again
                    time.sleep(5)
                
            except KeyboardInterrupt:
                self.log("Arrêt par utilisateur", "WARNING")
                break
            except Exception as e:
                self.log(f"Erreur monitoring: {str(e)}", "ERROR")
                time.sleep(10)
        
        self.log("Monitoring arrêté", "WARNING")
    
    def show_stats(self):
        """Show processing statistics"""
        runtime = datetime.now() - self.stats['start_time']
        
        print("\n📊 STATISTIQUES:")
        print(f"   ⏱️ Durée: {runtime}")
        print(f"   📈 Total traité: {self.stats['total_processed']}")
        print(f"   ✅ Succès: {self.stats['success']}")
        print(f"   ❌ Erreurs: {self.stats['errors']}")
        if self.stats['total_processed'] > 0:
            success_rate = (self.stats['success'] / self.stats['total_processed']) * 100
            print(f"   📊 Taux succès: {success_rate:.1f}%")
    
    def start_processing(self):
        """Start the automatic processing"""
        try:
            # Initial connections
            if not self.connect_database():
                self.log("Impossible de se connecter à la base", "ERROR")
                return False
            
            if not self.connect_modem():
                self.log("Impossible de se connecter au modem", "ERROR")
                return False
            
            # Start monitoring in thread
            monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
            monitoring_thread.start()
            
            # Interactive control
            print("\n🎮 CONTRÔLES:")
            print("   S - Afficher statistiques")
            print("   Q - Quitter")
            print()
            
            while self.processing:
                try:
                    choice = input("Commande (S/Q): ").strip().upper()
                    
                    if choice == 'Q':
                        self.processing = False
                        break
                    elif choice == 'S':
                        self.show_stats()
                    
                except KeyboardInterrupt:
                    self.processing = False
                    break
            
            self.log("Arrêt du système...", "WARNING")
            return True
            
        except Exception as e:
            self.log(f"Erreur démarrage: {str(e)}", "ERROR")
            return False
    
    def cleanup(self):
        """Clean up connections"""
        self.processing = False
        
        if self.modem_port:
            try:
                self.modem_port.close()
            except:
                pass
        
        if self.db_connection:
            try:
                self.db_connection.close()
            except:
                pass
        
        self.log("Nettoyage terminé", "SUCCESS")

def main():
    """Main function"""
    processor = None
    
    try:
        processor = OrangeAutoProcessor()
        processor.start_processing()
        
    except KeyboardInterrupt:
        print("\n\n👋 Arrêt par utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur critique: {str(e)}")
    finally:
        if processor:
            processor.cleanup()
        
        input("\nAppuyez sur Entrée pour quitter...")

if __name__ == "__main__":
    main()