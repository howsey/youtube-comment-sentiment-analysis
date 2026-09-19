# YouTube Comment Scraper + AI Sentiment Analysis

Scraper komentar YouTube yang dilengkapi dengan analisis sentimen menggunakan AI. Tools ini mengambil komentar dari video YouTube dan menganalisis apakah komentar tersebut bersifat positif, negatif, atau netral.

## Fitur

- Mengambil komentar langsung tanpa membuka browser (tanpa Selenium)
- Mendukung URL standar YouTube, Shorts, dan Embed
- Scraping replies/komentar balasan (opsional)
- Filter minimum likes
- Analisis sentimen otomatis menggunakan model AI (Bahasa Indonesia)
- Deteksi GPU/CUDA untuk pemrosesan yang lebih cepat
- Export ke CSV dan/atau JSON
- Output filename timestamped otomatis atau custom
- Retry mechanism untuk error handling
- Logging ke file `scraper.log`
- Sentiment summary dengan visualisasi bar chart

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

### Mode Interaktif

```bash
python scraper.py
```

User akan diminta input secara interaktif:
- URL YouTube
- Jumlah maksimal komentar (default: 100)
- Sort mode (1 = Terbaru, 2 = Terpopuler)
- Minimum likes
- Sertakan replies (y/n)
- Export JSON (y/n)

### Mode CLI

```bash
python scraper.py <URL> [options]
```

#### Opsi

| Flag | Keterangan | Default |
|------|------------|---------|
| `url` | URL video YouTube (posisi argumen) | - |
| `-n, --max` | Jumlah maksimal komentar | 100 |
| `-s, --sort` | Sort mode: `new` atau `popular` | new |
| `--min-likes` | Filter minimum likes | 0 |
| `--replies` | Sertakan replies | false |
| `--csv` | Export ke CSV | true |
| `--json` | Export ke JSON | false |
| `-o, --output` | Custom output filename (tanpa ekstensi) | auto timestamp |
| `-v, --verbose` | Debug logging | false |

#### Contoh

```bash
# Ambil 200 komentar terbaru, export CSV + JSON
python scraper.py "https://youtube.com/watch?v=xxx" -n 200 --json

# Ambil komentar terpopuler dengan min 10 likes dan replies
python scraper.py "https://youtube.com/watch?v=xxx" -s popular --min-likes 10 --replies

# Custom output filename
python scraper.py "https://youtube.com/watch?v=xxx" -o hasil_analisis
```

## Format Output

| Kolom | Keterangan |
|-------|------------|
| platform | Sumber komentar (youtube) |
| comment_id | ID unik komentar |
| parent_id | ID komentar induk (hanya untuk replies) |
| author | Nama pembuat komentar |
| comment | Isi komentar |
| likes | Jumlah like |
| timestamp | Waktu komentar dibuat |
| video_url | URL video asli |
| scraped_at | Waktu data diambil (ISO format) |
| label | Hasil analisis sentimen (positive/negative/neutral) |
| confidence | Skor kepercayaan model (0-1) |

## Contoh Output

```
platform,comment_id,author,comment,likes,timestamp,video_url,scraped_at,label,confidence
youtube,abc123,John,Video ini sangat bagus!,5,2 hours ago,https://...,2026-09-19T10:30:00,positive,0.9523
```

## Sentiment Summary

Setelah proses selesai, tool menampilkan ringkasan sentimen dalam format visual:

```
=======================================================
                 SENTIMENT SUMMARY
=======================================================
Positive : ██████████░░░░░░░░░░░░░░░░░░░░  33% (33)
Negative : ████████████████░░░░░░░░░░░░░░  50% (50)
Neutral  : ████░░░░░░░░░░░░░░░░░░░░░░░░░░  16% (16)
=======================================================
Total    : 100 komentar
Avg Conf : 0.8742
=======================================================
```

## Catatan

- Model AI yang digunakan: `sahri/indonesiasentiment` (khusus Bahasa Indonesia)
- Proses sentiment analysis akan lebih cepat jika menggunakan GPU
- Komentar kosong akan otomatis di-skip
- Duplikat komentar akan di-skip berdasarkan comment ID
- Error handling dengan retry mechanism (maksimal 3 percobaan)
- Log disimpan di `scraper.log`
