/* Shared GA4 bootstrap. No form answers, emails or URL query strings are sent. */
(function () {
  'use strict';
  const ID = 'G-HFRM2G8C7C';
  const KEY = 'framepact.analytics.internal';
  const SESSION = 'framepact.analytics.visit.v1';
  const FORM = 'https://docs.google.com/forms/d/e/1FAIpQLSeS-G-8U9p5-zMiFGaH3Y0TZjswVbvKOLl1Rg1_uK2GKw0blg/viewform';
  const TTL = 30 * 60 * 1000;
  function read(store, key) { try { return window[store].getItem(key); } catch (_) { return null; } }
  function write(store, key, value) { try { window[store].setItem(key, value); return true; } catch (_) { return false; } }
  const internal = read('localStorage', KEY) === '1';
  const production = location.hostname === 'framepact.jp' || location.hostname === 'www.framepact.jp';
  window['ga-disable-' + ID] = internal || !production;
  window.dataLayer = window.dataLayer || [];
  window.gtag = function () {
    if (!window['ga-disable-' + ID]) window.dataLayer.push(arguments);
  };
  window.FramepactAnalytics = {
    isExcluded: function () { return window['ga-disable-' + ID]; },
    setInternal: function (enabled) {
      const saved = write('localStorage', KEY, enabled ? '1' : '0');
      if (enabled) {
        window['ga-disable-' + ID] = true;
        try { window.sessionStorage.removeItem(SESSION); } catch (_) {}
      }
      return saved;
    }
  };
  if (window['ga-disable-' + ID]) return;

  // Restrict retained paths to this static site's public page names.
  function safePath(value) {
    return /^\/(?:[a-z0-9-]+(?:\.html)?)?$/.test(value) ? value : '/';
  }
  function source() {
    try {
      const ref = new URL(document.referrer);
      if (ref.hostname === location.hostname) return null;
      const host = ref.hostname.toLowerCase();
      if (/(^|\.)chatgpt\.com$/.test(host)) return 'chatgpt';
      if (/(^|\.)google\.(com|co\.jp)$/.test(host)) return 'google';
      if (/(^|\.)bing\.com$/.test(host)) return 'bing';
      if (/(^|\.)(youtube\.com|youtu\.be)$/.test(host)) return 'youtube';
      if (/(^|\.)(x\.com|t\.co)$/.test(host)) return 'x';
      if (/(^|\.)note\.com$/.test(host)) return 'note';
      return 'other_referral';
    } catch (_) { return null; }
  }
  let visit;
  try { visit = JSON.parse(read('sessionStorage', SESSION)); } catch (_) {}
  const now = Date.now();
  if (!visit || !Number.isFinite(visit.lastSeen) || now - visit.lastSeen > TTL || now < visit.lastSeen) {
    visit = { landing: safePath(location.pathname), source: source() || 'direct_or_unknown', started: now };
  }
  visit.lastSeen = now;
  write('sessionStorage', SESSION, JSON.stringify(visit));
  const page = safePath(location.pathname);
  const pageURL = location.origin + page;
  // Keep only known campaign labels. Arbitrary query values may contain personal data.
  const incoming = new URLSearchParams(location.search);
  const campaignSources = ['google', 'bing', 'chatgpt', 'chatgpt.com', 'x', 'twitter', 'note', 'youtube'];
  const campaignMedia = ['organic', 'referral', 'social', 'email', 'cpc', 'ai-assistant'];
  const config = { page_location: pageURL, page_referrer: '', send_page_view: true };
  try { const ref = new URL(document.referrer); config.page_referrer = ref.origin; } catch (_) {}
  if (campaignSources.includes(incoming.get('utm_source')) && campaignMedia.includes(incoming.get('utm_medium'))) {
    config.campaign_source = incoming.get('utm_source');
    config.campaign_medium = incoming.get('utm_medium');
  }
  gtag('js', new Date());
  gtag('config', ID, config);
  const script = document.createElement('script');
  script.async = true;
  script.src = 'https://www.googletagmanager.com/gtag/js?id=' + ID;
  document.head.appendChild(script);

  function params() {
    return { page_location: pageURL, source_page: page, landing_page: safePath(visit.landing),
      observed_referrer: ['chatgpt','google','bing','youtube','x','note','other_referral','direct_or_unknown'].includes(visit.source) ? visit.source : 'direct_or_unknown', traffic_type: 'external', measurement_version: '20260929' };
  }
  if (/^\/ai-video-price(?:\.html)?$/.test(page)) gtag('event', 'pricing_view', params());
  const portfolioViewIds = ['mv-1', 'mv-2', 'mv-3'];
  const portfolioIds = [...portfolioViewIds, 'showreel', 'brand-pr', 'training'];
  const portfolioPlacements = ['homepage_card', 'homepage_dialog', 'portfolio_case', 'portfolio_intro', 'portfolio_footer', 'service_related'];
  function portfolioContext(id, placement) {
    if (!portfolioIds.includes(id) || !portfolioPlacements.includes(placement)) return null;
    return { portfolio_id: id, cta_location: placement };
  }
  if (/^\/mv-portfolio(?:\.html)?$/.test(page)) {
    const values = params();
    const id = (location.hash || '').slice(1);
    if (portfolioViewIds.includes(id)) values.portfolio_id = id;
    gtag('event', 'portfolio_view', values);
  }
  document.addEventListener('click', function (event) {
    const link = event.target.closest && event.target.closest('a[href]');
    if (!link) return;
    let url;
    try { url = new URL(link.href); } catch (_) { return; }
    if (url.origin + url.pathname !== FORM) return;
    const values = params();
    values.contact_channel = 'google_forms';
    values.click_time_utc = new Date().toISOString();
    const data = link.dataset || {};
    const context = portfolioContext(data.portfolioId, data.ctaLocation);
    if (context) Object.assign(values, context);
    gtag('event', 'contact_form_click', values);
    visit.lastSeen = Date.now();
    write('sessionStorage', SESSION, JSON.stringify(visit));
  });
  // Count actual dialog openings, including #price links, not merely button clicks.
  document.addEventListener('framepact:pricing-view', function () {
    gtag('event', 'pricing_view', params());
  });
  // These are explicit portfolio interactions, not playback or completed inquiries.
  // Accept fixed labels only; never send the copied brief, form answers or arbitrary data.
  document.addEventListener('framepact:portfolio-action', function (event) {
    const detail = event.detail || {};
    if (!['video_open', 'video_external', 'copy_brief'].includes(detail.action)) return;
    const context = portfolioContext(detail.portfolio_id, detail.placement);
    if (!context) return;
    gtag('event', 'portfolio_' + detail.action, Object.assign(params(), context));
  });
})();

