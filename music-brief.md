# 냥상(猫商) 음악 상자

게임에는 음악을 넣을 **자리(상자) 56개**만 준비되어 있어요 (1부 + 2부, 2026-10-27). 지금은 음악 파일이 하나도 없어서 조용하고, 음악 버튼도 숨어 있어요.
상자에 음악 파일을 넣으면 그 화면에서 자동으로 흘러나와요 (바뀔 때 1.5초 동안 겹쳐 바뀜, 끝없이 반복).

## 1. 음악 넣는 법

원본은 **`music-source/`** 에 상자 이름으로 모아요 (저장소에는 올라가지 않아요). 자세한 순서와 상자 이름표는 [music-source/README.md](../music-source/README.md).

```bash
# music-source/kr.wav, music-source/trial.storm.mp3 … 처럼 넣은 뒤
tools/add-music.sh
```

- 새로 넣거나 바뀐 원본만 128kbps MP3로 바꿔 `public/audio/<상자>.mp3`에 저장하고, `public/js/audio.js`의 `MUSIC_FILES`에 등록해요.
- 다운로드 폴더에서 바로: `tools/add-music.sh kr ~/Downloads/joseon.wav` (music-source/에 복사한 뒤 변환)
- 첫 음악이 들어가면 헤더와 타이틀 화면에 🔊 음악 버튼과 음량 막대가 나타나요 (설정은 이 기기에 기억).
- 어느 상자에 음악이 들었는지: 브라우저 콘솔에서 `checkMusic()`
- 필요: `ffmpeg` (`brew install ffmpeg`, 이 Mac에는 이미 있어요)

## 2. 상자 고르는 순서

화면에 맞는 상자를 앞에서부터 찾고, **음악이 들어 있는 첫 상자**를 틀어요.

1. 대화 장면 중이면 → `scene.<장면 id>` → `scene`
2. 바다의 시련 창이면 → `trial.<시련 id>` → `trial`
3. 목표 달성 창이면 → `goal.<단계>` → `goal`
4. 기본 음악 → 타이틀 화면이면 `title`, 게임 중이면 지금 도시의 지역 (1부 `kr`·`jp`·`cn`·`isle`·`southsea`·`indian` / 2부 `eu`·`atl`)

그래서 이벤트 음악을 하나도 안 넣으면 지역 음악이 계속 흐르고, `trial` 하나만 넣으면 모든 시련에서 그 음악이, `trial.storm`까지 넣으면 폭풍만 따로 나와요.

## 3. 상자 목록

### 기본 음악 (지역별)

| 상자 | 언제 | 분위기 (추천) |
|---|---|---|
| `title` | 타이틀·주인공 고르기 | 바다 건너 두 고양이가 만나는 설렘. 가야금 + 고토 이중주 |
| `kr` | 조선(한냥족) 도시 | 장터의 활기. 가야금·대금·장구, 세마치·굿거리 장단 |
| `jp` | 和猫族 땅 | 항구 마을의 맑고 단정한 느낌. 고토·샤쿠하치·작은 다이코 |
| `cn` | 명나라 땅 | 붉은 등롱의 번화한 상가. 고쟁·얼후·딱따기 |
| `isle` | 섬의 항구 대원 | 두 나라 상인이 만나는 모래톱. 고토 + 고쟁, 밝은 바닷바람 |
| `southsea` | 남쪽 바다 (동남아 항구) | 야자수와 물 위 마을, 느긋한 열대의 항구. 가믈란풍 금속 타악기·대나무 악기 |
| `indian` | 인도양 (인도·아라비아 반도·서아시아·아프리카 동쪽 바다·희망봉) | 향신료 바람, 계절풍을 기다리는 넓은 바다. 시타르·타블라풍, 우드 |
| `eu` | **2부** 유럽 20도시 (지중해·이베리아·프랑스·북해) | 운하와 항구의 시장, 류트·리코더·비올, 1600년 무렵 르네상스 춤곡 느낌 |
| `atl` | **2부** 대서양의 섬 (마데이라·카나리아·아소르스) | 무역풍이 부는 넓은 바다와 섬 항구. 기타 류·플루트·가벼운 북, 밝고 탁 트인 느낌 |

> 서쪽 바다를 나누면([west-seas-plan.md](west-seas-plan.md)) `indian` 상자를 `india`·`westasia`·`africa` 셋으로 나눌 수 있어요 (그때 다시 정리).

