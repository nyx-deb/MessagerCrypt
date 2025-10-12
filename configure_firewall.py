#!/usr/bin/env python3
"""
Script de configuration du firewall Windows pour MessagerCrypt
"""

import subprocess
import sys
import os

def run_as_admin():
    """Vérifie si le script est exécuté en tant qu'administrateur"""
    try:
        return os.getuid() == 0
    except AttributeError:
        # Windows
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

def configure_firewall_windows():
    """Configure le firewall Windows pour MessagerCrypt"""
    print("🔥 CONFIGURATION DU FIREWALL WINDOWS")
    print("=" * 50)
    
    if not run_as_admin():
        print("⚠️  Ce script doit être exécuté en tant qu'administrateur")
        print("   Clic droit sur le terminal > 'Exécuter en tant qu'administrateur'")
        return False
    
    try:
        # Règle entrante pour le port 8888
        print("📥 Ajout de la règle entrante...")
        result_inbound = subprocess.run([
            "netsh", "advfirewall", "firewall", "add", "rule",
            "name=MessagerCrypt Inbound",
            "dir=in",
            "action=allow",
            "protocol=TCP",
            "localport=8888",
            "description=MessagerCrypt Server Port"
        ], capture_output=True, text=True, timeout=30)
        
        if result_inbound.returncode == 0:
            print("✅ Règle entrante ajoutée avec succès")
        else:
            print(f"⚠️  Règle entrante: {result_inbound.stderr}")
        
        # Règle sortante pour le port 8888
        print("📤 Ajout de la règle sortante...")
        result_outbound = subprocess.run([
            "netsh", "advfirewall", "firewall", "add", "rule",
            "name=MessagerCrypt Outbound",
            "dir=out",
            "action=allow",
            "protocol=TCP",
            "localport=8888",
            "description=MessagerCrypt Client Port"
        ], capture_output=True, text=True, timeout=30)
        
        if result_outbound.returncode == 0:
            print("✅ Règle sortante ajoutée avec succès")
        else:
            print(f"⚠️  Règle sortante: {result_outbound.stderr}")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Timeout lors de la configuration du firewall")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de la configuration du firewall: {e}")
        return False

def check_firewall_rules():
    """Vérifie les règles du firewall"""
    print("\n🔍 VÉRIFICATION DES RÈGLES FIREWALL")
    print("=" * 40)
    
    try:
        result = subprocess.run([
            "netsh", "advfirewall", "firewall", "show", "rule", "name=MessagerCrypt"
        ], capture_output=True, text=True, timeout=10)
        
        if "MessagerCrypt" in result.stdout:
            print("✅ Règles MessagerCrypt trouvées dans le firewall")
            print(result.stdout)
        else:
            print("❌ Aucune règle MessagerCrypt trouvée")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")

def show_manual_instructions():
    """Affiche les instructions manuelles"""
    print("\n📋 INSTRUCTIONS MANUELLES")
    print("=" * 30)
    print("Si la configuration automatique échoue :")
    print()
    print("1. Ouvrir le Panneau de configuration Windows")
    print("2. Aller dans 'Système et sécurité' > 'Pare-feu Windows Defender'")
    print("3. Cliquer sur 'Paramètres avancés'")
    print("4. Dans 'Règles de trafic entrant', cliquer 'Nouvelle règle...'")
    print("5. Sélectionner 'Port' > 'TCP' > 'Ports locaux spécifiques' > '8888'")
    print("6. Sélectionner 'Autoriser la connexion'")
    print("7. Appliquer à tous les profils")
    print("8. Nommer la règle 'MessagerCrypt'")
    print()
    print("Répéter pour les règles de trafic sortant.")

def main():
    """Fonction principale"""
    print("🚀 CONFIGURATION FIREWALL MESSAGERCRYPT")
    print("=" * 60)
    
    if sys.platform != "win32":
        print("ℹ️  Ce script est conçu pour Windows")
        print("   Sur Linux/Mac, utilisez iptables ou ufw")
        return
    
    # Configuration automatique
    if configure_firewall_windows():
        print("\n✅ Configuration du firewall terminée")
    else:
        print("\n❌ Échec de la configuration automatique")
        show_manual_instructions()
    
    # Vérification
    check_firewall_rules()
    
    print(f"\n💡 PROCHAINES ÉTAPES :")
    print("=" * 20)
    print("1. Démarrer le serveur : python src/main.py")
    print("2. Sur l'autre PC, se connecter à votre IP:192.168.1.101:8888")
    print("3. Tester la communication entre les deux PC")

if __name__ == "__main__":
    main()
