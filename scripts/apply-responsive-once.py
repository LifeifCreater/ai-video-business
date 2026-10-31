#!/usr/bin/env python3
"""Temporary deterministic patch; deleted before the fix PR is merged."""
from pathlib import Path
import hashlib
import re
ROOT=Path(__file__).resolve().parents[1]
HASHES=[
('404.html','e51d0f822fb8fbfb253eb470c9f88bb3c05debdd','83b8a320b60d6931f9bd8861f3ff8106d9e807d5'),
('ai-audio-processing-approval.html','08483dca77725de7443bb188d143b03a31f7b5fb','c0cddc2aadea1a2dd7e22932eaa15817e59cf6c3'),
('ai-avatar-training-video-operations.html','e51ef82db4c71a4b825ecbbcbcbe5595ce74f5ad','afaed9ddd3c1e33810eb2d570c120894da1dfccd'),
('ai-generated-insert-shot-register.html','36047cec93a18caf1c8be836ba52433cd460507f','5ccf4b1113f7e13428f658f4db19d8881bcabaf6'),
('ai-video-ad-disclosure.html','bcb949d4ca4614ea2790fc2c35b236275f958709','af6674b3c06cac0909f4d54e100023b5582bcf78'),
('ai-video-data-management.html','51b40dad376c37ffc7362de09d3bc138abdab8bc','7001781a1f5b2ff2a7eb1e1071adb164d00851cf'),
('ai-video-outsourcing-checklist.html','75b447d406313f7bfbfc0a9395553740124f4ac7','0ec668ea65fe122d71e6c188c2777da0481248ba'),
('ai-video-price.html','bbb7f73f9973dd1c94d1a15d9d7d039f844c00ca','1d67c14d77124e6beaca34dd9b9fbf1b6a3648cc'),
('ai-video-vs-traditional-video.html','ffdfaebe7a99bea4ba6a6e1cb98712aca65668f4','57cddd4d4cda9fd230cb9c274a6dd6c89fd7080e'),
('column.html','b75dbcccaf5e361873c87835bbc54267031fc46b','cf988cc0d0cdcaee4004c671c6aa70910efbca99'),
('corporate-ai-video.html','395c2813e19225e8763bc24142b584cfdc9f41bb','87d33c9881f7970f673c14c3af2b910583028484'),
('corporate-pr-video-storyboard.html','202833c410db8821b76d0742957d57b93d30d0e4','09944299e3709f4378f7d88be91d752718d877ce'),
('corporate-pr-video.html','cc1d620dbe9442a470b0a510bf79a35b21d3377a','1d5c710cdd2e359330a4fc4c12ab7f6895b8b505'),
('customer-voices.html','c9f88d024f850147f455f17d03bb96b8d8307b61','54de3c5f136634d79c9b68a28382bd16e07130d3'),
('event-video.html','01032b0feca7d2215120d9b48a2cf778ef96578d','9e21cfc0a896518bdd9b4f18456ab3b0c3151c85'),
('exhibition-video.html','ef6c46db8c2e05096374570b3405a83413d0c5cb','d4143beb676ca1e5dc15a3fa46ee8085352c8225'),
('index.html','bffe5e6cd3988fc66808762b35330dccb1592b77','c035ae73cd9be089289039489e9acadd69c2bff5'),
('multi-platform-video-production.html','cc996ff7aeab5c236d1c4ebfc7862afe50a5cbdb','4dff97aee0a156d30f9e37f274a13177841aa22a'),
('no-material-ai-video.html','74a927610a2b6ede21c73d003816dc5cdd8c44a1','c371b3e4592e293c9e484d2a887df6f44bb1c5a9'),
('operator.html','cdca0363855bcdd3c5251c056e576af36aa95ed1','2db41e0388eb7699012bb545ba7c6b56ad85b955'),
('philosophy.html','b2f95b7fa0401a4f0945a6f37bfdfb9168d626be','23ecbc9448757b85e68a838d9cba3c3ef70d7939'),
('privacy.html','a4c404b85e680f18e1a740af47505cd439d0ff22','9ad467827e3cd420c1033fb64f824d8ffb8516ae'),
('recruit-video.html','00a9d7aa3e770de58a6e5c8f236ea02e2cb15186','9fad4b1468cc8ced2b0e399e120aaed35b7d0a04'),
('training-video.html','1bc13387aa09524bbf5d23794a905b9ff8302610','3322575edad0dcb6e4951b839ee586abeab71878'),
('video-production-brief-template.html','acef0bf6ce6afa2b244a505e7df5fdeecec4acfc','b3bd46e99eb4e3e74730a760279082a6d769084b'),
('video-production-company-vs-ai-creator.html','a6287743a6287f0680a0dfdb43863828b2b78549','639fad027c9097c23e06da1ad3ff76c3f427c8a9'),
('what-is-ai-video-production.html','0b0ee1dcd15209c0be961a711111754578f6eb33','7090be8f00a04bc8c71915c8ed4f29cb20e60987'),
('youtube-shorts-thumbnail-approval.html','4095c4f0b1644a83285364b56df145783897a37c','9a44d4e8b52582f7c2158eee50ddfec36195d2a4')]
def blob(s):
 b=s.encode();return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
def visible(m):
 rule=m.group(0)
 if re.search(r'opacity\s*:\s*0\s*[;}]',rule):
  rule=re.sub(r'opacity\s*:\s*0(?=\s*[;}])','opacity:1',rule)
  rule=re.sub(r'transform\s*:\s*translateY\([^)]*\)','transform:none',rule)
 return rule
updates=[]
for name,before,after in HASHES:
 p=ROOT/name;s=p.read_text();assert blob(s)==before,(name,'source changed; refusing overwrite')
 s=re.sub(r'(?<![\w.-])\.(?:reveal|process-step)\s*\{[^}]*\}',visible,s)
 if name=='column.html':
  s=s.replace('class="section-head reveal"','class="section-head"').replace('class="article-list reveal"','class="article-list"').replace('class="article-list-note reveal"','class="article-list-note"')
 assert s.count('</head>')==1,name
 s=s.replace('</head>','<link rel="stylesheet" href="/framepact-responsive.css?v=20261031">\n</head>')
 assert blob(s)==after,(name,'patch differs from reviewed local bytes')
 updates.append((p,s))
for p,s in updates:p.write_text(s)
print('Applied 28 checksum-matched HTML changes. Body text, links and scripts unchanged.')
