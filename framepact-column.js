/* No fetch, no tracking: HTML links remain readable if this script cannot run. */
(function () {
 'use strict';
 function initColumn(){
 var root=document.getElementById('article-list');
 if(!root)return;
 var cards=Array.from(root.querySelectorAll('.article-card'));
 var tools=root.querySelector('[data-column-controls]');
 var search=document.getElementById('column-search');
 var category=document.getElementById('column-category');
 var reset=document.getElementById('column-reset');
 var status=document.getElementById('column-status');
 var more=root.querySelector('[data-column-more]');
 var next=document.getElementById('column-next');
 var all=document.getElementById('column-all');
 var empty=document.getElementById('column-empty');
 if(!cards.length||!tools||!search||!category||!reset||!status||!more||!next||!all||!empty)return;
 var step=6, limit=step, matches=[];
 function normalize(s){return s.normalize('NFKC').toLocaleLowerCase().trim();}
 function fallback(){cards.forEach(function(c){c.hidden=false;});tools.hidden=true;more.hidden=true;empty.hidden=true;status.textContent='全'+cards.length+'記事｜新しい順';}
 function save(){try{var u=new URL(location.href);[['q',search.value.trim()],['category',category.value],['show',limit>step?String(limit):'']].forEach(function(p){if(p[1])u.searchParams.set(p[0],p[1]);else u.searchParams.delete(p[0]);});history.replaceState(null,'',u);}catch(e){/* A blocked history API must not hide content. */}}
 function render(persist){
  var words=normalize(search.value).split(/\s+/).filter(Boolean);
  matches=cards.filter(function(c){var text=normalize(c.textContent);return (!category.value||c.dataset.category===category.value)&&words.every(function(w){return text.includes(w);});});
  cards.forEach(function(c){c.hidden=true;});
  matches.slice(0,limit).forEach(function(c){c.hidden=false;});
  var shown=Math.min(limit,matches.length),remaining=matches.length-shown;
  status.textContent=matches.length+'件中'+shown+'件を表示｜新しい順';
  empty.hidden=matches.length!==0;more.hidden=remaining===0;reset.hidden=!search.value&&!category.value;
  next.textContent='さらに'+Math.min(step,remaining)+'件を見る（残り'+remaining+'件）';
  if(persist)save();
 }
 function guarded(fn){return function(){try{fn();}catch(e){fallback();}};}
 try{
  var params=new URL(location.href).searchParams;
  search.value=params.get('q')||'';
  var value=params.get('category')||'';
  if(Array.from(category.options).some(function(o){return o.value===value;}))category.value=value;
  var requested=Number(params.get('show'));
  if(Number.isFinite(requested)&&requested>=step)limit=Math.min(cards.length,Math.floor(requested));
  search.addEventListener('input',guarded(function(){limit=step;render(true);}));
  category.addEventListener('change',guarded(function(){limit=step;render(true);}));
  reset.addEventListener('click',guarded(function(){search.value='';category.value='';limit=step;render(true);search.focus();}));
  function expand(showAll){var first=limit;limit=showAll?cards.length:limit+step;render(true);if(matches[first])matches[first].focus({preventScroll:true});}
  next.addEventListener('click',guarded(function(){expand(false);}));
  all.addEventListener('click',guarded(function(){expand(true);}));
  tools.hidden=false;render(false);
 }catch(e){fallback();}
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initColumn,{once:true});else initColumn();
})();
