import pandas as pd
import numpy as np
from datetime import datetime

def convert_excel_to_sql(excel_file, output_file):
    try:
        # Baca file Excel
        df = pd.read_excel(excel_file)
        
        # Rename kolom sesuai dengan yang diharapkan
        df = df.rename(columns={
            'Merk HP': 'merk_hp',
            'Tipe HP': 'tipe_hp',
            'RAM (GB)': 'ram',
            'Penyimpanan (GB)': 'penyimpanan',
            'Tahun Keluaran': 'tahun',
            'Nilai Gadai': 'nilai_gadai',
            'Tanggal Gadai': 'tanggal_transaksi'
        })
        
        # Validasi data
        df['ram'] = pd.to_numeric(df['ram'], errors='coerce')
        df['penyimpanan'] = pd.to_numeric(df['penyimpanan'], errors='coerce')
        df['tahun'] = pd.to_numeric(df['tahun'], errors='coerce')
        df['nilai_gadai'] = pd.to_numeric(df['nilai_gadai'], errors='coerce')
        
        # Hapus baris dengan nilai NaN
        df = df.dropna()
        
        # Buat SQL statements
        sql_statements = []
        sql_statements.append("-- Generated SQL from Excel data")
        sql_statements.append("-- Generated on: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        sql_statements.append("\n-- Hapus data lama jika ada")
        sql_statements.append("DELETE FROM data_historis_hp;")
        sql_statements.append("\n-- Insert data baru")
        
        # Generate INSERT statements
        for idx, row in df.iterrows():
            sql = f"INSERT INTO data_historis_hp (merk_hp, tipe_hp, ram, penyimpanan, tahun_keluaran, nilai_gadai, tanggal_transaksi) VALUES "
            sql += f"('{row['merk_hp']}', '{row['tipe_hp']}', {int(row['ram'])}, {int(row['penyimpanan'])}, "
            sql += f"{int(row['tahun'])}, {float(row['nilai_gadai'])}, '{row['tanggal_transaksi']}');"
            sql_statements.append(sql)
        
        # Tulis ke file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sql_statements))
        
        print(f"Berhasil mengkonversi {len(df)} data ke {output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Contoh penggunaan
    excel_file = "Data_Historis_Pegadaian.xlsx"  # Nama file Excel yang benar
    output_file = "data_historis.sql"
    convert_excel_to_sql(excel_file, output_file) 