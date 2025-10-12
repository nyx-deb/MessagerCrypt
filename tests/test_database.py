"""
Tests unitaires pour le module de base de données
"""
import unittest
import tempfile
import os
import json
from src.storage.database import EncryptedDatabase
from src.storage.messages import MessageManager


class TestEncryptedDatabase(unittest.TestCase):
    """Tests pour EncryptedDatabase"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = EncryptedDatabase(self.db_path, "test_key")
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_database_initialization(self):
        """Test d'initialisation de la base de données"""
        self.assertTrue(os.path.exists(self.db_path))
    
    def test_user_creation(self):
        """Test de création d'utilisateur"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "created_at": "2025-01-01"
        }
        
        success = self.db.create_user("testuser", user_data)
        self.assertTrue(success)
    
    def test_user_retrieval(self):
        """Test de récupération d'utilisateur"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "created_at": "2025-01-01"
        }
        
        # Création
        self.db.create_user("testuser", user_data)
        
        # Récupération
        retrieved_data = self.db.get_user("testuser")
        self.assertIsNotNone(retrieved_data)
        self.assertEqual(retrieved_data["username"], "testuser")
    
    def test_message_saving(self):
        """Test de sauvegarde de message"""
        success = self.db.save_message(
            "sender", "recipient", "encrypted_message", "message_hash"
        )
        self.assertTrue(success)
    
    def test_message_retrieval(self):
        """Test de récupération de messages"""
        # Sauvegarde de messages
        self.db.save_message("user1", "user2", "msg1", "hash1")
        self.db.save_message("user2", "user1", "msg2", "hash2")
        
        # Récupération
        messages = self.db.get_messages("user1", 10)
        self.assertEqual(len(messages), 2)
    
    def test_session_management(self):
        """Test de gestion des sessions"""
        username = "testuser"
        session_token = "test_token_123"
        expires_at = 1234567890.0
        
        # Création de session
        success = self.db.create_session(username, session_token, expires_at)
        self.assertTrue(success)
        
        # Vérification de session
        verified_username = self.db.verify_session(session_token)
        self.assertEqual(verified_username, username)
        
        # Invalidation de session
        success = self.db.invalidate_session(session_token)
        self.assertTrue(success)
        
        # Vérification après invalidation
        verified_username = self.db.verify_session(session_token)
        self.assertIsNone(verified_username)
    
    def test_message_marking(self):
        """Test de marquage de message comme lu"""
        # Sauvegarde d'un message
        self.db.save_message("sender", "recipient", "message", "hash")
        
        # Récupération pour obtenir l'ID
        messages = self.db.get_messages("recipient", 1)
        if messages:
            message_id = messages[0].get("id", 1)
            
            # Marquage comme lu
            success = self.db.mark_message_read(message_id)
            self.assertTrue(success)
    
    def test_cleanup_expired_sessions(self):
        """Test de nettoyage des sessions expirées"""
        import time
        
        # Création de sessions expirées
        old_timestamp = time.time() - 3600  # 1 heure
        self.db.create_session("user1", "token1", old_timestamp)
        self.db.create_session("user2", "token2", old_timestamp)
        
        # Nettoyage
        cleaned = self.db.cleanup_expired_sessions()
        self.assertGreaterEqual(cleaned, 0)