### 이벤트 음악

| 상자 | 언제 |
|---|---|
| `scene` | 모든 대화 장면 (장면별 상자가 비어 있을 때) |
| `scene.opening` | 서장 — 해랑, 부산포 장터 |
| `scene.openingJp` | 서장 — 나기, 하카타 |
| `scene.voyage` · `scene.voyageJp` | 1장 끝 — 바다로 가자는 제안 (해랑 / 나기) |
| `scene.tsushima` · `scene.busanJp` | 처음 바다를 건너 도착 (대마도 / 부산포) |
| `scene.hakata` · `scene.hakataJp` | 하카타의 타마 이야기 |
| `scene.envoy` | 3장 — 통신사 소식 |
| `scene.festival` | 3장 — 에도 통신사 환영 축제 |
| `scene.ming` | 4장 — 처음 명나라 땅에 |
| `scene.silverSea` | 4장 끝 — 은의 바다 |
| `scene.jeongpa` · `scene.magyo` | 무림 세력과 처음 만남 (정파 무림맹 / 야묘신교) |
| `scene.peaceCall` · `scene.peaceTea` | 두 세력의 화해와 서호 다회 |
| `scene.southSea` · `scene.monsoon` | 5장 — 남쪽 바다 도착 / 말라카의 계절풍 |
| `scene.indianOcean` | 6장 — 인도양을 건너 도착 |
| `scene.cloveguild` · `scene.nutmegguild` · `scene.spiceCall` · `scene.spiceBlend` | 5장 막간 — 향료 섬의 두 조합과 화해의 차 |
| `scene.kaskazi` · `scene.kusi` · `scene.windCall` · `scene.dhowRace` | 6~7장 막간 — 두 바람 가문과 다우선 경주 |
| `scene.cape` | 7장 — 희망봉 (1부 클라이맥스) |
| **2부** `scene.openingMc` · `scene.openingIn` | 2부 서장 — 마르코(베네치아) / 이네스(리스본) |
| `scene.voyageEu` | 1,000냥 — 배를 사서 바다로 |
| `scene.meetMc` · `scene.meetIn` | 바다 건너 친구와 처음 만남 (리스본 / 베네치아) |
| `scene.northSea` | 2-2장 — 북해의 창고 도시 암스테르담 |
| `scene.atlanticCall` | 5,000냥 — 대서양의 섬 이야기 |
| `scene.atlanticIsles` · `scene.volta` | 2-3장 — 무역풍을 배운다 / 아소르스를 도는 귀로 |
| `trial` | 모든 바다의 시련 (시련별 상자가 비어 있을 때) |
| `trial.storm` | ⛈️ 폭풍 |
| `trial.fog` | 🌫️ 안개와 암초 |
| `trial.fever` | 🤒 선원 열병 |
| `trial.pirates` | 🏴 해적선 (긴장하되 전투 음악은 아님) |
| `goal` | 목표 달성 창 (단계별 상자가 비어 있을 때) |
| `goal.0` · `goal.1` · `goal.2` | 1,000냥 / 5,000냥 / 20,000냥 달성 |

> 새 장면(`SCENES`)·시련(`TRIALS`)·목표(`GOALS`)를 만들면 그 상자도 자동으로 생겨요. 이 표에도 한 줄 더해 주세요.

## 4. 파일 규격

- 길이: 기본 음악은 **1분 30초 ~ 3분**의 반복용(끝과 처음이 자연스럽게 이어지게), 이벤트 음악은 30초 ~ 1분 반복용
- 처음 몇 초에 큰 소리가 나지 않게 (바뀔 때 겹쳐 들려요)
- 원본 형식은 WAV·MP3·M4A 아무거나
- 두 나라 음악이 똑같이 아름답게. 군악·행진곡·전투 음악 느낌은 피해요 (게임에 전투가 없어요)

## 5. 음악을 구하는 방법과 권리

| 방법 | 확인할 것 |
|---|---|
| 직접 작곡·연주 | 가장 안전해요 |
| 작곡가에게 의뢰 | 계약서에 **게임(상업 서비스) 이용·수정 권리**를 적어요 |
| AI 음악 도구 | 그 도구의 **상업 이용 약관**을 꼭 확인해요. 무료 플랜은 상업 이용이 안 되는 경우가 많아요 |
| 로열티 프리 음악 | 라이선스가 **게임 이용**을 허락하는지, 출처 표기가 필요한지 확인해요 |

