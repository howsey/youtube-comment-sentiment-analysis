import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

import argparse
import csv
import json
import logging
import re
import time
from datetime import datetime
from urllib.parse import urlparse

import torch
from transformers import pipeline
from yt_comment_dl import YoutubeCommentDownloader


OUTPUT_DIR = "output"
MODEL_NAME = "sahri/indonesiasentiment"
MAX_RETRIES = 3
RETRY_DELAY = 2


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(
            "scraper.log",
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def clean_text(text):
    if not text:
        return ""

    return re.sub(r"\s+", " ", str(text)).strip()


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def save_csv(data, filename):
    ensure_output_dir()

    path = os.path.join(
        OUTPUT_DIR,
        filename
    )

    if not data:
        logger.warning("Tidak ada data untuk disimpan.")
        return path

    keys = list(data[0].keys())

    with open(
        path,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=keys
        )

        writer.writeheader()
        writer.writerows(data)

    logger.info(f"File CSV: {path}")
    logger.info(f"Total: {len(data)} komentar")

    return path


def save_json(data, filename):
    ensure_output_dir()

    path = os.path.join(
        OUTPUT_DIR,
        filename
    )

    if not data:
        logger.warning("Tidak ada data untuk disimpan.")
        return path

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )

    logger.info(f"File JSON: {path}")
    logger.info(f"Total: {len(data)} komentar")

    return path


def generate_filename(extension="csv"):
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )
    return f"youtube_comments_{timestamp}.{extension}"


def extract_video_id(url):
    parsed = urlparse(url)

    if "youtu.be" in parsed.netloc:
        return parsed.path.strip("/")

    if "youtube.com" in parsed.netloc:

        if parsed.path == "/watch":
            query = parsed.query

            for part in query.split("&"):
                if part.startswith("v="):
                    return part[2:]

        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/")[2]

        if parsed.path.startswith("/embed/"):
            return parsed.path.split("/")[2]

    return None


def load_sentiment_model():
    logger.info("Loading sentiment model...")

    if torch.cuda.is_available():

        device = 0

        logger.info(
            f"Device: "
            f"{torch.cuda.get_device_name(0)}"
        )

        logger.info("CUDA aktif.")

    else:

        device = -1

        logger.info("Device: CPU")
        logger.info("CUDA belum tersedia.")

    model = pipeline(
        "sentiment-analysis",
        model=MODEL_NAME,
        tokenizer=MODEL_NAME,
        device=device
    )

    logger.info("Model siap.")

    return model


def normalize_label(label):
    label = str(label).lower()

    if "positive" in label:
        return "positive"

    if "negative" in label:
        return "negative"

    if "neutral" in label:
        return "neutral"

    if "positif" in label:
        return "positive"

    if "negatif" in label:
        return "negative"

    if "netral" in label:
        return "neutral"

    return label


