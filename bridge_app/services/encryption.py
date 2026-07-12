# ==================================================================
# File: bridge_app/services/encryption.py
# Description: Service for securely encrypting and decrypting sensitive DB fields.
#
# Copyright (C) 2026 Arean Narrayan - SynoraStudio
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ==================================================================

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from dotenv import load_dotenv

def get_encryption_key():
    load_dotenv()
    key_b64 = os.environ.get('ENCRYPTION_KEY')
    if not key_b64:
        return None
    try:
        return base64.b64decode(key_b64.encode('utf-8'))
    except Exception:
        return None

def encrypt_token(plain_text: str) -> str:
    if not plain_text:
        return plain_text
        
    key = get_encryption_key()
    if not key:
        # If no key is configured, fallback to plaintext. 
        # (The migration script ensures a key exists in production).
        return plain_text
    
    try:
        # AESGCM requires a unique 12-byte nonce for every encryption
        nonce = os.urandom(12)
        aesgcm = AESGCM(key)
        
        # Encrypt the plain text
        cipher_text = aesgcm.encrypt(nonce, plain_text.encode('utf-8'), None)
        
        # Concatenate nonce and cipher_text, then base64 encode for safe DB storage
        combined = nonce + cipher_text
        return base64.b64encode(combined).decode('utf-8')
    except Exception as e:
        import logging
        logging.error(f"Failed to encrypt token: {e}")
        return plain_text

def decrypt_token(encrypted_b64: str) -> str:
    if not encrypted_b64:
        return encrypted_b64
        
    key = get_encryption_key()
    if not key:
        return encrypted_b64
        
    try:
        combined = base64.b64decode(encrypted_b64.encode('utf-8'))
        
        # AES-GCM combined payload must be at least 12 bytes (nonce) + 16 bytes (tag) = 28 bytes
        if len(combined) < 28:
            return encrypted_b64 # Likely a legacy plaintext token
            
        nonce = combined[:12]
        cipher_text = combined[12:]
        
        aesgcm = AESGCM(key)
        plain_text_bytes = aesgcm.decrypt(nonce, cipher_text, None)
        return plain_text_bytes.decode('utf-8')
    except (InvalidTag, ValueError, TypeError, Exception):
        # If decryption fails (e.g. InvalidTag), it means the string is either corrupted, 
        # encrypted with a different key, or it's just a legacy plaintext token.
        return encrypted_b64
