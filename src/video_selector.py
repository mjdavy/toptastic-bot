import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

# Heuristic weights (tweak as needed)
try:
    from rapidfuzz import fuzz as rf_fuzz
    _RAPIDFUZZ_AVAILABLE = True
except Exception:  # pragma: no cover - fallback path
    _RAPIDFUZZ_AVAILABLE = False

WEIGHTS = {
    'official_keyword': 25.0,
    'artist_channel_exact': 35.0,
    'vevo_channel': 28.0,
    'good_title_match': 22.0,
    'category_music': 10.0,
    'view_count': 0.000005,  # scaled
    'duration_in_range': 8.0,
    'recent_release_bonus': 4.0,
    'explicit_match': 2.0,
    'rapidfuzz_similarity': 30.0,  # multiplied by (similarity/100)
    # Penalties
    'lyrics_penalty': -30.0,
    'audio_penalty': -22.0,
    'visualizer_penalty': -18.0,
    'static_image_penalty': -12.0,
    # Live performances are usually less preferred than official MV but better than lyric/static variants
    'live_penalty': -10.0,
    'remix_penalty': -6.0,
    'cover_penalty': -14.0,
}

OFFICIAL_KEYWORDS = [
    'official video', 'official music video', 'official mv', 'official hd', 'official 4k', 'official visual',
]
BLOCK_LYRIC = ['lyric video', 'lyrics', 'l y r i c', 'letra']
BLOCK_AUDIO = ['audio only', 'official audio', 'full audio', 'hq audio']
BLOCK_STATIC = ['still image', 'static image']
BLOCK_VISUALIZER = ['visualizer', 'visualiser']
BLOCK_LIVE = ['live at', 'live from', 'live session', 'live performance']
BLOCK_COVER = ['cover by', 'acoustic cover']
BLOCK_REMIX = ['remix', 'bootleg']

OFFICIAL_CHANNEL_HINTS = ['vevo']

DURATION_MIN = 90      # 1:30
DURATION_MAX = 600     # 10:00

@dataclass
class VideoCandidate:
    video_id: str
    title: str
    channel_title: str
    view_count: int = 0
    duration_seconds: Optional[int] = None
    category_id: Optional[str] = None
    published_at: Optional[str] = None
    raw: Dict[str, Any] = None

    score: float = 0.0
    reasons: List[str] = None

    def add(self, pts: float, reason: str):
        self.score += pts
        if self.reasons is None:
            self.reasons = []
        self.reasons.append(f"{reason}:{pts:+.1f}")

TITLE_NORMALIZE_RE = re.compile(r"[^a-z0-9]+")

def normalize(text: str) -> str:
    return TITLE_NORMALIZE_RE.sub(' ', text.lower()).strip()

def ratio_overlap(a: str, b: str) -> float:
    sa = set(normalize(a).split())
    sb = set(normalize(b).split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)

def contains_any(text: str, phrases: List[str]) -> bool:
    t = text.lower()
    return any(p in t for p in phrases)

def is_artist_channel(artist: str, channel: str) -> bool:
    return normalize(artist) in normalize(channel)

def parse_iso8601_duration(d: str) -> Optional[int]:
    # Simplistic ISO8601 duration parser for YouTube (PnDTnHnMnS)
    if not d:
        return None
    pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
    m = pattern.fullmatch(d)
    if not m:
        return None
    h, m_, s = m.groups()
    seconds = (int(h) if h else 0) * 3600 + (int(m_) if m_ else 0) * 60 + (int(s) if s else 0)
    return seconds

