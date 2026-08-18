"""
Client de messagerie pour MessagerCrypt
Interface utilisateur pour la communication sécurisée
"""
import socket
import json
import threading
import time
from typing import Dict, List, Optional, Tuple
import logging

from config.settings import DEFAULT_HOST, DEFAULT_PORT, BUFFER_SIZE, DEBUG
from .crypto.encryption import EncryptionManager
from .crypto.auth import AuthManager
from .crypto.keys import KeyManager
from .storage.database import EncryptedDatabase
from .storage.messages import MessageManager
from .ui.ascii import ASCIIArt
from .ui.menu import MenuManager


class MessagerCryptClient:
    """Client de messagerie pour MessagerCrypt"""
    
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.authenticated = False
        self.username = None
        self.session_token = None
        self.user_keys = None
        
        # Modules
        self.encryption_manager = EncryptionManager()
        self.auth_manager = AuthManager()
        self.key_manager = KeyManager()
        self.database = EncryptedDatabase()
        self.message_manager = MessageManager()
        self.ascii_art = ASCIIArt()
        self.menu_manager = MenuManager()
        
        # Couleurs pour l'affichage
        self.colors = {
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'magenta': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'dim': '\033[2m',
            'bright_red': '\033[91m',
            'bright_green': '\033[92m',
            'bright_yellow': '\033[93m',
            'bright_blue': '\033[94m',
            'bright_magenta': '\033[95m',
            'bright_cyan': '\033[96m',
            'bright_white': '\033[97m',
            'reset': '\033[0m'
        }
        
        # Thread de réception des messages
        self.receive_thread = None
        self.running = False
        
        # Configuration du logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure le système de logging"""
        log_level = logging.DEBUG if DEBUG else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/client.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('MessagerCryptClient')
    
    def connect(self) -> bool:
        """Se connecte au serveur"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            # Démarrage du thread de réception
            self.running = True
            self.receive_thread = threading.Thread(target=self._receive_messages, daemon=True)
            self.receive_thread.start()
            
            self.logger.info(f"Connecté au serveur {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur de connexion: {e}")
            self.ascii_art.show_error(f"Erreur de connexion: {e}")
            return False
    
    def disconnect(self):
        """Se déconnecte du serveur"""
        self.running = False
        self.connected = False
        
        if self.socket:
            self.socket.close()
            self.socket = None
        
        self.logger.info("Déconnecté du serveur")
    
    def authenticate(self, username: str, password: str) -> bool:
        """S'authentifie auprès du serveur"""
        try:
            if not self.connected:
                self.ascii_art.show_error("Non connecté au serveur")
                return False
            
            # Chargement des clés utilisateur
            self.user_keys = self.key_manager.load_user_keys(username, password)
            if not self.user_keys:
                self.ascii_art.show_error("Identifiants invalides")
                return False
            
            # Envoi de la demande d'authentification
            auth_message = {
                'type': 'auth',
                'username': username,
                'password': password
            }
            
            self._send_message(auth_message)
            
            # Attente de la réponse (simplifié pour l'exemple)
            time.sleep(1)
            
            if self.authenticated:
                self.username = username
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur lors de l'authentification: {e}")
            self.ascii_art.show_error(f"Erreur d'authentification: {e}")
            return False
    
    def register(self, username: str, password: str) -> bool:
        """S'inscrit auprès du serveur"""
        try:
            # Vérification que l'utilisateur n'existe pas déjà
            existing_keys = self.key_manager.load_user_keys(username, password)
            if existing_keys:
                self.ascii_art.show_error("Utilisateur déjà existant")
                return False
            
            # Génération des clés
            user_keys = self.key_manager.generate_user_keys(username, password)
            if user_keys["status"] == "success":
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur lors de l'inscription: {e}")
            self.ascii_art.show_error(f"Erreur d'inscription: {e}")
            return False
    
    def send_message(self, recipient: str, message: str) -> bool:
        """Envoie un message à un destinataire"""
        try:
            if not self.authenticated:
                self.ascii_art.show_error("Authentification requise")
                return False
            
            # Récupération de la clé publique du destinataire
            recipient_public_key = self.key_manager.get_public_key(recipient)
            if not recipient_public_key:
                self.ascii_art.show_error(f"Utilisateur {recipient} introuvable")
                return False
            
            # Chiffrement du message
            message_packet = self.encryption_manager.create_message_packet(
                message, self.username, recipient, 
                self.encryption_manager.generate_aes_key(), 
                recipient_public_key
            )
            
            # Envoi du message chiffré
            message_data = {
                'type': 'message',
                'recipient': recipient,
                'message': json.dumps(message_packet)
            }
            
            self._send_message(message_data)
            self.ascii_art.show_message_sent(recipient)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi du message: {e}")
            self.ascii_art.show_error(f"Erreur lors de l'envoi: {e}")
            return False
    
    def _get_multiline_input(self) -> str:
        """
        Saisie multiligne avec Entrée pour nouvelle ligne et double Entrée pour envoyer
        
        Returns:
            str: Message saisi
        """
        print(f"{self.colors['cyan']}Tapez votre message:{self.colors['reset']}")
        print(f"{self.colors['dim']}Entrée pour nouvelle ligne, double Entrée pour envoyer{self.colors['reset']}")
        print()
        
        lines = []
        empty_lines = 0
        
        while True:
            try:
                line = input()
                
                if line.strip() == "":
                    empty_lines += 1
                    if empty_lines >= 2:
                        # Double ligne vide = fin du message
                        break
                else:
                    empty_lines = 0
                    lines.append(line)
                    
            except KeyboardInterrupt:
                # Ctrl+C pour annuler
                print(f"\n{self.colors['yellow']}Saisie annulée{self.colors['reset']}")
                return ""
        
        return '\n'.join(lines)
    
    def get_users(self) -> List[str]:
        """Récupère la liste des utilisateurs"""
        try:
            if not self.authenticated:
                self.ascii_art.show_error("Authentification requise")
                return []
            
            # Envoi de la demande
            request = {'type': 'get_users'}
            self._send_message(request)
            
            # Attente de la réponse (simplifié)
            time.sleep(0.5)
            
            return []  # Retour simplifié
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des utilisateurs: {e}")
            return []
    
    def get_message_history(self, limit: int = 50) -> List[Dict]:
        """Récupère l'historique des messages"""
        try:
            if not self.authenticated:
                self.ascii_art.show_error("Authentification requise")
                return []
            
            # Récupération depuis la base de données locale
            messages = self.message_manager.get_user_messages(self.username, limit)
            return messages
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération de l'historique: {e}")
            return []
    
    def get_received_messages(self) -> List[Dict]:
        """Récupère les messages reçus"""
        try:
            if not self.authenticated:
                self.ascii_art.show_error("Authentification requise")
                return []
            
            # Récupération des messages reçus depuis la base de données locale
            messages = self.message_manager.get_received_messages(self.username)
            return messages
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des messages reçus: {e}")
            return []
    
    def search_messages(self, query: str) -> List[Dict]:
        """Recherche dans les messages"""
        try:
            if not self.authenticated:
                self.ascii_art.show_error("Authentification requise")
                return []
            
            # Recherche dans les messages
            messages = self.message_manager.search_messages(self.username, query)
            return messages
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche: {e}")
            return []
    
    def _send_message(self, message: Dict):
        """Envoie un message au serveur"""
        try:
            if self.connected and self.socket:
                data = json.dumps(message).encode('utf-8')
                self.socket.send(data)
                
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi du message: {e}")
    
    def _receive_messages(self):
        """Thread de réception des messages"""
        while self.running and self.connected:
            try:
                data = self.socket.recv(BUFFER_SIZE)
                if not data:
                    break
                
                message = json.loads(data.decode('utf-8'))
                self._handle_received_message(message)
                
            except Exception as e:
                if self.running:
                    self.logger.error(f"Erreur lors de la réception: {e}")
                break
    
    def _handle_received_message(self, message: Dict):
        """Traite un message reçu du serveur"""
        message_type = message.get('type')
        
        if message_type == 'auth_success':
            self.authenticated = True
            self.session_token = message.get('session_token')
            # Authentification réussie - gérée par l'interface principale
            
        elif message_type == 'error':
            # Erreur serveur - gérée par l'interface principale
            pass
            
        elif message_type == 'message_received':
            sender = message.get('sender')
            encrypted_content = message.get('message')
            
            # Déchiffrement du message
            try:
                import json
                import base64
                
                # Parse du message chiffré
                message_packet = json.loads(encrypted_content)
                
                # Récupération des clés pour le déchiffrement
                recipient_private_key = self.user_keys.get('private_key')
                sender_public_key = self.key_manager.get_public_key(sender)
                
                if not recipient_private_key or not sender_public_key:
                    raise Exception("Clés de déchiffrement manquantes")
                
                # Déchiffrement de la clé de session avec la clé privée du destinataire
                encrypted_session_key = base64.b64decode(message_packet['aes_key'])
                session_key = self.encryption_manager.decrypt_with_rsa(
                    encrypted_session_key, recipient_private_key
                )
                
                # Déchiffrement du message avec la clé de session
                encrypted_message = base64.b64decode(message_packet['message'])
                nonce = base64.b64decode(message_packet['nonce'])
                
                decrypted_content = self.encryption_manager.decrypt_with_aes(
                    encrypted_message, session_key, nonce
                ).decode('utf-8')
                
                # Sauvegarde du message reçu
                self.message_manager.save_received_message(sender, self.username, decrypted_content)
                
                # Affichage du message avec notification visible
                print(f"\n{'='*60}")
                print(f"📨 NOUVEAU MESSAGE DE {sender.upper()}")
                print(f"{'='*60}")
                print(f"{self.colors['white']}{decrypted_content}{self.colors['reset']}")
                print(f"{'='*60}")
                print()
                
            except Exception as e:
                self.logger.error(f"Erreur lors du déchiffrement du message: {e}")
                # Affichage du message brut en cas d'erreur
                print(f"\n{'='*60}")
                print(f"📨 NOUVEAU MESSAGE DE {sender.upper()}")
                print(f"{'='*60}")
                print(f"{self.colors['yellow']}Erreur de déchiffrement: {str(e)}{self.colors['reset']}")
                print(f"{self.colors['dim']}Message chiffré reçu:{self.colors['reset']}")
                print(f"{self.colors['white']}{encrypted_content[:100]}...{self.colors['reset']}")
                print(f"{'='*60}")
                print()
            
        elif message_type == 'message_sent':
            # Message envoyé - géré par l'interface principale
            pass
            
        elif message_type == 'users_list':
            users = message.get('connected_users', [])
            print(f"\n👥 Utilisateurs connectés: {', '.join(users)}")
            
        elif message_type == 'history':
            messages = message.get('messages', [])
            self.menu_manager.show_message_history(messages, self.username)
            
        elif message_type == 'pong':
            # Réponse au ping
            pass
            
        else:
            self.logger.debug(f"Message reçu: {message_type}")
    
    def run_client_interface(self):
        """Interface principale du client"""
        while True:
            choice = self.menu_manager.show_main_menu()
            
            if choice == "1":
                # Démarrer le serveur (non implémenté dans le client)
                self.ascii_art.show_warning("Utilisez le serveur séparément")
                self.menu_manager.pause()
            
            elif choice == "2":
                # S'inscrire
                self._handle_registration()
            
            elif choice == "3":
                # Se connecter
                self._handle_login()
            
            elif choice == "4":
                # Consulter l'historique
                if self.authenticated:
                    self._handle_history()
                else:
                    self.ascii_art.show_error("Authentification requise")
                    self.menu_manager.pause()
            
            elif choice == "5":
                # Configuration
                self._handle_configuration()
            
            elif choice == "6":
                # Quitter
                if self.connected:
                    self.disconnect()
                break
            
            else:
                self.ascii_art.show_error("Choix invalide")
    
    def _handle_registration(self):
        """Gère l'inscription d'un utilisateur"""
        form_data = self.menu_manager.show_register_form()
        
        if form_data['password'] != form_data['confirm_password']:
            self.ascii_art.show_error("Les mots de passe ne correspondent pas")
            return
        
        if not form_data['username'] or not form_data['password']:
            self.ascii_art.show_error("Nom d'utilisateur et mot de passe requis")
            return
        
        # Connexion au serveur si nécessaire
        if not self.connected:
            if not self.connect():
                return
        
        # Inscription
        success = self.register(form_data['username'], form_data['password'])
        if success:
            self.menu_manager.pause()
    
    def _handle_login(self):
        """Gère la connexion d'un utilisateur"""
        form_data = self.menu_manager.show_login_form()
        
        if not form_data['username'] or not form_data['password']:
            self.ascii_art.show_error("Nom d'utilisateur et mot de passe requis")
            return
        
        # Connexion au serveur si nécessaire
        if not self.connected:
            if not self.connect():
                return
        
        # Authentification
        success = self.authenticate(form_data['username'], form_data['password'])
        if success:
            self._run_messaging_interface()
    
    def _handle_history(self):
        """Gère l'affichage de l'historique"""
        history = self.get_message_history()
        if history:
            self.menu_manager.show_message_history(history, self.username)
        else:
            self.ascii_art.show_warning("Aucun message dans l'historique")
            self.menu_manager.pause()
    
    def _handle_configuration(self):
        """Gère la configuration"""
        choice = self.menu_manager.show_configuration_menu()
        
        if choice == "1":
            self.ascii_art.show_success("Paramètres de sécurité")
            self.menu_manager.pause()
        elif choice == "2":
            self.ascii_art.show_success("Paramètres réseau")
            self.menu_manager.pause()
        elif choice == "3":
            self.ascii_art.show_success("Thème et couleurs")
            self.menu_manager.pause()
        elif choice == "4":
            self._show_stats()
        elif choice == "5":
            self._handle_cleanup()
        elif choice == "6":
            pass  # Retour
    
    def _run_messaging_interface(self):
        """Interface de messagerie"""
        while True:
            choice = self.menu_manager.show_messaging_interface(self.username)
            
            if choice == "1":
                # Envoyer un message
                self._handle_send_message()
            
            elif choice == "2":
                # Messages reçus
                self._handle_received_messages()
            
            elif choice == "3":
                # Historique
                self._handle_history()
            
            elif choice == "4":
                # Rechercher
                self._handle_search()
            
            elif choice == "5":
                # Paramètres
                self._handle_configuration()
            
            elif choice == "6":
                # Déconnexion
                self.authenticated = False
                self.username = None
                break
            
            else:
                self.ascii_art.show_error("Choix invalide")
    
    def _handle_send_message(self):
        """Gère l'envoi d'un message"""
        message_data = self.menu_manager.show_message_compose()
        
        if message_data['recipient'] and message_data['message']:
            success = self.send_message(message_data['recipient'], message_data['message'])
            if success:
                self.menu_manager.pause()
        else:
            self.ascii_art.show_error("Destinataire et message requis")
            self.menu_manager.pause()
    
    def _handle_received_messages(self):
        """Gère l'affichage des messages reçus"""
        self.ascii_art.show_success("Messages reçus (fonctionnalité en développement)")
        self.menu_manager.pause()
    
    def _handle_search(self):
        """Gère la recherche de messages"""
        query = input(f"\n{self.menu_manager.colors['yellow']}Rechercher: {self.menu_manager.colors['reset']}")
        if query:
            self.ascii_art.show_success(f"Recherche pour: {query}")
        self.menu_manager.pause()
    
    def _show_stats(self):
        """Affiche les statistiques"""
        print(f"\n{'='*50}")
        print(f"📊 STATISTIQUES")
        print(f"{'='*50}")
        print(f"Utilisateur: {self.username or 'Non connecté'}")
        print(f"Statut: {'🟢 Connecté' if self.connected else '🔴 Déconnecté'}")
        print(f"Authentifié: {'✅ Oui' if self.authenticated else '❌ Non'}")
        print(f"{'='*50}\n")
        self.menu_manager.pause()
    
    def _handle_cleanup(self):
        """Gère le nettoyage des données"""
        if self.menu_manager.show_rich_confirm("Voulez-vous nettoyer les données locales?"):
            self.ascii_art.show_success("Données nettoyées")
        self.menu_manager.pause()


def main():
    """Point d'entrée du client"""
    client = MessagerCryptClient()
    
    try:
        client.run_client_interface()
    except KeyboardInterrupt:
        print("\nArrêt du client...")
        client.disconnect()
    except Exception as e:
        print(f"Erreur: {e}")
        client.disconnect()


if __name__ == "__main__":
    main()
