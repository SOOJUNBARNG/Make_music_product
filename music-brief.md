
# music-source — 음악 의뢰서 · 원본 모음

게임 음악의 **원본 파일**을 모아 두는 곳이에요. 이 폴더의 음악 파일은 저장소(GitHub)에 올라가지 않아요 (`art-source/`와 같아요).
게임에는 `tools/add-music.sh`가 MP3로 바꾼 `public/audio/<상자>.mp3`만 올라가요.

**지금 상태 (2026-11-03)**: 음악 상자 **92개 중 66개**에 음악이 있어요. 10-30 이후 게임에 더해진 장면·지역 **26개가 비어 있어요** → 아래 「🆕 아직 빈 상자」.
비어 있어도 조용해지지는 않아요: 빈 장면은 `scene`, 남아메리카(`sam`)는 아메리카(`nw`), 남대서양(`satl`)은 대서양(`atl`) 음악이 나와요.
곡을 바꾸려면 같은 이름의 원본을 이 폴더에 덮어쓰고 `tools/add-music.sh`. 어느 상자가 비었는지는 브라우저 콘솔에서 `checkMusic()`.

## 🐾 모든 곡의 방향 — 지역의 소리 + 살짝 고양이

**바탕은 그 지역의 음악**이에요 (조선은 가야금, 和猫族 땅은 고토, 유럽은 류트…). 여기에 **고양이다운 감성을 한 숟가락만** 더해요. 지역색이 먼저, 고양이는 양념이에요.

| 고양이 감성        | 음악으로                                                              | 얼마나                |
| ------------------ | --------------------------------------------------------------------- | --------------------- |
| 🐾 사뿐한 발걸음   | 현을 가볍게 뜯는 소리(피치카토·가야금 뜯기)가 살금살금 걷는 리듬으로 | 곡의 바탕 리듬에 살짝 |
| 🔔 방울            | 작은 방울·풍경 소리 (나기의 방울 꼬리)                               | 한 곡에 한두 번만     |
| 😸 장난스러운 폴짝 | 살금살금 → 폴짝! 짧게 뛰어오르는 꾸밈음·장식음                      | 프레이즈 끝에 가끔    |
| 💤 그르릉          | 낮고 따뜻한 지속음(드론)이나 부드러운 저음                            | 조용한 곡의 바닥에    |
| 🌙 느긋함          | 서두르지 않는 템포, 낮잠 같은 여백                                    | 쉼터·장면 곡         |

- **진짜 고양이 울음 소리(야옹 샘플)는 넣지 않아요.** 악기로만 "고양이 같은 느낌"을 내요 (얼후·바이올린의 짧은 미끄러짐 정도는 좋아요).
- **냥상 모티프 (작곡가에게)**: 네 음의 짧은 동기 "살금-살금-살금-폴짝!" (예: 솔·라·도에 꾸밈음을 달고 높은 레로 뛰어오름). 지역마다 그 지역 악기로 한 번씩 숨겨 두면 게임 전체가 하나로 이어져요.
- 두 나라(그리고 모든 지역)의 음악을 **똑같이 아름답게**. 군악·행진곡·위협적인 소리는 피해요. 전투는 `battle` 상자뿐이고, 그것도 무섭지 않게.

## 넣는 법

1. 원본을 **상자 이름**으로 이 폴더에 넣어요. 확장자는 `wav`·`mp3`·`m4a`·`aac`·`flac`·`ogg` 아무거나.

   ```
   music-source/kr.wav
   music-source/trial.storm.mp3
   music-source/scene.opening.m4a
   ```
2. 프로젝트 폴더에서 실행해요. 새로 넣거나 바뀐 원본만 변환해서 게임에 등록해요.

   ```bash
   tools/add-music.sh
   ```

   - 다운로드 폴더에서 바로 넣을 때: `tools/add-music.sh kr ~/Downloads/joseon.wav` (이 폴더에 `kr.wav`로 복사한 뒤 변환)
3. 커밋하고 main에 push하면 사이트에 반영돼요. (Claude에게 "음악 넣었어, 배포해 줘"라고 해도 돼요.)

## ① 꼭 필요한 16곡

이 16곡이면 1부·2부의 모든 화면에 음악이 나와요. 길이는 지역 곡 1분 30초~3분, 장면·시련 30초~1분, 목표 20~40초.

### 1부 「냥해 상회」 지역 (7곡)

