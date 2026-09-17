'use strict';
const cinema=document.getElementById('cinema');
const scenes=[...document.querySelectorAll('.scene')];
const chapters=[['PROLOGUE','想像の、その先へ。'],['POSSIBILITIES','映像でできること'],['SELECTED FILMS','制作実績'],['HUMAN','私たちの想い'],['PROCESS','制作の流れ・料金'],['YOUR STORY','次の物語を、一緒に。']];
const ids=scenes.map(s=>s.id);
const prev=document.getElementById('prev-scene'),next=document.getElementById('next-scene');
const index=document.getElementById('chapter-index'),info=document.getElementById('info-dialog'),film=document.getElementById('film-dialog');
const dialogs=[index,info,film];
const ambient=document.getElementById('ambient-film'),ambientToggle=document.getElementById('ambient-toggle'),ambientLabel=document.getElementById('ambient-label');
const reduceMotion=window.matchMedia('(prefers-reduced-motion: reduce)');
let current=0,lastChange=0,wheelSum=0,wheelReset,ambientWanted=false,userChangedPlayback=false;
function showScene(n,updateHash=true){
 if(!Number.isInteger(n)||n<0||n>=scenes.length)return;
 dialogs.forEach(d=>{if(d.open)d.close()});
 current=n;lastChange=Date.now();wheelSum=0;
 scenes.forEach((s,i)=>{const active=i===n;s.classList.toggle('active',active);s.inert=!active;s.setAttribute('aria-hidden',String(!active))});
 cinema.dataset.scene=String(n);
 document.querySelectorAll('.timeline [data-go]').forEach(b=>{if(Number(b.dataset.go)===n)b.setAttribute('aria-current','step');else b.removeAttribute('aria-current')});
 document.getElementById('scene-number').textContent=String(n+1).padStart(2,'0');
 document.getElementById('chapter-kicker').textContent=chapters[n][0];document.getElementById('chapter-title').textContent=chapters[n][1];
 prev.disabled=n===0;next.disabled=n===scenes.length-1;
 if(updateHash)history.replaceState(null,'','#'+ids[n]);
 // Keep keyboard focus on the visible chapter after a scene change.
 const activeEl=document.activeElement;if(activeEl&&activeEl.closest('.scene')&&!activeEl.closest('.scene').classList.contains('active'))document.querySelector('.timeline [data-go="'+n+'"]').focus({preventScroll:true});
}
document.querySelectorAll('[data-go]').forEach(b=>b.addEventListener('click',()=>showScene(Number(b.dataset.go))));
document.querySelector('.brand').addEventListener('click',e=>{e.preventDefault();showScene(0)});
prev.addEventListener('click',()=>showScene(current-1));next.addEventListener('click',()=>showScene(current+1));
window.addEventListener('hashchange',routeHash);
window.addEventListener('keydown',e=>{if(dialogs.some(d=>d.open)||e.altKey||e.ctrlKey||e.metaKey||['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName))return;if(['ArrowRight','PageDown'].includes(e.key)){e.preventDefault();showScene(current+1)}else if(['ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();showScene(current-1)}else if(e.key==='Home'){e.preventDefault();showScene(0)}else if(e.key==='End'){e.preventDefault();showScene(5)}});
// A deliberate wheel gesture dissolves to a chapter; it never moves a long page.
cinema.addEventListener('wheel',e=>{if(dialogs.some(d=>d.open)||window.innerHeight<=530||e.ctrlKey)return;e.preventDefault();if(Date.now()-lastChange<1100)return;wheelSum+=e.deltaY*(e.deltaMode===1?16:1);clearTimeout(wheelReset);wheelReset=setTimeout(()=>{wheelSum=0},150);if(Math.abs(wheelSum)>65)showScene(current+(wheelSum>0?1:-1));},{passive:false});
let touchStart=null;
document.getElementById('story').addEventListener('touchstart',e=>{if(e.touches.length===1)touchStart={x:e.touches[0].clientX,y:e.touches[0].clientY};},{passive:true});
document.getElementById('story').addEventListener('touchend',e=>{if(!touchStart||dialogs.some(d=>d.open))return;const dx=e.changedTouches[0].clientX-touchStart.x,dy=e.changedTouches[0].clientY-touchStart.y;touchStart=null;if(Math.abs(dx)>65&&Math.abs(dx)>Math.abs(dy)*1.3)showScene(current+(dx<0?1:-1));},{passive:true});
function playbackUi(playing){cinema.classList.toggle('playing',playing);ambientToggle.setAttribute('aria-pressed',String(playing));ambientToggle.setAttribute('aria-label',playing?'背景映像を一時停止':'背景映像を再生');ambientLabel.textContent=playing?'背景映像を一時停止':'背景映像を再生';ambientToggle.querySelector('.motion-icon').textContent=playing?'Ⅱ':'▶'}
async function startAmbient(){try{ambient.muted=true;await ambient.play();if(ambientWanted&&!dialogs.some(d=>d.open))playbackUi(true);else ambient.pause();}catch{playbackUi(false)}}
ambientToggle.addEventListener('click',()=>{userChangedPlayback=true;ambientWanted=!ambientWanted;if(ambientWanted)startAmbient();else{ambient.pause();playbackUi(false)}});
ambient.addEventListener('error',()=>{ambientWanted=false;playbackUi(false);ambientLabel.textContent='背景画像を表示中';ambientToggle.disabled=true});
document.addEventListener('visibilitychange',()=>{if(document.hidden)ambient.pause();else if(ambientWanted&&!dialogs.some(d=>d.open))startAmbient()});
function openDialog(d){dialogs.forEach(other=>{if(other!==d&&other.open)other.close()});ambient.pause();d.showModal()}
dialogs.forEach(d=>{d.querySelector('.dialog-close').addEventListener('click',()=>d.close());d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close()}});d.addEventListener('close',()=>{if(d===film)document.getElementById('film-content').replaceChildren();if(ambientWanted&&!document.hidden&&!dialogs.some(x=>x.open))startAmbient()})});
document.getElementById('open-index').addEventListener('click',()=>openDialog(index));
const services=[
 ['企業PR動画','CORPORATE FILM','企業やサービスの価値を整理し、魅力が伝わるストーリーへ。誰に何を届けたいのかを一緒に考え、構成・映像生成・編集まで一貫して制作します。','corporate-pr-video.html'],
 ['採用動画','RECRUITMENT','働く人や仕事の魅力、企業が大切にしていることを映像で伝えます。応募する人が会社への理解を深められる構成をご提案します。','recruit-video.html'],
 ['研修・マニュアル動画','TRAINING & LEARNING','複雑な情報を整理し、理解しやすく、実践につながる映像に。研修や業務マニュアルなど、視聴する人の知識や目的に合わせて制作します。','training-video.html'],
 ['広告・SNS動画','ADS & SOCIAL','限られた時間の中で興味を引き、次の行動につながる映像を。伝えたいメッセージと使用する媒体に合わせて、構成やテンポを設計します。','corporate-ai-video.html'],
 ['イベント映像','EVENT & EXHIBITION','展示会やイベントで、参加者の関心を高める映像を制作します。上映シーンや伝えたい内容を伺い、場に合う見せ方をご提案します。','event-video.html'],
 ['生成AI映像制作','GENERATIVE AI','撮影素材がない状態からでも、必要な映像を生成AIで制作します。希望する表現の実現可能性を確認し、人の目で選定・編集・品質確認を行います。','no-material-ai-video.html']
];
const questions=[
 ['素材がまったくなくても制作できますか？','はい。ヒアリングした内容をもとに、必要な映像を生成AIで制作します。完成イメージが固まっていない段階でもご相談いただけます。'],
 ['どのような動画に対応していますか？','企業PR、採用、研修・マニュアル、広告・SNS、イベント映像に対応しています。そのほかの用途についても、まずはご相談ください。'],
 ['制作期間はどのくらいですか？','内容や動画尺によって異なりますが、通常はヒアリングから納品まで3〜4週間程度が目安です。お急ぎの場合は事前にご相談ください。'],
 ['修正は何回まで可能ですか？','基本プランでは2回まで対応しています。修正の範囲によっては追加費用をご相談する場合があります。'],
 ['AIで制作できない表現はありますか？','生成AIでは再現が難しい表現もあります。ご希望を伺った上で、実現可能な方法を丁寧にご提案します。'],
 ['実在人物や特定の商品を登場させられますか？','内容によって対応できる範囲が異なります。権利やガイドラインに配慮しながら、可能な表現方法をご案内します。'],
 ['機密情報や非公開の案件も相談できますか？','はい。必要に応じて秘密保持の取り決めをご相談いただけます。社内限定など、制作物の公開範囲のご希望にも対応します。'],
 ['内容が決まっていなくても相談できますか？','はい。目的や課題を伺いながら、内容を一緒に整理するところからお手伝いします。']
];
const contactUrl='https://docs.google.com/forms/d/e/1FAIpQLSeS-G-8U9p5-zMiFGaH3Y0TZjswVbvKOLl1Rg1_uK2GKw0blg/viewform';
const infoCopy={
 pricing:['料金・納期について','<p class="eyebrow">PRICING & SCHEDULE</p><p>動画の長さに応じた基本料金です。内容・生成難易度・納期に応じて、個別にお見積もりします。</p><dl class="pricing-plans"><div><dt>10秒の動画<small>Webサイトのヘッダー動画など</small></dt><dd>15万円〜</dd></div><div><dt>30秒の動画<small>企業PR・CM・SNS広告など</small></dt><dd>30万円〜</dd></div><div><dt>60秒の動画<small>実在の人物を登場させるショートムービー、社内イベント・結婚式の余興映像など</small></dt><dd>50万円〜</dd></div><div><dt>その他の尺・制作内容</dt><dd>個別お見積もり</dd></div></dl><p class="note">特殊なAI生成／フェイススワップ・人物置換／AIナレーション／AI楽曲制作／特急対応／大幅な追加修正などは、別途費用が発生する場合があります。</p><h3>制作期間と修正</h3><p>通常はヒアリングから納品まで3〜4週間程度が目安です。基本プランでは2回まで修正に対応しています。内容や尺により異なるため、詳しくはご相談ください。</p><a href="'+contactUrl+'" target="_blank" rel="noopener">無料で相談する ↗</a>'],
 founder:['創業者の想い','<p class="eyebrow">FOUNDER’S NOTE</p><h3>伝えたい想いが、素材や体制の制約で埋もれないように。</h3><p>はじめまして。FRAMEPACT創業者のよっしーです。</p><p>私の原点は、個人で始めたYouTubeでした。公開後の反応を見ながら、冒頭の見せ方や言葉の順番、映像のテンポを何度も見直す中で、同じ内容でも伝え方によって人の受け取り方が変わることを学びました。</p><p>企業の動画制作と情報発信では、誰に何を届けるのか、何を残して何を削るのかを整理し、関係者と認識を合わせながら形にする経験を重ねました。</p><p>「使える素材がない」「完成イメージを言葉にできない」。そうしたご相談に、目的や届けたい相手を一緒に整理するところから向き合います。</p><p>目指すのは、動画をつくって納品することの先。企業やサービスの想いが伝わり、見た人が「もっと知りたい」「使ってみたい」と感じる映像をつくることです。</p><h3>FRAME + IMPACT</h3><p>一つひとつの映像表現を通じて、人の心と行動を動かしたい。黄色の再生マークと、そこから走り出す人の姿には、その想いを込めています。</p>'],
 faq:['よくある質問',questions.map(([q,a])=>'<details><summary>'+q+'</summary><p>'+a+'</p></details>').join('')]
};
function showInfo(title,html){document.getElementById('info-title').textContent=title;document.getElementById('info-content').innerHTML=html;openDialog(info);info.scrollTop=0}
document.querySelectorAll('[data-service]').forEach(b=>b.addEventListener('click',()=>{const [title,en,copy,url]=services[Number(b.dataset.service)];showInfo(title,'<p class="eyebrow">'+en+'</p><p>'+copy+'</p><a href="https://framepact.jp/'+url+'" target="_blank" rel="noopener">サービスの詳細を見る ↗</a>')}));
document.querySelectorAll('[data-info]').forEach(b=>b.addEventListener('click',()=>{const [title,html]=infoCopy[b.dataset.info];showInfo(title,html)}));
const works=[{title:'FRAMEPACT 制作技術紹介',video:'https://framepact.jp/videos/framepact-showreel.mp4',description:'生成AIと映像編集を組み合わせた制作事例をまとめたショーリール。'},{title:'高級スキンケアブランド PR動画',youtube:'dlV_P4kCxRY',description:'高級スキンケアブランドを想定したポートフォリオ作品。企画から映像生成、編集、音響、仕上げまで一貫して制作。'},{title:'災害時研修動画',youtube:'dTmCFYJe3EQ',description:'地震発生から避難所運営、地域での支え合いまでを、AI映像と編集で構成した研修コンテンツ。'}];
document.querySelectorAll('[data-work]').forEach(b=>b.addEventListener('click',()=>{const w=works[Number(b.dataset.work)];document.getElementById('film-title').textContent=w.title;document.getElementById('film-description').textContent=w.description;let media;if(w.youtube){media=document.createElement('iframe');media.src='https://www.youtube-nocookie.com/embed/'+w.youtube+'?autoplay=1&rel=0';media.allow='autoplay; encrypted-media; fullscreen; picture-in-picture';media.allowFullscreen=true;media.title=w.title;document.getElementById('film-direct').href='https://youtu.be/'+w.youtube;}else{media=document.createElement('video');media.src=w.video;media.controls=true;media.autoplay=true;media.playsInline=true;document.getElementById('film-direct').href=w.video;}document.getElementById('film-content').replaceChildren(media);openDialog(film)}));
function routeHash(){const key=location.hash.slice(1),aliases={reasons:3,services:1,about:3,founder:3,price:4,faq:4};showScene(aliases[key]??Math.max(0,ids.indexOf(key)),false);if(key==='price'||key==='faq'){const [title,html]=infoCopy[key==='price'?'pricing':'faq'];showInfo(title,html);}}
routeHash();playbackUi(false);
// The supplied WebP is the first frame and remains the fallback behind the original film.
setTimeout(()=>{if(!reduceMotion.matches&&!userChangedPlayback&&!document.hidden){ambientWanted=true;if(!dialogs.some(d=>d.open))startAmbient();}},1800);
reduceMotion.addEventListener('change',e=>{if(e.matches){ambientWanted=false;ambient.pause();playbackUi(false)}});

// Delegate to include consultation links created inside dialogs.
// A click is not a completed inquiry: keep it separate from generate_lead.
document.addEventListener('click', function(event) {
  const link = event.target.closest && event.target.closest('a');
  if (!link || link.href !== contactUrl || typeof gtag !== 'function') return;
  gtag('event', 'contact_form_click', {
    source_page: 'home',
    link_url: contactUrl,
    link_text: (link.textContent || '').trim()
  });
});
