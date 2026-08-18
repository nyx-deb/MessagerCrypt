"""
Tests unitaires pour le module de chiffrement
"""
import unittest
import os
import tempfile
from src.crypto.encryption import EncryptionManager
from src.crypto.keys import KeyManager
from src.crypto.auth import AuthManager


class TestEncryptionManager(unittest.TestCase):
    """Tests pour EncryptionManager"""
    
    def setUp(self):
        self.encryption = EncryptionManager()
    
    def test_rsa_keypair_generation(self):
        """Test de génération de paire de clés RSA"""
        private_key, public_key = self.encryption.generate_rsa_keypair()
        
        self.assertIsInstance(private_key, bytes)
        self.assertIsInstance(public_key, bytes)
        self.assertGreater(len(private_key), 0)
        self.assertGreater(len(public_key), 0)
    
    def test_rsa_encryption_decryption(self):
        """Test de chiffrement/déchiffrement RSA"""
        private_key, public_key = self.encryption.generate_rsa_keypair()
        test_data = b"Test message for RSA encryption"
        
        # Chiffrement
        encrypted = self.encryption.encrypt_with_rsa(test_data, public_key)
        self.assertIsInstance(encrypted, bytes)
        self.assertNotEqual(encrypted, test_data)
        
        # Déchiffrement
        decrypted = self.encryption.decrypt_with_rsa(encrypted, private_key)
        self.assertEqual(decrypted, test_data)
    
    def test_aes_key_generation(self):
        """Test de génération de clé AES"""
        key = self.encryption.generate_aes_key()
        
        self.assertIsInstance(key, bytes)
        self.assertEqual(len(key), 32)  # 256 bits
    
    def test_aes_encryption_decryption(self):
        """Test de chiffrement/déchiffrement AES"""
        key = self.encryption.generate_aes_key()
        test_data = b"Test message for AES encryption"
        
        # Chiffrement
        nonce, encrypted = self.encryption.encrypt_with_aes(test_data, key)
        self.assertIsInstance(nonce, bytes)
        self.assertIsInstance(encrypted, bytes)
        self.assertNotEqual(encrypted, test_data)
        
        # Déchiffrement
        decrypted = self.encryption.decrypt_with_aes(encrypted, key, nonce)
        self.assertEqual(decrypted, test_data)
    
    def test_message_packet_creation(self):
        """Test de création de paquet de message"""
        private_key, public_key = self.encryption.generate_rsa_keypair()
        aes_key = self.encryption.generate_aes_key()
        
        packet = self.encryption.create_message_packet(
            "Test message", "sender", "recipient", aes_key, public_key
        )
        
        self.assertIsInstance(packet, dict)
        self.assertIn("version", packet)
        self.assertIn("message", packet)
        self.assertIn("nonce", packet)
        self.assertIn("aes_key", packet)
    
    def test_message_packet_decryption(self):
        """Test de déchiffrement de paquet de message"""
        private_key, public_key = self.encryption.generate_rsa_keypair()
        aes_key = self.encryption.generate_aes_key()
        
        # Création du paquet
        packet = self.encryption.create_message_packet(
            "Test message", "sender", "recipient", aes_key, public_key
        )
        
        # Déchiffrement
        message, sender, timestamp = self.encryption.decrypt_message_packet(
            packet, private_key
        )
        
        self.assertEqual(message, "Test message")
        self.assertEqual(sender, "sender")