| 상자         | 언제                                    | 지역의 소리                                                        | 🐾 고양이 한 숟가락                                   |
| ------------ | --------------------------------------- | ------------------------------------------------------------------ | ----------------------------------------------------- |
| `title`    | 타이틀·주인공 고르기                   | 가야금 + 고토 이중주, 낮은 현악. 바다 건너 두 고양이가 만나는 설렘 | 끝부분에 방울 한 번, 두 악기가 장난치듯 주고받는 폴짝 |
| `kr`       | 조선(한냥족) 도시                       | 가야금·대금·장구, 세마치·굿거리 장단의 정겨운 장터              | 가야금 뜯기가 살금살금 걷는 발걸음처럼                |
| `jp`       | 和猫族 땅                               | 고토·샤쿠하치·작은 다이코, 맑고 단정한 항구 마을                 | 고토의 짧은 꾸밈음 폴짝, 풍경(후린) 소리 한 번        |
| `cn`       | 명나라 땅                               | 고쟁·얼후·딱따기, 붉은 등롱의 번화한 상가                        | 얼후의 짧은 미끄러짐이 "냐~" 같은 느낌으로 아주 가끔  |
| `isle`     | 섬의 항구 대원                          | 고토 + 고쟁, 가벼운 타악. 두 나라 상인이 만나는 모래톱             | 햇볕에 늘어진 고양이처럼 느긋한 템포                  |
| `southsea` | 남쪽 바다 (동남아 항구)                 | 가믈란풍 금속 타악기·대나무 악기, 물 위 마을                      | 금속 타악이 방울처럼, 낮잠 같은 여백                  |
| `indian`   | 인도양·아라비아·아프리카 동쪽·희망봉 | 시타르·우드풍 뜯는 현, 타블라풍 손북. 향신료 바람과 계절풍        | 손북이 사뿐한 발걸음, 낮은 드론이 그르릉              |

### 2부 「남쪽 끝에서 만나요」 지역 (5곡)

| 상자    | 언제                                                    | 지역의 소리                                                                     | 🐾 고양이 한 숟가락                                     |
| ------- | ------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------- |
| `eu`  | 유럽 20도시                                             | 류트·리코더·비올, 탬버린. 운하와 항구의 르네상스 춤곡 (3/4·6/8)              | 류트 피치카토 발걸음, 리코더의 폴짝                     |
| `naf` | 북아프리카 (튀니스·알렉산드리아·카이로·테투안·페스) | 우드·카눈·나이(갈대 피리), 다르부카. 흰 벽의 항구와 시장 골목                 | 다르부카가 살금살금, 작은 손방울(징글) 한 번            |
| `atl` | 대서양의 섬                                             | 기타 류·나무 피리·프레임 드럼. 무역풍이 부는 넓은 바다                        | 바람 속 방울 한 번, 바다를 바라보는 고양이처럼 느긋하게 |
| `nw`  | 아메리카 (아바나·베라크루스·멕시코시티)               | 나무 피리·흙 피리(오카리나풍)·마림바풍 나무 타악·기타 류. 카카오 장터의 햇살 | 나무 타악의 톡톡 발걸음, 피리의 짧은 폴짝               |
| `waf` | 서아프리카 (아크라·베닌)                               | 코라풍 하프·발라폰(나무 실로폰)·토킹 드럼·손뼉. 장날의 북소리와 파도         | 코라의 뜯는 소리가 사뿐한 발걸음, 작은 방울 한 번       |

### 이야기·이벤트 공통 (4곡)

| 상자       | 언제                            | 컨셉                                                                       | 🐾 고양이 한 숟가락                               |
| ---------- | ------------------------------- | -------------------------------------------------------------------------- | ------------------------------------------------- |
| `scene`  | 모든 대화 장면                  | 이야기를 듣는 차분한 분위기. 대사를 가리지 않게 작게. 현악 + 가야금·고토  | 무릎 위에서 졸듯 그르릉 저음                      |
| `trial`  | 모든 바다의 시련                | 긴장감, 하지만 싸움은 아님. 낮은 현악·다이코·바람 소리                   | 귀를 쫑긋 세운 듯한 짧은 멈춤과 숨죽임            |
| `goal`   | 목표 달성 창                    | 짧고 밝은 축하 한 마디. 북과 피리                                          | 마지막에 폴짝 + 방울 "딸랑"                       |
| `battle` | 탐험 전투 (야수·도적을 쫓아냄) | 경쾌하고 긴장된, **무섭지 않은** 놀이 같은 싸움. 빠른 타악과 뜯는 현 | 고양이가 장난감에 덤비듯 — 살금살금 노리다 폴짝! |

