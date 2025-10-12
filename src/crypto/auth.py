"""
Module d'authentification pour MessagerCrypt
Gestion des signatures et authentification
"""
import hashlib
import hmac
import time
from typing import Dict, Optional
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

from config.settings import MESSAGE_TIMEOUT


class AuthManager:
    """Gestionnaire d'authentification pour MessagerCrypt"""
    
    def __init__(self):
        self.backend = default_backend()
    
    def create_signature(self, data: bytes, private_key_pem: bytes) -> bytes:
        """
        Crée une signature RSA pour des données
        
        Args:
            data: Données à signer
            private_key_pem: Clé privée PEM
            
        Returns:
            bytes: Signature
        """
        private_key = serialization.load_pem_private_key(
            private_key_pem, password=None, backend=self.backend
        )
        
        signature = private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return signature
    
    def verify_signature(self, data: bytes, signature: bytes, public_key_pem: bytes) -> bool:
        """
        Vérifie une signature RSA
        
        Args:
            data: Données originales
            signature: Signature à vérifier
            public_key_pem: Clé publique PEM
            
        Returns:
            bool: True si signature valide
        """
        try:
            public_key = serialization.load_pem_public_key(
                public_key_pem, backend=self.backend
            )
            
            public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
            
        except Exception:
            return False
    
    def create_hmac(self, data: bytes, key: bytes) -> bytes:
        """
        Crée un HMAC pour des données
        
        Args:
            data: Données à hacher
            key: Clé HMAC
            
        Returns:
            bytes: HMAC
        """
        return hmac.new(key, data, hashlib.sha256).digest()
    
    def verify_hmac(self, data: bytes, signature: bytes, key: bytes) -> bool:
        """
        Vérifie un HMAC
        
        Args:
            data: Données originales
            signature: HMAC à vérifier
            key: Clé HMAC
            
        Returns:
            bool: True si HMAC valide
        """
        expected_hmac = self.create_hmac(data, key)
        return hmac.compare_digest(signature, expected_hmac)
    
    def create_anti_replay_token(self, username: str, timestamp: float) -> str:
        """
        Crée un token anti-rejeu
        
        Args:
            username: Nom d'utilisateur
            timestamp: Timestamp
            
        Returns:
            str: Token anti-rejeu
        """
        data = f"{username}:{timestamp}".encode()
        token = hashlib.sha256(data).hexdigest()
        return token
    
    def verify_anti_replay_token(self, token: str, username: str, timestamp: float) -> bool:
        """
        Vérifie un token anti-rejeu
        
        Args:
            token: Token à vérifier
            username: Nom d'utilisateur
            timestamp: Timestamp
            
        Returns:
            bool: True si token valide
        """
        expected_token = self.create_anti_replay_token(username, timestamp)
        return token == expected_token
    
    def is_message_fresh(self, timestamp: float) -> bool:
        """
        Vérifie si un message est récent (anti-rejeu temporel)
        
        Args:
            timestamp: Timestamp du message
            
        Returns:
            bool: True si message récent
        """
        current_time = time.time()
        return (current_time - timestamp) <= MESSAGE_TIMEOUT
    
    def create_authenticated_message(self, message: str, sender: str, 
                                   private_key_pem: bytes) -> Dict:
        """
        Crée un message authentifié avec signature
        
        Args:
            message: Message à envoyer
            sender: Expéditeur
            private_key_pem: Clé privée de l'expéditeur
            
        Returns:
            Dict: Message authentifié
        """
        timestamp = time.time()
        
        # Création du contenu à signer
        content = f"{sender}:{message}:{timestamp}".encode()
        
        # Signature du contenu
        signature = self.create_signature(content, private_key_pem)
        
        # Token anti-rejeu
        anti_replay_token = self.create_anti_replay_token(sender, timestamp)
        
        return {
            "message": message,
            "sender": sender,
            "timestamp": timestamp,
            "signature": signature.hex(),
            "anti_replay_token": anti_replay_token,
            "content_hash": hashlib.sha256(content).hexdigest()
        }
    
    def verify_authenticated_message(self, message_data: Dict, 
                                   public_key_pem: bytes) -> bool:
        """
        Vérifie un message authentifié
        
        Args:
            message_data: Données du message
            public_key_pem: Clé publique de l'expéditeur
            
        Returns:
            bool: True si message valide
        """
        try:
            # Vérification de la fraîcheur
            if not self.is_message_fresh(message_data["timestamp"]):
                return False
            
            # Reconstruction du contenu
            content = f"{message_data['sender']}:{message_data['message']}:{message_data['timestamp']}".encode()
            
            # Vérification de la signature
            signature = bytes.fromhex(message_data["signature"])
            if not self.verify_signature(content, signature, public_key_pem):
                return False
            
            # Vérification du token anti-rejeu
            if not self.verify_anti_replay_token(
                message_data["anti_replay_token"],
                message_data["sender"],
                message_data["timestamp"]
            ):
                return False
            
            return True
            
        except Exception:
            return False
    
    def create_session_token(self, username: str, session_key: bytes) -> str:
        """
        Crée un token de session
        
        Args:
            username: Nom d'utilisateur
            session_key: Clé de session
            
        Returns:
            str: Token de session
        """
        timestamp = time.time()
        data = f"{username}:{timestamp}".encode()
        token = hmac.new(session_key, data, hashlib.sha256).hexdigest()
        return token
    
    def verify_session_token(self, token: str, username: str, 
                           session_key: bytes) -> bool:
        """
        Vérifie un token de session
        
        Args:
            token: Token à vérifier
            username: Nom d'utilisateur
            session_key: Clé de session
            
        Returns:
            bool: True si token valide
        """
        try:
            # Pour la vérification, on utilise le timestamp actuel
            # En production, on devrait stocker les tokens valides
            timestamp = time.time()
            data = f"{username}:{timestamp}".encode()
            expected_token = hmac.new(session_key, data, hashlib.sha256).hexdigest()
            
            return hmac.compare_digest(token, expected_token)
            
        except Exception:
            return False
