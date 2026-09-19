# Technical Workflow - YouTube Comment Scraper

## Arsitektur Sistem

```
[User Input] --> [URL Parser] --> [Comment Scraper] --> [AI Sentiment] --> [CSV Export]
```

## Workflow Detail

### 1. Inisialisasi (`main`)

- Menampilkan header aplikasi
- Menerima input dari user:
  - URL YouTube
  - Jumlah maksimal komentar
  - Mode sorting (terbaru/terpopuler)
- Validasi input numerik

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

- Library: `yt_comment_downloader.YoutubeCommentDownloader`
- Method: `get_comments(video_id, sort_by=mode)`
  - `sort_by=0`: Popular comments
  - `sort_by=1`: Recent comments
- Setiap komentar di-extract:
  - `text`: Isi komentar
  - `author`: Username
  - `votes`: Jumlah like
  - `time`: Timestamp
  - `cid`: Comment ID
- Text dibersihkan dari whitespace berlebih via `clean_text()`
- Iterasi dihentikan saat mencapai `max_comments`

### 4. Sentiment Analysis (`load_sentiment_model` + `add_sentiment_labels`)

#### Model Loading
- Model: `sahri/indonesiasentiment` (Hugging Face Transformers)
- Pipeline: `sentiment-analysis`
- Device detection:
  - CUDA available → `device=0` (GPU)
  - Tidak available → `device=-1` (CPU)

#### Inference
- Batch size: 32 komentar per iterasi
- Truncation: aktif, max length 256 tokens
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

### 5. Export (`save_csv`)

- Directory: `output/`
- Encoding: UTF-8 with BOM (`utf-8-sig`)
- Format: CSV dengan DictWriter
- Kolom diambil dari keys dictionary pertama

## Flowchart

```
┌─────────────────────┐
│     User Input      │
│  - URL YouTube      │
│  - Max comments     │
│  - Sort mode        │
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
│  - Clean text       │
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
│  Export to CSV      │
│  - UTF-8 BOM        │
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
| `urllib` | stdlib | URL parsing |

## Error Handling

- **Invalid URL**: `extract_video_id` returns `None`, scraping stopped
- **Empty comments**: Warning ditampilkan, proses berhenti
- **KeyboardInterrupt**: Scraping dihentikan graceful
- **Network error**: Exception ditangkap dan ditampilkan

## Environment Variables

```python
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"  # Prevent OpenMP error
os.environ["OMP_NUM_THREADS"] = "1"           # Single thread untuk stabilitas
```
