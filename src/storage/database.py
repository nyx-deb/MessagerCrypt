"""
Module de base de données chiffrée pour MessagerCrypt
Gestion SQLite avec chiffrement
"""
import sqlite3
import json
import base64
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import secrets

from config.settings import DATABASE_PATH, DATABASE_KEY, SALT_SIZE, AES_KEY_SIZE


class EncryptedDatabase:
    """Base de données SQLite chiffrée pour MessagerCrypt"""
    
    def __init__(self, db_path: Path = None, db_key: str = None):
        self.db_path = db_path or DATABASE_PATH
        self.db_key = db_key or DATABASE_KEY
        self.backend = default_backend()
        self._init_database()
    
    def _init_database(self):
        """Initialise la base de données avec les tables nécessaires"""
        try:
            # Connexion à la base de données
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Table des utilisateurs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    encrypted_data BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            
            # Table des messages
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    encrypted_message BLOB NOT NULL,
                    message_hash TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Table des sessions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Index pour optimiser les requêtes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_recipient ON messages(recipient)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_username ON sessions(username)')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Erreur lors de l'initialisation de la base de données: {e}")
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Dérive une clé à partir d'un mot de passe"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=AES_KEY_SIZE,
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        return kdf.derive(password.encode())
    
    def _encrypt_data(self, data: bytes, key: bytes) -> Tuple[bytes, bytes]:
        """Chiffre des données avec AES-GCM"""
        nonce = secrets.token_bytes(12)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        return nonce, ciphertext
    
    def _decrypt_data(self, ciphertext: bytes, key: bytes, nonce: bytes) -> bytes:
        """Déchiffre des données avec AES-GCM"""
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)
    
    def create_user(self, username: str, user_data: Dict) -> bool:
        """
        Crée un nouvel utilisateur dans la base de données
        
        Args:
            username: Nom d'utilisateur
            user_data: Données de l'utilisateur à chiffrer
            
        Returns:
            bool: True si succès
        """
        try:
            # Génération d'un sel pour cet utilisateur
            salt = secrets.token_bytes(SALT_SIZE)
            
            # Dérivation de la clé
            key = self._derive_key(self.db_key, salt)
            
            # Chiffrement des données utilisateur
            user_data_json = json.dumps(user_data).encode()
            nonce, encrypted_data = self._encrypt_data(user_data_json, key)
            
            # Sauvegarde en base : sel + nonce + ciphertext
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (username, encrypted_data)
                VALUES (?, ?)
            ''', (username, salt + nonce + encrypted_data))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de la création de l'utilisateur: {e}")
            return False
    
    def get_user(self, username: str) -> Optional[Dict]:
        """
        Récupère les données d'un utilisateur
        
        Args:
            username: Nom d'utilisateur
            
        Returns:
            Optional[Dict]: Données utilisateur ou None
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT encrypted_data FROM users WHERE username = ?
            ''', (username,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                # Déchiffrement des données
                encrypted_data = result[0]
                salt = encrypted_data[:SALT_SIZE]
                nonce = encrypted_data[SALT_SIZE:SALT_SIZE + 12]
                ciphertext = encrypted_data[SALT_SIZE + 12:]
                
                key = self._derive_key(self.db_key, salt)
                
                decrypted_data = self._decrypt_data(ciphertext, key, nonce)
                return json.loads(decrypted_data.decode())
            
            return None
            
        except Exception as e:
            print(f"Erreur lors de la récupération de l'utilisateur: {e}")
            return None
    
    def save_message(self, sender: str, recipient: str, message: str, 
                    message_hash: str) -> bool:
        """
        Sauvegarde un message chiffré
        
        Args:
            sender: Expéditeur
            recipient: Destinataire
            message: Message chiffré (base64)
            message_hash: Hash du message
            
        Returns:
            bool: True si succès
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO messages (sender, recipient, encrypted_message, message_hash)
                VALUES (?, ?, ?, ?)
            ''', (sender, recipient, message, message_hash))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du message: {e}")
            return False
    
    def get_messages(self, username: str, limit: int = 50) -> List[Dict]:
        """
        Récupère les messages d'un utilisateur
        
        Args:
            username: Nom d'utilisateur
            limit: Nombre maximum de messages
            
        Returns:
            List[Dict]: Liste des messages
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT sender, recipient, encrypted_message, timestamp, is_read
                FROM messages 
                WHERE sender = ? OR recipient = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (username, username, limit))
            
            results = cursor.fetchall()
            conn.close()
            
            messages = []
            for row in results:
                messages.append({
                    "sender": row[0],
                    "recipient": row[1],
                    "encrypted_message": row[2],
                    "timestamp": row[3],
                    "is_read": bool(row[4])
                })
            
            return messages
            
        except Exception as e:
            print(f"Erreur lors de la récupération des messages: {e}")
            return []
    
    def mark_message_read(self, message_id: int) -> bool:
        """
        Marque un message comme lu
        
        Args:
            message_id: ID du message
            
        Returns:
            bool: True si succès
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE messages SET is_read = TRUE WHERE id = ?
            ''', (message_id,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de la mise à jour du message: {e}")
            return False
    
    def create_session(self, username: str, session_token: str, 
                      expires_at: float) -> bool:
        """
        Crée une session utilisateur
        
        Args:
            username: Nom d'utilisateur
            session_token: Token de session
            expires_at: Timestamp d'expiration
            
        Returns:
            bool: True si succès
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sessions (username, session_token, expires_at)
                VALUES (?, ?, ?)
            ''', (username, session_token, expires_at))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de la création de la session: {e}")
            return False
    
    def verify_session(self, session_token: str) -> Optional[str]:
        """
        Vérifie un token de session
        
        Args:
            session_token: Token à vérifier
            
        Returns:
            Optional[str]: Nom d'utilisateur si session valide
        """
        try:
            import time
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT username FROM sessions 
                WHERE session_token = ? AND expires_at > ? AND is_active = TRUE
            ''', (session_token, time.time()))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
            
        except Exception as e:
            print(f"Erreur lors de la vérification de la session: {e}")
            return None
    
    def invalidate_session(self, session_token: str) -> bool:
        """
        Invalide une session
        
        Args:
            session_token: Token de session à invalider
            
        Returns:
            bool: True si succès
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE sessions SET is_active = FALSE WHERE session_token = ?
            ''', (session_token,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'invalidation de la session: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Nettoie les sessions expirées
        
        Returns:
            int: Nombre de sessions nettoyées
        """
        try:
            import time
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE sessions SET is_active = FALSE 
                WHERE expires_at <= ? AND is_active = TRUE
            ''', (time.time(),))
            
            cleaned = cursor.rowcount
            conn.commit()
            conn.close()
            
            return cleaned
            
        except Exception as e:
            print(f"Erreur lors du nettoyage des sessions: {e}")
            return 0
    
    def get_user_messages(self, username: str, limit: int = 50) -> List[Dict]:
        """
        Récupère les messages d'un utilisateur
        
        Args:
            username: Nom d'utilisateur
            limit: Nombre maximum de messages
            
        Returns:
            List[Dict]: Liste des messages
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT sender, recipient, encrypted_message, timestamp, is_read
                FROM messages 
                WHERE sender = ? OR recipient = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (username, username, limit))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'sender': row[0],
                    'recipient': row[1],
                    'message': row[2],
                    'timestamp': row[3],
                    'is_read': bool(row[4])
                })
            
            conn.close()
            return messages
            
        except Exception as e:
            print(f"Erreur lors de la récupération des messages: {e}")
            return []
    
    def get_received_messages(self, username: str) -> List[Dict]:
        """
        Récupère les messages reçus par un utilisateur
        
        Args:
            username: Nom d'utilisateur
            
        Returns:
            List[Dict]: Liste des messages reçus
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT sender, recipient, encrypted_message, timestamp, is_read
                FROM messages 
                WHERE recipient = ?
                ORDER BY timestamp DESC
            """, (username,))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'sender': row[0],
                    'recipient': row[1],
                    'message': row[2],
                    'timestamp': row[3],
                    'is_read': bool(row[4])
                })
            
            conn.close()
            return messages
            
        except Exception as e:
            print(f"Erreur lors de la récupération des messages reçus: {e}")
            return []
    
    def search_messages(self, username: str, query: str) -> List[Dict]:
        """
        Recherche dans les messages d'un utilisateur
        
        Args:
            username: Nom d'utilisateur
            query: Terme de recherche
            
        Returns:
            List[Dict]: Liste des messages correspondants
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT sender, recipient, encrypted_message, timestamp, is_read
                FROM messages 
                WHERE (sender = ? OR recipient = ?) 
                AND message_hash LIKE ?
                ORDER BY timestamp DESC
            """, (username, username, f'%{query}%'))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'sender': row[0],
                    'recipient': row[1],
                    'message': row[2],
                    'timestamp': row[3],
                    'is_read': bool(row[4])
                })
            
            conn.close()
            return messages
            
        except Exception as e:
            print(f"Erreur lors de la recherche: {e}")
            return []
