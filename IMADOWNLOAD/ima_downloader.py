"""
IMA Knowledge Base Downloader
Downloads all files from an IMA knowledge base share page.

Usage:
    python ima_downloader.py --url "https://ima.qq.com/wiki/?shareId=YOUR_SHARE_ID"
    python ima_downloader.py --url "adf7c2eb...your_share_id..."
"""

import argparse
import json
import os
import re
import sys
import time

try:
    import requests
except ImportError:
    print("Error: requests not installed. Run: pip install requests")
    sys.exit(1)

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: playwright not installed. Run: pip install playwright && python -m playwright install chromium")
    sys.exit(1)

API_BASE = "https://ima.qq.com/cgi-bin/knowledge_share_get/get_share_info"
PAGE_SIZE = 50
MEDIA_TYPE_NOTE = 11
MEDIA_TYPE_FOLDER = 99


def extract_share_id(url_or_id):
    if "shareId=" in url_or_id:
        return url_or_id.split("shareId=")[1].split("&")[0]
    return url_or_id


def is_valid_hex_share_id(sid):
    return len(sid) == 64 and all(c in "0123456789abcdef" for c in sid.lower())


def find_valid_share_id(bad_id):
    if is_valid_hex_share_id(bad_id):
        return [bad_id]
    non_hex = [i for i, c in enumerate(bad_id.lower()) if c not in "0123456789abcdef"]
    if len(non_hex) != 1 or len(bad_id) != 64:
        return [bad_id]
    pos = non_hex[0]
    return [bad_id[:pos] + c + bad_id[pos + 1:] for c in "0123456789abcdef"]


def api_get_share_info(share_id, folder_id=None):
    payload = {"shareId": share_id, "limit": PAGE_SIZE}
    if folder_id:
        payload["folder_id"] = folder_id
    r = requests.post(API_BASE, json=payload, timeout=15)
    d = r.json()
    if d.get("code") == 0:
        return d
    return None


def list_folder_recursive(share_id, folder_id, path, all_files, depth=0):
    indent = "  " * depth
    page_cursor = ""
    page_count = 0

    while True:
        payload = {"shareId": share_id, "limit": PAGE_SIZE}
        if folder_id:
            payload["folder_id"] = folder_id
        if page_cursor:
            payload["cursor"] = page_cursor

        r = requests.post(API_BASE, json=payload, timeout=15)
        d = r.json()
        if d.get("code") != 0:
            break

        items = d.get("knowledge_list", [])
        is_end = d.get("is_end", True)
        next_cursor = d.get("next_cursor", "")

        for item in items:
            fi = item.get("folder_info")
            if fi:
                sub_id = fi["folder_id"]
                sub_name = fi.get("name", "unknown")
                sub_count = fi.get("file_number", "0")
                sub_path = os.path.join(path, sanitize(sub_name))
                print("%s[DIR] %s (%s items)" % (indent, sub_name, sub_count))
                list_folder_recursive(share_id, sub_id, sub_path, all_files, depth + 1)
            else:
                title = item.get("title", "untitled")
                media_type = item.get("media_type", 0)
                file_size = item.get("file_size", "0")
                jump_url = item.get("jump_url", "")
                cover_urls = item.get("cover_urls", [])

                all_files.append({
                    "title": title,
                    "media_type": media_type,
                    "file_size": int(file_size) if file_size else 0,
                    "jump_url": jump_url,
                    "cover_urls": cover_urls,
                    "path": path,
                    "media_id": item.get("media_id", ""),
                    "raw_file_url": item.get("raw_file_url", ""),
                })

        page_count += 1
        if is_end or not next_cursor:
            break
        page_cursor = next_cursor


def sanitize(name):
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    name = name.strip(". ")
    return name[:200] if name else "unnamed"


def download_notes_via_browser(share_id, notes, output_dir):
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for i, note in enumerate(notes):
            title = note["title"]
            jump_url = note["jump_url"]
            save_path = note["save_path"]

            print("[%d/%d] Downloading note: %s" % (i + 1, len(notes), title))

            if not jump_url:
                print("  -> Skipped (no URL)")
                results.append({"title": title, "status": "skipped", "reason": "no_url"})
                continue

            try:
                page.goto(jump_url, wait_until="networkidle", timeout=30000)
                time.sleep(2)

                content = page.inner_text("body")

                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write("Title: %s\n" % title)
                    f.write("URL: %s\n" % jump_url)
                    f.write("=" * 60 + "\n\n")
                    f.write(content)

                size = os.path.getsize(save_path)
                print("  -> Saved: %s (%d bytes)" % (save_path, size))
                results.append({"title": title, "status": "ok", "path": save_path, "size": size})

            except Exception as e:
                print("  -> Error: %s" % str(e))
                results.append({"title": title, "status": "error", "reason": str(e)})

        browser.close()

    return results


