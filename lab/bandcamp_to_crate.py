import html
import json
import re
import sys
import urllib.request
from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class EngineTrack:
    track_number: int
    track_id: int
    title: str
    artist: str
    album: str
    duration_sec: float
    stream_url: Optional[str]
    source_url: str


def parse_bandcamp_html(page_html: str, source_url: Optional[str] = None) -> List[EngineTrack]:
    """Parses Bandcamp release HTML (data-tralbum) into Engine OS-ready track metadata."""
    if "Client Challenge" in page_html and "data-tralbum" not in page_html:
        raise RuntimeError(
            "Blocked by Bandcamp 'Client Challenge' (common on cloud/datacenter IPs). "
            "Run locally on a residential IP or pass a saved .html file."
        )

    tralbum_match = re.search(r'data-tralbum=(["\'])(.*?)\1', page_html, re.DOTALL)
    if not tralbum_match:
        raise ValueError("Could not find data-tralbum metadata in the provided HTML.")

    data = json.loads(html.unescape(tralbum_match.group(2)))
    album_name = data.get('current', {}).get('title', 'Unknown Release')
    default_artist = data.get('artist', 'Unknown Artist')

    resolved_url = source_url or data.get('url') or "https://bandcamp.com"
    domain_match = re.match(r'(https?://[^/]+)', resolved_url)
    base_domain = domain_match.group(1) if domain_match else "https://bandcamp.com"

    tracks: List[EngineTrack] = []
    for idx, item in enumerate(data.get('trackinfo', []), start=1):
        file_info = item.get('file') or {}
        rel_link = item.get('title_link', '')
        tracks.append(EngineTrack(
            track_number=idx,
            track_id=item.get('id', 0),
            title=item.get('title', 'Untitled'),
            artist=item.get('artist') or default_artist,
            album=album_name,
            duration_sec=round(float(item.get('duration', 0.0)), 2),
            stream_url=file_info.get('mp3-128'),
            source_url=f"{base_domain}{rel_link}" if rel_link.startswith('/') else resolved_url
        ))
    return tracks


def fetch_bandcamp_crate(target: str) -> List[EngineTrack]:
    """Accepts either a live Bandcamp URL (for residential IPs) or a local .html file path."""
    if target.endswith(".html"):
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            return parse_bandcamp_html(f.read())

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    req = urllib.request.Request(target, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as response:
        page_html = response.read().decode('utf-8', errors='replace')
    return parse_bandcamp_html(page_html, source_url=target)


def export_manifest(tracks: List[EngineTrack], out_path: str = "crate_manifest.json") -> str:
    """Exports extracted tracks to a JSON manifest for the SC6000M EAAS server."""
    payload = {
        "source": "bandcamp-dev-bridge",
        "track_count": len(tracks),
        "tracks": [asdict(t) for t in tracks]
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return out_path


if __name__ == "__main__":
    args = iter(sys.argv)
    next(args)
    source = next(args, "https://bandcamp.com")
    extracted = fetch_bandcamp_crate(source)
    out_file = export_manifest(extracted)
    print(f"Exported {len(extracted)} tracks to {out_file}")