def score_candidate(candidate: VideoCandidate, artist: str, song: str) -> VideoCandidate:
    title = candidate.title.lower()
    artist_norm = normalize(artist)
    song_norm = normalize(song)
    combined = f"{artist_norm} {song_norm}".strip()

    # Positive signals
    if contains_any(title, OFFICIAL_KEYWORDS):
        candidate.add(WEIGHTS['official_keyword'], 'official_keyword')
    if candidate.category_id == '10':  # Music category
        candidate.add(WEIGHTS['category_music'], 'category_music')
    if any(hint in candidate.channel_title.lower() for hint in OFFICIAL_CHANNEL_HINTS):
        candidate.add(WEIGHTS['vevo_channel'], 'vevo_channel')
    if is_artist_channel(artist, candidate.channel_title):
        candidate.add(WEIGHTS['artist_channel_exact'], 'artist_channel_exact')

    overlap = ratio_overlap(candidate.title, f"{artist} {song}")
    if overlap > 0.5:
        candidate.add(WEIGHTS['good_title_match'] * overlap, f'title_overlap_{overlap:.2f}')

    # RapidFuzz similarity (token_set + partial hybrid) if library is available
    if _RAPIDFUZZ_AVAILABLE:
        base_query = f"{artist} {song}".strip()
        ts_score = rf_fuzz.token_set_ratio(base_query, candidate.title)
        pr_score = rf_fuzz.partial_ratio(base_query, candidate.title)
        similarity = max(ts_score, pr_score)
        if similarity >= 60:  # threshold to count as useful match
            candidate.add(WEIGHTS['rapidfuzz_similarity'] * (similarity / 100.0), f'rf_sim_{similarity:.0f}')
        else:
            candidate.add(-5.0, f'rf_low_{similarity:.0f}')

    if candidate.view_count:
        candidate.add(min(candidate.view_count * WEIGHTS['view_count'], 18.0), 'view_count_scaled')

    if candidate.duration_seconds is not None:
        if DURATION_MIN <= candidate.duration_seconds <= DURATION_MAX:
            candidate.add(WEIGHTS['duration_in_range'], 'duration_in_range')
        else:
            candidate.add(-5.0, 'duration_out_of_range')

    # Negative signals
    if contains_any(title, BLOCK_LYRIC):
        candidate.add(WEIGHTS['lyrics_penalty'], 'lyrics_penalty')
    if contains_any(title, BLOCK_AUDIO):
        candidate.add(WEIGHTS['audio_penalty'], 'audio_penalty')
    if contains_any(title, BLOCK_VISUALIZER):
        candidate.add(WEIGHTS['visualizer_penalty'], 'visualizer_penalty')
    if contains_any(title, BLOCK_STATIC):
        candidate.add(WEIGHTS['static_image_penalty'], 'static_image_penalty')
    if contains_any(title, BLOCK_LIVE):
        candidate.add(WEIGHTS['live_penalty'], 'live_penalty')
    if contains_any(title, BLOCK_COVER):
        candidate.add(WEIGHTS['cover_penalty'], 'cover_penalty')
    if contains_any(title, BLOCK_REMIX) and 'remix' not in song_norm:
        candidate.add(WEIGHTS['remix_penalty'], 'remix_penalty')

    return candidate

def select_best_video(candidates: List[VideoCandidate], artist: str, song: str) -> Optional[VideoCandidate]:
    scored = [score_candidate(c, artist, song) for c in candidates]
    if not scored:
        return None
    # Sort by score desc then by view_count desc for tie-break
    scored.sort(key=lambda c: (c.score, c.view_count), reverse=True)
    return scored[0]

def build_candidates_from_api(search_items: List[Dict[str, Any]], videos_map: Dict[str, Dict[str, Any]]) -> List[VideoCandidate]:
    out: List[VideoCandidate] = []
    for item in search_items:
        vid = item['id']['videoId']
        video_details = videos_map.get(vid, {})
        snippet = video_details.get('snippet', item.get('snippet', {}))
        stats = video_details.get('statistics', {})
        content = video_details.get('contentDetails', {})
        candidate = VideoCandidate(
            video_id=vid,
            title=snippet.get('title', ''),
            channel_title=snippet.get('channelTitle', ''),
            view_count=int(stats.get('viewCount', 0)) if stats.get('viewCount') else 0,
            duration_seconds=parse_iso8601_duration(content.get('duration')) if content.get('duration') else None,
            category_id=snippet.get('categoryId'),
            published_at=snippet.get('publishedAt'),
            raw=video_details or item
        )
        out.append(candidate)
    return out
