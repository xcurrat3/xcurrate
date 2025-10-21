# --- soal Bahasa Inggris (arti kata) ---
soal_inggris = [
    ("Apa arti kata 'Apple'?", "Apel,Pisang,Jeruk,Anggur", "Apel", "Inggris"),
    ("Apa arti kata 'Dog'?", "Kucing,Anjing,Kuda,Bebek", "Anjing", "Inggris"),
    ("Apa arti kata 'House'?", "Rumah,Sekolah,Toko,Kantor", "Rumah", "Inggris"),
]

# --- soal Bahasa Jepang (arti kata) ---
soal_jepang = [
    ("Apa arti kata 'Neko'?", "Anjing,Kucing,Burung,Ikan", "Kucing", "Jepang"),
    ("Apa arti kata 'Inu'?", "Kucing,Kuda,Anjing,Bebek", "Anjing", "Jepang"),
    ("Apa arti kata 'Kuruma'?", "Sepeda,Kereta,Mobil,Pesawat", "Mobil", "Jepang"),
]

# ...dan seterusnya...

# Masukkan semua soal ke database
cursor.executemany("INSERT INTO soal (pertanyaan, pilihan, jawaban, bahasa) VALUES (?, ?, ?, ?)", soal_inggris)
cursor.executemany("INSERT INTO soal (pertanyaan, pilihan, jawaban, bahasa) VALUES (?, ?, ?, ?)", soal_jepang)