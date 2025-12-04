from supabase import create_client
import os

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

# Lee todos los usuarios
resultado = supabase.table('usuarios').select('*').execute()
for u in resultado.data:
    print("email:", u['email'], "rol:", u['rol'], "hash:", u['password_hash'][:20] + "...")