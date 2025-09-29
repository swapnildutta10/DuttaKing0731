import os
from flask import Flask, request, send_file
import yt_dlp

app = Flask(__name__)
OUT_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(OUT_DIR, exist_ok=True)

PROGRESSIVE_FMT = (
    "best[height<=480][ext=mp4][acodec!=none][vcodec!=none]/"
    "best[height<=480][acodec!=none][vcodec!=none]/"
    "best[ext=mp4][acodec!=none][vcodec!=none]/"
    "best[acodec!=none][vcodec!=none]/best"
)

def final_path(info, ydl):
    rd = info.get("requested_downloads")
    if rd and isinstance(rd, list) and "filepath" in rd[0]:
        return rd[0]["filepath"]
    return ydl.prepare_filename(info)

@app.get("/")
def index():
    return send_file("index.html")

@app.post("/download")
def download():
    url = (request.form.get("url") or "").strip()
    format_id = (request.form.get("format_id") or "").strip()
    if not url:
        return "Missing URL", 400

    # Use user format_id if provided, else default progressive
    ydl_opts = {
        "outtmpl": os.path.join(OUT_DIR, "%(title).200s [%(id)s].%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": format_id if format_id else PROGRESSIVE_FMT,
    }

    try:
        info = None
        path = None
        ydl_used = None
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                ydl_used = ydl
        except yt_dlp.utils.DownloadError:
            try:
                with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl_list:
                    info = ydl_list.extract_info(url, download=False)
                    formats = info.get('formats', [])
                    format_list = []
                    for f in formats:
                        format_id = f.get('format_id')
                        ext = f.get('ext')
                        note = f.get('format_note', '')
                        res = f.get('resolution', '')
                        format_list.append(f"ID: {format_id}, ext: {ext}, note: {note}, res: {res}")
                    if format_list:
                        return (
                            "Download failed: No compatible formats.\n" +
                            "Available formats:\n" +
                            "\n".join(format_list) +
                            "\n\nPlease copy a format ID and enter it in the Format ID field on the main page."
                        ), 400
                    else:
                        return "Download failed: No available formats for this video.", 500
            except Exception as e:
                return f"Download failed: Could not retrieve formats. {e}", 500
        if info and ydl_used:
            path = final_path(info, ydl_used)
            return send_file(path, as_attachment=True,
                             download_name=os.path.basename(path))
        else:
            return "Download failed: No available formats for this video.", 500
    except Exception as e:
        return f"Download failed: {e}", 500

if __name__ == "__main__":
    app.run(debug=True)
