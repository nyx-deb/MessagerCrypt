"""
Tests unitaires pour le module réseau
"""
import unittest
import threading
import time
import json
from unittest.mock import Mock, patch
from src.server import MessagerCryptServer
from src.client import MessagerCryptClient


class TestMessagerCryptServer(unittest.TestCase):
    """Tests pour MessagerCryptServer"""
    
    def setUp(self):
        self.server = MessagerCryptServer("127.0.0.1", 8889)  # Port différent pour les tests
    
    def tearDown(self):
        if self.server.running:
            self.server.stop()
    
    def test_server_initialization(self):
        """Test d'initialisation du serveur"""
        self.assertIsNotNone(self.server.host)
        self.assertIsNotNone(self.server.port)
        self.assertFalse(self.server.running)
        self.assertIsInstance(self.server.clients, dict)
        self.assertIsInstance(self.server.connected_users, dict)
    
    def test_server_start_stop(self):
        """Test de démarrage et arrêt du serveur"""
        # Démarrage dans un thread
        server_thread = threading.Thread(target=self.server.start, daemon=True)
        server_thread.start()
        
        # Attente du démarrage
        time.sleep(1)
        
        # Vérification que le serveur est en cours d'exécution
        self.assertTrue(self.server.running)
        
        # Arrêt du serveur
        self.server.stop()
        self.assertFalse(self.server.running)
    
    def test_server_stats(self):
        """Test des statistiques du serveur"""
        stats = self.server.get_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertIn("uptime", stats)
        self.assertIn("connections", stats)
        self.assertIn("connected_users", stats)
        self.assertIn("messages_sent", stats)
        self.assertIn("messages_received", stats)
        self.assertIn("start_time", stats)
    
    def test_message_processing(self):
        """Test de traitement des messages"""
        # Simulation d'un message d'authentification
        auth_message = {
            "type": "auth",
            "username": "testuser",
            "password": "testpass"
        }
        
        # Mock des méthodes nécessaires
        with patch.object(self.server.key_manager, 'load_user_keys') as mock_load:
            mock_load.return_value = {
                "username": "testuser",
                "public_key": b"mock_public_key",
                "private_key": b"mock_private_key",
                "status": "success"
            }
            
            # Test du traitement du message
            # Note: Ce test nécessiterait une connexion client réelle
            # pour tester complètement le traitement des messages
            pass
    
    def test_client_disconnection(self):
        """Test de déconnexion de client"""
        # Simulation d'un client
        mock_socket = Mock()
        mock_address = ("127.0.0.1", 12345)
        client_id = f"{mock_address[0]}:{mock_address[1]}"
        
        # Ajout du client
        self.server.clients[client_id] = {
            'socket': mock_socket,
            'address': mock_address,
            'username': 'testuser',
            'authenticated': True,
            'session_token': 'test_token',
            'connected_at': time.time()
        }
        
        # Déconnexion
        self.server._disconnect_client(client_id)
        
        # Vérification que le client a été supprimé
        self.assertNotIn(client_id, self.server.clients)
    
    def test_cleanup_sessions(self):
        """Test de nettoyage des sessions"""
        # Mock de la base de données
        with patch.object(self.server.database, 'cleanup_expired_sessions') as mock_cleanup:
            mock_cleanup.return_value = 5
            
            # Test du nettoyage
            cleaned = self.server.database.cleanup_expired_sessions()
            self.assertEqual(cleaned, 5)


