from cryptography.fernet import Fernet

key = b"wh-eYBC4sgtNtaVqVr4VUA87e5ETPoBHHXroTv2RtCA="

def encrypt_password(password):
    fernet = Fernet(key)
    encrypted_password = fernet.encrypt(password.encode())
    return encrypted_password.decode()

def decrypt_password(encrypted_password):
    try:
        fernet = Fernet(key)
        encrypted_password_bytes = encrypted_password.encode()
        decrypted_password = fernet.decrypt(encrypted_password_bytes).decode()
        return {
            "success":True,
            "decrypted_password":decrypted_password
        }
    except:
        return {
            "success":False
        }