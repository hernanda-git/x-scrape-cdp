/**
 * Extract structured fields from one tweet article (DOM root = data-testid="tweet").
 * @param {Element} el - The tweet article element
 * @returns {Object|null} - Extracted tweet data or null if extraction fails
 */
module.exports = function(el) {
  const q = (root, sel) => root.querySelector(sel);
  const qa = (root, sel) => Array.from(root.querySelectorAll(sel));

  const quoteRoot = q(el, '[data-testid="quoteTweet"]');
  const socialEl = q(el, '[data-testid="socialContext"]');
  const socialText = socialEl ? (socialEl.textContent || "").trim() : "";

  const statusIdFromHref = (h) => {
    if (!h) return null;
    const m = String(h).match(/\/status\/(\d+)/);
    return m ? m[1] : null;
  };

  /** Username segment before /status/ID in path or full URL. */
  const handleFromStatusHref = (h) => {
    if (!h) return null;
    try {
      const path = h.startsWith("http") ? new URL(h).pathname : h;
      const m = path.match(/^\/?([^/]+)\/status\/\d+/i);
      if (!m) return null;
      const u = m[1];
      if (!u || u === "i" || u === "home" || u === "explore") return null;
      return u;
    } catch (e) {
      return null;
    }
  };

  /**
   * Canonical tweet id: X almost always wraps <time> in <a href=".../status/THIS_ID">.
   * Using the first /status/ link breaks replies: the parent link often appears above.
   */
  let statusHref = null;
  let id = null;
  for (const t of qa(el, "time")) {
    if (quoteRoot && quoteRoot.contains(t)) continue;
    const parentA = t.closest("a");
    if (!parentA) continue;
    const h = parentA.getAttribute("href");
    const sid = statusIdFromHref(h);
    if (sid) {
      statusHref = h;
      id = sid;
      break;
    }
  }
  if (!id) {
    for (const a of qa(el, 'a[href*="/status/"]')) {
      if (quoteRoot && quoteRoot.contains(a)) continue;
      const h = a.getAttribute("href");
      if (!h || !/\/status\/\d+/.test(h)) continue;
      statusHref = h;
      id = statusIdFromHref(h);
      break;
    }
  }
  if (!id || !statusHref) return null;

  const parseAriaCount = (testid) => {
    const btn = q(el, '[data-testid="' + testid + '"]');
    if (!btn) return null;
    const label = btn.getAttribute("aria-label") || "";
    const m = label.match(/([\d,.]+)\s*[KkMmBb]?/);
    if (!m) return null;
    let raw = m[1].replace(/,/g, "");
    if (raw.endsWith(".")) raw = raw.slice(0, -1);
    const n = parseFloat(raw);
    if (Number.isNaN(n)) return null;
    const mult = /[Kk]/.test(label) ? 1000 : /[Mm]/.test(label) ? 1000000 : /[Bb]/.test(label) ? 1000000000 : 1;
    return Math.round(n * mult);
  };

  const tweetTexts = qa(el, '[data-testid="tweetText"]');
  let mainText = "";
  if (quoteRoot) {
    const mainBlocks = tweetTexts.filter((t) => !quoteRoot.contains(t));
    mainText = mainBlocks.map((t) => (t.innerText || "").trim()).join(" ").trim();
  } else {
    mainText = tweetTexts.map((t) => (t.innerText || "").trim()).join(" ").trim();
  }

  let ts = null;
  for (const t of qa(el, "time")) {
    if (quoteRoot && quoteRoot.contains(t)) continue;
    ts = t.getAttribute("datetime");
    if (ts) break;
  }

  let inReplyToStatusId = null;
  let inReplyToHandle = null;

  const trySetParent = (href) => {
    const pid = statusIdFromHref(href);
    if (!pid || pid === id) return false;
    inReplyToStatusId = pid;
    inReplyToHandle = handleFromStatusHref(href);
    return true;
  };

  if (socialEl) {
    for (const a of qa(socialEl, 'a[href*="/status/"]')) {
      if (trySetParent(a.getAttribute("href"))) break;
    }
    if (!inReplyToHandle) {
      for (const a of qa(socialEl, 'a[href^="/"]')) {
        const h = a.getAttribute("href") || "";
        if (!/^\/[A-Za-z0-9_]{1,30}\/?$/.test(h) || h.includes("/i/")) continue;
        const handle = h.replace(/^\//, "").split("/")[0];
        if (handle && handle !== "home" && handle !== "explore" && handle !== "messages") {
          inReplyToHandle = handle;
          break;
        }
      }
    }
  }

  /**
   * Parent permalink often lives outside socialContext (or UI omits status links there).
   * Any other /status/ID in the article (outside quote) that is not this tweet is the reply target.
   */
  if (!inReplyToStatusId) {
    for (const a of qa(el, 'a[href*="/status/"]')) {
      if (quoteRoot && quoteRoot.contains(a)) continue;
      const h = a.getAttribute("href");
      if (trySetParent(h)) break;
    }
  }

  if (!inReplyToHandle && socialText) {
    const hm = socialText.match(/@([A-Za-z0-9_]{1,30})\b/);
    if (hm) inReplyToHandle = hm[1];
  }

  const st = socialText.toLowerCase();
  let kind = "original";
  if (st.includes("reposted") || st.includes("retweeted") || st.includes("repost")) {
    kind = "retweet";
  } else if (st.includes("replying to") || st.includes("reply to")) {
    kind = "reply";
  } else if (st.includes("replied")) {
    kind = "reply";
  }
  if (inReplyToStatusId && kind === "original") {
    kind = "reply";
  }
  if (quoteRoot) {
    if (kind === "original") kind = "quote";
    else kind = kind + "_with_quote";
  }

  const mediaItems = [];
  for (const img of qa(el, "img")) {
    if (quoteRoot && quoteRoot.contains(img)) continue;
    const src = img.getAttribute("src");
    if (!src || !src.startsWith("http")) continue;
    if (src.includes("profile_images")) continue;
    if (src.includes("/emoji/")) continue;
    mediaItems.push({ kind: "image", url: src });
  }

  let quoted = null;
  if (quoteRoot) {
    let qh = null;
    let qid = null;
    for (const a of qa(quoteRoot, 'a[href*="/status/"]')) {
      const h = a.getAttribute("href");
      const m = h && h.match(/\/status\/(\d+)/);
      if (m) {
        qh = h;
        qid = m[1];
        break;
      }
    }
    const qt = q(quoteRoot, '[data-testid="tweetText"]');
    const qUser = q(quoteRoot, '[data-testid="User-Name"]');
    let qAuthor = null;
    if (qUser) {
      for (const a of qa(qUser, 'a[href^="/"]')) {
        const h = a.getAttribute("href") || "";
        if (/^\/[^/]+\/?$/.test(h) && !h.includes("/i/")) {
          qAuthor = h.replace(/^\//, "").split("/")[0] || null;
          break;
        }
      }
    }
    quoted = {
      id: qid,
      text: qt ? (qt.innerText || "").trim() : "",
      url: qh ? (qh.startsWith("http") ? qh : "https://x.com" + qh) : null,
      author_handle: qAuthor,
    };
  }

  const userNameRoot = q(el, '[data-testid="User-Name"]');
  let authorHandle = null;
  let displayName = null;
  if (userNameRoot) {
    for (const a of qa(userNameRoot, 'a[href^="/"]')) {
      const h = a.getAttribute("href") || "";
      if (/^\/[^/]+\/?$/.test(h) && !h.includes("/i/")) {
        authorHandle = h.replace(/^\//, "").split("/")[0] || null;
        break;
      }
    }
    const sp = q(userNameRoot, "span");
    if (sp) displayName = (sp.innerText || "").trim() || null;
  }

  let views = null;
  for (const a of qa(el, "a")) {
    const href = a.getAttribute("href") || "";
    if (!href.includes("analytics")) continue;
    const lab = a.getAttribute("aria-label") || a.innerText || "";
    const m = lab.match(/([\d,.]+)\s*[KkMmBb]?/);
    if (m) {
      let raw = m[1].replace(/,/g, "");
      const n = parseFloat(raw);
      if (!Number.isNaN(n)) {
        const mult = /[Kk]/.test(lab) ? 1000 : /[Mm]/.test(lab) ? 1000000 : 1;
        views = Math.round(n * mult);
        break;
      }
    }
  }

  return {
    id,
    statusHref,
    mainText,
    ts,
    kind,
    socialContext: socialText || null,
    inReplyToStatusId,
    inReplyToHandle,
    engagement: {
      replies: parseAriaCount("reply"),
      retweets: parseAriaCount("retweet"),
      likes: parseAriaCount("like"),
      views,
      bookmarks: parseAriaCount("bookmark"),
    },
    quoted,
    authorHandle,
    displayName,
    mediaItems,
  };
};