def download_covers(notes, output_dir):
    results = []
    for i, note in enumerate(notes):
        title = note["title"]
        save_path = note["save_path"]

        if not note.get("cover_urls"):
            results.append({"title": title, "status": "skipped"})
            continue

        cover_url = note["cover_urls"][0]
        print("[%d/%d] Downloading cover: %s" % (i + 1, len(notes), title))

        try:
            r = requests.get(cover_url, timeout=30)
            if r.status_code == 200:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, "wb") as f:
                    f.write(r.content)
                print("  -> Saved: %s (%d bytes)" % (save_path, len(r.content)))
                results.append({"title": title, "status": "ok", "path": save_path})
            else:
                print("  -> HTTP %d" % r.status_code)
                results.append({"title": title, "status": "error"})
        except Exception as e:
            print("  -> Error: %s" % str(e))
            results.append({"title": title, "status": "error"})

    return results


def get_file_ext(title, url):
    ext_map = {".pdf": ".pdf", ".doc": ".doc", ".docx": ".docx", ".xls": ".xls",
               ".xlsx": ".xlsx", ".ppt": ".ppt", ".pptx": ".pptx",
               ".jpg": ".jpg", ".jpeg": ".jpeg", ".png": ".png", ".gif": ".gif",
               ".bmp": ".bmp", ".dwg": ".dwg", ".zip": ".zip"}
    lower = title.lower()
    for suffix, ext in ext_map.items():
        if lower.endswith(suffix):
            return ext
    if url:
        url_path = url.split("?")[0].lower()
        for suffix, ext in ext_map.items():
            if url_path.endswith(suffix):
                return ext
    return ".bin"


def download_all_files(files, output_dir):
    results = []
    ok = 0
    fail = 0
    skip = 0

    for i, f in enumerate(files):
        title = f["title"]
        jump_url = f.get("jump_url", "")
        path = f["path"]

        if not jump_url:
            skip += 1
            continue

        url = jump_url
        ext = get_file_ext(title, url)
        safe_title = sanitize(title)
        if not safe_title.lower().endswith(ext):
            safe_title += ext
        save_path = os.path.join(path, safe_title)

        if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
            skip += 1
            continue

        print("[%d/%d] %s" % (i + 1, len(files), title))

        try:
            r = requests.get(url, timeout=60, stream=True)
            if r.status_code == 200:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, "wb") as fobj:
                    for chunk in r.iter_content(8192):
                        fobj.write(chunk)
                size = os.path.getsize(save_path)
                print("  -> Saved: %d bytes" % size)
                ok += 1
                results.append({"title": title, "status": "ok", "path": save_path, "size": size})
            else:
                print("  -> HTTP %d" % r.status_code)
                fail += 1
                results.append({"title": title, "status": "error", "reason": "HTTP %d" % r.status_code})
        except Exception as e:
            print("  -> Error: %s" % str(e))
            fail += 1
            results.append({"title": title, "status": "error", "reason": str(e)})

    return results, ok, fail, skip


