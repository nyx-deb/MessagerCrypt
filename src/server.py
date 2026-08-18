"""
Serveur TCP sécurisé pour MessagerCrypt
Gestion des connexions et des messages chiffrés
"""
import socket
import threading
import json
import time
import base64
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

from config.settings import DEFAULT_HOST, DEFAULT_PORT, MAX_CONNECTIONS, BUFFER_SIZE, DEBUG
from .crypto.encryption import EncryptionManager
from .crypto.auth import AuthManager
from .crypto.keys import KeyManager
from .storage.database import EncryptedDatabase
from .storage.messages import MessageManager
from .ui.ascii import ASCIIArt
from .ui.menu import MenuManager


class MessagerCryptServer:
    """Serveur TCP sécurisé pour MessagerCrypt"""
    
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.clients = {}
        self.connected_users = {}
        
        # Modules
        self.encryption_manager = EncryptionManager()
        self.auth_manager = AuthManager()
        self.key_manager = KeyManager()
        self.database = EncryptedDatabase()
        self.message_manager = MessageManager()
        self.ascii_art = ASCIIArt()
        self.menu_manager = MenuManager()
        
        # Configuration du logging
        self._setup_logging()
        
        # Statistiques
        self.stats = {
            "connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "start_time": None
        }
    
    def _setup_logging(self):
        """Configure le système de logging"""
        log_level = logging.DEBUG if DEBUG else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/server.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('MessagerCryptServer')
    
    def start(self):
        """Démarre le serveur"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(MAX_CONNECTIONS)
            
            self.running = True
            self.stats["start_time"] = time.time()
            
            self.logger.info(f"Serveur démarré sur {self.host}:{self.port}")
            
            # Thread de nettoyage des sessions
            cleanup_thread = threading.Thread(target=self._cleanup_sessions, daemon=True)
            cleanup_thread.start()
            
            # Boucle principale d'acceptation des connexions
            while self.running:
                try:
                    client_socket, address = self.socket.accept()
                    self.logger.info(f"Nouvelle connexion depuis {address}")
                    
                    # Création d'un thread pour chaque client
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.error as e:
                    if self.running:
                        self.logger.error(f"Erreur d'acceptation: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Erreur lors du démarrage du serveur: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Arrête le serveur"""
        self.running = False
        
        # Fermeture des connexions clients (copie : le dict est modifié par les threads clients)
        for client_id, client_info in list(self.clients.items()):
            try:
                client_info['socket'].close()
            except:
                pass
        
        # Fermeture du socket serveur (shutdown réveille le thread bloqué dans accept)
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.socket.close()
        
        self.logger.info("Serveur arrêté")
    
    def _handle_client(self, client_socket: socket.socket, address: Tuple[str, int]):
        """Gère une connexion client"""
        client_id = f"{address[0]}:{address[1]}"
        self.clients[client_id] = {
            'socket': client_socket,
            'address': address,
            'username': None,
            'authenticated': False,
            'session_token': None,
            'connected_at': time.time()
        }
        
        self.stats["connections"] += 1
        
        try:
            while self.running:
                # Réception des données
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break
                
                # Traitement du message
                self._process_message(client_id, data)
                
        except Exception as e:
            self.logger.error(f"Erreur avec le client {client_id}: {e}")
        finally:
            # Nettoyage de la connexion
            self._disconnect_client(client_id)
    
    def _process_message(self, client_id: str, data: bytes):
        """Traite un message reçu d'un client"""
        try:
            # Décodage du message JSON
            message = json.loads(data.decode('utf-8'))
            message_type = message.get('type')
            
            self.logger.debug(f"Message reçu de {client_id}: {message_type}")
            
            if message_type == 'auth':
                self._handle_authentication(client_id, message)
            elif message_type == 'message':
                self._handle_message(client_id, message)
            elif message_type == 'get_users':
                self._handle_get_users(client_id)
            elif message_type == 'get_history':
                self._handle_get_history(client_id, message)
            elif message_type == 'ping':
                self._handle_ping(client_id)
            else:
                self._send_error(client_id, f"Type de message inconnu: {message_type}")
                
        except json.JSONDecodeError:
            self._send_error(client_id, "Format de message invalide")
        except Exception as e:
            self.logger.error(f"Erreur lors du traitement du message: {e}")
            self._send_error(client_id, "Erreur interne du serveur")
    
    def _handle_authentication(self, client_id: str, message: Dict):
        """Gère l'authentification d'un client"""
        try:
            username = message.get('username')
            password = message.get('password')
            
            if not username or not password:
                self._send_error(client_id, "Nom d'utilisateur et mot de passe requis")
                return
            
            # Vérification des identifiants
            user_keys = self.key_manager.load_user_keys(username, password)
            
            if user_keys:
                # Génération d'un token de session
                session_token = self.auth_manager.create_session_token(
                    username, self.encryption_manager.generate_aes_key()
                )
                
                # Mise à jour des informations client
                self.clients[client_id]['username'] = username
                self.clients[client_id]['authenticated'] = True
                self.clients[client_id]['session_token'] = session_token
                
                # Ajout à la liste des utilisateurs connectés
                self.connected_users[username] = {
                    'client_id': client_id,
                    'connected_at': time.time(),
                    'last_activity': time.time()
                }
                
                # Sauvegarde de la session en base
                expires_at = time.time() + 3600  # 1 heure
                self.database.create_session(username, session_token, expires_at)
                
                # Envoi de la réponse
                response = {
                    'type': 'auth_success',
                    'message': 'Authentification réussie',
                    'session_token': session_token,
                    'public_key': base64.b64encode(user_keys['public_key']).decode()
                }
                
                self._send_message(client_id, response)
                self.logger.info(f"Utilisateur {username} authentifié")
                
            else:
                self._send_error(client_id, "Identifiants invalides")
                
        except Exception as e:
            self.logger.error(f"Erreur lors de l'authentification: {e}")
            self._send_error(client_id, "Erreur d'authentification")
    
    def _handle_message(self, client_id: str, message: Dict):
        """Gère l'envoi d'un message"""
        try:
            if not self.clients[client_id]['authenticated']:
                self._send_error(client_id, "Authentification requise")
                return
            
            sender = self.clients[client_id]['username']
            recipient = message.get('recipient')
            encrypted_message = message.get('message')
            
            if not recipient or not encrypted_message:
                self._send_error(client_id, "Destinataire et message requis")
                return
            
            # Vérification que le destinataire existe
            recipient_public_key = self.key_manager.get_public_key(recipient)
            if not recipient_public_key:
                self._send_error(client_id, f"Utilisateur {recipient} introuvable")
                return
            
            # Sauvegarde du message chiffré
            message_hash = self._hash_message(encrypted_message)
            success = self.database.save_message(
                sender, recipient, encrypted_message, message_hash
            )
            
            if success:
                # Notification au destinataire s'il est connecté
                if recipient in self.connected_users:
                    recipient_client_id = self.connected_users[recipient]['client_id']
                    
                    notification = {
                        'type': 'message_received',
                        'sender': sender,
                        'message': encrypted_message,  # Message chiffré
                        'timestamp': time.time()
                    }
                    self._send_message(recipient_client_id, notification)
                
                # Confirmation à l'expéditeur
                response = {
                    'type': 'message_sent',
                    'message': 'Message envoyé avec succès',
                    'recipient': recipient
                }
                self._send_message(client_id, response)
                
                self.stats["messages_sent"] += 1
                self.logger.info(f"Message envoyé de {sender} à {recipient}")
                
            else:
                self._send_error(client_id, "Erreur lors de la sauvegarde du message")
                
        except Exception as e:
            self.logger.error(f"Erreur lors du traitement du message: {e}")
            self._send_error(client_id, "Erreur lors de l'envoi du message")
    
    def _handle_get_users(self, client_id: str):
        """Gère la demande de liste des utilisateurs"""
        try:
            if not self.clients[client_id]['authenticated']:
                self._send_error(client_id, "Authentification requise")
                return
            
            # Liste des utilisateurs connectés
            connected_users = list(self.connected_users.keys())
            
            # Liste de tous les utilisateurs (depuis la base de données)
            all_users = self.key_manager.list_users()
            
            response = {
                'type': 'users_list',
                'connected_users': connected_users,
                'all_users': all_users
            }
            
            self._send_message(client_id, response)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des utilisateurs: {e}")
            self._send_error(client_id, "Erreur lors de la récupération des utilisateurs")
    
    def _handle_get_history(self, client_id: str, message: Dict):
        """Gère la demande d'historique des messages"""
        try:
            if not self.clients[client_id]['authenticated']:
                self._send_error(client_id, "Authentification requise")
                return
            
            username = self.clients[client_id]['username']
            limit = message.get('limit', 50)
            
            # Récupération de l'historique
            history = self.database.get_messages(username, limit)
            
            response = {
                'type': 'history',
                'messages': history
            }
            
            self._send_message(client_id, response)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération de l'historique: {e}")
            self._send_error(client_id, "Erreur lors de la récupération de l'historique")
    
    def _handle_ping(self, client_id: str):
        """Gère un ping client"""
        response = {
            'type': 'pong',
            'timestamp': time.time()
        }
        self._send_message(client_id, response)
    
    def _send_message(self, client_id: str, message: Dict):
        """Envoie un message à un client"""
        try:
            if client_id in self.clients:
                data = json.dumps(message).encode('utf-8')
                self.clients[client_id]['socket'].send(data)
                
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi du message: {e}")
    
    def _send_error(self, client_id: str, error_message: str):
        """Envoie un message d'erreur à un client"""
        error_response = {
            'type': 'error',
            'message': error_message
        }
        self._send_message(client_id, error_response)
    
    def _disconnect_client(self, client_id: str):
        """Déconnecte un client"""
        try:
            if client_id in self.clients:
                client_info = self.clients[client_id]
                
                # Suppression de la liste des utilisateurs connectés
                if client_info['username'] in self.connected_users:
                    del self.connected_users[client_info['username']]
                
                # Fermeture de la connexion
                client_info['socket'].close()
                del self.clients[client_id]
                
                self.logger.info(f"Client {client_id} déconnecté")
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la déconnexion du client: {e}")
    
    def _hash_message(self, message: str) -> str:
        """Calcule le hash d'un message"""
        import hashlib
        return hashlib.sha256(message.encode()).hexdigest()
    
    def _cleanup_sessions(self):
        """Nettoie les sessions expirées"""
        while self.running:
            try:
                time.sleep(300)  # Nettoyage toutes les 5 minutes
                cleaned = self.database.cleanup_expired_sessions()
                if cleaned > 0:
                    self.logger.info(f"{cleaned} sessions expirées nettoyées")
                    
            except Exception as e:
                self.logger.error(f"Erreur lors du nettoyage des sessions: {e}")
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques du serveur"""
        uptime = time.time() - self.stats["start_time"] if self.stats["start_time"] else 0
        
        return {
            "uptime": uptime,
            "connections": len(self.clients),
            "connected_users": len(self.connected_users),
            "messages_sent": self.stats["messages_sent"],
            "messages_received": self.stats["messages_received"],
            "start_time": self.stats["start_time"]
        }
    
    def show_server_status(self):
        """Affiche le statut du serveur"""
        stats = self.get_stats()
        
        # Calcul de la largeur du terminal
        try:
            import shutil
            terminal_width = shutil.get_terminal_size().columns
        except:
            terminal_width = 80
        
        title = "🖥️  STATUT DU SERVEUR MESSAGERCRYPT"
        title_centered = title.center(terminal_width)
        
        print(f"\n{'='*terminal_width}")
        print(title_centered)
        print(f"{'='*terminal_width}")
        print(f"Adresse: {self.host}:{self.port}")
        print(f"Statut: {'🟢 Actif' if self.running else '🔴 Arrêté'}")
        print(f"Connexions: {stats['connections']}")
        print(f"Utilisateurs connectés: {stats['connected_users']}")
        print(f"Messages envoyés: {stats['messages_sent']}")
        print(f"Messages reçus: {stats['messages_received']}")
        print(f"Temps de fonctionnement: {int(stats['uptime'])} secondes")
        print(f"{'='*60}\n")
    
    def run_server_interface(self):
        """Interface de gestion du serveur"""
        while True:
            choice = self.menu_manager.show_server_menu()
            
            if choice == "1":
                # Démarrer le serveur
                if not self.running:
                    server_thread = threading.Thread(target=self.start, daemon=True)
                    server_thread.start()
                    time.sleep(1)
                    self.menu_manager.show_success("Serveur démarré")
                else:
                    self.menu_manager.show_warning("Le serveur est déjà en cours d'exécution")
            
            elif choice == "2":
                # Afficher les statistiques
                self.show_server_status()
                self.menu_manager.pause()
            
            elif choice == "3":
                # Afficher les utilisateurs connectés
                if self.connected_users:
                    print(f"\n👥 Utilisateurs connectés ({len(self.connected_users)}):")
                    for username, info in self.connected_users.items():
                        print(f"  • {username} (depuis {int(time.time() - info['connected_at'])}s)")
                else:
                    print("\n👥 Aucun utilisateur connecté")
                self.menu_manager.pause()
            
            elif choice == "4":
                # Afficher les logs
                print("\n📝 Derniers logs du serveur:")
                try:
                    with open('logs/server.log', 'r') as f:
                        lines = f.readlines()
                        for line in lines[-10:]:  # 10 dernières lignes
                            print(f"  {line.strip()}")
                except FileNotFoundError:
                    print("  Aucun log disponible")
                self.menu_manager.pause()
            
            elif choice == "5":
                # Retour au menu principal
                break
            
            else:
                self.menu_manager.show_error("Choix invalide")


def main():
    """Point d'entrée du serveur"""
    server = MessagerCryptServer()
    
    try:
        server.run_server_interface()
    except KeyboardInterrupt:
        print("\nArrêt du serveur...")
        server.stop()
    except Exception as e:
        print(f"Erreur: {e}")
        server.stop()


if __name__ == "__main__":
    main()
