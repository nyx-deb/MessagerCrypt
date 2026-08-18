# Changelog

Tous les changements notables du projet sont documentés ici.

## [Non publié] - 2026-08-19

### Ajouté

- Inscription distante : le client s'inscrit désormais auprès du serveur
  (message `register` avec nom d'utilisateur, mot de passe et clé publique).
  La clé privée reste chiffrée localement, le serveur ne stocke que la clé publique
  et le hachage Argon2 du mot de passe (`KeyManager.register_user`).
- Distribution des clés publiques : nouveau message `get_public_key`. Lors d'un envoi,
  si le destinataire est inconnu localement, le client récupère sa clé auprès du
  serveur puis la met en cache (`KeyManager.cache_public_key`).
- Le formulaire d'inscription demande désormais l'adresse IP et le port du serveur,
  comme le formulaire de connexion.
- `KeyManager.verify_user` : vérification d'identifiants sans clé privée locale (usage serveur).

### Modifié

- Le serveur utilise `data/server_keys.json` au lieu de `data/user_keys.json` :
  serveur et client sur une même machine ne s'écrasent plus mutuellement les clés.
- `_handle_authentication` (serveur) utilise `verify_user` au lieu de `load_user_keys`.
- Protection anti-détournement : la ré-enregistrement d'un nom existant sur le serveur
  nécessite le mot de passe d'origine (permet la rotation de clé légitime).

## [Non publié] - 2026-08-18

### Corrigé

- `src/storage/database.py` : le sel de chiffrement est désormais stocké dans le BLOB
  (`sel + nonce + ciphertext`) lors de la création d'un utilisateur. Auparavant, `get_user()`
  régénérait un sel aléatoire à la lecture, rendant tout déchiffrement impossible.
- `src/storage/database.py` : correction des requêtes SQL utilisant la colonne `message`
  inexistante (désormais `encrypted_message`) dans `get_user_messages()`,
  `get_received_messages()` et `search_messages()`. La recherche s'effectue sur
  `message_hash`, le contenu chiffré n'étant pas cherchable par conception.
- `src/ui/ascii.py` : ajout des méthodes `show_error()`, `show_warning()` et
  `show_success()` à `ASCIIArt`, appelées par le client mais absentes de la classe.
- `src/server.py` : arrêt du serveur fiable. `stop()` itère désormais sur une copie des
  clients (le dict était muté par les threads pendant l'itération, provoquant une
  `RuntimeError`) et effectue un `shutdown()` avant `close()` pour réveiller le thread
  bloqué dans `accept()`. Auparavant, le port d'écoute restait occupé après l'arrêt.
- `src/client.py` : `disconnect()` remet `self.socket` à `None` ; suppression de
  l'import dupliqué de `ASCIIArt`.

### Tests

- `tests/test_crypto.py` : `keys_file` assigné en `Path` (une chaîne cassait
  `_save_user_keys`).
- `tests/test_database.py` : `test_session_management` utilisait une date d'expiration
  dans le passé (2009).
- `tests/test_network.py` et `tests/test_integration.py` : simulation de la réponse
  serveur pour l'authentification, mock de `create_message_packet` (les clés factices
  ne sont pas du PEM valide), patch du `key_manager` du serveur dans les tests
  d'intégration, attente de synchronisation pour le test multi-clients.
- Suite complète : **63/63 tests passent** (contre 49/63 à la reprise du projet).

### Infrastructure

- Ajout de `.venv/` au `.gitignore`.
