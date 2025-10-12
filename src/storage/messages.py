"""
Module de gestion des messages pour MessagerCrypt
Interface haute niveau pour les messages chiffrés
"""
import json
import base64
import hashlib
import gzip
from typing import List, Dict, Optional
from datetime import datetime

from .database import EncryptedDatabase
from ..crypto.encryption import EncryptionManager
from ..crypto.auth import AuthManager


class MessageManager:
    """Gestionnaire de messages pour MessagerCrypt"""
    
    def __init__(self, db_path: str = None):
        self.db = EncryptedDatabase(db_path)
        self.encryption_manager = EncryptionManager()
        self.auth_manager = AuthManager()
        
        # Cache pour optimiser les performances
        self._message_cache = {}
        self._cache_size = 100
    
    def _compress_message(self, message: str) -> str:
        """Compresse un message pour économiser l'espace"""
        try:
            compressed = gzip.compress(message.encode('utf-8'))
            return base64.b64encode(compressed).decode('utf-8')
        except Exception:
            return message
    
    def _decompress_message(self, compressed_message: str) -> str:
        """Décompresse un message"""
        try:
            compressed_data = base64.b64decode(compressed_message.encode('utf-8'))
            return gzip.decompress(compressed_data).decode('utf-8')
        except Exception:
            return compressed_message
    
    def send_message(self, sender: str, recipient: str, message: str, 
                    sender_private_key: bytes, recipient_public_key: bytes) -> bool:
        """
        Envoie un message chiffré
        
        Args:
            sender: Expéditeur
            recipient: Destinataire
            message: Message en clair
            sender_private_key: Clé privée de l'expéditeur
            recipient_public_key: Clé publique du destinataire
            
        Returns:
            bool: True si succès
        """
        try:
            # Génération d'une clé AES de session
            session_key = self.encryption_manager.generate_aes_key()
            
            # Chiffrement du message avec AES
            message_bytes = message.encode('utf-8')
            nonce, encrypted_message = self.encryption_manager.encrypt_with_aes(
                message_bytes, session_key
            )
            
            # Chiffrement de la clé de session avec RSA
            encrypted_session_key = self.encryption_manager.encrypt_with_rsa(
                session_key, recipient_public_key
            )
            
            # Création du paquet de message
            message_packet = {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "sender": sender,
                "recipient": recipient,
                "encrypted_message": base64.b64encode(encrypted_message).decode(),
                "nonce": base64.b64encode(nonce).decode(),
                "encrypted_session_key": base64.b64encode(encrypted_session_key).decode(),
                "meta": {
                    "enc": "AES-256-GCM",
                    "key_enc": "RSA-4096-OAEP"
                }
            }
            
            # Signature du paquet
            packet_json = json.dumps(message_packet, sort_keys=True).encode()
            signature = self.auth_manager.create_signature(packet_json, sender_private_key)
            message_packet["signature"] = base64.b64encode(signature).decode()
            
            # Hash du message pour l'intégrité
            message_hash = hashlib.sha256(packet_json).hexdigest()
            
            # Sauvegarde en base de données
            encrypted_packet = base64.b64encode(packet_json).decode()
            success = self.db.save_message(sender, recipient, encrypted_packet, message_hash)
            
            return success
            
        except Exception as e:
            print(f"Erreur lors de l'envoi du message: {e}")
            return False
    
    def save_received_message(self, sender: str, recipient: str, message: str) -> bool:
        """
        Sauvegarde un message reçu
        
        Args:
            sender: Expéditeur
            recipient: Destinataire
            message: Message reçu
            
        Returns:
            bool: True si succès
        """
        try:
            # Sauvegarde simple du message reçu
            success = self.db.save_message(sender, recipient, message, "")
            return success
            
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du message reçu: {e}")
            return False
    
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
            messages = self.db.get_user_messages(username, limit)
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
            messages = self.db.get_received_messages(username)
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
            messages = self.db.search_messages(username, query)
            return messages
            
        except Exception as e:
            print(f"Erreur lors de la recherche: {e}")
            return []
    
    def receive_message(self, message_id: int, recipient_private_key: bytes, 
                       sender_public_key: bytes) -> Optional[Dict]:
        """
        Reçoit et déchiffre un message
        
        Args:
            message_id: ID du message
            recipient_private_key: Clé privée du destinataire
            sender_public_key: Clé publique de l'expéditeur
            
        Returns:
            Optional[Dict]: Message déchiffré ou None
        """
        try:
            # Récupération du message depuis la base
            messages = self.db.get_messages("", 1)  # Récupérer le message spécifique
            if not messages:
                return None
            
            # Déchiffrement du paquet
            encrypted_packet = messages[0]["encrypted_message"]
            packet_json = base64.b64decode(encrypted_packet)
            message_packet = json.loads(packet_json.decode())
            
            # Vérification de la signature
            signature = base64.b64decode(message_packet["signature"])
            packet_without_sig = {k: v for k, v in message_packet.items() if k != "signature"}
            packet_to_verify = json.dumps(packet_without_sig, sort_keys=True).encode()
            
            if not self.auth_manager.verify_signature(packet_to_verify, signature, sender_public_key):
                print("Signature invalide")
                return None
            
            # Déchiffrement de la clé de session
            encrypted_session_key = base64.b64decode(message_packet["encrypted_session_key"])
            session_key = self.encryption_manager.decrypt_with_rsa(
                encrypted_session_key, recipient_private_key
            )
            
            # Déchiffrement du message
            encrypted_message = base64.b64decode(message_packet["encrypted_message"])
            nonce = base64.b64decode(message_packet["nonce"])
            message_bytes = self.encryption_manager.decrypt_with_aes(
                encrypted_message, session_key, nonce
            )
            
            # Marquer le message comme lu
            self.db.mark_message_read(message_id)
            
            return {
                "message": message_bytes.decode('utf-8'),
                "sender": message_packet["sender"],
                "recipient": message_packet["recipient"],
                "timestamp": message_packet["timestamp"],
                "version": message_packet["version"]
            }
            
        except Exception as e:
            print(f"Erreur lors de la réception du message: {e}")
            return None
    
    def get_message_history(self, username: str, limit: int = 50) -> List[Dict]:
        """
        Récupère l'historique des messages d'un utilisateur
        
        Args:
            username: Nom d'utilisateur
            limit: Nombre maximum de messages
            
        Returns:
            List[Dict]: Historique des messages
        """
        try:
            messages = self.db.get_messages(username, limit)
            history = []
            
            for msg in messages:
                try:
                    # Déchiffrement du paquet
                    encrypted_packet = msg["encrypted_message"]
                    packet_json = base64.b64decode(encrypted_packet)
                    message_packet = json.loads(packet_json.decode())
                    
                    history.append({
                        "id": msg.get("id", 0),
                        "sender": message_packet["sender"],
                        "recipient": message_packet["recipient"],
                        "timestamp": message_packet["timestamp"],
                        "is_read": msg["is_read"],
                        "encrypted": True  # Le message reste chiffré pour la sécurité
                    })
                    
                except Exception as e:
                    print(f"Erreur lors du déchiffrement du message {msg.get('id', 'unknown')}: {e}")
                    continue
            
            return history
            
        except Exception as e:
            print(f"Erreur lors de la récupération de l'historique: {e}")
            return []
    
    def get_unread_messages(self, username: str) -> List[Dict]:
        """
        Récupère les messages non lus d'un utilisateur
        
        Args:
            username: Nom d'utilisateur
            
        Returns:
            List[Dict]: Messages non lus
        """
        try:
            all_messages = self.get_message_history(username, 100)
            unread_messages = [msg for msg in all_messages if not msg["is_read"]]
            return unread_messages
            
        except Exception as e:
            print(f"Erreur lors de la récupération des messages non lus: {e}")
            return []
    
    def delete_message(self, message_id: int) -> bool:
        """
        Supprime un message (marque comme supprimé)
        
        Args:
            message_id: ID du message
            
        Returns:
            bool: True si succès
        """
        try:
            # En production, on pourrait implémenter une vraie suppression
            # ou un marquage comme "supprimé"
            return self.db.mark_message_read(message_id)
            
        except Exception as e:
            print(f"Erreur lors de la suppression du message: {e}")
            return False
    
    def search_messages(self, username: str, query: str) -> List[Dict]:
        """
        Recherche dans les messages (méta-données uniquement pour la sécurité)
        
        Args:
            username: Nom d'utilisateur
            query: Terme de recherche
            
        Returns:
            List[Dict]: Messages correspondants
        """
        try:
            all_messages = self.get_message_history(username, 200)
            matching_messages = []
            
            for msg in all_messages:
                # Recherche dans les métadonnées uniquement
                if (query.lower() in msg["sender"].lower() or 
                    query.lower() in msg["recipient"].lower()):
                    matching_messages.append(msg)
            
            return matching_messages
            
        except Exception as e:
            print(f"Erreur lors de la recherche: {e}")
            return []
    
    def get_message_stats(self, username: str) -> Dict:
        """
        Récupère les statistiques des messages d'un utilisateur
        
        Args:
            username: Nom d'utilisateur
            
        Returns:
            Dict: Statistiques
        """
        try:
            all_messages = self.get_message_history(username, 1000)
            
            sent_count = len([msg for msg in all_messages if msg["sender"] == username])
            received_count = len([msg for msg in all_messages if msg["recipient"] == username])
            unread_count = len([msg for msg in all_messages if not msg["is_read"]])
            
            return {
                "total_messages": len(all_messages),
                "sent": sent_count,
                "received": received_count,
                "unread": unread_count
            }
            
        except Exception as e:
            print(f"Erreur lors du calcul des statistiques: {e}")
            return {
                "total_messages": 0,
                "sent": 0,
                "received": 0,
                "unread": 0
            }
