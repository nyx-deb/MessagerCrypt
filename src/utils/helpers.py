"""
Module d'utilitaires pour MessagerCrypt
Fonctions d'aide et utilitaires généraux
"""
import os
import time
import hashlib
import base64
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


class MessagerCryptHelpers:
    """Classe d'utilitaires pour MessagerCrypt"""
    
    # Cache pour les validations fréquentes
    _validation_cache = {}
    _cache_max_size = 1000
    
    # Regex compilées pour optimiser les performances
    _username_regex = re.compile(r'^[a-zA-Z0-9_-]{3,20}$')
    _email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    @staticmethod
    def generate_session_id() -> str:
        """Génère un ID de session unique"""
        timestamp = str(int(time.time() * 1000))
        random_bytes = os.urandom(16)
        return hashlib.sha256(f"{timestamp}{random_bytes}".encode()).hexdigest()[:32]
    
    @staticmethod
    def hash_password(password: str, salt: bytes = None) -> tuple:
        """
        Hache un mot de passe avec un sel
        
        Args:
            password: Mot de passe à hacher
            salt: Sel optionnel
            
        Returns:
            tuple: (hash, salt)
        """
        if salt is None:
            salt = os.urandom(32)
        
        # Utilisation de PBKDF2 pour le hachage
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.backends import default_backend
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        password_hash = kdf.derive(password.encode())
        return password_hash, salt
    
    @staticmethod
    def verify_password(password: str, stored_hash: bytes, salt: bytes) -> bool:
        """
        Vérifie un mot de passe contre un hash stocké
        
        Args:
            password: Mot de passe à vérifier
            stored_hash: Hash stocké
            salt: Sel utilisé
            
        Returns:
            bool: True si le mot de passe est correct
        """
        try:
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.backends import default_backend
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            
            password_hash = kdf.derive(password.encode())
            return password_hash == stored_hash
            
        except Exception:
            return False
    
    @staticmethod
    def format_timestamp(timestamp: float) -> str:
        """
        Formate un timestamp en chaîne lisible
        
        Args:
            timestamp: Timestamp Unix
            
        Returns:
            str: Timestamp formaté
        """
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        Formate une durée en chaîne lisible
        
        Args:
            seconds: Durée en secondes
            
        Returns:
            str: Durée formatée
        """
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Nettoie un nom de fichier pour la sécurité
        
        Args:
            filename: Nom de fichier à nettoyer
            
        Returns:
            str: Nom de fichier nettoyé
        """
        # Caractères interdits
        forbidden_chars = '<>:"/\\|?*'
        for char in forbidden_chars:
            filename = filename.replace(char, '_')
        
        # Limitation de la longueur
        if len(filename) > 255:
            filename = filename[:255]
        
        return filename
    
    @classmethod
    def validate_username(cls, username: str) -> bool:
        """
        Valide un nom d'utilisateur avec cache
        
        Args:
            username: Nom d'utilisateur à valider
            
        Returns:
            bool: True si valide
        """
        # Vérification du cache
        if username in cls._validation_cache:
            return cls._validation_cache[username]
        
        # Validation avec regex compilée
        is_valid = bool(cls._username_regex.match(username))
        
        # Mise en cache
        if len(cls._validation_cache) >= cls._cache_max_size:
            cls._validation_cache.clear()
        cls._validation_cache[username] = is_valid
        
        return is_valid
    
    @staticmethod
    def validate_password(password: str) -> tuple:
        """
        Valide un mot de passe
        
        Args:
            password: Mot de passe à valider
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Le mot de passe doit contenir au moins 8 caractères"
        
        if len(password) > 128:
            return False, "Le mot de passe ne peut pas dépasser 128 caractères"
        
        # Vérification de la complexité
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        if not (has_lower and has_upper and has_digit):
            return False, "Le mot de passe doit contenir des majuscules, minuscules et chiffres"
        
        return True, "Mot de passe valide"
    
    @staticmethod
    def generate_random_string(length: int = 32) -> str:
        """
        Génère une chaîne aléatoire
        
        Args:
            length: Longueur de la chaîne
            
        Returns:
            str: Chaîne aléatoire
        """
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """
        Calcule le hash SHA-256 d'un fichier
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            str: Hash du fichier
        """
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    @staticmethod
    def create_backup(data: Dict, backup_path: str) -> bool:
        """
        Crée une sauvegarde des données
        
        Args:
            data: Données à sauvegarder
            backup_path: Chemin de sauvegarde
            
        Returns:
            bool: True si succès
        """
        try:
            import json
            from pathlib import Path
            
            # Création du répertoire si nécessaire
            Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Ajout du timestamp
            backup_data = {
                "timestamp": time.time(),
                "data": data
            }
            
            # Sauvegarde
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def load_backup(backup_path: str) -> Optional[Dict]:
        """
        Charge une sauvegarde
        
        Args:
            backup_path: Chemin de la sauvegarde
            
        Returns:
            Optional[Dict]: Données de sauvegarde ou None
        """
        try:
            import json
            
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
            
            return backup_data.get("data")
            
        except Exception:
            return None
    
    @staticmethod
    def cleanup_old_files(directory: str, max_age_days: int = 30) -> int:
        """
        Nettoie les anciens fichiers
        
        Args:
            directory: Répertoire à nettoyer
            max_age_days: Âge maximum en jours
            
        Returns:
            int: Nombre de fichiers supprimés
        """
        try:
            from pathlib import Path
            import time
            
            directory_path = Path(directory)
            if not directory_path.exists():
                return 0
            
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 3600
            deleted_count = 0
            
            for file_path in directory_path.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        deleted_count += 1
            
            return deleted_count
            
        except Exception:
            return 0
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """
        Récupère les informations système
        
        Returns:
            Dict[str, Any]: Informations système
        """
        try:
            import platform
            import psutil
            
            return {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "architecture": platform.architecture()[0],
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_usage": psutil.disk_usage('/').percent
            }
            
        except Exception:
            return {
                "platform": "Unknown",
                "platform_version": "Unknown",
                "architecture": "Unknown",
                "processor": "Unknown",
                "python_version": "Unknown"
            }
    
    @staticmethod
    def format_bytes(bytes_value: int) -> str:
        """
        Formate une valeur en bytes en chaîne lisible
        
        Args:
            bytes_value: Valeur en bytes
            
        Returns:
            str: Valeur formatée
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
    
    @classmethod
    def is_valid_email(cls, email: str) -> bool:
        """
        Valide une adresse email avec regex compilée
        
        Args:
            email: Adresse email à valider
            
        Returns:
            bool: True si valide
        """
        return bool(cls._email_regex.match(email))
    
    @staticmethod
    def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
        """
        Masque des données sensibles
        
        Args:
            data: Données à masquer
            visible_chars: Nombre de caractères visibles
            
        Returns:
            str: Données masquées
        """
        if len(data) <= visible_chars:
            return "*" * len(data)
        
        return data[:visible_chars] + "*" * (len(data) - visible_chars)
    
    @staticmethod
    def create_secure_temp_file(content: str, prefix: str = "messagercrypt_") -> str:
        """
        Crée un fichier temporaire sécurisé
        
        Args:
            content: Contenu du fichier
            prefix: Préfixe du nom de fichier
            
        Returns:
            str: Chemin du fichier temporaire
        """
        import tempfile
        import os
        
        # Création d'un fichier temporaire sécurisé
        with tempfile.NamedTemporaryFile(mode='w', prefix=prefix, delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        # Définition des permissions restrictives
        os.chmod(temp_path, 0o600)
        
        return temp_path
    
    @staticmethod
    def cleanup_temp_files(directory: str = None) -> int:
        """
        Nettoie les fichiers temporaires
        
        Args:
            directory: Répertoire à nettoyer (optionnel)
            
        Returns:
            int: Nombre de fichiers nettoyés
        """
        try:
            import tempfile
            import glob
            
            if directory is None:
                directory = tempfile.gettempdir()
            
            pattern = os.path.join(directory, "messagercrypt_*")
            temp_files = glob.glob(pattern)
            
            cleaned_count = 0
            for file_path in temp_files:
                try:
                    os.unlink(file_path)
                    cleaned_count += 1
                except OSError:
                    pass
            
            return cleaned_count
            
        except Exception:
            return 0
