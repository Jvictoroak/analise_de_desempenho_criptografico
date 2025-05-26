import time
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding as asymmetric_padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as symmetric_padding
from cryptography.hazmat.backends import default_backend
import os
from openpyxl import Workbook
from openpyxl.styles import Font

# Increased text size for measurable operations
texto_original = "RSA eh um algoritmo que leva o nome de 3 professores do MIT: Rivest, Shamir e Adleman " * 100
texto_bytes = texto_original.encode('utf-8')

def medir_tempo(funcao, *args):
    tempos = []
    for _ in range(3):
        inicio = time.perf_counter()  # High precision timer
        funcao(*args)
        fim = time.perf_counter()
        tempos.append(fim - inicio)
    return tempos

def dividir_em_blocos(dados, tamanho_bloco):
    return [dados[i:i+tamanho_bloco] for i in range(0, len(dados), tamanho_bloco)]

def testar_rsa(tamanho_chave):
    def funcao():
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=tamanho_chave,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        
        max_tamanho = (tamanho_chave // 8) - 66
        blocos = dividir_em_blocos(texto_bytes, max_tamanho) if len(texto_bytes) > max_tamanho else [texto_bytes]
        
        ciphertexts = []
        for bloco in blocos:
            ciphertext = public_key.encrypt(
                bloco,
                asymmetric_padding.OAEP(
                    mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            ciphertexts.append(ciphertext)
        
        for ciphertext in ciphertexts:
            private_key.decrypt(
                ciphertext,
                asymmetric_padding.OAEP(
                    mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
    return medir_tempo(funcao)

def testar_aes(tamanho_chave):
    def funcao():
        key = os.urandom(tamanho_chave // 8)
        iv = os.urandom(16)
        
        # Use larger data payload for measurable results
        dados = texto_bytes * 10  
        
        padder = symmetric_padding.PKCS7(128).padder()
        padded_data = padder.update(dados) + padder.finalize()
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = symmetric_padding.PKCS7(128).unpadder()
        unpadder.update(decrypted_data) + unpadder.finalize()
    
    return medir_tempo(funcao)

print("Iniciando testes...")
resultados = {
    "RSA 1024": testar_rsa(1024),
    "RSA 2048": testar_rsa(2048),
    "RSA 4096": testar_rsa(4096),
    "RSA 8192": testar_rsa(8192),
    "AES 128": testar_aes(128),
    "AES 256": testar_aes(256),
}

# Create Excel workbook
wb = Workbook()
ws = wb.active
ws.title = "Resultados Criptográficos"

# Headers
headers = ['Algoritmo', 'Execução 1 (s)', 'Execução 2 (s)', 'Execução 3 (s)', 'Média (s)']
for col_num, header in enumerate(headers, 1):
    ws.cell(row=1, column=col_num, value=header).font = Font(bold=True)

# Data
for row_num, (algoritmo, tempos) in enumerate(resultados.items(), 2):
    media = sum(tempos) / len(tempos)
    ws.cell(row=row_num, column=1, value=algoritmo)
    for col_num, tempo in enumerate(tempos, 2):
        ws.cell(row=row_num, column=col_num, value=tempo)
    ws.cell(row=row_num, column=5, value=media)

# Format numbers
for row in ws.iter_rows(min_row=2, max_col=5, max_row=len(resultados)+1):
    for cell in row[1:]:
        cell.number_format = '0.000000'

# Adjust column widths
for col in ws.columns:
    max_length = max(len(str(cell.value)) for cell in col)
    adjusted_width = (max_length + 2) * 1.2
    ws.column_dimensions[col[0].column_letter].width = adjusted_width

# Save file
excel_filename = "resultados_criptograficos.xlsx"
wb.save(excel_filename)

print("\nResultados dos testes (segundos):")
for algoritmo, tempos in resultados.items():
    print(f"{algoritmo}: {[f'{t:.6f}' for t in tempos]} (Média: {sum(tempos)/len(tempos):.6f}s)")

print(f"\nPlanilha '{excel_filename}' gerada com sucesso!")