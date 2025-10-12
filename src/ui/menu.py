"""
Module de menu interactif pour MessagerCrypt
Interface utilisateur en ligne de commande
"""
import sys
import time
from typing import Dict, List, Optional, Callable
from colorama import init, Fore, Back, Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.align import Align

# Initialisation de colorama
init(autoreset=True)

# Console Rich
console = Console()


class MenuManager:
    """Gestionnaire de menus interactifs pour MessagerCrypt"""
    
    def __init__(self):
        self.colors = {
            'red': Fore.RED,
            'green': Fore.GREEN,
            'yellow': Fore.YELLOW,
            'blue': Fore.BLUE,
            'magenta': Fore.MAGENTA,
            'cyan': Fore.CYAN,
            'white': Fore.WHITE,
            'dim': Style.DIM,
            'bright_red': Style.BRIGHT + Fore.RED,
            'bright_green': Style.BRIGHT + Fore.GREEN,
            'bright_blue': Style.BRIGHT + Fore.BLUE,
            'bright_yellow': Style.BRIGHT + Fore.YELLOW,
            'bright_cyan': Style.BRIGHT + Fore.CYAN,
            'bright_white': Style.BRIGHT + Fore.WHITE,
            'reset': Style.RESET_ALL
        }
        self.current_user = None
        self.menu_actions = {}
        
        # Gestion responsive
        self.min_width = 60
        self.max_width = 120
        self.optimal_width = 80
    
    def get_terminal_size(self) -> tuple:
        """
        Récupère la taille du terminal
        
        Returns:
            tuple: (width, height)
        """
        try:
            import shutil
            size = shutil.get_terminal_size()
            return (size.columns, size.lines)
        except:
            return (80, 24)  # Taille par défaut
    
    def get_responsive_width(self) -> int:
        """
        Calcule la largeur responsive optimale
        
        Returns:
            int: Largeur optimale
        """
        width, _ = self.get_terminal_size()
        
        # Limiter la largeur entre min et max
        if width < self.min_width:
            return self.min_width
        elif width > self.max_width:
            return self.max_width
        else:
            return width
    
    def get_responsive_height(self) -> int:
        """
        Calcule la hauteur responsive optimale
        
        Returns:
            int: Hauteur optimale
        """
        _, height = self.get_terminal_size()
        
        # Hauteur minimale de 20 lignes
        return max(height, 20)
    
    def is_small_terminal(self) -> bool:
        """
        Vérifie si le terminal est petit
        
        Returns:
            bool: True si petit terminal
        """
        width, height = self.get_terminal_size()
        return width < 80 or height < 24
    
    def is_very_small_terminal(self) -> bool:
        """
        Vérifie si le terminal est très petit
        
        Returns:
            bool: True si très petit terminal
        """
        width, height = self.get_terminal_size()
        return width < 60 or height < 20
    
    def get_responsive_spacing(self) -> int:
        """
        Calcule l'espacement responsive
        
        Returns:
            int: Nombre de lignes d'espacement
        """
        if self.is_very_small_terminal():
            return 1
        elif self.is_small_terminal():
            return 2
        else:
            return 3
    
    def get_responsive_padding(self) -> int:
        """
        Calcule le padding responsive
        
        Returns:
            int: Nombre de caractères de padding
        """
        width = self.get_responsive_width()
        
        if width < 70:
            return 2
        elif width < 90:
            return 4
        else:
            return 6
    
    def show_main_menu(self) -> str:
        """
        Affiche le menu principal
        
        Returns:
            str: Choix de l'utilisateur
        """
        self.clear_screen()
        
        # Largeur responsive
        terminal_width = self.get_responsive_width()
        spacing = self.get_responsive_spacing()
        
        # En-tête adaptatif
        if self.is_very_small_terminal():
            # Version compacte pour très petits terminaux
            title = "MESSAGERCRYPT v1.0"
            header = f"""
╔{'═'*(terminal_width-2)}╗
║{title.center(terminal_width-2)}║
╚{'═'*(terminal_width-2)}╝
"""
        else:
            # Version complète
            title = "MESSAGERCRYPT v1.0 — Sécurisé"
            header = f"""
╔{'═'*(terminal_width-2)}╗
║{' '*(terminal_width-2)}║
║{title.center(terminal_width-2)}║
║{' '*(terminal_width-2)}║
╚{'═'*(terminal_width-2)}╝
"""
        
        print(self.colors['bright_blue'] + header + self.colors['reset'])
        
        # Espacement responsive
        for _ in range(spacing):
            print()
        
        # Options du menu adaptatives
        if self.is_very_small_terminal():
            menu_options = [
                "[1] 🖥️  Serveur",
                "[2] 👤  Inscription",
                "[3] 🔐  Connexion",
                "[4] 💬  Historique",
                "[5] ⚙️  Config",
                "[6] 🚪  Quitter"
            ]
        else:
            menu_options = [
                "[1] 🖥️  Démarrer le serveur",
                "[2] 👤  S'inscrire",
                "[3] 🔐  Se connecter",
                "[4] 💬  Consulter l'historique",
                "[5] ⚙️  Configuration",
                "[6] 🚪  Quitter"
            ]
        
        for option in menu_options:
            print(f"  {self.colors['white']}{option}{self.colors['reset']}")
        
        # Espacement responsive
        for _ in range(spacing):
            print()
        
        # Séparateur adaptatif
        separator_width = min(terminal_width - 20, 60)
        print(f"{self.colors['cyan']}{'='*separator_width}{self.colors['reset']}")
        
        for _ in range(spacing):
            print()
        
        # Saisie du choix
        choice = input(f"\n{self.colors['yellow']}Votre choix (1-6): {self.colors['reset']}")
        return choice.strip()
    
    def show_rich_main_menu(self) -> str:
        """
        Affiche le menu principal avec Rich
        
        Returns:
            str: Choix de l'utilisateur
        """
        self.clear_screen()
        
        # En-tête avec Rich
        header_text = Text("MESSAGERCRYPT v1.0 — Sécurisé", style="bold blue")
        header_panel = Panel(
            header_text,
            border_style="blue",
            padding=(1, 2)
        )
        # Centrage du panneau
        from rich.align import Align
        centered_panel = Align.center(header_panel)
        console.print(centered_panel)
        
        # Table des options
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Option", style="cyan", width=8)
        table.add_column("Description", style="white")
        
        options = [
            ("[1]", "🖥️  Démarrer le serveur"),
            ("[2]", "👤  S'inscrire"),
            ("[3]", "🔐  Se connecter"),
            ("[4]", "💬  Consulter l'historique"),
            ("[5]", "⚙️  Configuration"),
            ("[6]", "🚪  Quitter")
        ]
        
        for option, description in options:
            table.add_row(option, description)
        
        console.print(table)
        console.print()
        
        # Saisie du choix
        choice = Prompt.ask(
            "[bold yellow]Votre choix",
            choices=["1", "2", "3", "4", "5", "6"],
            default="1"
        )
        
        return choice
    
    def show_login_form(self) -> Dict[str, str]:
        """
        Affiche le formulaire de connexion
        
        Returns:
            Dict[str, str]: Informations de connexion
        """
        self.clear_screen()
        
        # Calcul de la largeur du terminal
        try:
            import shutil
            terminal_width = shutil.get_terminal_size().columns
        except:
            terminal_width = 80
        
        title = "🔐 CONNEXION"
        title_centered = title.center(terminal_width)
        print(self.colors['bright_blue'] + title_centered + self.colors['reset'])
        print(self.colors['cyan'] + "="*terminal_width + self.colors['reset'])
        
        # Espacement
        print()
        print()
        
        # Configuration du serveur
        print(f"{self.colors['cyan']}Configuration du serveur:{self.colors['reset']}")
        print()
        
        server_ip = input(f"{self.colors['yellow']}Adresse IP du serveur (Entrée pour localhost): {self.colors['reset']}")
        if not server_ip.strip():
            server_ip = "127.0.0.1"
        
        server_port = input(f"{self.colors['yellow']}Port du serveur (Entrée pour 8888): {self.colors['reset']}")
        if not server_port.strip():
            server_port = "8888"
        
        print()
        print(f"{self.colors['cyan']}Identifiants:{self.colors['reset']}")
        print()
        
        username = input(f"{self.colors['yellow']}Nom d'utilisateur: {self.colors['reset']}")
        print()
        password = input(f"{self.colors['yellow']}Mot de passe: {self.colors['reset']}")
        
        # Espacement
        print()
        print()
        
        return {
            "username": username.strip(),
            "password": password.strip(),
            "server_ip": server_ip.strip(),
            "server_port": int(server_port.strip()) if server_port.strip().isdigit() else 8888
        }
    
    def show_register_form(self) -> Dict[str, str]:
        """
        Affiche le formulaire d'inscription
        
        Returns:
            Dict[str, str]: Informations d'inscription
        """
        self.clear_screen()
        
        # Calcul de la largeur du terminal
        try:
            import shutil
            terminal_width = shutil.get_terminal_size().columns
        except:
            terminal_width = 80
        
        title = "👤 INSCRIPTION"
        title_centered = title.center(terminal_width)
        print(self.colors['bright_green'] + title_centered + self.colors['reset'])
        print(self.colors['cyan'] + "="*terminal_width + self.colors['reset'])
        
        # Espacement
        print()
        print()
        
        username = input(f"{self.colors['yellow']}Nom d'utilisateur: {self.colors['reset']}")
        print()
        password = input(f"{self.colors['yellow']}Mot de passe: {self.colors['reset']}")
        print()
        confirm_password = input(f"{self.colors['yellow']}Confirmer le mot de passe: {self.colors['reset']}")
        
        # Espacement
        print()
        print()
        
        return {
            "username": username.strip(),
            "password": password.strip(),
            "confirm_password": confirm_password.strip()
        }
    
    def show_server_menu(self) -> str:
        """
        Affiche le menu du serveur
        
        Returns:
            str: Choix de l'utilisateur
        """
        self.clear_screen()
        
        # Calcul de la largeur du terminal
        try:
            import shutil
            terminal_width = shutil.get_terminal_size().columns
        except:
            terminal_width = 80
        
        title = "🖥️  SERVEUR MESSAGERCRYPT"
        title_centered = title.center(terminal_width)
        print(self.colors['bright_blue'] + title_centered + self.colors['reset'])
        print(self.colors['cyan'] + "="*terminal_width + self.colors['reset'])
        
        options = [
            "[1] 🚀 Démarrer le serveur",
            "[2] 📊 Statistiques",
            "[3] 👥 Utilisateurs connectés",
            "[4] 📝 Logs",
            "[5] 🔙 Retour au menu principal"
        ]
        
        for option in options:
            print(f"  {self.colors['white']}{option}{self.colors['reset']}")
        
        choice = input(f"\n{self.colors['yellow']}Votre choix (1-5): {self.colors['reset']}")
        return choice.strip()
    
    def show_messaging_interface(self, username: str) -> str:
        """
        Affiche l'interface de messagerie
        
        Args:
            username: Nom d'utilisateur connecté
            
        Returns:
            str: Choix de l'utilisateur
        """
        self.clear_screen()
        
        # Calcul de la largeur du terminal
        try:
            import shutil
            terminal_width = shutil.get_terminal_size().columns
        except:
            terminal_width = 80
        
        title = f"💬 MESSAGERIE - {username.upper()}"
        title_centered = title.center(terminal_width)
        print(self.colors['bright_green'] + title_centered + self.colors['reset'])
        print(self.colors['cyan'] + "="*terminal_width + self.colors['reset'])
        
        # Espacement
        print()
        print()
        
        options = [
            "[1] 📤 Envoyer un message",
            "[2] 📥 Messages reçus",
            "[3] 📜 Historique",
            "[4] 🔍 Rechercher",
            "[5] ⚙️  Paramètres",
            "[6] 🔙 Déconnexion"
        ]
        
        for option in options:
            print(f"  {self.colors['white']}{option}{self.colors['reset']}")
        
        # Espacement
        print()
        print()
        
        choice = input(f"{self.colors['yellow']}Votre choix (1-6): {self.colors['reset']}")
        return choice.strip()
    
    def show_message_compose(self, recipient: str = None) -> Dict[str, str]:
        """
        Affiche l'interface de composition de message
        
        Args:
            recipient: Destinataire par défaut
            
        Returns:
            Dict[str, str]: Informations du message
        """
        self.clear_screen()
        
        # Calcul de la largeur du terminal
        try:
            import shutil
            terminal_width = shutil.get_terminal_size().columns
        except:
            terminal_width = 80
        
        title = "📤 COMPOSER UN MESSAGE"
        title_centered = title.center(terminal_width)
        print(self.colors['bright_blue'] + title_centered + self.colors['reset'])
        print(self.colors['cyan'] + "="*terminal_width + self.colors['reset'])
        
        # Espacement
        print()
        print()
        
        if not recipient:
            recipient = input(f"{self.colors['yellow']}Destinataire: {self.colors['reset']}")
        
        print()
        print()
        print(f"{self.colors['yellow']}Message (Entrée pour nouvelle ligne, double Entrée pour envoyer):{self.colors['reset']}")
        print(self.colors['white'] + "-" * 50 + self.colors['reset'])
        print()
        print()
        
        # Saisie du message (multiligne) - sera gérée par le client
        print(f"{self.colors['cyan']}Tapez votre message:{self.colors['reset']}")
        print(f"{self.colors['dim']}Entrée pour nouvelle ligne, double Entrée pour envoyer{self.colors['reset']}")
        print()
        
        lines = []
        empty_lines = 0
        
        while True:
            try:
                line = input()
                
                if line.strip() == "":
                    empty_lines += 1
                    if empty_lines >= 2:
                        # Double ligne vide = fin du message
                        break
                else:
                    empty_lines = 0
                    lines.append(line)
                    
            except KeyboardInterrupt:
                # Ctrl+C pour annuler
                print(f"\n{self.colors['yellow']}Saisie annulée{self.colors['reset']}")
                return {"recipient": recipient.strip(), "message": ""}
        
        message = '\n'.join(lines)
        
        return {
            "recipient": recipient.strip(),
            "message": message.strip()
        }
    
    def show_message_history(self, messages: List[Dict], username: str, title: str = None):
        """
        Affiche l'historique des messages
        
        Args:
            messages: Liste des messages
            username: Nom d'utilisateur
            title: Titre personnalisé
        """
        self.clear_screen()
        
        # Calcul de la largeur du terminal
        try:
            import shutil
            terminal_width = shutil.get_terminal_size().columns
        except:
            terminal_width = 80
        
        if not title:
            title = f"📜 HISTORIQUE - {username.upper()}"
        title_centered = title.center(terminal_width)
        print(self.colors['bright_blue'] + title_centered + self.colors['reset'])
        print(self.colors['cyan'] + "="*terminal_width + self.colors['reset'])
        
        # Espacement
        print()
        print()
        
        if not messages:
            print(f"{self.colors['yellow']}Aucun message dans l'historique.{self.colors['reset']}")
            print()
            print()
            input(f"{self.colors['cyan']}Appuyez sur Entrée pour continuer...{self.colors['reset']}")
            return
        
        # Affichage des messages
        for i, msg in enumerate(messages):
            sender_color = self.colors['green'] if msg['sender'] == username else self.colors['blue']
            status_color = self.colors['green'] if msg.get('is_read', False) else self.colors['yellow']
            
            print(f"\n{self.colors['white']}{'─' * 60}{self.colors['reset']}")
            print(f"{self.colors['cyan']}De: {sender_color}{msg['sender']}{self.colors['reset']}")
            print(f"{self.colors['cyan']}À: {self.colors['white']}{msg['recipient']}{self.colors['reset']}")
            print(f"{self.colors['cyan']}Date: {self.colors['white']}{msg['timestamp']}{self.colors['reset']}")
            print(f"{self.colors['cyan']}Statut: {status_color}{'✓ Lu' if msg.get('is_read', False) else '● Non lu'}{self.colors['reset']}")
            
            if not msg.get('encrypted', True):
                print(f"{self.colors['cyan']}Message: {self.colors['white']}{msg.get('message', '[Chiffré]')}{self.colors['reset']}")
        
        print(f"\n{self.colors['white']}{'─' * 60}{self.colors['reset']}")
        input(f"\n{self.colors['cyan']}Appuyez sur Entrée pour continuer...{self.colors['reset']}")
    
    def show_rich_message_history(self, messages: List[Dict], username: str):
        """
        Affiche l'historique avec Rich
        
        Args:
            messages: Liste des messages
            username: Nom d'utilisateur
        """
        self.clear_screen()
        
        # En-tête
        header_text = Text(f"HISTORIQUE - {username.upper()}", style="bold blue")
        header_panel = Panel(header_text, border_style="blue")
        # Centrage du panneau
        from rich.align import Align
        centered_panel = Align.center(header_panel)
        console.print(centered_panel)
        
        if not messages:
            console.print("[yellow]Aucun message dans l'historique.[/yellow]")
            console.print()
            Prompt.ask("[cyan]Appuyez sur Entrée pour continuer[/cyan]", default="")
            return
        
        # Table des messages
        table = Table(title="Messages", show_header=True, header_style="bold blue")
        table.add_column("De", style="green", width=15)
        table.add_column("À", style="blue", width=15)
        table.add_column("Date", style="cyan", width=20)
        table.add_column("Statut", style="yellow", width=10)
        
        for msg in messages:
            sender = msg['sender']
            recipient = msg['recipient']
            timestamp = msg['timestamp']
            status = "✓ Lu" if msg.get('is_read', False) else "● Non lu"
            
            table.add_row(sender, recipient, timestamp, status)
        
        console.print(table)
        console.print()
        Prompt.ask("[cyan]Appuyez sur Entrée pour continuer[/cyan]", default="")
    
    def show_configuration_menu(self) -> str:
        """
        Affiche le menu de configuration
        
        Returns:
            str: Choix de l'utilisateur
        """
        self.clear_screen()
        
        # Calcul de la largeur du terminal
        try:
            import shutil
            terminal_width = shutil.get_terminal_size().columns
        except:
            terminal_width = 80
        
        title = "⚙️  CONFIGURATION"
        title_centered = title.center(terminal_width)
        print(self.colors['bright_blue'] + title_centered + self.colors['reset'])
        print(self.colors['cyan'] + "="*terminal_width + self.colors['reset'])
        
        # Espacement
        print()
        print()
        
        options = [
            "[1] 🔐 Paramètres de sécurité",
            "[2] 🌐 Paramètres réseau",
            "[3] 🎨 Thème et couleurs",
            "[4] 📊 Statistiques",
            "[5] 🗑️  Nettoyer les données",
            "[6] 🔙 Retour"
        ]
        
        for option in options:
            print(f"  {self.colors['white']}{option}{self.colors['reset']}")
        
        # Espacement
        print()
        print()
        
        choice = input(f"{self.colors['yellow']}Votre choix (1-6): {self.colors['reset']}")
        return choice.strip()
    
    def show_rich_prompt(self, message: str, choices: List[str] = None, default: str = None) -> str:
        """
        Affiche une invite avec Rich
        
        Args:
            message: Message à afficher
            choices: Choix possibles
            default: Valeur par défaut
            
        Returns:
            str: Réponse de l'utilisateur
        """
        if choices:
            return Prompt.ask(message, choices=choices, default=default)
        else:
            return Prompt.ask(message, default=default)
    
    def show_rich_confirm(self, message: str, default: bool = True) -> bool:
        """
        Affiche une confirmation avec Rich
        
        Args:
            message: Message à afficher
            default: Valeur par défaut
            
        Returns:
            bool: Réponse de l'utilisateur
        """
        return Confirm.ask(message, default=default)
    
    def show_rich_table(self, title: str, data: List[Dict], columns: List[str]):
        """
        Affiche un tableau avec Rich
        
        Args:
            title: Titre du tableau
            data: Données à afficher
            columns: Colonnes du tableau
        """
        table = Table(title=title, show_header=True, header_style="bold blue")
        
        for col in columns:
            table.add_column(col, style="white")
        
        for row in data:
            table.add_row(*[str(row.get(col, "")) for col in columns])
        
        console.print(table)
    
    def show_notification(self, message: str, type: str = "info"):
        """
        Affiche une notification
        
        Args:
            message: Message de notification
            type: Type de notification (info, success, warning, error)
        """
        colors = {
            "info": self.colors['blue'],
            "success": self.colors['green'],
            "warning": self.colors['yellow'],
            "error": self.colors['red']
        }
        
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        
        color = colors.get(type, self.colors['white'])
        icon = icons.get(type, "ℹ️")
        
        print(f"\n{color}{icon} {message}{self.colors['reset']}")
        time.sleep(1)
    
    def show_rich_notification(self, message: str, type: str = "info"):
        """
        Affiche une notification avec Rich
        
        Args:
            message: Message de notification
            type: Type de notification
        """
        styles = {
            "info": "blue",
            "success": "green",
            "warning": "yellow",
            "error": "red"
        }
        
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        
        style = styles.get(type, "white")
        icon = icons.get(type, "ℹ️")
        
        notification = Text(f"{icon} {message}", style=style)
        console.print(notification)
        time.sleep(1)
    
    def show_success(self, message: str):
        """
        Affiche un message de succès
        
        Args:
            message: Message de succès
        """
        print(f"\n{self.colors['green']}✅ {message}{self.colors['reset']}")
    
    def show_error(self, message: str):
        """
        Affiche un message d'erreur
        
        Args:
            message: Message d'erreur
        """
        print(f"\n{self.colors['red']}❌ {message}{self.colors['reset']}")
    
    def show_warning(self, message: str):
        """
        Affiche un avertissement
        
        Args:
            message: Message d'avertissement
        """
        print(f"\n{self.colors['yellow']}⚠️  {message}{self.colors['reset']}")
    
    def _get_multiline_input(self) -> str:
        """
        Saisie multiligne avec Entrée pour nouvelle ligne et double Entrée pour envoyer
        
        Returns:
            str: Message saisi
        """
        print(f"{self.colors['cyan']}Tapez votre message:{self.colors['reset']}")
        print(f"{self.colors['dim']}Entrée pour nouvelle ligne, double Entrée pour envoyer{self.colors['reset']}")
        print()
        
        lines = []
        empty_lines = 0
        
        while True:
            try:
                line = input()
                
                if line.strip() == "":
                    empty_lines += 1
                    if empty_lines >= 2:
                        # Double ligne vide = fin du message
                        break
                else:
                    empty_lines = 0
                    lines.append(line)
                    
            except KeyboardInterrupt:
                # Ctrl+C pour annuler
                print(f"\n{self.colors['yellow']}Saisie annulée{self.colors['reset']}")
                return ""
        
        return '\n'.join(lines)
    
    def show_messaging_menu(self, username: str) -> str:
        """
        Affiche le menu de messagerie
        
        Args:
            username: Nom d'utilisateur connecté
            
        Returns:
            str: Choix de l'utilisateur
        """
        self.clear_screen()
        
        # Largeur responsive
        terminal_width = self.get_responsive_width()
        spacing = self.get_responsive_spacing()
        
        # Titre adaptatif
        if self.is_very_small_terminal():
            title = f"💬 {username.upper()}"
        else:
            title = f"💬 MESSAGERIE - {username.upper()}"
        
        title_centered = title.center(terminal_width)
        print(self.colors['bright_green'] + title_centered + self.colors['reset'])
        print(self.colors['cyan'] + "="*terminal_width + self.colors['reset'])
        
        # Espacement responsive
        for _ in range(spacing):
            print()
        
        # Options adaptatives
        if self.is_very_small_terminal():
            options = [
                "[1] 📤 Envoyer",
                "[2] 📥 Reçus",
                "[3] 📜 Historique",
                "[4] 🔍 Rechercher",
                "[5] ⚙️  Paramètres",
                "[6] 🔙 Déconnexion"
            ]
        else:
            options = [
                "[1] 📤 Envoyer un message",
                "[2] 📥 Messages reçus",
                "[3] 📜 Historique",
                "[4] 🔍 Rechercher",
                "[5] ⚙️  Paramètres",
                "[6] 🔙 Déconnexion"
            ]
        
        for option in options:
            print(f"  {self.colors['white']}{option}{self.colors['reset']}")
        
        # Espacement responsive
        for _ in range(spacing):
            print()
        
        choice = input(f"{self.colors['yellow']}Votre choix (1-6): {self.colors['reset']}")
        return choice.strip()
    
    def show_compose_message(self, recipient: str = None) -> Dict[str, str]:
        """
        Affiche le formulaire de composition de message
        
        Args:
            recipient: Destinataire pré-rempli
            
        Returns:
            Dict[str, str]: Informations du message
        """
        self.clear_screen()
        
        # Largeur responsive
        terminal_width = self.get_responsive_width()
        spacing = self.get_responsive_spacing()
        
        # Titre adaptatif
        if self.is_very_small_terminal():
            title = "📤 NOUVEAU MESSAGE"
        else:
            title = "📤 COMPOSER UN MESSAGE"
        
        title_centered = title.center(terminal_width)
        print(self.colors['bright_blue'] + title_centered + self.colors['reset'])
        print(self.colors['cyan'] + "="*terminal_width + self.colors['reset'])
        
        # Espacement responsive
        for _ in range(spacing):
            print()
        
        if not recipient:
            recipient = input(f"{self.colors['yellow']}Destinataire: {self.colors['reset']}")
        
        # Espacement responsive
        for _ in range(spacing):
            print()
        
        # Instructions adaptatives
        if self.is_very_small_terminal():
            print(f"{self.colors['yellow']}Message:{self.colors['reset']}")
        else:
            print(f"{self.colors['yellow']}Message (Entrée pour nouvelle ligne, double Entrée pour envoyer):{self.colors['reset']}")
        
        # Séparateur adaptatif
        separator_width = min(terminal_width - 20, 50)
        print(self.colors['white'] + "-" * separator_width + self.colors['reset'])
        
        # Espacement responsive
        for _ in range(spacing):
            print()
        
        # Saisie du message (multiligne)
        if not self.is_very_small_terminal():
            print(f"{self.colors['cyan']}Tapez votre message:{self.colors['reset']}")
            print(f"{self.colors['dim']}Entrée pour nouvelle ligne, double Entrée pour envoyer{self.colors['reset']}")
            print()
        
        lines = []
        empty_lines = 0
        
        while True:
            try:
                line = input()
                
                if line.strip() == "":
                    empty_lines += 1
                    if empty_lines >= 2:
                        # Double ligne vide = fin du message
                        break
                else:
                    empty_lines = 0
                    lines.append(line)
                    
            except KeyboardInterrupt:
                # Ctrl+C pour annuler
                print(f"\n{self.colors['yellow']}Saisie annulée{self.colors['reset']}")
                return {"recipient": recipient.strip(), "message": ""}
        
        message = '\n'.join(lines)
        
        return {
            "recipient": recipient.strip(),
            "message": message.strip()
        }
    
    def show_rich_panel(self, title: str, content: str):
        """
        Affiche un panneau Rich
        
        Args:
            title: Titre du panneau
            content: Contenu du panneau
        """
        from rich.panel import Panel
        from rich.text import Text
        from rich.align import Align
        
        panel_text = Text(content, style="white")
        panel = Panel(panel_text, title=title, border_style="blue")
        centered_panel = Align.center(panel)
        console.print(centered_panel)
    
    def show_rich_text(self, text: str, style: str = "white"):
        """
        Affiche du texte Rich
        
        Args:
            text: Texte à afficher
            style: Style du texte
        """
        from rich.text import Text
        from rich.align import Align
        
        rich_text = Text(text, style=style)
        centered_text = Align.center(rich_text)
        console.print(centered_text)
    
    def show_rich_table(self, title: str, data: List[Dict], columns: List[str]):
        """
        Affiche un tableau Rich
        
        Args:
            title: Titre du tableau
            data: Données du tableau
            columns: Colonnes du tableau
        """
        from rich.table import Table
        from rich.align import Align
        
        table = Table(title=title, border_style="blue")
        
        for col in columns:
            table.add_column(col, style="white")
        
        for row in data:
            table.add_row(*[str(row.get(col, "")) for col in columns])
        
        centered_table = Align.center(table)
        console.print(centered_table)
    
    def show_rich_notification(self, message: str, type: str = "info"):
        """
        Affiche une notification avec Rich
        
        Args:
            message: Message de notification
            type: Type de notification
        """
        from rich.text import Text
        from rich.align import Align
        
        styles = {
            "info": "blue",
            "success": "green",
            "warning": "yellow",
            "error": "red"
        }
        
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        
        style = styles.get(type, "white")
        icon = icons.get(type, "ℹ️")
        
        notification = Text(f"{icon} {message}", style=style)
        centered_notification = Align.center(notification)
        console.print(centered_notification)
        time.sleep(1)
    
    def show_rich_confirm(self, message: str) -> bool:
        """
        Affiche une confirmation avec Rich
        
        Args:
            message: Message de confirmation
            
        Returns:
            bool: True si confirmé
        """
        from rich.text import Text
        from rich.align import Align
        
        confirm_text = Text(f"{message} (o/n)", style="yellow")
        centered_text = Align.center(confirm_text)
        console.print(centered_text)
        
        response = input().strip().lower()
        return response in ['o', 'oui', 'y', 'yes']
    
    def clear_screen(self):
        """Efface l'écran"""
        print('\033[2J\033[H', end='')
    
    def pause(self, message: str = "Appuyez sur Entrée pour continuer..."):
        """Met en pause l'exécution"""
        input(f"\n{self.colors['cyan']}{message}{self.colors['reset']}")
    
    def show_loading(self, message: str, duration: float = 2.0):
        """
        Affiche un indicateur de chargement
        
        Args:
            message: Message à afficher
            duration: Durée du chargement
        """
        print(f"\n{self.colors['blue']}{message}...{self.colors['reset']}", end='', flush=True)
        
        for _ in range(int(duration * 2)):
            print(".", end='', flush=True)
            time.sleep(0.5)
        
        print(f" {self.colors['green']}Terminé!{self.colors['reset']}")
    
    def show_rich_loading(self, message: str, duration: float = 2.0):
        """
        Affiche un indicateur de chargement avec Rich
        
        Args:
            message: Message à afficher
            duration: Durée du chargement
        """
        from rich.progress import Progress, BarColumn, TextColumn
        
        with Progress(
            TextColumn(f"[bold blue]{message}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("", total=100)
            
            for i in range(100):
                progress.update(task, advance=1)
                time.sleep(duration / 100)