class TestKeyManager(unittest.TestCase):
    """Tests pour KeyManager"""
    
    def setUp(self):
        from pathlib import Path
        self.key_manager = KeyManager()
        self.temp_dir = tempfile.mkdtemp()
        self.key_manager.keys_file = Path(self.temp_dir) / "test_keys.json"
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_user_key_generation(self):
        """Test de génération de clés utilisateur"""
        result = self.key_manager.generate_user_keys("testuser", "testpass")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["username"], "testuser")
        self.assertIsInstance(result["public_key"], bytes)
        self.assertIsInstance(result["private_key"], bytes)
    
    def test_user_key_loading(self):
        """Test de chargement de clés utilisateur"""
        # Génération des clés
        self.key_manager.generate_user_keys("testuser", "testpass")
        
        # Chargement des clés
        keys = self.key_manager.load_user_keys("testuser", "testpass")
        
        self.assertIsNotNone(keys)
        self.assertEqual(keys["username"], "testuser")
        self.assertIsInstance(keys["public_key"], bytes)
        self.assertIsInstance(keys["private_key"], bytes)
    
    def test_invalid_credentials(self):
        """Test avec des identifiants invalides"""
        self.key_manager.generate_user_keys("testuser", "testpass")
        
        # Mauvais mot de passe
        keys = self.key_manager.load_user_keys("testuser", "wrongpass")
        self.assertIsNone(keys)
        
        # Utilisateur inexistant
        keys = self.key_manager.load_user_keys("nonexistent", "testpass")
        self.assertIsNone(keys)
    
    def test_public_key_retrieval(self):
        """Test de récupération de clé publique"""
        self.key_manager.generate_user_keys("testuser", "testpass")
        
        public_key = self.key_manager.get_public_key("testuser")
        self.assertIsInstance(public_key, bytes)
        self.assertGreater(len(public_key), 0)
    
    def test_user_listing(self):
        """Test de listing des utilisateurs"""
        self.key_manager.generate_user_keys("user1", "pass1")
        self.key_manager.generate_user_keys("user2", "pass2")
        
        users = self.key_manager.list_users()
        self.assertIn("user1", users)
        self.assertIn("user2", users)
    
    def test_remote_user_registration(self):
        """Test d'enregistrement d'un utilisateur distant"""
        _, public_key = self.key_manager.encryption_manager.generate_rsa_keypair()
        
        success = self.key_manager.register_user("remote", "remotepass", public_key)
        self.assertTrue(success)
        
        retrieved = self.key_manager.get_public_key("remote")
        self.assertEqual(retrieved, public_key)
    
    def test_remote_registration_protection(self):
        """Test de protection contre le détournement de compte"""
        _, public_key = self.key_manager.encryption_manager.generate_rsa_keypair()
        self.key_manager.register_user("remote", "remotepass", public_key)
        
        _, attacker_key = self.key_manager.encryption_manager.generate_rsa_keypair()
        success = self.key_manager.register_user("remote", "wrongpass", attacker_key)
        self.assertFalse(success)
        self.assertEqual(self.key_manager.get_public_key("remote"), public_key)
    
    def test_remote_registration_rotation(self):
        """Test de rotation de clé via ré-enregistrement"""
        _, old_key = self.key_manager.encryption_manager.generate_rsa_keypair()
        self.key_manager.register_user("remote", "remotepass", old_key)
        
        _, new_key = self.key_manager.encryption_manager.generate_rsa_keypair()
        success = self.key_manager.register_user("remote", "remotepass", new_key)
        self.assertTrue(success)
        self.assertEqual(self.key_manager.get_public_key("remote"), new_key)
    
    def test_verify_user(self):
        """Test de vérification d'identifiants distants"""
        _, public_key = self.key_manager.encryption_manager.generate_rsa_keypair()
        self.key_manager.register_user("remote", "remotepass", public_key)
        
        result = self.key_manager.verify_user("remote", "remotepass")
        self.assertEqual(result, public_key)
        
        self.assertIsNone(self.key_manager.verify_user("remote", "wrongpass"))
        self.assertIsNone(self.key_manager.verify_user("ghost", "whatever"))
    
    def test_verify_user_with_local_account(self):
        """Test verify_user avec un compte local complet"""
        generated = self.key_manager.generate_user_keys("localuser", "localpass")
        
        result = self.key_manager.verify_user("localuser", "localpass")
        self.assertEqual(result, generated["public_key"])
        
        self.assertIsNone(self.key_manager.verify_user("localuser", "wrongpass"))
    
    def test_public_key_caching(self):
        """Test de mise en cache d'une clé publique distante"""
        _, public_key = self.key_manager.encryption_manager.generate_rsa_keypair()
        
        success = self.key_manager.cache_public_key("friend", public_key)
        self.assertTrue(success)
        self.assertEqual(self.key_manager.get_public_key("friend"), public_key)
        
        _, new_key = self.key_manager.encryption_manager.generate_rsa_keypair()
        self.key_manager.cache_public_key("friend", new_key)
        self.assertEqual(self.key_manager.get_public_key("friend"), new_key)