## 🆕 아직 빈 상자 (2026-11-03) — 26개

10-30에 66곡을 넣은 뒤 게임에 더해진 것들이에요. 위에서부터 중요해요.

### 지역 (2곡) — 그 땅에 있는 동안 계속 흘러요

| 상자     | 언제                                                                                                  | 비어 있으면 | 프롬프트 (앞에 이것 + 공통 꼬리)                                                                                                                                                                                                      |
| -------- | ----------------------------------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sam`  | 남아메리카 8도시 (카르타헤나·포르토벨로·파나마·과야킬·리마·쿠스코·레시페·사우바도르, 2부·3부) | `nw`      | `South America around 1610, Andean quena flute and siku panpipes with small charango-like strings, a hint of coastal guitar and soft maraca rattles, high mountain air and warm Pacific and Atlantic shores, light tiptoeing steps` |
| `satl` | 남대서양 (세인트헬레나 → 희망봉, 2부 2-6장)                                                          | `atl`     | `Lonely wide South Atlantic, long swells and steady wind, soft strings and a wooden flute, a small green island with a fresh spring, quiet hope before reaching the Cape`                                                           |

### 클라이맥스·엔딩 장면 (11곡) — 비어 있으면 `scene`

| 상자                                         | 언제                                                 | 프롬프트 (앞에 이것 + 공통 꼬리)                                                                                                                                                                                      |
| -------------------------------------------- | ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scene.meetCape` · `scene.meetCape2`    | 2부 끝: 희망봉에서 네 주인공이 만남 (2부 클라이맥스) | `Four cat friends from the eastern and western seas finally meet at the Cape of Good Hope, gayageum, koto, lute and Iberian guitar playing one theme together, sweeping and joyful, one small bell at the very end` |
| `scene.finale`                             | 1부 종장: 고향 항구에서 「냥해 상회」를 염           | `Opening a trading house at the home harbor after the long voyage, warm and festive gayageum and koto with soft strings, pride and gratitude`                                                                       |
| `scene.harmony` · `scene.harmony2`      | 1부·2부 에필로그: 경쟁 상회와 손잡음                | `Epilogue where former rival merchant houses join hands, gentle and generous, instruments of many seas (gayageum, koto, oud, lute, kora) taking turns on one warm melody`                                           |
| `scene.worldOpening`                       | 3부 시작: 「세계를 잇는 상회」                       | `A trading house that connects the whole world is born, a grand but friendly overture mixing East Asian and European instruments, the seas connected`                                                               |
| `scene.worldPacific`                       | 3부: 태평양을 처음 건넘                              | `Crossing the vast Pacific on a galleon for months, long swells and starry nights, marimba-like wood and koto, awe and patience`                                                                                    |
| `scene.worldEnd` · `scene.worldHarmony` | 3부 엔딩 / 종장 (희망봉에 모두 모임)                 | `Grand finale of the whole story, every regional instrument in one warm theme, the cat motif "sneak-sneak-sneak-pounce" played by each instrument in turn, one bell at the very end`                                |
| `scene.southAmerica`                       | 남아메리카에 처음                                    | `First landfall in South America, quena flute and charango with soft waves, wonder at mountains that touch the sky`                                                                                                 |
| `scene.stHelena`                           | 세인트헬레나 (편지 돌의 섬)                          | `A tiny green island in the middle of the ocean, a fresh spring and letter stones left by sailors, quiet guitar and wooden flute, tender`                                                                           |

### 세력·3부 장면 (13곡) — 비워 둬도 돼요 (`scene`이 나와요)

| 상자                                                                                          | 언제                                                                          |
| --------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `scene.qahwa` · `scene.sandledger` · `scene.newsCall` · `scene.newsLetter`         | 1부 정보상 (아덴 커피집 「바람의 귀」 / 이스파한 모래 장부회)과 화해의 소식지 |
| `scene.sealedchart` · `scene.printhouse` · `scene.chartCall` · `scene.sharedChart` | 2부 지도 공방 (리스본 봉인 해도방 / 암스테르담 인쇄소)과 함께 그린 지도       |
| `scene.sunstudio` · `scene.lampstudio` · `scene.brushCall` · `scene.twoLights`     | 2부 화실 (피렌체 햇살 화실 / 안트베르펜 등불 화실)과 두 빛의 붓               |
| `scene.worldRivals`                                                                         | 3부 시작 직후, 경쟁 상회의 편지                                               |

