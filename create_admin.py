import getpass
from werkzeug.security import generate_password_hash
from db_manager import create_user, init_db, get_user_by_username

def main():
    print("=== Creador de Usuarios Administradores ===")
    #Confirmar que la base de datos existe
    init_db()

    while True:
        username = input("Ingrese el nombre de usuario (o 'salir' para terminar): ").strip()
        if username.lower() == 'salir':
            break
        if not username:
            print("El usuario no puede estar vacío.")
            continue
            
        #Verificar si el usuario ya existe
        if get_user_by_username(username):
            print(f"Error: El usuario '{username}' ya existe.")
            continue

        #getpass oculta la contraseña mientras se escribe
        password = getpass.getpass("Ingrese la contraseña: ")
        confirm_password = getpass.getpass("Confirme la contraseña: ")

        if password != confirm_password:
            print("Error: Las contraseñas no coinciden.")
            continue

        # Generar hash y guardar
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
        if create_user(username, password_hash):
            print(f"¡ÉXITO! Usuario '{username}' creado correctamente.")
            break
        else:
            print("Error al guardar en la base de datos.")

if __name__ == "__main__":
    main()