- 민요(아리랑, 사쿠라사쿠라 등) 선율은 자유롭게 쓸 수 있어도, 남이 만든 편곡·녹음은 권리를 확인해요.

## 6. 진행 상황

모든 상자가 비어 있어요 (2026-10-27, 1부 46 + 2부 10 = 56개).

## 7. AI 음악 도구용 프롬프트 (복사용)

모든 프롬프트 끝에 공통으로 붙여요:
`instrumental, no vocals, seamless loop, game background music, calm enough to listen to for a long time, no war drums, no battle music`

### 꼭 필요한 10곡

| 상자 | 프롬프트 |
|---|---|
| `title` | `Gentle East Asian duet of Korean gayageum and Japanese koto with soft low strings, hopeful and tender, two friends meeting across the sea, slow 4/4, around 70 bpm` |
| `kr` | `Joseon-era Korean folk market music, gayageum and daegeum flute over janggu drum in a lilting 3-beat semachi rhythm, cheerful and friendly, pentatonic` |
| `jp` | `Early Edo-period Japanese port town, koto and shakuhachi with light taiko, clear and calm, miyako-bushi scale, slow to moderate 4/4` |
| `cn` | `Late Ming dynasty bustling merchant street with red lanterns, guzheng and erhu with wooden clappers, lively pentatonic melody, moderate 4/4` |
| `isle` | `Sunny sandbar trading port where Chinese and Japanese merchants meet, koto and guzheng together, light percussion, sea breeze, bright and relaxed` |
| `southsea` | `Relaxed Southeast Asian tropical harbor around 1610, gamelan-like metallophones and bamboo instruments, stilt houses over calm water, warm and easygoing` |
| `indian` | `Wide Indian Ocean trading winds, sitar-like and oud-like plucked strings over soft tabla-like hand drums, spice markets and waiting for the monsoon, spacious and warm` |
| `scene` | `Soft story-telling background, quiet strings with gentle gayageum and koto phrases, warm and intimate, very understated so dialogue stays clear` |
| `trial` | `Tense sea voyage, low strings and deep taiko, wind and waves, suspenseful East Asian pentatonic, not a battle, moderate tempo` |
| `goal` | `Short bright celebration jingle, festive drums and bamboo flute, cheerful East Asian pentatonic, about 30 seconds` |

### 있으면 좋은 6곡

| 상자 | 프롬프트 |
|---|---|
| `scene.opening` · `scene.openingJp` | `A story begins on a spring morning at a small harbor, gentle gayageum and koto with soft strings, hopeful and fresh` |
| `scene.festival` | `A joyful festival where Korean and Japanese musicians play together, janggu and taiko, daegeum and shakuhachi trading phrases, celebratory but graceful` |
| `scene.cape` | `Emotional finale at the end of the world's sea, sweeping strings with gayageum and koto, two friends keeping a promise at the Cape of Good Hope, wide and moving` |
| `trial.storm` | `Violent sea storm, rolling taiko and low strings, crashing waves and wind, dramatic but not a battle` |
| `trial.pirates` | `Suspicious ship approaching at dusk, sparse low strings and muted drums, tense and mysterious, no fighting` |
| `scene.dhowRace` | `Festive dhow sailing race on the Swahili coast, lively East African hand drums and clapping, bright and fun` |

### 2부 「남쪽 끝에서 만나요」 — 꼭 필요한 2곡

| 상자 | 프롬프트 |
|---|---|
| `eu` | `Bustling European harbor market around 1610, Renaissance dance music with lute, recorder and viol, light tambourine, warm and friendly, moderate 3/4 or 6/8` |
| `atl` | `Bright open Atlantic sea and small island ports under steady trade winds, Iberian guitar-like plucked strings with wooden flute and soft frame drum, airy and hopeful` |

### 2부 — 있으면 좋은 3곡

| 상자 | 프롬프트 |
|---|---|
| `scene.openingMc` · `scene.openingIn` | `A story begins in a spring canal city, gentle lute and recorder with soft strings, curious and hopeful` (같은 곡을 두 이름으로 넣어도 돼요) |
| `scene.meetMc` · `scene.meetIn` | `Two young merchants from different seas meet for the first time, warm lute and Iberian guitar duet, friendly and bright` |
| `scene.volta` | `Mid-ocean island harbor, sails drying in the wind, slow guitar and flute, nostalgic and wide, the long way home` |