class TestAuthManager(unittest.TestCase):
    """Tests pour AuthManager"""
    
    def setUp(self):
        self.auth = AuthManager()
        self.encryption = EncryptionManager()
        private_key, public_key = self.encryption.generate_rsa_keypair()
        self.private_key = private_key
        self.public_key = public_key
    
    def test_signature_creation_verification(self):
        """Test de création et vérification de signature"""
        data = b"Test data for signature"
        
        # Création de la signature
        signature = self.auth.create_signature(data, self.private_key)
        self.assertIsInstance(signature, bytes)
        self.assertGreater(len(signature), 0)
        
        # Vérification de la signature
        is_valid = self.auth.verify_signature(data, signature, self.public_key)
        self.assertTrue(is_valid)
    
    def test_invalid_signature(self):
        """Test avec signature invalide"""
        data = b"Test data for signature"
        wrong_data = b"Wrong data"
        
        signature = self.auth.create_signature(data, self.private_key)
        
        # Signature avec mauvaises données
        is_valid = self.auth.verify_signature(wrong_data, signature, self.public_key)
        self.assertFalse(is_valid)
    
    def test_hmac_creation_verification(self):
        """Test de création et vérification HMAC"""
        data = b"Test data for HMAC"
        key = b"test_key_32_bytes_long_for_hmac"
        
        # Création du HMAC
        hmac = self.auth.create_hmac(data, key)
        self.assertIsInstance(hmac, bytes)
        self.assertEqual(len(hmac), 32)  # SHA-256
        
        # Vérification du HMAC
        is_valid = self.auth.verify_hmac(data, hmac, key)
        self.assertTrue(is_valid)
    
    def test_anti_replay_token(self):
        """Test de token anti-rejeu"""
        username = "testuser"
        timestamp = 1234567890.0
        
        token = self.auth.create_anti_replay_token(username, timestamp)
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)
        
        # Vérification du token
        is_valid = self.auth.verify_anti_replay_token(token, username, timestamp)
        self.assertTrue(is_valid)
        
        # Token invalide
        is_valid = self.auth.verify_anti_replay_token(token, "wronguser", timestamp)
        self.assertFalse(is_valid)
    
    def test_message_freshness(self):
        """Test de fraîcheur des messages"""
        import time
        
        # Message récent
        recent_timestamp = time.time() - 10  # 10 secondes
        is_fresh = self.auth.is_message_fresh(recent_timestamp)
        self.assertTrue(is_fresh)
        
        # Message ancien
        old_timestamp = time.time() - 3600  # 1 heure
        is_fresh = self.auth.is_message_fresh(old_timestamp)
        self.assertFalse(is_fresh)
    
    def test_authenticated_message(self):
        """Test de message authentifié"""
        message = "Test message"
        sender = "testuser"
        
        auth_message = self.auth.create_authenticated_message(
            message, sender, self.private_key
        )
        
        self.assertIsInstance(auth_message, dict)
        self.assertEqual(auth_message["message"], message)
        self.assertEqual(auth_message["sender"], sender)
        self.assertIn("signature", auth_message)
        self.assertIn("anti_replay_token", auth_message)
    
    def test_authenticated_message_verification(self):
        """Test de vérification de message authentifié"""
        message = "Test message"
        sender = "testuser"
        
        auth_message = self.auth.create_authenticated_message(
            message, sender, self.private_key
        )
        
        is_valid = self.auth.verify_authenticated_message(
            auth_message, self.public_key
        )
        self.assertTrue(is_valid)


if __name__ == "__main__":
    unittest.main()
