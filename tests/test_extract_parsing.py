from __future__ import annotations

from x_scrape_cdp.extract import parse_posts_from_html


def test_parse_posts_from_html():
    html = """
    <article data-testid="tweet">
      <a href="/alice/status/111"></a>
      <div data-testid="tweetText">First post</div>
    </article>
    <article data-testid="tweet">
      <a href="/alice/status/222"></a>
      <div data-testid="tweetText">Second post</div>
    </article>
    """
    posts = parse_posts_from_html(html)
    assert [p.id for p in posts] == ["111", "222"]
    assert posts[0].text == "First post"