def print_sentiment_summary(data):
    total = len(data)

    if total == 0:
        return

    positive = sum(
        1 for d in data if d["label"] == "positive"
    )
    negative = sum(
        1 for d in data if d["label"] == "negative"
    )
    neutral = sum(
        1 for d in data if d["label"] == "neutral"
    )
    avg_conf = (
        sum(d["confidence"] for d in data) / total
    )

    pos_pct = positive * 100 // total
    neg_pct = negative * 100 // total
    neu_pct = neutral * 100 // total

    bar_len = 30

    pos_bar = (
        "█" * (pos_pct * bar_len // 100)
        + "░" * (bar_len - pos_pct * bar_len // 100)
    )
    neg_bar = (
        "█" * (neg_pct * bar_len // 100)
        + "░" * (bar_len - neg_pct * bar_len // 100)
    )
    neu_bar = (
        "█" * (neu_pct * bar_len // 100)
        + "░" * (bar_len - neu_pct * bar_len // 100)
    )

    print()
    print("=" * 55)
    print("                 SENTIMENT SUMMARY")
    print("=" * 55)
    print(
        f"Positive : {pos_bar}"
        f"  {pos_pct}% ({positive})"
    )
    print(
        f"Negative : {neg_bar}"
        f"  {neg_pct}% ({negative})"
    )
    print(
        f"Neutral  : {neu_bar}"
        f"  {neu_pct}% ({neutral})"
    )
    print("=" * 55)
    print(f"Total    : {total} komentar")
    print(f"Avg Conf : {avg_conf:.4f}")
    print("=" * 55)


def add_sentiment_labels(
    data,
    sentiment_model
):
    logger.info("Melakukan sentiment analysis...")

    comments = [
        item["comment"]
        for item in data
    ]

    results = []

    batch_size = 32
    total = len(comments)

    for start in range(
        0,
        total,
        batch_size
    ):

        batch = comments[
            start:start + batch_size
        ]

        predictions = sentiment_model(
            batch,
            truncation=True,
            max_length=256
        )

        results.extend(predictions)

        progress = min(
            start + batch_size,
            total
        )

        print(
            f"\r[AI] "
            f"{progress}/{total}",
            end=""
        )

    print()

    for item, prediction in zip(
        data,
        results
    ):

        item["label"] = normalize_label(
            prediction["label"]
        )

        item["confidence"] = round(
            float(prediction["score"]),
            4
        )

    return data


def scrape_replies(
    video_id,
    comment_id,
    downloader
):
    replies = []

    try:
        reply_generator = (
            downloader.get_replies(
                comment_id
            )
        )

        for reply in reply_generator:

            text = clean_text(
                getattr(reply, "text", "")
            )

            if not text:
                continue

            author = clean_text(
                getattr(reply, "author", "")
            )

            votes = getattr(
                reply,
                "votes",
                0
            )

            timestamp = clean_text(
                getattr(
                    reply,
                    "time",
                    ""
                )
            )

            reply_id = clean_text(
                getattr(
                    reply,
                    "cid",
                    ""
                )
            )

            replies.append({
                "platform": "youtube",
                "comment_id": reply_id,
                "parent_id": comment_id,
                "author": author,
                "comment": text,
                "likes": votes,
                "timestamp": timestamp,
                "video_url": f"https://youtube.com/watch?v={video_id}",
                "scraped_at": datetime.now().isoformat(
                    timespec="seconds"
                )
            })

    except Exception as e:
        logger.debug(
            f"Gagal ambil reply: {e}"
        )

    return replies


def scrape_youtube(
    url,
    max_comments,
    sort_mode,
    min_likes,
    include_replies
):
    logger.info("Direct comment scraper")
    logger.info("Tidak membuka browser.")

    video_id = extract_video_id(url)

    if not video_id:
        logger.error(
            "Video ID YouTube tidak ditemukan."
        )
        return []

    logger.info(f"Video ID: {video_id}")
    logger.info(f"Target: {max_comments} komentar")
    logger.info(f"Min likes: {min_likes}")
    logger.info(
        f"Include replies: {include_replies}"
    )
    logger.info("Mengambil komentar...")

    downloader = YoutubeCommentDownloader()

    comments = []
    seen_ids = set()
    retries = 0

    while retries < MAX_RETRIES:

        try:
            comment_generator = (
                downloader.get_comments(
                    video_id,
                    sort_by=sort_mode
                )
            )

            for item in comment_generator:

                if len(comments) >= max_comments:
                    break

                comment_id = clean_text(
                    getattr(item, "cid", "")
                )

                if comment_id in seen_ids:
                    continue

                seen_ids.add(comment_id)

                text = clean_text(
                    getattr(item, "text", "")
                )

                if not text:
                    continue

                votes = getattr(
                    item,
                    "votes",
                    0
                )

                if votes < min_likes:
                    continue

                author = clean_text(
                    getattr(item, "author", "")
                )

                timestamp = clean_text(
                    getattr(
                        item,
                        "time",
                        ""
                    )
                )

                comment_data = {
                    "platform": "youtube",
                    "comment_id": comment_id,
                    "author": author,
                    "comment": text,
                    "likes": votes,
                    "timestamp": timestamp,
                    "video_url": url,
                    "scraped_at": (
                        datetime.now().isoformat(
                            timespec="seconds"
                        )
                    )
                }

                comments.append(comment_data)

                if include_replies:

                    replies = scrape_replies(
                        video_id,
                        comment_id,
                        downloader
                    )

                    comments.extend(replies)

                print(
                    f"\r[YouTube] "
                    f"{len(comments)}/{max_comments}",
                    end=""
                )

            break

        except KeyboardInterrupt:

            logger.warning("Scraping dihentikan.")
            break

        except Exception as error:

            retries += 1

            if retries < MAX_RETRIES:
                logger.warning(
                    f"Error: {error}"
                )
                logger.info(
                    f"Retry {retries}/{MAX_RETRIES}"
                    f" dalam {RETRY_DELAY}s..."
                )
                time.sleep(RETRY_DELAY)
            else:
                logger.error(
                    f"Gagal setelah"
                    f" {MAX_RETRIES} percobaan:"
                    f" {error}"
                )

    print()

    return comments


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "YouTube Comment Scraper"
            " + AI Sentiment Analysis"
        )
    )

    parser.add_argument(
        "url",
        nargs="?",
        help="URL video YouTube"
    )

    parser.add_argument(
        "-n", "--max",
        type=int,
        default=100,
        help="Max komentar (default: 100)"
    )

    parser.add_argument(
        "-s", "--sort",
        choices=["popular", "new"],
        default="new",
        help="Sort mode (default: new)"
    )

    parser.add_argument(
        "--min-likes",
        type=int,
        default=0,
        help="Min likes filter (default: 0)"
    )

    parser.add_argument(
        "--replies",
        action="store_true",
        help="Sertakan replies"
    )

    parser.add_argument(
        "--csv",
        action="store_true",
        default=True,
        help="Export ke CSV (default: True)"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Export ke JSON"
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Custom output filename"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )

    return parser.parse_args()


def interactive_mode():
    print("=" * 55)
    print("YouTube Comment Scraper")
    print("Direct Scraping + AI Sentiment")
    print("=" * 55)

    url = input(
        "\nURL YouTube: "
    ).strip()

    max_comments_input = input(
        "Max komentar [100]: "
    ).strip()

    if max_comments_input:

        try:
            max_comments = int(
                max_comments_input
            )

        except ValueError:
            logger.error(
                "Masukkan angka yang valid."
            )
            return None

    else:
        max_comments = 100

    if max_comments <= 0:
        logger.error(
            "Max komentar harus > 0."
        )
        return None

    print()
    print("Sort komentar:")
    print("1. Terbaru")
    print("2. Terpopuler")

    sort_choice = input(
        "Pilih [1]: "
    ).strip()

    if sort_choice == "2":
        sort_mode = "popular"
    else:
        sort_mode = "new"

    min_likes_input = input(
        "Min likes [0]: "
    ).strip()

    min_likes = 0

    if min_likes_input:
        try:
            min_likes = int(min_likes_input)
        except ValueError:
            min_likes = 0

    replies_input = input(
        "Sertakan replies? (y/n) [n]: "
    ).strip().lower()

    include_replies = replies_input == "y"

    export_json_input = input(
        "Export JSON juga? (y/n) [n]: "
    ).strip().lower()

    export_json = export_json_input == "y"

    return {
        "url": url,
        "max": max_comments,
        "sort": sort_mode,
        "min_likes": min_likes,
        "replies": include_replies,
        "csv": True,
        "json": export_json,
        "output": None,
        "verbose": False
    }


def main():
    args = parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if args.url:
        config = vars(args)
    else:
        config = interactive_mode()

    if not config:
        return

    print()
    print(
        f"[Config] Target  : "
        f"{config['max']}"
    )

    print(
        f"[Config] Sort    : "
        f"{config['sort']}"
    )

    print(
        f"[Config] Likes   : "
        f">= {config['min_likes']}"
    )

    print(
        f"[Config] Replies : "
        f"{config['replies']}"
    )

    sort_mode = (
        0 if config["sort"] == "popular" else 1
    )

    comments = scrape_youtube(
        config["url"],
        config["max"],
        sort_mode,
        config["min_likes"],
        config["replies"]
    )

    if not comments:
        logger.warning(
            "Tidak ada komentar berhasil diambil."
        )
        return

    logger.info(
        f"Berhasil mengambil "
        f"{len(comments)} komentar."
    )

    sentiment_model = load_sentiment_model()

    comments = add_sentiment_labels(
        comments,
        sentiment_model
    )

    print_sentiment_summary(comments)

    if config.get("output"):
        base_name = config["output"]
        csv_name = f"{base_name}.csv"
        json_name = f"{base_name}.json"
    else:
        csv_name = generate_filename("csv")
        json_name = generate_filename("json")

    if config.get("csv", True):
        save_csv(comments, csv_name)

    if config.get("json"):
        save_json(comments, json_name)

    print()
    logger.info("Selesai.")


if __name__ == "__main__":
    main()