def main():
    parser = argparse.ArgumentParser(description="IMA Knowledge Base Downloader")
    parser.add_argument("--url", required=True, help="Share URL or shareId")
    parser.add_argument("--output", default="ima_downloads", help="Output directory")
    args = parser.parse_args()

    share_id = extract_share_id(args.url)
    output_dir = args.output

    print("=" * 60)
    print("IMA Knowledge Base Downloader")
    print("=" * 60)
    print("Share ID: %s" % share_id)

    candidates = find_valid_share_id(share_id)
    if len(candidates) > 1:
        print("[*] ShareId has non-hex char, trying %d replacements..." % len(candidates))

    best_data = None
    best_sid = None

    for i, sid in enumerate(candidates):
        if len(candidates) > 1:
            print("\n--- Candidate %d/%d: ...%s ---" % (i + 1, len(candidates), sid[-16:]))

        data = api_get_share_info(sid)
        if data:
            print("[+] Valid shareId found: ...%s" % sid[-8:])
            best_data = data
            best_sid = sid
            break

    if not best_data:
        print("\n[-] Failed to find valid shareId.")
        print("    The knowledge base may require authentication or may have been deleted.")
        print("    Please copy the shareId from your browser address bar.")
        print('    Usage: python ima_downloader.py --url "YOUR_CORRECT_URL"')
        sys.exit(1)

    kb_info = best_data.get("knowledge_base_info", {}).get("basic_info", {})
    kb_name = sanitize(kb_info.get("name", "unknown"))
    total_size = best_data.get("total_size", 0)
    kb_dir = os.path.join(output_dir, kb_name)
    os.makedirs(kb_dir, exist_ok=True)

    print("\nKnowledge Base: %s" % kb_info.get("name", "unknown"))
    print("Total items: %s" % total_size)
    print("Output dir: %s" % os.path.abspath(kb_dir))
    print()

    print("[1/4] Scanning folder structure...")
    all_files = []
    root_folder_id = None

    root_items = best_data.get("knowledge_list", [])
    for item in root_items:
        fi = item.get("folder_info")
        if fi:
            sub_id = fi["folder_id"]
            sub_name = fi.get("name", "unknown")
            sub_count = fi.get("file_number", "0")
            sub_path = os.path.join(kb_dir, sanitize(sub_name))
            print("  [DIR] %s (%s items)" % (sub_name, sub_count))
            list_folder_recursive(best_sid, sub_id, sub_path, all_files, depth=1)
        else:
            title = item.get("title", "untitled")
            media_type = item.get("media_type", 0)
            file_size = int(item.get("file_size", "0") or "0")
            jump_url = item.get("jump_url", "")
            cover_urls = item.get("cover_urls", [])

            all_files.append({
                "title": title,
                "media_type": media_type,
                "file_size": file_size,
                "jump_url": jump_url,
                "cover_urls": cover_urls,
                "path": kb_dir,
                "media_id": item.get("media_id", ""),
                "raw_file_url": item.get("raw_file_url", ""),
            })

    notes = [f for f in all_files if f["media_type"] == MEDIA_TYPE_NOTE]
    images = [f for f in all_files if f["media_type"] not in (MEDIA_TYPE_NOTE, MEDIA_TYPE_FOLDER)]

    print("\n[2/4] Found %d notes, %d other files" % (len(notes), len(images)))

    total_bytes = sum(f["file_size"] for f in all_files)
    print("       Total data: %.1f MB" % (total_bytes / 1024 / 1024))

    with open(os.path.join(kb_dir, "_file_list.json"), "w", encoding="utf-8") as f:
        json.dump(all_files, f, ensure_ascii=False, indent=2)

    print("\n[3/4] Downloading %d notes..." % len(notes))
    for note in notes:
        note["save_path"] = os.path.join(note["path"], sanitize(note["title"]) + ".txt")
    note_results = download_notes_via_browser(best_sid, notes, kb_dir)

    print("\n[4/4] Saving %d cover images..." % len(notes))
    for note in notes:
        note["save_path"] = os.path.join(note["path"], sanitize(note["title"]) + "_cover.jpg")
    cover_results = download_covers(notes, kb_dir)

    print("\n[5/5] Downloading %d files (PDFs, images, etc.)..." % len(images))
    file_results, file_ok, file_fail, file_skip = download_all_files(images, kb_dir)

    ok_notes = sum(1 for r in note_results if r["status"] == "ok")
    ok_covers = sum(1 for r in cover_results if r["status"] == "ok")

    print()
    print("=" * 60)
    print("Complete!")
    print("=" * 60)
    print("Notes downloaded: %d/%d" % (ok_notes, len(notes)))
    print("Covers downloaded: %d/%d" % (ok_covers, len(notes)))
    print("Files downloaded: %d, failed: %d, skipped: %d" % (file_ok, file_fail, file_skip))
    print("Total files in KB: %d" % len(all_files))
    print("Output directory: %s" % os.path.abspath(kb_dir))
    print()
    print("File list saved to: %s" % os.path.join(kb_dir, "_file_list.json"))


if __name__ == "__main__":
    main()
