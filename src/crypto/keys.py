"""
Gestion des clés pour MessagerCrypt
Génération, stockage et rotation des clés
"""
import os
import json
import base64
from pathlib import Path
from typing import Dict, Optional, Tuple
from cryptography.hazmat.primitives import serialization
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from config.settings import DATA_DIR, SALT_SIZE
from .encryption import EncryptionManager


class KeyManager:
    """Gestionnaire de clés pour MessagerCrypt"""
    
    def __init__(self):
        self.encryption_manager = EncryptionManager()
        self.ph = PasswordHasher()
        self.keys_file = DATA_DIR / "user_keys.json"
    
    def generate_user_keys(self, username: str, password: str) -> Dict:
        """
        Génère et stocke les clés pour un nouvel utilisateur
        
        Args:
            username: Nom d'utilisateur
            password: Mot de passe
            
        Returns:
            Dict: Informations des clés générées
        """
        # Génération de la paire RSA
        private_key_pem, public_key_pem = self.encryption_manager.generate_rsa_keypair()
        
        # Génération d'un sel pour le chiffrement de la clé privée
        salt = os.urandom(SALT_SIZE)
        
        # Dérivation d'une clé à partir du mot de passe
        derived_key = self.encryption_manager.derive_key_from_password(password, salt)
        
        # Chiffrement de la clé privée avec AES
        nonce, encrypted_private_key = self.encryption_manager.encrypt_with_aes(
            private_key_pem, derived_key
        )
        
        # Hachage du mot de passe avec Argon2
        password_hash = self.ph.hash(password)
        
        # Création de l'entrée utilisateur
        user_data = {
            "username": username,
            "password_hash": password_hash,
            "public_key": base64.b64encode(public_key_pem).decode(),
            "encrypted_private_key": base64.b64encode(encrypted_private_key).decode(),
            "salt": base64.b64encode(salt).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "created_at": self._get_timestamp()
        }
        
        # Sauvegarde des clés
        self._save_user_keys(user_data)
        
        return {
            "username": username,
            "public_key": public_key_pem,
            "private_key": private_key_pem,
            "status": "success"
        }
    
    def load_user_keys(self, username: str, password: str) -> Optional[Dict]:
        """
        Charge les clés d'un utilisateur existant
        
        Args:
            username: Nom d'utilisateur
            password: Mot de passe
            
        Returns:
            Optional[Dict]: Clés de l'utilisateur ou None si échec
        """
        try:
            user_data = self._load_user_data(username)
            if not user_data:
                return None
            
            # Vérification du mot de passe
            try:
                self.ph.verify(user_data["password_hash"], password)
            except VerifyMismatchError:
                return None
            
            # Déchiffrement de la clé privée
            salt = base64.b64decode(user_data["salt"])
            nonce = base64.b64decode(user_data["nonce"])
            encrypted_private_key = base64.b64decode(user_data["encrypted_private_key"])
            
            derived_key = self.encryption_manager.derive_key_from_password(
                password, salt
            )
            
            private_key_pem = self.encryption_manager.decrypt_with_aes(
                encrypted_private_key, derived_key, nonce
            )
            
            public_key_pem = base64.b64decode(user_data["public_key"])
            
            return {
                "username": username,
                "public_key": public_key_pem,
                "private_key": private_key_pem,
                "status": "success"
            }
            
        except Exception as e:
            print(f"Erreur lors du chargement des clés: {e}")
            return None
    
    def get_public_key(self, username: str) -> Optional[bytes]:
        """
        Récupère la clé publique d'un utilisateur
        
        Args:
            username: Nom d'utilisateur
            
        Returns:
            Optional[bytes]: Clé publique ou None
        """
        try:
            user_data = self._load_user_data(username)
            if user_data:
                return base64.b64decode(user_data["public_key"])
            return None
        except Exception:
            return None
    
    def rotate_keys(self, username: str, password: str) -> bool:
        """
        Effectue une rotation des clés pour un utilisateur
        
        Args:
            username: Nom d'utilisateur
            password: Mot de passe actuel
            
        Returns:
            bool: True si succès, False sinon
        """
        try:
            # Vérification de l'authentification
            user_data = self._load_user_data(username)
            if not user_data:
                return False
            
            try:
                self.ph.verify(user_data["password_hash"], password)
            except VerifyMismatchError:
                return False
            
            # Génération de nouvelles clés
            new_keys = self.generate_user_keys(username, password)
            
            return new_keys["status"] == "success"
            
        except Exception:
            return False
    
    def _save_user_keys(self, user_data: Dict) -> None:
        """Sauvegarde les données utilisateur"""
        try:
            # Chargement des données existantes
            if self.keys_file.exists():
                with open(self.keys_file, 'r') as f:
                    all_users = json.load(f)
            else:
                all_users = {}
            
            # Ajout/mise à jour de l'utilisateur
            all_users[user_data["username"]] = user_data
            
            # Sauvegarde
            with open(self.keys_file, 'w') as f:
                json.dump(all_users, f, indent=2)
                
        except Exception as e:
            print(f"Erreur lors de la sauvegarde: {e}")
    
    def _load_user_data(self, username: str) -> Optional[Dict]:
        """Charge les données d'un utilisateur"""
        try:
            if not self.keys_file.exists():
                return None
            
            with open(self.keys_file, 'r') as f:
                all_users = json.load(f)
            
            return all_users.get(username)
            
        except Exception:
            return None
    
    def _get_timestamp(self) -> str:
        """Retourne un timestamp formaté"""
        import time
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    def list_users(self) -> list:
        """Liste tous les utilisateurs enregistrés"""
        try:
            if not self.keys_file.exists():
                return []
            
            with open(self.keys_file, 'r') as f:
                all_users = json.load(f)
            
            return list(all_users.keys())
            
        except Exception:
            return []
