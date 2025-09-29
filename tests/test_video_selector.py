import pytest

from src.video_selector import VideoCandidate, select_best_video, score_candidate

def make_candidate(**kwargs):
    base = dict(
        video_id='vid',
        title='Title',
        channel_title='Channel',
        view_count=1000,
        duration_seconds=210,
        category_id='10',
        published_at='2024-01-01T00:00:00Z',
        raw={}
    )
    base.update(kwargs)
    return VideoCandidate(**base)

@pytest.fixture
def artist_song():
    return ('Taylor Swift', 'Cardigan')

def test_official_beats_lyric(artist_song):
    artist, song = artist_song
    lyric = make_candidate(video_id='lyric1', title='Taylor Swift - Cardigan (Lyric Video)')
    official = make_candidate(video_id='off1', title='Taylor Swift - cardigan (Official Music Video)', channel_title='Taylor Swift')
    best = select_best_video([lyric, official], artist, song)
    assert best.video_id == 'off1', f"Expected official video, got {best.video_id} with reasons {best.reasons}"


def test_audio_penalized(artist_song):
    artist, song = artist_song
    audio = make_candidate(video_id='aud1', title='Taylor Swift - Cardigan (Official Audio)')
    mv = make_candidate(video_id='mv1', title='Taylor Swift - cardigan (Official Video)')
    best = select_best_video([audio, mv], artist, song)
    assert best.video_id == 'mv1'


def test_channel_match_bonus(artist_song):
    artist, song = artist_song
    random_ch = make_candidate(video_id='r1', title='Taylor Swift - cardigan (Official Music Video)')
    artist_ch = make_candidate(video_id='a1', title='Taylor Swift - cardigan', channel_title='Taylor Swift')
    # Score individually
    scored_random = score_candidate(random_ch, artist, song)
    scored_artist = score_candidate(artist_ch, artist, song)
    assert scored_artist.score > scored_random.score, (scored_artist.score, scored_random.score)


def test_lyric_vs_live_fallback(artist_song):
    artist, song = artist_song
    lyric = make_candidate(video_id='l1', title='Taylor Swift - cardigan (Lyrics)')
    live = make_candidate(video_id='live1', title='Taylor Swift - cardigan (Live at NYC)')
    best = select_best_video([lyric, live], artist, song)
    # Both are penalized; ensure deterministic ordering but live penalty less severe than lyrics
    assert best.video_id == 'live1'


def test_rapidfuzz_similarity_boost(artist_song):
    artist, song = artist_song
    # Intentionally reorder and add noise vs a poorer partial match
    good = make_candidate(video_id='g1', title='Cardigan by Taylor Swift (Official Video)')
    poorer = make_candidate(video_id='p1', title='Swift Taylor - Crdgn (Teaser)')
    best = select_best_video([poorer, good], artist, song)
    assert best.video_id == 'g1', 'Expected higher RapidFuzz similarity candidate to win'