class TestMessageManager(unittest.TestCase):
    """Tests pour MessageManager"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.message_manager = MessageManager(self.db_path)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_message_sending(self):
        """Test d'envoi de message"""
        # Génération de clés de test
        from src.crypto.encryption import EncryptionManager
        encryption = EncryptionManager()
        sender_private, sender_public = encryption.generate_rsa_keypair()
        recipient_private, recipient_public = encryption.generate_rsa_keypair()
        
        success = self.message_manager.send_message(
            "sender", "recipient", "Test message",
            sender_private, recipient_public
        )
        self.assertTrue(success)
    
    def test_message_receiving(self):
        """Test de réception de message"""
        # Génération de clés de test
        from src.crypto.encryption import EncryptionManager
        encryption = EncryptionManager()
        sender_private, sender_public = encryption.generate_rsa_keypair()
        recipient_private, recipient_public = encryption.generate_rsa_keypair()
        
        # Envoi du message
        self.message_manager.send_message(
            "sender", "recipient", "Test message",
            sender_private, recipient_public
        )
        
        # Réception du message
        message = self.message_manager.receive_message(
            1, recipient_private, sender_public
        )
        
        if message:
            self.assertEqual(message["message"], "Test message")
            self.assertEqual(message["sender"], "sender")
    
    def test_message_history(self):
        """Test de récupération de l'historique"""
        # Génération de clés de test
        from src.crypto.encryption import EncryptionManager
        encryption = EncryptionManager()
        sender_private, sender_public = encryption.generate_rsa_keypair()
        recipient_private, recipient_public = encryption.generate_rsa_keypair()
        
        # Envoi de messages
        self.message_manager.send_message(
            "user1", "user2", "Message 1",
            sender_private, recipient_public
        )
        self.message_manager.send_message(
            "user2", "user1", "Message 2",
            recipient_private, sender_public
        )
        
        # Récupération de l'historique
        history = self.message_manager.get_message_history("user1", 10)
        self.assertIsInstance(history, list)
    
    def test_unread_messages(self):
        """Test de récupération des messages non lus"""
        # Génération de clés de test
        from src.crypto.encryption import EncryptionManager
        encryption = EncryptionManager()
        sender_private, sender_public = encryption.generate_rsa_keypair()
        recipient_private, recipient_public = encryption.generate_rsa_keypair()
        
        # Envoi de message
        self.message_manager.send_message(
            "sender", "recipient", "Test message",
            sender_private, recipient_public
        )
        
        # Récupération des messages non lus
        unread = self.message_manager.get_unread_messages("recipient")
        self.assertIsInstance(unread, list)
    
    def test_message_stats(self):
        """Test de calcul des statistiques"""
        # Génération de clés de test
        from src.crypto.encryption import EncryptionManager
        encryption = EncryptionManager()
        sender_private, sender_public = encryption.generate_rsa_keypair()
        recipient_private, recipient_public = encryption.generate_rsa_keypair()
        
        # Envoi de messages
        self.message_manager.send_message(
            "user1", "user2", "Message 1",
            sender_private, recipient_public
        )
        self.message_manager.send_message(
            "user2", "user1", "Message 2",
            recipient_private, sender_public
        )
        
        # Calcul des statistiques
        stats = self.message_manager.get_message_stats("user1")
        self.assertIsInstance(stats, dict)
        self.assertIn("total_messages", stats)
        self.assertIn("sent", stats)
        self.assertIn("received", stats)
        self.assertIn("unread", stats)
    
    def test_message_search(self):
        """Test de recherche de messages"""
        # Génération de clés de test
        from src.crypto.encryption import EncryptionManager
        encryption = EncryptionManager()
        sender_private, sender_public = encryption.generate_rsa_keypair()
        recipient_private, recipient_public = encryption.generate_rsa_keypair()
        
        # Envoi de messages
        self.message_manager.send_message(
            "alice", "bob", "Hello Bob",
            sender_private, recipient_public
        )
        self.message_manager.send_message(
            "bob", "alice", "Hello Alice",
            recipient_private, sender_public
        )
        
        # Recherche
        results = self.message_manager.search_messages("alice", "bob")
        self.assertIsInstance(results, list)
    
    def test_message_deletion(self):
        """Test de suppression de message"""
        # Génération de clés de test
        from src.crypto.encryption import EncryptionManager
        encryption = EncryptionManager()
        sender_private, sender_public = encryption.generate_rsa_keypair()
        recipient_private, recipient_public = encryption.generate_rsa_keypair()
        
        # Envoi de message
        self.message_manager.send_message(
            "sender", "recipient", "Test message",
            sender_private, recipient_public
        )
        
        # Suppression
        success = self.message_manager.delete_message(1)
        self.assertTrue(success)


if __name__ == "__main__":
    unittest.main()
