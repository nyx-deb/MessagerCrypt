"""
Module d'ASCII art et d'animations pour MessagerCrypt
Interface visuelle dynamique pour le terminal
"""
import time
import sys
import itertools
from typing import List, Optional
from colorama import init, Fore, Back, Style
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

# Initialisation de colorama
init(autoreset=True)

# Console Rich pour les animations avancées
console = Console()


class ASCIIArt:
    """Gestionnaire d'ASCII art et d'animations pour MessagerCrypt"""
    
    def __init__(self):
        self.colors = {
            'red': Fore.RED,
            'green': Fore.GREEN,
            'yellow': Fore.YELLOW,
            'blue': Fore.BLUE,
            'magenta': Fore.MAGENTA,
            'cyan': Fore.CYAN,
            'white': Fore.WHITE,
            'bright_red': Style.BRIGHT + Fore.RED,
            'bright_green': Style.BRIGHT + Fore.GREEN,
            'bright_blue': Style.BRIGHT + Fore.BLUE,
            'reset': Style.RESET_ALL
        }
    
    def clear_screen(self):
        """Efface l'écran du terminal"""
        print('\033[2J\033[H', end='')
    
    def show_logo(self, color: str = 'red', animated: bool = True):
        """
        Affiche le logo MessagerCrypt
        
        Args:
            color: Couleur du logo
            animated: Animation du logo
        """
        # Récupération de la taille du terminal
        try:
            import shutil
            terminal_width = shutil.get_terminal_size().columns
            terminal_height = shutil.get_terminal_size().lines
        except:
            terminal_width = 80
            terminal_height = 24
        
        # Espacement responsive
        spacing = 3 if terminal_height > 30 else (2 if terminal_height > 20 else 1)
        for _ in range(spacing):
            print()
        
        # Logo adaptatif selon la taille du terminal
        if terminal_width < 60:
            # Version très compacte
            logo_lines = [
                "███╗   ███╗███████╗███████╗███████╗ █████╗ ",
                "████╗ ████║██╔════╝██╔════╝██╔════╝██╔══██╗",
                "██╔████╔██║█████╗  ███████╗███████╗███████║",
                "██║╚██╔╝██║██╔══╝  ╚════██║╚════██║██╔══██║",
                "██║ ╚═╝ ██║███████╗███████║███████║██║  ██║",
                "╚═╝     ╚═╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝"
            ]
        elif terminal_width < 100:
            # Version compacte
            logo_lines = [
                "███╗   ███╗███████╗███████╗███████╗ █████╗  ██████╗ ███████╗██████╗ ",
                "████╗ ████║██╔════╝██╔════╝██╔════╝██╔══██╗██╔════╝ ██╔════╝██╔══██╗",
                "██╔████╔██║█████╗  ███████╗███████╗███████║██║  ███╗█████╗  ██████╔╝",
                "██║╚██╔╝██║██╔══╝  ╚════██║╚════██║██╔══██║██║   ██║██╔══╝  ██╔══██╗",
                "██║ ╚═╝ ██║███████╗███████║███████║██║  ██║╚██████╔╝███████╗██║  ██║",
                "╚═╝     ╚═╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝"
            ]
        else:
            # Version complète
            logo_lines = [
                "███╗   ███╗███████╗███████╗███████╗ █████╗  ██████╗ ███████╗██████╗  ██████╗██████╗ ██╗   ██╗██████╗ ████████╗",
                "████╗ ████║██╔════╝██╔════╝██╔════╝██╔══██╗██╔════╝ ██╔════╝██╔══██╗██╔════╝██╔══██╗╚██╗ ██╔╝██╔══██╗╚══██╔══╝",
                "██╔████╔██║█████╗  ███████╗███████╗███████║██║  ███╗█████╗  ██████╔╝██║     ██████╔╝ ╚████╔╝ ██████╔╝   ██║   ",
                "██║╚██╔╝██║██╔══╝  ╚════██║╚════██║██╔══██║██║   ██║██╔══╝  ██╔══██╗██║     ██╔══██╗  ╚██╔╝  ██╔═══╝    ██║   ",
                "██║ ╚═╝ ██║███████╗███████║███████║██║  ██║╚██████╔╝███████╗██║  ██║╚██████╗██║  ██║   ██║   ██║        ██║   ",
                "╚═╝     ╚═╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝        ╚═╝   "
            ]
        
        if animated:
            # Animation avec centrage responsive
            for line in logo_lines:
                centered_line = line.center(terminal_width)
                print(f"{self.colors[color]}{centered_line}{self.colors['reset']}")
                time.sleep(0.1)
        else:
            # Affichage simple avec centrage responsive
            for line in logo_lines:
                centered_line = line.center(terminal_width)
                print(f"{self.colors[color]}{centered_line}{self.colors['reset']}")
        
        # Espacement responsive en-dessous
        for _ in range(spacing):
            print()
    
    def show_subtitle(self, text: str = "Messagerie Sécurisée v1.0", color: str = 'cyan'):
        """Affiche le sous-titre"""
        # Calcul de la largeur du terminal
        try:
            import shutil
            terminal_width = shutil.get_terminal_size().columns
        except:
            terminal_width = 80
        
        subtitle = f"\n{'='*terminal_width}\n{text:^{terminal_width}}\n{'='*terminal_width}\n"
        print(self.colors.get(color, self.colors['cyan']) + subtitle + self.colors['reset'])
    
    def show_loading_animation(self, steps: List[str], duration: float = 0.5):
        """
        Affiche une animation de chargement
        
        Args:
            steps: Liste des étapes à afficher
            duration: Durée entre chaque étape
        """
        for i, step in enumerate(steps):
            # Barre de progression
            progress = "█" * (i + 1) + "░" * (len(steps) - i - 1)
            percentage = int((i + 1) / len(steps) * 100)
            
            print(f"\r{step} [{progress}] {percentage}%", end='', flush=True)
            time.sleep(duration)
        
        print(f"\r{steps[-1]} [{'█' * len(steps)}] 100%")
        print(self.colors['green'] + "✓ Initialisation terminée" + self.colors['reset'])
    
    def show_connection_animation(self, host: str = "127.0.0.1", port: int = 8888):
        """
        Affiche une animation de connexion
        
        Args:
            host: Adresse du serveur
            port: Port du serveur
        """
        print(f"\n{self.colors['blue']}Connexion au serveur {host}:{port}...{self.colors['reset']}")
        
        # Animation de points
        for i in range(3):
            print(f"\rConnexion{'.' * (i + 1)}", end='', flush=True)
            time.sleep(0.5)
        
        print(f"\r{self.colors['green']}✓ Connexion établie{self.colors['reset']}")
    
    def show_message_sent(self, recipient: str):
        """
        Affiche une confirmation d'envoi de message
        
        Args:
            recipient: Destinataire du message
        """
        print(f"\n{self.colors['green']}✅ Message envoyé à {recipient}{self.colors['reset']}")
    
    def show_message_received(self, sender: str, message: str):
        """
        Affiche la réception d'un message
        
        Args:
            sender: Expéditeur du message
            message: Contenu du message
        """
        print(f"\n{self.colors['cyan']}📨 Nouveau message de {sender}:{self.colors['reset']}")
        print(f"{self.colors['white']}{message}{self.colors['reset']}")
    
    # Les méthodes show_error, show_success, show_warning sont maintenant dans MenuManager
    # pour éviter les doublons de validation
    
    def show_typing_animation(self, text: str, speed: float = 0.05):
        """
        Affiche un effet de frappe
        
        Args:
            text: Texte à afficher
            speed: Vitesse de frappe
        """
        for char in text:
            print(char, end='', flush=True)
            time.sleep(speed)
        print()
    
    def show_progress_bar(self, current: int, total: int, width: int = 50):
        """
        Affiche une barre de progression
        
        Args:
            current: Valeur actuelle
            total: Valeur totale
            width: Largeur de la barre
        """
        percentage = current / total
        filled = int(width * percentage)
        bar = "█" * filled + "░" * (width - filled)
        print(f"\r[{bar}] {int(percentage * 100)}%", end='', flush=True)
    
    def show_rich_loading(self, title: str = "Chargement", steps: List[str] = None):
        """
        Affiche une animation de chargement avec Rich
        
        Args:
            title: Titre de l'animation
            steps: Étapes à afficher
        """
        if steps is None:
            steps = [
                "Initialisation du module de chiffrement",
                "Connexion au serveur",
                "Chargement des modules",
                "Vérification de la sécurité",
                "Préparation de l'interface"
            ]
        
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task(title, total=len(steps))
            
            for i, step in enumerate(steps):
                progress.update(task, description=step, advance=1)
                time.sleep(0.8)
    
    def show_rich_panel(self, title: str, content: str, color: str = "blue"):
        """
        Affiche un panneau avec Rich
        
        Args:
            title: Titre du panneau
            content: Contenu du panneau
            color: Couleur du panneau
        """
        panel = Panel(
            content,
            title=f"[bold {color}]{title}[/bold {color}]",
            border_style=color,
            padding=(1, 2)
        )
        # Centrage du panneau
        from rich.align import Align
        centered_panel = Align.center(panel)
        console.print(centered_panel)
    
    def show_rich_text(self, text: str, style: str = "bold white"):
        """
        Affiche du texte stylé avec Rich
        
        Args:
            text: Texte à afficher
            style: Style à appliquer
        """
        rich_text = Text(text, style=style)
        # Centrage du texte
        from rich.align import Align
        centered_text = Align.center(rich_text)
        console.print(centered_text)
    
    def show_centered_text(self, text: str, color: str = "white"):
        """
        Affiche du texte centré
        
        Args:
            text: Texte à centrer
            color: Couleur du texte
        """
        centered = Align.center(text)
        console.print(centered, style=color)
    
    def _animate_text(self, text: str, color: str):
        """
        Anime l'affichage d'un texte
        
        Args:
            text: Texte à animer
            color: Couleur du texte
        """
        lines = text.strip().split('\n')
        color_code = self.colors.get(color, self.colors['red'])
        
        for line in lines:
            if line.strip():
                print(color_code + line + self.colors['reset'])
                time.sleep(0.1)
            else:
                print()
    
    def show_cyber_animation(self):
        """Affiche une animation cyberpunk"""
        frames = [
            "01001000 01100101 01101100 01101100 01101111",
            "01010111 01101111 01110010 01101100 01100100",
            "01000011 01111001 01100010 01100101 01110010",
            "01010011 01100101 01100011 01110101 01110010 01101001 01110100 01111001"
        ]
        
        for frame in frames:
            print(f"\r{self.colors['green']}{frame}{self.colors['reset']}", end='', flush=True)
            time.sleep(0.3)
        print()
    
    def show_matrix_rain(self, duration: int = 3):
        """
        Affiche un effet Matrix (pluie de caractères)
        
        Args:
            duration: Durée en secondes
        """
        import random
        
        chars = "01"
        width = 80
        height = 20
        
        start_time = time.time()
        while time.time() - start_time < duration:
            print(f"\r{self.colors['green']}", end='')
            for _ in range(height):
                line = ''.join(random.choice(chars) for _ in range(width))
                print(line)
            time.sleep(0.1)
            self.clear_screen()
        
        print(self.colors['reset'])
    
    def show_startup_sequence(self):
        """Séquence de démarrage complète"""
        self.clear_screen()
        
        # Logo animé
        self.show_logo('red', animated=True)
        time.sleep(1)
        
        # Sous-titre
        self.show_subtitle("Messagerie Sécurisée v1.0", 'cyan')
        time.sleep(1)
        
        # Animation de chargement
        steps = [
            "Initialisation du module de chiffrement",
            "Connexion au serveur",
            "Chargement des modules",
            "Vérification de la sécurité",
            "Préparation de l'interface"
        ]
        
        self.show_loading_animation(steps, 0.8)
        time.sleep(1)
        
        # Animation cyberpunk
        self.show_cyber_animation()
        time.sleep(1)
        
        print(f"\n{self.colors['bright_green']}🚀 MessagerCrypt prêt à l'emploi !{self.colors['reset']}\n")
