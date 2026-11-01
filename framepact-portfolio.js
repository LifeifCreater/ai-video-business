/* MV portfolio: load YouTube only on request; copy static, non-personal inquiry notes. */
(function () {
  'use strict';

  const works = Object.freeze({
    'mv-1': { youtubeId: 's6zJ-bgTsDo', title: '実在人物を映画の世界へ。MV制作実績①（公開版・1分7秒）' },
    'mv-2': { youtubeId: 'L0W4Vx75RtE', title: '実在人物を映画の世界へ。MV制作実績②（公開版・1分11秒）' }
  });

  function track(id, action) {
    if (!Object.prototype.hasOwnProperty.call(works, id)) return;
    document.dispatchEvent(new CustomEvent('framepact:portfolio-action', {
      detail: { portfolio_id: id, action: action, placement: 'portfolio_case' }
    }));
  }

  document.querySelectorAll('[data-video-trigger]').forEach(function (link) {
    const id = link.dataset.videoTrigger;
    if (!Object.prototype.hasOwnProperty.call(works, id)) return;
    const work = works[id];
    const stage = link.closest('[data-video-stage]');
    if (!stage) return;

    const thumbnail = link.querySelector('img');
    if (thumbnail) {
      const showFallback = function () {
        thumbnail.hidden = true;
        link.classList.add('thumbnail-unavailable');
      };
      thumbnail.addEventListener('error', showFallback);
      thumbnail.addEventListener('load', function () {
        thumbnail.hidden = false;
        link.classList.remove('thumbnail-unavailable');
      });
      // An already-cached failure can precede this deferred script.
      if (thumbnail.complete && thumbnail.naturalWidth === 0) showFallback();
    }

    const label = link.querySelector('.poster-action');
    if (label) label.textContent = 'プレイヤーを開く';
    link.setAttribute('aria-label', work.title + 'のYouTubeプレイヤーをこのページで開く');

    link.addEventListener('click', function (event) {
      // Modified clicks retain the normal external-link behavior.
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
        track(id, 'video_external');
        return;
      }
      event.preventDefault();
      if (stage.querySelector('iframe')) return;

      const player = document.createElement('iframe');
      player.src = 'https://www.youtube-nocookie.com/embed/' + work.youtubeId + '?rel=0';
      player.title = work.title;
      player.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
      player.allowFullscreen = true;
      player.referrerPolicy = 'strict-origin-when-cross-origin';
      player.setAttribute('tabindex', '0');
      stage.replaceChildren(player);
      player.focus();
      // Opening the player is measured; this does not claim that playback began.
      track(id, 'video_open');
    });
  });

  document.querySelectorAll('[data-video-external]').forEach(function (link) {
    link.addEventListener('click', function () {
      track(link.dataset.videoExternal, 'video_external');
    });
  });

  document.querySelectorAll('[data-copy-brief]').forEach(function (button) {
    const id = button.dataset.copyBrief;
    if (!Object.prototype.hasOwnProperty.call(works, id)) return;
    const brief = document.getElementById('brief-text-' + id);
    const details = document.getElementById('brief-' + id);
    const status = document.getElementById('copy-status-' + id);
    if (!brief || !details || !status) return;
    button.hidden = false;

    button.addEventListener('click', async function () {
      status.textContent = '';
      button.disabled = true;
      try {
        if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error('Clipboard unavailable');
        await navigator.clipboard.writeText(brief.textContent.trim());
        status.textContent = 'コピーしました。分かる項目を追記して、フォームでお送りください。';
        track(id, 'copy_brief');
      } catch (_) {
        details.open = true;
        status.textContent = '自動コピーができませんでした。相談メモの文面を選択してコピーしてください。';
      } finally {
        button.disabled = false;
      }
    });
  });
})();
