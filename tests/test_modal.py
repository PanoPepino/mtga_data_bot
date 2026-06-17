

from cogs.utils import build_ladder_description
from cogs.embedding import build_embedding
from types import SimpleNamespace
from config import COLOR_TROPHY


def test_build_embedding_sets_trophy_color():
    user = SimpleNamespace(display_name="Pan", display_avatar=SimpleNamespace(url="http://x"))
    runs = [{
        "matches": "Opp 1 2-1\nOpp 2 2-1\nOpp 3 2-1\nOpp 4 2-1\nOpp 5 2-1\nOpp 6 2-1\nOpp 7 2-1",
        "comments": "",
    }]
    embed = build_embedding(user, "Izzet Tempo", runs)
    # color should be TROPHY color when 7-0-equivalent
    assert embed.colour.value == COLOR_TROPHY
    assert "🏆" in embed.description


def test_build_ladder_description_basic():
    desc = build_ladder_description(
        "Izzet Tempo",
        "GB Lands 2-1\nW Stompy 0-2",
        "",
    )
    assert "**deck:** Izzet Tempo" in desc
    assert "GB Lands 2-1" in desc
    assert "W Stompy 0-2" in desc
    assert "comments" not in desc


def test_build_ladder_description_with_comments():
    desc = build_ladder_description(
        "Izzet Tempo",
        "GB Lands 2-1",
        "felt great",
    )
    assert "*comments: felt great*" in desc