넣고 싶다면 짝마다 한 곡을 두 이름으로 넣어도 돼요 (예: 커피집 우드 + 페르시아 산투르 / 류트 + 하프시코드 / 류트 + 비올).

## ② 있으면 좋은 곡

중요한 순간에 따로 흐르는 음악이에요. 없으면 ①의 `scene`·`trial`·`battle`이 나와요.

| 상자                                       | 언제                                            | 컨셉                                                                                   |
| ------------------------------------------ | ----------------------------------------------- | -------------------------------------------------------------------------------------- |
| `battle.boss`                            | 우두머리 (호랑이·곰·흑곰·코끼리·표범·사자) | 크고 묵직하지만 위협적이지 않게. 큰 고양이(호랑이·사자)를 만난 작은 고양이의 두근거림 |
| `scene.opening` · `scene.openingJp`   | 1부 서장 (해랑 / 나기)                          | 이야기의 시작, 봄날의 항구 (같은 곡을 두 이름으로 넣어도 돼요)                         |
| `scene.festival`                         | 3장 에도 통신사 환영 축제                       | 두 나라 악기가 함께 연주하는 축제                                                      |
| `scene.cape`                             | 7장 희망봉 (1부 클라이맥스)                     | 바다 끝에서 지킨 약속. 가장 넓고 감동적으로, 마지막에 방울 한 번                       |
| `trial.storm` · `trial.pirates`       | 폭풍 / 해적선                                   | 거친 파도와 북소리 / 수상하고 긴장된, 싸움은 아닌 음악                                 |
| `scene.dhowRace`                         | 다우선 경주 축제                                | 스와힐리풍 북과 박수, 신나는 경주                                                      |
| `scene.openingMc` · `scene.openingIn` | 2부 서장 (마르코 / 이네스)                      | 운하·강의 봄, 류트와 리코더                                                           |
| `scene.meetMc` · `scene.meetIn`       | 2부 두 주인공의 만남                            | 류트와 이베리아 기타의 이중주                                                          |
| `scene.tianguis`                         | 2-4장 멕시코시티 장터                           | 카카오 장터의 북적임, 고양이 문양 도자기를 만나는 놀라움                               |
| `scene.goldcoast` · `scene.beninCity` | 2-5장 아크라의 장날 / 베닌 청동 장인 거리       | 토킹 드럼의 장날 / 망치와 풀무가 리듬이 되는 장인 거리                                 |

## ③ 나머지 상자 (원할 때만)

비워 두면 `scene`·`trial`·`goal` 공통 음악이 나와요.

| 상자                                                                                                                        | 언제                                                                                  |
| --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `scene.voyage` · `scene.voyageJp` · `scene.tsushima` · `scene.busanJp` · `scene.hakata` · `scene.hakataJp` | 1장 끝 ~ 2장 첫 뱃길                                                                  |
| `scene.envoy` · `scene.ming` · `scene.silverSea`                                                                    | 3장 통신사 소식 / 4장 명나라·은의 바다                                               |
| `scene.jeongpa` · `scene.magyo` · `scene.peaceCall` · `scene.peaceTea`                                           | 무림 세력과 서호 다회                                                                 |
| `scene.southSea` · `scene.monsoon` · `scene.indianOcean`                                                            | 5장 남쪽 바다·계절풍 / 6장 인도양                                                    |
| `scene.cloveguild` · `scene.nutmegguild` · `scene.spiceCall` · `scene.spiceBlend`                                | 향료 조합과 화해의 차                                                                 |
| `scene.kaskazi` · `scene.kusi` · `scene.windCall`                                                                   | 바람 가문                                                                             |
| `scene.voyageEu` · `scene.northSea` · `scene.atlanticCall` · `scene.atlanticIsles` · `scene.volta`            | 2부 첫 배 ~ 대서양의 섬                                                               |
| `scene.havana` · `scene.maghreb`                                                                                       | 2부 아바나에 처음 / 북아프리카에 처음                                                 |
| `trial.fog` · `trial.fever`                                                                                            | 안개와 암초 / 선원 열병                                                               |
| `goal.0` · `goal.1` · `goal.2`                                                                                      | 첫째·둘째·셋째 목표 달성 (1부·2부 3,000·5,000·20,000냥 / 3부 2만·10만·50만 냥) |

