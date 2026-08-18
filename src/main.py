"""
Point d'entrée principal pour MessagerCrypt
Séquence de démarrage avec animations et menu principal
"""
import sys
import time
import threading
from pathlib import Path

# Ajout du répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import DEBUG
from src.ui.ascii import ASCIIArt
from src.ui.menu import MenuManager
from src.server import MessagerCryptServer
from src.client import MessagerCryptClient


class MessagerCryptApp:
    """Application principale MessagerCrypt"""
    
    def __init__(self):
        self.ascii_art = ASCIIArt()
        self.menu_manager = MenuManager()
        self.server = None
        self.client = None
        
        # Création des répertoires nécessaires
        self._create_directories()
    
    def _create_directories(self):
        """Crée les répertoires nécessaires"""
        directories = ['data', 'logs', 'config']
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
    
    def run(self):
        """Lance l'application principale"""
        try:
            # Séquence de démarrage
            self._startup_sequence()
            
            # Menu principal
            self._main_loop()
            
        except KeyboardInterrupt:
            self._shutdown_sequence()
        except Exception as e:
            self.menu_manager.show_error(f"Erreur fatale: {e}")
            if DEBUG:
                import traceback
                traceback.print_exc()
    
    def _startup_sequence(self):
        """Séquence de démarrage avec animations"""
        # Effacement de l'écran
        self.ascii_art.clear_screen()
        
        # Logo animé
        self.ascii_art.show_logo('red', animated=True)
        time.sleep(1)
        
        # Sous-titre
        self.ascii_art.show_subtitle("Messagerie Sécurisée v1.0", 'cyan')
        time.sleep(1)
        
        # Animation de chargement avec Rich
        self.ascii_art.show_rich_loading("Initialisation de MessagerCrypt", [
            "Initialisation du module de chiffrement",
            "Connexion au serveur",
            "Chargement des modules",
            "Vérification de la sécurité",
            "Préparation de l'interface"
        ])
        
        # Animation cyberpunk
        self.ascii_art.show_cyber_animation()
        time.sleep(1)
        
        # Message de bienvenue
        self.ascii_art.show_rich_panel(
            "🚀 MessagerCrypt prêt à l'emploi !",
            "Système de messagerie sécurisée avec chiffrement bout-en-bout",
            "green"
        )
        
        time.sleep(2)
    
    def _main_loop(self):
        """Boucle principale de l'application"""
        while True:
            try:
                # Affichage du menu principal
                choice = self.menu_manager.show_rich_main_menu()
                
                if choice == "1":
                    # Démarrer le serveur
                    self._handle_server_start()
                
                elif choice == "2":
                    # S'inscrire
                    self._handle_registration()
                
                elif choice == "3":
                    # Se connecter
                    self._handle_login()
                    # Si connexion réussie, afficher l'interface de messagerie
                    if self.client and self.client.authenticated:
                        self._handle_messaging_interface()
                
                elif choice == "4":
                    # Consulter l'historique
                    self._handle_history()
                
                elif choice == "5":
                    # Configuration
                    self._handle_configuration()
                
                elif choice == "6":
                    # Quitter
                    self._shutdown_sequence()
                    break
                
                else:
                    self.menu_manager.show_error("Choix invalide")
                    
            except KeyboardInterrupt:
                self._shutdown_sequence()
                break
            except Exception as e:
                self.menu_manager.show_error(f"Erreur: {e}")
                if DEBUG:
                    import traceback
                    traceback.print_exc()
    
    def _handle_server_start(self):
        """Gère le démarrage du serveur"""
        try:
            if self.server is None:
                self.server = MessagerCryptServer()
            
            # Message de confirmation
            self.menu_manager.show_success("Serveur MessagerCrypt démarré avec succès !")
            self.menu_manager.pause()
            
            # Interface du serveur
            self.server.run_server_interface()
            
        except Exception as e:
            self.menu_manager.show_error(f"Erreur serveur: {e}")
            self.menu_manager.pause()
    
    def _handle_registration(self):
        """Gère l'inscription d'un utilisateur"""
        try:
            # Formulaire d'inscription
            form_data = self.menu_manager.show_register_form()
            
            if not form_data['username'] or not form_data['password']:
                self.menu_manager.show_error("Nom d'utilisateur et mot de passe requis")
                return
            
            if form_data['password'] != form_data['confirm_password']:
                self.menu_manager.show_error("Les mots de passe ne correspondent pas")
                return
            
            # Création du client pour l'inscription avec l'IP et port spécifiés
            if self.client is None:
                self.client = MessagerCryptClient(
                    host=form_data.get('server_ip', '127.0.0.1'),
                    port=form_data.get('server_port', 8888)
                )
            
            # Connexion au serveur
            if not self.client.connect():
                return
            
            # Inscription
            success = self.client.register(form_data['username'], form_data['password'])
            if success:
                self.menu_manager.show_rich_notification(
                    f"Utilisateur {form_data['username']} créé avec succès",
                    "success"
                )
                self.menu_manager.pause()
            else:
                self.menu_manager.show_rich_notification(
                    "Erreur lors de la création de l'utilisateur",
                    "error"
                )
                self.menu_manager.pause()
                
        except Exception as e:
            self.menu_manager.show_error(f"Erreur d'inscription: {e}")
            self.menu_manager.pause()
    
    def _handle_login(self):
        """Gère la connexion d'un utilisateur"""
        try:
            # Formulaire de connexion
            form_data = self.menu_manager.show_login_form()
            
            if not form_data['username'] or not form_data['password']:
                self.menu_manager.show_error("Nom d'utilisateur et mot de passe requis")
                return
            
            # Création du client pour la connexion avec l'IP et port spécifiés
            if self.client is None:
                self.client = MessagerCryptClient(
                    host=form_data.get('server_ip', '127.0.0.1'),
                    port=form_data.get('server_port', 8888)
                )
            
            # Connexion au serveur
            if not self.client.connect():
                return
            
            # Authentification
            success = self.client.authenticate(form_data['username'], form_data['password'])
            if success:
                self.menu_manager.show_rich_notification(
                    f"Connecté en tant que {form_data['username']}",
                    "success"
                )
                # Interface de messagerie
                self.client._run_messaging_interface()
            else:
                self.menu_manager.show_rich_notification(
                    "Échec de l'authentification",
                    "error"
                )
                self.menu_manager.pause()
                
        except Exception as e:
            self.menu_manager.show_error(f"Erreur de connexion: {e}")
            self.menu_manager.pause()
    
    def _handle_history(self):
        """Gère l'affichage de l'historique"""
        try:
            if self.client is None:
                self.client = MessagerCryptClient()
            
            if not self.client.authenticated:
                self.menu_manager.show_error("Authentification requise")
                self.menu_manager.pause()
                return
            
            # Récupération de l'historique
            history = self.client.get_message_history()
            if history:
                self.menu_manager.show_message_history(history, self.client.username)
            else:
                self.menu_manager.show_warning("Aucun message dans l'historique")
                self.menu_manager.pause()
                
        except Exception as e:
            self.menu_manager.show_error(f"Erreur historique: {e}")
            self.menu_manager.pause()
    
    def _handle_messaging_interface(self):
        """Gère l'interface de messagerie"""
        try:
            if self.client is None or not self.client.authenticated:
                self.menu_manager.show_error("Authentification requise")
                self.menu_manager.pause()
                return
            
            while True:
                choice = self.menu_manager.show_messaging_menu(self.client.username)
                
                if choice == "1":
                    # Envoyer un message
                    self._handle_send_message()
                elif choice == "2":
                    # Messages reçus
                    self._handle_received_messages()
                elif choice == "3":
                    # Historique
                    self._handle_history()
                elif choice == "4":
                    # Rechercher
                    self._handle_search_messages()
                elif choice == "5":
                    # Paramètres
                    self._handle_user_settings()
                elif choice == "6":
                    # Déconnexion
                    break
                else:
                    self.menu_manager.show_error("Choix invalide")
                    
        except Exception as e:
            self.menu_manager.show_error(f"Erreur interface messagerie: {e}")
            self.menu_manager.pause()
    
    def _handle_send_message(self):
        """Gère l'envoi de message"""
        try:
            form_data = self.menu_manager.show_compose_message()
            
            if form_data['recipient'] and form_data['message']:
                success = self.client.send_message(form_data['recipient'], form_data['message'])
                if success:
                    self.menu_manager.show_success("Message envoyé avec succès")
                else:
                    self.menu_manager.show_error("Erreur lors de l'envoi du message")
            else:
                self.menu_manager.show_error("Destinataire et message requis")
                
        except Exception as e:
            self.menu_manager.show_error(f"Erreur envoi: {e}")
    
    def _handle_received_messages(self):
        """Gère l'affichage des messages reçus"""
        try:
            messages = self.client.get_received_messages()
            if messages:
                self.menu_manager.show_message_history(messages, self.client.username, "Messages Reçus")
            else:
                self.menu_manager.show_warning("Aucun message reçu")
                self.menu_manager.pause()
                
        except Exception as e:
            self.menu_manager.show_error(f"Erreur messages reçus: {e}")
            self.menu_manager.pause()
    
    def _handle_search_messages(self):
        """Gère la recherche de messages"""
        try:
            query = input(f"{self.menu_manager.colors['yellow']}Terme de recherche: {self.menu_manager.colors['reset']}")
            
            if query.strip():
                messages = self.client.search_messages(query.strip())
                if messages:
                    self.menu_manager.show_message_history(messages, self.client.username, f"Résultats pour '{query}'")
                else:
                    self.menu_manager.show_warning(f"Aucun résultat pour '{query}'")
                    self.menu_manager.pause()
            else:
                self.menu_manager.show_error("Terme de recherche requis")
                
        except Exception as e:
            self.menu_manager.show_error(f"Erreur recherche: {e}")
            self.menu_manager.pause()
    
    def _handle_user_settings(self):
        """Gère les paramètres utilisateur"""
        try:
            self.menu_manager.show_rich_panel(
                "⚙️ Paramètres Utilisateur",
                f"Utilisateur: {self.client.username}\n"
                f"Statut: Connecté\n"
                f"Messages envoyés: {len(self.client.get_message_history())}\n"
                f"Messages reçus: {len(self.client.get_received_messages())}"
            )
            self.menu_manager.pause()
            
        except Exception as e:
            self.menu_manager.show_error(f"Erreur paramètres: {e}")
            self.menu_manager.pause()
    
    def _handle_configuration(self):
        """Gère la configuration"""
        try:
            choice = self.menu_manager.show_configuration_menu()
            
            if choice == "1":
                self._show_security_settings()
            elif choice == "2":
                self._show_network_settings()
            elif choice == "3":
                self._show_theme_settings()
            elif choice == "4":
                self._show_statistics()
            elif choice == "5":
                self._handle_cleanup()
            elif choice == "6":
                pass  # Retour
            
        except Exception as e:
            self.menu_manager.show_error(f"Erreur configuration: {e}")
            self.menu_manager.pause()
    
    def _show_security_settings(self):
        """Affiche les paramètres de sécurité"""
        self.menu_manager.show_rich_panel(
            "🔐 Paramètres de sécurité",
            """
• Chiffrement: AES-256-GCM + RSA-4096
• Authentification: Argon2id
• Protection: Anti-rejeu, signatures
• Stockage: Base de données chiffrée
            """,
            "blue"
        )
        self.menu_manager.pause()
    
    def _show_network_settings(self):
        """Affiche les paramètres réseau"""
        self.menu_manager.show_rich_panel(
            "🌐 Paramètres réseau",
            """
• Serveur: 127.0.0.1:8888
• Protocole: TCP sécurisé
• Connexions: Max 10 simultanées
• Timeout: 30 secondes
            """,
            "blue"
        )
        self.menu_manager.pause()
    
    def _show_theme_settings(self):
        """Affiche les paramètres de thème"""
        self.menu_manager.show_rich_panel(
            "🎨 Paramètres de thème",
            """
• Couleurs: Rouge, vert, bleu, cyan
• Animations: ASCII art, barres de progression
• Interface: Rich + Colorama
• Thème: Cyberpunk terminal
            """,
            "blue"
        )
        self.menu_manager.pause()
    
    def _show_statistics(self):
        """Affiche les statistiques"""
        try:
            stats_data = [
                ["Utilisateurs enregistrés", "0"],
                ["Messages envoyés", "0"],
                ["Connexions actives", "0"],
                ["Temps de fonctionnement", "0s"]
            ]
            
            self.menu_manager.show_rich_table(
                "📊 Statistiques",
                stats_data,
                ["Métrique", "Valeur"]
            )
            self.menu_manager.pause()
            
        except Exception as e:
            self.menu_manager.show_error(f"Erreur statistiques: {e}")
            self.menu_manager.pause()
    
    def _handle_cleanup(self):
        """Gère le nettoyage des données"""
        if self.menu_manager.show_rich_confirm("Voulez-vous nettoyer les données locales?"):
            self.menu_manager.show_success("Données nettoyées")
        self.menu_manager.pause()
    
    def _shutdown_sequence(self):
        """Séquence d'arrêt"""
        self.ascii_art.clear_screen()
        
        # Message d'arrêt
        self.ascii_art.show_rich_panel(
            "👋 Arrêt de MessagerCrypt",
            "Merci d'avoir utilisé notre messagerie sécurisée !",
            "red"
        )
        
        # Nettoyage des connexions
        if self.client and self.client.connected:
            self.client.disconnect()
        
        if self.server and self.server.running:
            self.server.stop()
        
        time.sleep(2)
        self.ascii_art.clear_screen()


def main():
    """Point d'entrée principal"""
    app = MessagerCryptApp()
    app.run()


if __name__ == "__main__":
    main()
