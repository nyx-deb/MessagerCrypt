"""
Module de chiffrement pour MessagerCrypt
Implémente AES-256-GCM et RSA-4096
"""
import base64
import json
import time
from typing import Dict, Tuple, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import secrets

from config.settings import RSA_KEY_SIZE, AES_KEY_SIZE, NONCE_SIZE, SALT_SIZE, ITERATIONS


class EncryptionManager:
    """Gestionnaire de chiffrement pour MessagerCrypt"""
    
    def __init__(self):
        self.backend = default_backend()
    
    def generate_rsa_keypair(self) -> Tuple[bytes, bytes]:
        """
        Génère une paire de clés RSA-4096
        
        Returns:
            Tuple[bytes, bytes]: (clé privée, clé publique)
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=RSA_KEY_SIZE,
            backend=self.backend
        )
        
        public_key = private_key.public_key()
        
        # Sérialisation des clés
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem, public_pem
    
    def encrypt_with_rsa(self, data: bytes, public_key_pem: bytes) -> bytes:
        """
        Chiffre des données avec RSA-OAEP
        
        Args:
            data: Données à chiffrer
            public_key_pem: Clé publique PEM
            
        Returns:
            bytes: Données chiffrées
        """
        public_key = serialization.load_pem_public_key(
            public_key_pem, backend=self.backend
        )
        
        encrypted = public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return encrypted
    
    def decrypt_with_rsa(self, encrypted_data: bytes, private_key_pem: bytes) -> bytes:
        """
        Déchiffre des données avec RSA-OAEP
        
        Args:
            encrypted_data: Données chiffrées
            private_key_pem: Clé privée PEM
            
        Returns:
            bytes: Données déchiffrées
        """
        private_key = serialization.load_pem_private_key(
            private_key_pem, password=None, backend=self.backend
        )
        
        decrypted = private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return decrypted
    
    def generate_aes_key(self) -> bytes:
        """Génère une clé AES-256"""
        return secrets.token_bytes(AES_KEY_SIZE)
    
    def encrypt_with_aes(self, data: bytes, key: bytes) -> Tuple[bytes, bytes]:
        """
        Chiffre des données avec AES-256-GCM
        
        Args:
            data: Données à chiffrer
            key: Clé AES
            
        Returns:
            Tuple[bytes, bytes]: (nonce, données chiffrées)
        """
        nonce = secrets.token_bytes(NONCE_SIZE)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        return nonce, ciphertext
    
    def decrypt_with_aes(self, ciphertext: bytes, key: bytes, nonce: bytes) -> bytes:
        """
        Déchiffre des données avec AES-256-GCM
        
        Args:
            ciphertext: Données chiffrées
            key: Clé AES
            nonce: Nonce utilisé pour le chiffrement
            
        Returns:
            bytes: Données déchiffrées
        """
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)
    
    def derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """
        Dérive une clé à partir d'un mot de passe avec PBKDF2
        
        Args:
            password: Mot de passe
            salt: Sel
            
        Returns:
            bytes: Clé dérivée
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=AES_KEY_SIZE,
            salt=salt,
            iterations=ITERATIONS,
            backend=self.backend
        )
        return kdf.derive(password.encode())
    
    def create_message_packet(self, message: str, sender: str, recipient: str, 
                            aes_key: bytes, rsa_public_key: bytes) -> Dict:
        """
        Crée un paquet de message chiffré
        
        Args:
            message: Message à envoyer
            sender: Expéditeur
            recipient: Destinataire
            aes_key: Clé AES de session
            rsa_public_key: Clé publique RSA du destinataire
            
        Returns:
            Dict: Paquet de message chiffré
        """
        # Chiffrement du message avec AES
        message_bytes = message.encode('utf-8')
        nonce, encrypted_message = self.encrypt_with_aes(message_bytes, aes_key)
        
        # Chiffrement de la clé AES avec RSA
        encrypted_aes_key = self.encrypt_with_rsa(aes_key, rsa_public_key)
        
        # Création du paquet
        packet = {
            "version": "1.0",
            "timestamp": time.time(),
            "sender": sender,
            "recipient": recipient,
            "message": base64.b64encode(encrypted_message).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "aes_key": base64.b64encode(encrypted_aes_key).decode(),
            "meta": {
                "enc": "AES-256-GCM",
                "key_enc": "RSA-4096-OAEP"
            }
        }
        
        return packet
    
    def decrypt_message_packet(self, packet: Dict, private_key_pem: bytes) -> Tuple[str, str, str]:
        """
        Déchiffre un paquet de message
        
        Args:
            packet: Paquet de message chiffré
            private_key_pem: Clé privée RSA
            
        Returns:
            Tuple[str, str, str]: (message, sender, timestamp)
        """
        # Déchiffrement de la clé AES
        encrypted_aes_key = base64.b64decode(packet["aes_key"])
        aes_key = self.decrypt_with_rsa(encrypted_aes_key, private_key_pem)
        
        # Déchiffrement du message
        encrypted_message = base64.b64decode(packet["message"])
        nonce = base64.b64decode(packet["nonce"])
        message_bytes = self.decrypt_with_aes(encrypted_message, aes_key, nonce)
        
        return message_bytes.decode('utf-8'), packet["sender"], str(packet["timestamp"])