## 상자 고르는 순서

화면에 맞는 상자를 앞에서부터 찾고, 음악이 들어 있는 첫 상자를 틀어요.

1. 대화 장면 중 → `scene.<장면>` → `scene`
2. 바다의 시련 창 → `trial.<시련>` → `trial`
3. 탐험 전투 창 → (우두머리면 `battle.boss`) → `battle`
4. 목표 달성 창 → `goal.<단계>` → `goal`
5. 기본 음악 → 타이틀이면 `title`, 게임 중이면 지금 도시의 지역 (1부 `kr`·`jp`·`cn`·`isle`·`southsea`·`indian` / 2부 `eu`·`naf`·`atl`·`nw`·`sam`→`nw`·`waf`·`satl`→`atl` / 3부는 그 도시의 1부·2부 지역)

## 규격과 주의

- 끝과 처음이 자연스럽게 이어지는 **반복용**으로. 처음 몇 초에 큰 소리가 나지 않게 (바뀔 때 1.5초 겹쳐 들려요). `goal`만 반복하지 않는 짧은 곡이어도 돼요
- 어느 상자에 음악이 들었는지: 브라우저 콘솔에서 `checkMusic()`

## 음악을 구하는 방법과 권리

| 방법             | 확인할 것                                                                                                            |
| ---------------- | -------------------------------------------------------------------------------------------------------------------- |
| 직접 작곡·연주  | 가장 안전해요                                                                                                        |
| 작곡가에게 의뢰  | 계약서에 **게임(상업 서비스) 이용·수정 권리**를 적어요. 위의 "🐾 모든 곡의 방향"과 ① 표를 그대로 보내면 돼요 |
| AI 음악 도구     | 그 도구의 **상업 이용 약관**을 꼭 확인해요. 무료 플랜은 상업 이용이 안 되는 경우가 많아요                      |
| 로열티 프리 음악 | 라이선스가 **게임 이용**을 허락하는지, 출처 표기가 필요한지 확인해요                                           |

- 민요(아리랑, 사쿠라사쿠라 등) 선율은 자유롭게 쓸 수 있어도, 남이 만든 편곡·녹음은 권리를 확인해요.

## AI 음악 도구용 프롬프트 (복사용)

**공통 꼬리** — 모든 프롬프트 끝에 붙여요 (`battle`·`battle.boss`는 아래 전투용 꼬리):

```text
instrumental, no vocals, seamless loop, game background music, calm enough to listen to for a long time, subtle playful cat-like touches (light plucked notes like soft paw steps, a tiny bell chime once or twice, a warm low purring drone), no real cat meow sounds, no war drums, no battle music
```

전투용 꼬리:

```text
instrumental, no vocals, seamless loop, playful game battle music, energetic but friendly and not scary, cat-like pouncing rhythms (sneaky plucked notes then a sudden leap), a tiny bell accent, no real cat meow sounds, no war drums, no brass fanfare
```

### ① 꼭 필요한 16곡

