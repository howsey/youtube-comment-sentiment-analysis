# Technical Workflow - YouTube Comment Scraper

## Arsitektur Sistem

```
[User Input] --> [URL Parser] --> [Comment Scraper] --> [AI Sentiment] --> [Export]
                                          │
                                          ▼
                                    [Reply Scraper]
```

## Workflow Detail

### 1. Inisialisasi (`main` + `parse_args`)

- `argparse` mendefinisikan CLI arguments:
  - `url` (posisi), `-n/--max`, `-s/--sort`, `--min-likes`, `--replies`, `--csv`, `--json`, `-o/--output`, `-v/--verbose`
- Jika URL tidak diberikan via CLI → masuk `interactive_mode()`
- `interactive_mode()` menampilkan header dan menerima input dari user secara interaktif
- Validasi input numerik (max komentar > 0, min likes >= 0)

### 2. URL Parsing (`extract_video_id`)

Fungsi mengekstrak video ID dari berbagai format URL YouTube:

| Format URL | Parsing Method |
|------------|----------------|
| `youtube.com/watch?v=xxx` | Query parameter `v=` |
| `youtu.be/xxx` | Path segment |
| `youtube.com/shorts/xxx` | Path segment `/shorts/` |
| `youtube.com/embed/xxx` | Path segment `/embed/` |

Menggunakan `urllib.parse.urlparse` untuk dekomposisi URL.

### 3. Comment Scraping (`scrape_youtube`)

- Library: `yt_comment_dl.YoutubeCommentDownloader`
- Retry mechanism: MAX_RETRIES = 3, RETRY_DELAY = 2 detik
- Method: `downloader.get_comments(video_id, sort_by=mode)`
  - `sort_by=0`: Popular comments
  - `sort_by=1`: Recent comments
- Deduplikasi berdasarkan comment ID (`seen_ids` set)
- Filter: skip komentar dengan `votes < min_likes`
- Text dibersihkan dari whitespace berlebih via `clean_text()`
- Iterasi dihentikan saat mencapai `max_comments`

### 4. Reply Scraping (`scrape_replies`)

- Dipanggil saat `--replies` aktif
- Method: `downloader.get_replies(comment_id)`
- Setiap reply memiliki field tambahan `parent_id` yang merujuk ke komentar induk
- Exception ditangkap dan di-log sebagai debug

### 5. Sentiment Analysis (`load_sentiment_model` + `add_sentiment_labels`)

#### Model Loading
- Model: `sahri/indonesiasentiment` (Hugging Face Transformers)
- Pipeline: `sentiment-analysis`
- Device detection:
  - CUDA available → `device=0` (GPU)
  - Tidak available → `device=-1` (CPU)

#### Inference
- Batch size: 32 komentar per iterasi
- Truncation: aktif, max length 256 tokens
- Progress bar ditampilkan ke stdout
- Output per komentar:
  - `label`: Positif/Negatif/Netral
  - `score`: Confidence score (0-1)

#### Label Normalization (`normalize_label`)
Mapping label model ke format standar:

| Model Output | Normalized Label |
|--------------|------------------|
| positive / positif | positive |
| negative / negatif | negative |
| neutral / netral | neutral |

### 6. Sentiment Summary (`print_sentiment_summary`)

- Menghitung jumlah dan persentase positive, negative, neutral
- Menghitung rata-rata confidence score
- Menampilkan bar chart visual ke stdout

### 7. Export

#### CSV (`save_csv`)
- Directory: `output/`
- Encoding: UTF-8 with BOM (`utf-8-sig`)
- Format: CSV dengan DictWriter

#### JSON (`save_json`)
- Directory: `output/`
- Encoding: UTF-8
- Format: JSON dengan indentasi (2 spasi) dan `ensure_ascii=False`

#### Filename Generation (`generate_filename`)
- Format: `youtube_comments_YYYYMMDD_HHMMSS.{ext}`
- Atau custom filename via `-o/--output`

## Flowchart

```
┌─────────────────────┐
│     User Input      │
│  - URL YouTube      │
│  - Max comments     │
│  - Sort mode        │
│  - Min likes        │
│  - Include replies  │
│  - Export format    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Extract Video ID   │
│  - watch?v=         │
│  - youtu.be/        │
│  - shorts/          │
│  - embed/           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Scrape Comments    │
│  - yt_comment_dl    │
│  - Loop until max   │
│  - Dedup by ID      │
│  - Filter min likes │
│  - Clean text       │
│  - Retry on error   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Scrape Replies?    │
│  - if --replies     │
│  - get_replies()    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Load AI Model      │
│  - Check CUDA       │
│  - Init pipeline    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Batch Sentiment    │
│  - 32 per batch     │
│  - truncation=True  │
│  - normalize label  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Print Summary      │
│  - Bar chart        │
│  - Statistics       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Export to File     │
│  - CSV (UTF-8 BOM)  │
│  - JSON (optional)  │
│  - output/ dir      │
└─────────────────────┘
```

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `torch` | any | GPU detection, model backend |
| `transformers` | any | Hugging Face sentiment pipeline |
| `yt_comment_dl` | any | YouTube comment extraction |
| `csv` | stdlib | CSV export |
| `json` | stdlib | JSON export |
| `urllib` | stdlib | URL parsing |
| `argparse` | stdlib | CLI argument parsing |
| `logging` | stdlib | Log management |
| `datetime` | stdlib | Timestamp generation |
| `re` | stdlib | Text cleaning (regex) |
| `time` | stdlib | Retry delay |

## Error Handling

- **Invalid URL**: `extract_video_id` returns `None`, scraping stopped
- **Empty comments**: Warning ditampilkan, proses berhenti
- **KeyboardInterrupt**: Scraping dihentikan graceful
- **Network error**: Exception ditangkap, retry hingga MAX_RETRIES (3x)
- **Deduplikasi**: Comment ID yang sudah di-skip jika sudah ada di `seen_ids`

## CLI Arguments

```
usage: scraper.py [-h] [-n MAX] [-s {popular,new}] [--min-likes MIN_LIKES]
                  [--replies] [--csv] [--json] [-o OUTPUT] [-v] [url]

YouTube Comment Scraper + AI Sentiment Analysis

positional arguments:
  url                   URL video YouTube

options:
  -h, --help            show this help message and exit
  -n, --max             Max komentar (default: 100)
  -s, --sort            Sort mode (default: new)
  --min-likes           Min likes filter (default: 0)
  --replies             Sertakan replies
  --csv                 Export ke CSV (default: True)
  --json                Export ke JSON
  -o, --output          Custom output filename
  -v, --verbose         Verbose output
```

## Environment Variables

```python
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"  # Prevent OpenMP error
os.environ["OMP_NUM_THREADS"] = "1"           # Single thread untuk stabilitas
```

## Output Structure

```
output/
├── youtube_comments_20260919_103000.csv
├── youtube_comments_20260919_103000.json   # jika --json
└── ...
scraper.log                                 # log file
```
