"""
Tests d'intégration pour MessagerCrypt
Tests complets du système
"""
import unittest
import threading
import time
import tempfile
import os
from unittest.mock import patch, Mock
from src.main import MessagerCryptApp
from src.server import MessagerCryptServer
from src.client import MessagerCryptClient
from src.crypto.encryption import EncryptionManager
from src.crypto.keys import KeyManager
from src.storage.database import EncryptedDatabase


class TestMessagerCryptIntegration(unittest.TestCase):
    """Tests d'intégration pour MessagerCrypt"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.app = MessagerCryptApp()
        self.server = MessagerCryptServer("127.0.0.1", 8891)
        self.client = MessagerCryptClient("127.0.0.1", 8891)
    
    def tearDown(self):
        if self.server.running:
            self.server.stop()
        if self.client.connected:
            self.client.disconnect()
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_full_encryption_flow(self):
        """Test du flux complet de chiffrement"""
        # Génération des clés
        encryption = EncryptionManager()
        private_key, public_key = encryption.generate_rsa_keypair()
        
        # Test de chiffrement/déchiffrement
        test_message = "Hello, MessagerCrypt!"
        aes_key = encryption.generate_aes_key()
        
        # Chiffrement du message
        message_packet = encryption.create_message_packet(
            test_message, "sender", "recipient", aes_key, public_key
        )
        
        # Vérification du paquet
        self.assertIsInstance(message_packet, dict)
        self.assertIn("message", message_packet)
        self.assertIn("nonce", message_packet)
        self.assertIn("aes_key", message_packet)
        
        # Déchiffrement du message
        decrypted_message, sender, timestamp = encryption.decrypt_message_packet(
            message_packet, private_key
        )
        
        # Vérification
        self.assertEqual(decrypted_message, test_message)
        self.assertEqual(sender, "sender")
    
    def test_user_registration_and_authentication(self):
        """Test d'inscription et d'authentification d'utilisateur"""
        # Création d'un utilisateur
        key_manager = KeyManager()
        result = key_manager.generate_user_keys("testuser", "testpass")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["username"], "testuser")
        
        # Authentification
        user_keys = key_manager.load_user_keys("testuser", "testpass")
        
        self.assertIsNotNone(user_keys)
        self.assertEqual(user_keys["username"], "testuser")
        self.assertIsInstance(user_keys["public_key"], bytes)
        self.assertIsInstance(user_keys["private_key"], bytes)
    
    def test_database_operations(self):
        """Test des opérations de base de données"""
        # Initialisation de la base de données
        db_path = os.path.join(self.temp_dir, "test.db")
        db = EncryptedDatabase(db_path, "test_key")
        
        # Test de création d'utilisateur
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "created_at": "2025-01-01"
        }
        
        success = db.create_user("testuser", user_data)
        self.assertTrue(success)
        
        # Test de récupération d'utilisateur
        retrieved_data = db.get_user("testuser")
        self.assertIsNotNone(retrieved_data)
        self.assertEqual(retrieved_data["username"], "testuser")
        
        # Test de sauvegarde de message
        success = db.save_message(
            "sender", "recipient", "encrypted_message", "message_hash"
        )
        self.assertTrue(success)
        
        # Test de récupération de messages
        messages = db.get_messages("recipient", 10)
        self.assertIsInstance(messages, list)
    
    def test_full_remote_registration_flow(self):
        """Test du flux complet d'inscription distante"""
        # Démarrage du serveur
        server_thread = threading.Thread(target=self.server.start, daemon=True)
        server_thread.start()
        
        # Attente du démarrage
        time.sleep(1)
        
        # Connexion du client
        success = self.client.connect()
        self.assertTrue(success)
        
        # Inscription distante (génération de clés réelle)
        registered = self.client.register("alice", "alicepass")
        self.assertTrue(registered)
        
        # Vérification côté serveur
        self.assertIn("alice", self.server.key_manager.list_users())
        server_key = self.server.key_manager.get_public_key("alice")
        self.assertIsNotNone(server_key)
        self.assertGreater(len(server_key), 0)
        
        # Vérification : le client conserve sa clé privée localement
        client_keys = self.client.key_manager.load_user_keys("alice", "alicepass")
        self.assertIsNotNone(client_keys)
        self.assertEqual(client_keys["public_key"], server_key)
        
        # Distribution de la clé publique à un autre client
        fetched = self.client._request_public_key("alice")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched, server_key)
        
        # Arrêt du serveur
        self.server.stop()
    
    def test_server_client_communication(self):
        """Test de communication serveur-client"""
        # Démarrage du serveur
        server_thread = threading.Thread(target=self.server.start, daemon=True)
        server_thread.start()
        
        # Attente du démarrage
        time.sleep(1)
        
        # Connexion du client
        with patch.object(self.server.key_manager, 'verify_user') as mock_verify:
            mock_verify.return_value = b"mock_public_key"
            
            with patch.object(self.client.key_manager, 'load_user_keys') as mock_load:
                mock_load.return_value = {
                    "username": "testuser",
                    "public_key": b"mock_public_key",
                    "private_key": b"mock_private_key",
                    "status": "success"
                }
                
                # Test de connexion
                success = self.client.connect()
                self.assertTrue(success)
                
                # Test d'authentification
                auth_success = self.client.authenticate("testuser", "testpass")
                self.assertTrue(auth_success)
                
                # Test d'envoi de message
                with patch.object(self.client.key_manager, 'get_public_key') as mock_get_key:
                    mock_get_key.return_value = b"mock_public_key"
                    
                    with patch.object(self.client.encryption_manager, 'create_message_packet') as mock_packet:
                        mock_packet.return_value = {
                            "version": "1.0", "message": "encrypted",
                            "nonce": "nonce", "aes_key": "key"
                        }
                        
                        message_success = self.client.send_message("recipient", "Test message")
                        self.assertTrue(message_success)
        
        # Arrêt du serveur
        self.server.stop()
    
    def test_message_encryption_and_storage(self):
        """Test de chiffrement et stockage des messages"""
        # Génération des clés
        encryption = EncryptionManager()
        sender_private, sender_public = encryption.generate_rsa_keypair()
        recipient_private, recipient_public = encryption.generate_rsa_keypair()
        
        # Création du message
        message = "Test message for encryption"
        aes_key = encryption.generate_aes_key()
        
        # Chiffrement
        message_packet = encryption.create_message_packet(
            message, "sender", "recipient", aes_key, recipient_public
        )
        
        # Stockage en base de données
        db_path = os.path.join(self.temp_dir, "test.db")
        db = EncryptedDatabase(db_path, "test_key")
        
        success = db.save_message(
            "sender", "recipient", str(message_packet), "message_hash"
        )
        self.assertTrue(success)
        
        # Récupération et déchiffrement
        messages = db.get_messages("recipient", 10)
        self.assertIsInstance(messages, list)
        
        if messages:
            # Déchiffrement du message
            decrypted_message, sender, timestamp = encryption.decrypt_message_packet(
                message_packet, recipient_private
            )
            
            self.assertEqual(decrypted_message, message)
            self.assertEqual(sender, "sender")
    
    def test_session_management(self):
        """Test de gestion des sessions"""
        # Initialisation de la base de données
        db_path = os.path.join(self.temp_dir, "test.db")
        db = EncryptedDatabase(db_path, "test_key")
        
        # Création de session
        username = "testuser"
        session_token = "test_token_123"
        expires_at = time.time() + 3600  # 1 heure
        
        success = db.create_session(username, session_token, expires_at)
        self.assertTrue(success)
        
        # Vérification de session
        verified_username = db.verify_session(session_token)
        self.assertEqual(verified_username, username)
        
        # Invalidation de session
        success = db.invalidate_session(session_token)
        self.assertTrue(success)
        
        # Vérification après invalidation
        verified_username = db.verify_session(session_token)
        self.assertIsNone(verified_username)
    
    def test_error_handling(self):
        """Test de gestion des erreurs"""
        # Test avec des données invalides
        encryption = EncryptionManager()
        
        # Test avec clé invalide
        try:
            encryption.encrypt_with_rsa(b"test", b"invalid_key")
            self.fail("Expected exception")
        except Exception:
            pass  # Erreur attendue
        
        # Test avec données corrompues
        try:
            encryption.decrypt_with_aes(b"corrupted", b"key", b"nonce")
            self.fail("Expected exception")
        except Exception:
            pass  # Erreur attendue
    
    def test_performance_metrics(self):
        """Test des métriques de performance"""
        # Test de génération de clés
        encryption = EncryptionManager()
        
        start_time = time.time()
        private_key, public_key = encryption.generate_rsa_keypair()
        key_generation_time = time.time() - start_time
        
        self.assertLess(key_generation_time, 5.0)  # Moins de 5 secondes
        
        # Test de chiffrement
        test_data = b"Test data for performance testing"
        aes_key = encryption.generate_aes_key()
        
        start_time = time.time()
        nonce, encrypted = encryption.encrypt_with_aes(test_data, aes_key)
        encryption_time = time.time() - start_time
        
        self.assertLess(encryption_time, 1.0)  # Moins de 1 seconde
        
        # Test de déchiffrement
        start_time = time.time()
        decrypted = encryption.decrypt_with_aes(encrypted, aes_key, nonce)
        decryption_time = time.time() - start_time
        
        self.assertLess(decryption_time, 1.0)  # Moins de 1 seconde
        self.assertEqual(decrypted, test_data)
    
    def test_concurrent_operations(self):
        """Test d'opérations concurrentes"""
        # Test de génération de clés concurrente
        encryption = EncryptionManager()
        
        def generate_keys():
            return encryption.generate_rsa_keypair()
        
        # Création de threads
        threads = []
        results = []
        
        for _ in range(5):
            thread = threading.Thread(target=lambda: results.append(generate_keys()))
            threads.append(thread)
            thread.start()
        
        # Attente de la fin des threads
        for thread in threads:
            thread.join()
        
        # Vérification des résultats
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 2)
            self.assertIsInstance(result[0], bytes)  # Clé privée
            self.assertIsInstance(result[1], bytes)  # Clé publique
    
    def test_data_persistence(self):
        """Test de persistance des données"""
        # Création d'une base de données
        db_path = os.path.join(self.temp_dir, "test.db")
        db = EncryptedDatabase(db_path, "test_key")
        
        # Ajout de données
        user_data = {"username": "testuser", "email": "test@example.com"}
        db.create_user("testuser", user_data)
        
        db.save_message("sender", "recipient", "message1", "hash1")
        db.save_message("sender", "recipient", "message2", "hash2")
        
        # Création d'une nouvelle instance de base de données
        db2 = EncryptedDatabase(db_path, "test_key")
        
        # Vérification de la persistance
        retrieved_user = db2.get_user("testuser")
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user["username"], "testuser")
        
        messages = db2.get_messages("recipient", 10)
        self.assertEqual(len(messages), 2)
    
    def test_security_features(self):
        """Test des fonctionnalités de sécurité"""
        # Test de génération de clés sécurisées
        encryption = EncryptionManager()
        private_key, public_key = encryption.generate_rsa_keypair()
        
        # Vérification de la taille des clés
        self.assertGreater(len(private_key), 1000)  # Clé RSA-4096
        self.assertGreater(len(public_key), 500)
        
        # Test de chiffrement avec différentes clés
        test_data = b"Test data for security"
        
        # Chiffrement avec la clé publique
        encrypted = encryption.encrypt_with_rsa(test_data, public_key)
        self.assertNotEqual(encrypted, test_data)
        
        # Déchiffrement avec la clé privée
        decrypted = encryption.decrypt_with_rsa(encrypted, private_key)
        self.assertEqual(decrypted, test_data)
        
        # Test avec clé incorrecte
        try:
            encryption.decrypt_with_rsa(encrypted, public_key)  # Mauvaise clé
            self.fail("Expected exception")
        except Exception:
            pass  # Erreur attendue


if __name__ == "__main__":
    unittest.main()