| 상자         | 프롬프트 (앞에 이것 + 공통 꼬리)                                                                                                                                                                                       |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title`    | `Gentle duet of Korean gayageum and Japanese koto with soft low strings, hopeful and tender, two cat friends meeting across the sea, the two instruments playfully answering each other, slow 4/4 around 70 bpm`     |
| `kr`       | `Joseon-era Korean folk market around 1610, gayageum and daegeum flute over janggu drum in a lilting 3-beat semachi rhythm, plucked gayageum notes tiptoeing like a cat, cheerful pentatonic`                        |
| `jp`       | `Early Edo-period Japanese port town, koto and shakuhachi with light taiko, clear and calm, miyako-bushi scale, a small wind chime (furin) once, little koto grace-note leaps, moderate 4/4`                         |
| `cn`       | `Late Ming dynasty merchant street with red lanterns, guzheng and erhu with wooden clappers, lively pentatonic melody, an occasional short playful erhu slide, moderate 4/4`                                         |
| `isle`     | `Sunny sandbar trading port where Chinese and Japanese merchants meet, koto and guzheng together, light percussion, sea breeze, lazy and relaxed like a cat basking in the sun`                                      |
| `southsea` | `Relaxed Southeast Asian tropical harbor around 1610, gamelan-like metallophones and bamboo instruments, stilt houses over calm water, bell-like metal tones, unhurried like a nap in the shade`                     |
| `indian`   | `Wide Indian Ocean trading winds, sitar-like and oud-like plucked strings over soft tabla-like hand drums stepping lightly, spice markets and waiting for the monsoon, warm low drone, spacious`                     |
| `eu`       | `Bustling European harbor market around 1610, Renaissance dance music with lute, recorder and viol, light tambourine, lute pizzicato like soft paw steps, warm and friendly, 3/4 or 6/8`                             |
| `naf`      | `North African Mediterranean port and old medina around 1610, oud, qanun and ney flute over a light darbuka groove that tiptoes, white walls and blue doors, warm afternoon, a small hand-jingle once`               |
| `atl`      | `Bright open Atlantic sea and small island ports under steady trade winds, Iberian guitar-like plucked strings with wooden flute and soft frame drum, airy and hopeful, a cat watching the horizon`                  |
| `nw`       | `Sunny market of New Spain around 1610, wooden flutes and clay ocarina-like whistles, gentle marimba-like wooden percussion and guitar-like strings, cacao and maize stalls, light tapping steps, warm and friendly` |
| `waf`      | `West African coastal market town around 1610, kora-like harp and balafon wooden xylophone with talking drum and hand claps, surf in the distance, market-day joy, kora plucks like light paw steps`                 |
| `scene`    | `Soft story-telling background, quiet strings with gentle gayageum and koto phrases, warm and intimate like a cat dozing on a lap, very understated so dialogue stays clear`                                         |
| `trial`    | `Tense sea voyage, low strings and deep taiko, wind and waves, suspenseful pentatonic, short pauses like ears pricked up, not a battle, moderate tempo`                                                              |
| `goal`     | `Short bright celebration jingle, festive drums and bamboo flute, cheerful pentatonic, ends with a playful leap and a tiny bell ring, about 30 seconds, no loop needed`                                              |
| `battle`   | `Light-hearted turn-based battle in the countryside, quick plucked strings and hand drums, a cat sneaking up on a toy then pouncing, bright and brave` (전투용 꼬리)                                                 |

### ② 있으면 좋은 곡

| 상자                                       | 프롬프트                                                                                                                                                                                     |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `battle.boss`                            | `Big boss encounter with a great wild animal, deeper drums and strong strings, a small cat's pounding heart facing a big cat, brave and dramatic but never scary or violent` (전투용 꼬리) |
| `scene.opening` · `scene.openingJp`   | `A story begins on a spring morning at a small harbor, gentle gayageum and koto with soft strings, hopeful and fresh`                                                                      |
| `scene.festival`                         | `A joyful festival where Korean and Japanese musicians play together, janggu and taiko, daegeum and shakuhachi trading phrases, celebratory but graceful`                                  |
| `scene.cape`                             | `Emotional finale at the end of the sea, sweeping strings with gayageum and koto, two friends keeping a promise at the Cape of Good Hope, wide and moving, one small bell at the very end` |
| `trial.storm`                            | `Violent sea storm, rolling taiko and low strings, crashing waves and wind, dramatic but not a battle`                                                                                     |
| `trial.pirates`                          | `Suspicious ship approaching at dusk, sparse low strings and muted drums, tense and mysterious, no fighting`                                                                               |
| `scene.dhowRace`                         | `Festive dhow sailing race on the Swahili coast, lively East African hand drums and clapping, bright and fun`                                                                              |
| `scene.openingMc` · `scene.openingIn` | `A story begins in a spring canal city, gentle lute and recorder with soft strings, curious and hopeful`                                                                                   |
| `scene.meetMc` · `scene.meetIn`       | `Two young merchants from different seas meet for the first time, warm lute and Iberian guitar duet, friendly and bright`                                                                  |
| `scene.tianguis`                         | `Great open-air market by a lake in New Spain, wooden flutes and marimba-like percussion, bustling and colorful, a moment of wonder when an old crest is found`                            |
| `scene.goldcoast`                        | `Market day on a West African beach, talking drums calling the market open, balafon and hand claps, surf and joy`                                                                          |
| `scene.beninCity`                        | `Brass casters' street in a royal city, kora and soft percussion with hammer-and-bellows rhythms, admiration for fine craft, warm and dignified`                                           |