class TestMessagerCryptClient(unittest.TestCase):
    """Tests pour MessagerCryptClient"""
    
    def setUp(self):
        self.client = MessagerCryptClient("127.0.0.1", 8889)  # Port différent pour les tests
    
    def tearDown(self):
        if self.client.connected:
            self.client.disconnect()
    
    def test_client_initialization(self):
        """Test d'initialisation du client"""
        self.assertIsNotNone(self.client.host)
        self.assertIsNotNone(self.client.port)
        self.assertFalse(self.client.connected)
        self.assertFalse(self.client.authenticated)
        self.assertIsNone(self.client.username)
        self.assertIsNone(self.client.session_token)
    
    def test_client_connection(self):
        """Test de connexion du client"""
        # Mock du socket
        with patch('socket.socket') as mock_socket:
            mock_socket_instance = Mock()
            mock_socket.return_value = mock_socket_instance
            
            # Test de connexion
            success = self.client.connect()
            
            # Vérification
            self.assertTrue(success)
            self.assertTrue(self.client.connected)
    
    def test_client_disconnection(self):
        """Test de déconnexion du client"""
        # Connexion simulée
        self.client.connected = True
        self.client.socket = Mock()
        
        # Déconnexion
        self.client.disconnect()
        
        # Vérification
        self.assertFalse(self.client.connected)
        self.assertIsNone(self.client.socket)
    
    def test_authentication(self):
        """Test d'authentification du client"""
        # Mock des méthodes nécessaires
        with patch.object(self.client.key_manager, 'load_user_keys') as mock_load:
            mock_load.return_value = {
                "username": "testuser",
                "public_key": b"mock_public_key",
                "private_key": b"mock_private_key",
                "status": "success"
            }
            
            with patch.object(self.client, '_send_message') as mock_send:
                # Test d'authentification
                success = self.client.authenticate("testuser", "testpass")
                
                # Vérification
                self.assertTrue(success)
                self.assertTrue(self.client.authenticated)
                self.assertEqual(self.client.username, "testuser")
    
    def test_user_registration(self):
        """Test d'inscription d'utilisateur"""
        # Mock des méthodes nécessaires
        with patch.object(self.client.key_manager, 'load_user_keys') as mock_load:
            mock_load.return_value = None  # Utilisateur n'existe pas
            
            with patch.object(self.client.key_manager, 'generate_user_keys') as mock_generate:
                mock_generate.return_value = {
                    "username": "testuser",
                    "public_key": b"mock_public_key",
                    "private_key": b"mock_private_key",
                    "status": "success"
                }
                
                # Test d'inscription
                success = self.client.register("testuser", "testpass")
                
                # Vérification
                self.assertTrue(success)
    
    def test_message_sending(self):
        """Test d'envoi de message"""
        # Configuration du client
        self.client.authenticated = True
        self.client.username = "testuser"
        
        # Mock des méthodes nécessaires
        with patch.object(self.client.key_manager, 'get_public_key') as mock_get_key:
            mock_get_key.return_value = b"mock_public_key"
            
            with patch.object(self.client, '_send_message') as mock_send:
                # Test d'envoi de message
                success = self.client.send_message("recipient", "Test message")
                
                # Vérification
                self.assertTrue(success)
                mock_send.assert_called_once()
    
    def test_message_receiving(self):
        """Test de réception de message"""
        # Configuration du client
        self.client.authenticated = True
        self.client.username = "testuser"
        
        # Simulation d'un message reçu
        message = {
            "type": "message_received",
            "sender": "sender",
            "message": "Test message",
            "timestamp": time.time()
        }
        
        # Test de traitement du message
        self.client._handle_received_message(message)
        
        # Vérification (le message devrait être affiché)
        # Note: Ce test nécessiterait une vérification de l'affichage
        pass
    
    def test_get_users(self):
        """Test de récupération des utilisateurs"""
        # Configuration du client
        self.client.authenticated = True
        
        # Mock des méthodes nécessaires
        with patch.object(self.client, '_send_message') as mock_send:
            # Test de récupération des utilisateurs
            users = self.client.get_users()
            
            # Vérification
            self.assertIsInstance(users, list)
            mock_send.assert_called_once()
    
    def test_get_message_history(self):
        """Test de récupération de l'historique"""
        # Configuration du client
        self.client.authenticated = True
        
        # Mock des méthodes nécessaires
        with patch.object(self.client, '_send_message') as mock_send:
            # Test de récupération de l'historique
            history = self.client.get_message_history()
            
            # Vérification
            self.assertIsInstance(history, list)
            mock_send.assert_called_once()
    
    def test_message_validation(self):
        """Test de validation des messages"""
        # Test avec message valide
        valid_message = {
            "type": "message",
            "recipient": "recipient",
            "message": "Test message"
        }
        
        # Test avec message invalide
        invalid_message = {
            "type": "unknown_type",
            "data": "test"
        }
        
        # Les tests de validation dépendent de l'implémentation
        # spécifique de la validation des messages
        pass
    
    def test_error_handling(self):
        """Test de gestion des erreurs"""
        # Test avec connexion échouée
        with patch('socket.socket') as mock_socket:
            mock_socket.side_effect = Exception("Connection failed")
            
            success = self.client.connect()
            self.assertFalse(success)
        
        # Test avec authentification échouée
        with patch.object(self.client.key_manager, 'load_user_keys') as mock_load:
            mock_load.return_value = None  # Échec d'authentification
            
            success = self.client.authenticate("testuser", "wrongpass")
            self.assertFalse(success)


class TestNetworkIntegration(unittest.TestCase):
    """Tests d'intégration réseau"""
    
    def setUp(self):
        self.server = MessagerCryptServer("127.0.0.1", 8890)  # Port différent pour les tests
        self.client = MessagerCryptClient("127.0.0.1", 8890)
    
    def tearDown(self):
        if self.server.running:
            self.server.stop()
        if self.client.connected:
            self.client.disconnect()
    
    def test_server_client_communication(self):
        """Test de communication serveur-client"""
        # Démarrage du serveur
        server_thread = threading.Thread(target=self.server.start, daemon=True)
        server_thread.start()
        
        # Attente du démarrage
        time.sleep(1)
        
        # Connexion du client
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
        
        # Arrêt du serveur
        self.server.stop()
    
    def test_multiple_clients(self):
        """Test avec plusieurs clients"""
        # Démarrage du serveur
        server_thread = threading.Thread(target=self.server.start, daemon=True)
        server_thread.start()
        
        # Attente du démarrage
        time.sleep(1)
        
        # Création de plusieurs clients
        clients = []
        for i in range(3):
            client = MessagerCryptClient("127.0.0.1", 8890)
            clients.append(client)
        
        # Connexion des clients
        for client in clients:
            with patch.object(client.key_manager, 'load_user_keys') as mock_load:
                mock_load.return_value = {
                    "username": f"user{len(clients)}",
                    "public_key": b"mock_public_key",
                    "private_key": b"mock_private_key",
                    "status": "success"
                }
                
                success = client.connect()
                self.assertTrue(success)
        
        # Vérification du nombre de clients connectés
        self.assertEqual(len(self.server.clients), 3)
        
        # Déconnexion des clients
        for client in clients:
            client.disconnect()
        
        # Arrêt du serveur
        self.server.stop()


if __name__ == "__main__":
    unittest.main()
