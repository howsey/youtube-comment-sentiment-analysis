# YouTube Comment Scraper + AI Sentiment Analysis

Scraper komentar YouTube yang dilengkapi dengan analisis sentimen menggunakan AI. Tools ini mengambil komentar dari video YouTube dan menganalisis apakah komentar tersebut bersifat positif, negatif, atau netral.

## Fitur

- Mengambil komentar langsung tanpa membuka browser
- Mendukung URL standar YouTube, Shorts, dan Embed
- Analisis sentimen otomatis menggunakan model AI (Bahasa Indonesia)
- Deteksi GPU/CUDA untuk pemrosesan yang lebih cepat
- Hasil disimpan dalam format CSV

## Persiapan

### Kebutuhan

- Python 3.8 atau lebih baru
- Koneksi internet

### Instalasi

1. Clone atau download project ini

2. Install dependency:
```bash
pip install torch transformers yt_comment_dl
```

## Cara Penggunaan

1. Jalankan script:
```bash
python scraper.py
```

2. Masukkan URL video YouTube saat diminta

3. Tentukan jumlah komentar yang ingin diambil (default: 100)

4. Pilih metode sorting:
   - **1** = Terbaru
   - **2** = Terpopuler

5. Tunggu proses selesai

6. Hasil tersimpan di folder `output/youtube_comments_labeled.csv`

## Format Output

| Kolom | Keterangan |
|-------|------------|
| platform | Sumber komentar (youtube) |
| comment_id | ID unik komentar |
| author | Nama pembuat komentar |
| comment | Isi komentar |
| likes | Jumlah like |
| timestamp | Waktu komentar dibuat |
| video_url | URL video asli |
| scraped_at | Waktu data diambil |
| label | Hasil analisis sentimen (positive/negative/neutral) |
| confidence | Skor kepercayaan model (0-1) |

## Contoh Output

```
platform,comment_id,author,comment,likes,timestamp,video_url,scraped_at,label,confidence
youtube,abc123,John,Video ini sangat bagus!,5,2 hours ago,https://...,2026-09-19,positive,0.9523
```

## Catatan

- Model AI yang digunakan: `sahri/indonesiasentiment` (khusus Bahasa Indonesia)
- Proses sentiment analysis akan lebih cepat jika menggunakan GPU
- Komentar kosong akan otomatis di-skip
