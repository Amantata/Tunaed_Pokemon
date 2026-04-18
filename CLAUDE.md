# CLAUDE.md — Project Guide (for AI Agents)

> This document defines project requirements and conventions that AI agents must follow when writing code.
> Client requirements may be added as development progresses.

---

## 1. Project Overview

- **Project name**: Tunaed_Pokemon (어장식 포켓몬)
- **Purpose**: An extended battle simulator based on the Pokémon battle system
- **Base system**: "오레마스" system (어장식 포켓몬 TRPG ruleset)

---

## 2. Client Requirements

### 2.1 Final Implementation Goals

| ID | Requirement | Status |
|----|-------------|--------|
| F-01 | Single and double battle 6v6 | Not started |
| F-02 | Online battle support | Not started |
| F-03 | **Runnable as a standalone executable (.exe etc.) with no separate installation** | Not started |
| F-04 | Compare online battle approaches (executable server vs. domain browser) and recommend | Not started |
| F-05 | Real-time spectator mode during online battles | Not started |

### 2.2 Battle Features

| ID | Requirement | Status |
|----|-------------|--------|
| B-01 | Save / load in-progress battle state | Not started |
| B-02 | Store turn history for Undo / Redo navigation | Not started |

### 2.3 Party System

| ID | Requirement | Status |
|----|-------------|--------|
| P-01 | A party consists of a trainer + party members | Not started |
| P-02 | Default 6 party members; variable 5–8 depending on context | Not started |

### 2.4 Potential System

| ID | Requirement | Status |
|----|-------------|--------|
| PT-01 | New potentials can be written as scripts within the program | Not started |
| PT-02 | Existing potentials can be selected from a list | Not started |
| PT-03 | Potentials trigger automatically during the battle processing step when conditions are met | Not started |
| PT-04 | Individual-specific potentials (계제 1–4, 속별, PT1, PT2, 전용포텐셜, 고유포텐셜) must be customizable per entity via script writing or an in-app editor | Not started |
| PT-05 | Potential naming is strict — see note below | Not started |

> **PT-05 naming rules:**
> - **고유포텐셜** (Unique Potential): A collective term for potentials uniquely held by each *trainer*. Every trainer has different 고유포텐셜.
> - **전용포텐셜** (Exclusive Potential): A particularly powerful potential held by a *Pokémon*, distinct from ordinary potentials. It is not revealed by normal encyclopedia (도감) analysis.
>
> These two categories must be implemented as separate, clearly named fields in the data model.

### 2.5 Skills and Abilities

| ID | Requirement | Status |
|----|-------------|--------|
| SK-01 | 기술 (moves) and 특성 (abilities) are selected from a pre-existing list; the list must be updatable within the program via an in-app editor (add, edit, delete entries) | Not started |

### 2.6 Interface

| ID | Requirement | Status |
|----|-------------|--------|
| UI-01 | GUI-based interface | Not started |
| UI-02 | Primary color `#34E5FF`, secondary color `#FFE66D` | Not started |
| UI-03 | Refer to provided screenshots (to be supplied) | Not started |

### 2.7 Image System

| ID | Requirement | Status |
|----|-------------|--------|
| IMG-01 | Trainers must support an assignable image (illustration) | Not started |
| IMG-02 | Party members (Pokémon) must support an assignable image | Not started |
| IMG-03 | Assigned images must be viewable in the encyclopedia, battle screen, and other relevant views | Not started |

> ⚠️ Client requirements may be added during development. Update this section and README.md whenever new requirements are added.

---

## 3. Technical Constraints and Considerations

### 3.1 Distribution
- **Required**: Single executable distribution with no installation steps
- Consider cross-platform support
- Compare server-based vs. browser-based approaches for online battle

### 3.2 Tech Stack Considerations
- GUI framework: Must support straightforward executable builds
- Online features: Real-time communication (WebSocket etc.)
- Spectator mode: Real-time state synchronization required
- Battle state serialization: Required for save/load and Undo/Redo

### 3.3 Image System Considerations
- Link and persist image files (PNG, JPG etc.) on trainer and Pokémon records
- Display contexts: encyclopedia (data viewer), battle screen, party editor
- Image file path stored in data for serialization / deserialization support
- Display a default placeholder image when no image is set

### 3.4 Potential Scripting / Editor Considerations
- Individual-specific potentials (계제 1–4, 속별, PT1, PT2, 전용포텐셜, 고유포텐셜) vary per entity — the system must allow authoring new effect logic
- Implementation options: embedded scripting language (Lua, Python etc.) or a structured in-app effect editor
- Effects authored in the editor must integrate with the automatic battle-processing trigger system (PT-03)

### 3.5 Move / Ability List Editor Considerations
- 기술 and 특성 are chosen from a master list; the master list must be editable at runtime
- In-app editor must support add, edit, and delete operations on the master lists
- Changes to master lists should persist across sessions (file-based or DB storage)

---

## 4. Game System Summary (based on docs)

> See the `docs/` directory for full rules. The sections below summarize what is most important for implementation.

### 4.1 Data Models

#### Trainer (트레이너)
- **Basic info**: name, alias (별칭), origin (출신), career (경력)
- **Image**: image file path for encyclopedia / battle screen display
- **Qualities (자질, 4 types)**: 지시, 통솔, 육성, 능력
  - Ranks: E / D / C / B / A / AA / AAA / S
  - At creation, distribute up to 34 points (or 26) across 4 qualities
  - Points needed per rank: E=0, D=2, C=4, B=6, A=10, AA=14, AAA=20, S=26
- **Command potentials (지령 포텐셜)**: 4 basic forms + mastery/deployment commands (range varies by quality rank)
- **고유포텐셜**: Potentials unique to this specific trainer — every trainer has different ones
- Detail: `docs/trainer_data_template.md`, `docs/trainer_qualities.md`

#### Pokémon (포켓몬)
- **Basic info**: name, gender, alien-species flag (아인종), type(s) (1–2), ability (특성), level
- **Image**: image file path for encyclopedia / battle screen display
- **Stats (능력치, 6 types)**: HP, Attack, Defense, Sp.Atk, Sp.Def, Speed
- **Base stat rank (종족치 랭크)**: E (1–35) to S (200+)
- **Moves (기술)**: 4–8 depending on total base stat
- **Potentials**: 역할, 분류, 주인, 이명, 계제, 속별, 유대, 선제, 회피, 내성, 격, 범용, 부수, 특권, PT, 전용
  - **전용포텐셜**: Particularly powerful potential held by a Pokémon, hidden from normal encyclopedia analysis — stored as a separate named field
- Detail: `docs/pokemon_data_template.md`

### 4.2 Core System Rules

#### Quality Effect Summary
| Quality | Role | Key Effect |
|---------|------|------------|
| 지시 | Battle command | C+1 per rank difference, determines command type/count, 타임(묘수) count |
| 통솔 | Party management | Role assignment, bond count, total base stat limit, PT potential grant |
| 육성 | Pokémon growth | Level correction, 계제 limit, 극화 eligibility, TM usage |
| 능력 | Unique/exclusive potentials | Count and strength of 고유포텐셜 / 전용포텐셜 |

#### Battle Flow (Turn Order)
1. Start-of-turn processing
2. Command input (including pre-input trainer potentials)
3. Action order determination: 가장 먼저 > 상대보다 먼저 > priority+N > speed comparison
4. Move / switch execution
5. End-of-turn processing
6. Turn-end effects: damage (status/weather etc.) → drain → recovery → switch

#### Damage Calculation Highlights
- Critical hits: Gen 5 basis; probability by C+N; ×2 (some ×3)
- STAB (Same-Type Attack Bonus) applies
- Type chart: 18-type compatibility table
- Dual-type moves: use the more favorable compatibility; both type effects apply

#### Switch System
- 임의 교대: Voluntary switch
- 통상 교대: Switch without using a move (subset of 임의 교대)
- 강제 교대: Forced random switch by opponent / field
- 추격 / 유턴: Special switch-handling rules apply

### 4.3 Potential Categories

| Category | Description | Reference |
|----------|-------------|-----------|
| 역할 | 에이스, 선발, 킬러, 어시스트, etc. | `docs/템플릿 포텐셜 목록.md` |
| 분류 | 올드 타입, 고유종, 변종, 하프, etc. | `docs/템플릿 포텐셜 목록.md` |
| 대○ | Type-weakness response set (회피/내성/격) | `docs/템플릿 포텐셜 목록.md` |
| 유대 | 영혼의 유대, 사랑의 유대, 왕의 유대 | `docs/템플릿 포텐셜 목록.md` |
| 선제 | 선의 선, 대의 선, 후의 선 | `docs/템플릿 포텐셜 목록.md` |
| 범용 | 기합, 초근성, 전투속행, etc. | `docs/템플릿 포텐셜 목록.md` |
| 특권 | 익스펜션 (per type), 계약의 특권, 주인 | `docs/템플릿 포텐셜 목록.md` |
| 전용 | Particularly powerful Pokémon-exclusive potentials; hidden from encyclopedia | Individual data sheets |
| 고유 | Trainer-unique potentials; varies per trainer | Individual trainer data |

### 4.4 Status Conditions / Status Changes

#### Status Conditions (6 + confusion)
화상, 동상, 독, 맹독, 잠듦 (max 2 active), 마비, 얼음, 혼란 (treated as both status change and status condition)

#### Status Changes (many)
가열, 충전, 냉각, 침수, 송전, 악인, 하품, 동면, 요격, 분노, 혼란, 침묵, 망각, 헤롱헤롱, 사슬묶기, 앵콜, 봉인, 도발, 트집, 분진, 죽음의 카운트, 길동무, 아쿠아링, 뿌리박기, 저주, 씨뿌리기, 불꽃속/물속/땅속/어둠속, 텔레키네시스, 꿰뚫어보기, 미라클아이, 폭탄, 마음의눈, 회복봉인, 조이기, 검은눈빛, 대타출동, 난동부리기, 변신, 미래예지

See: `docs/기본 규칙.md`, `docs/기타 시스템 처리규칙.md`

### 4.5 Item System
- No duplicates within a party (쥬얼/플레이트 allowed if different types)
- Banned items: 진화의휘석, 약점보험, 돌격조끼, 파괴의유전자, etc.
- Original items exist: 보코열매, 마쥬열매, 옐로카드, etc.
- See: `docs/소지품목록.md`, `docs/기본 규칙.md`

### 4.6 Potential Text Specification
- Standard text formats defined for condition triggers and effect triggers
- Equivalent text handling (e.g. "무시한다" = "무효화한다" = "관통한다")
- Probability tiers: 드물게 (5–15%), 저확률 (20–30%), 중확률 (40–60%), 고확률 (60%+)
- See: `docs/potential_text.md`

---

## 5. docs Directory Structure

| File | Description | Used for |
|------|-------------|----------|
| `기본 규칙.md` | Full system rules (status conditions, weather, field, making rules) | Battle engine core logic |
| `기타 시스템 처리규칙.md` | Detailed processing rules (switch, pursuit, status changes, moves, items) | Edge-case handling |
| `pokemon_data_template.md` | Pokémon data sheet template | Data model design |
| `trainer_data_template.md` | Trainer data sheet template | Data model design |
| `trainer_qualities.md` | Quality (지시/통솔/육성/능력) rank effects | Quality system implementation |
| `potential_text.md` | Potential text specification (condition/effect trigger classification) | Potential parser / engine |
| `능력랭크 대략적 기준점 및 포텐셜 목록 효과 정리.md` | Ability-rank strength benchmarks and potential effect list | Potential balancing |
| `소지품목록.md` | Full item list and effects | Item system |
| `템플릿 포텐셜 목록.md` | Full potential list: 역할/분류/대○/유대/선제/범용/특권/주인 | Potential database |
| `트레이너 예제.md` | Trainer + party creation examples | Data validation |
| `te` | Empty file (ignore) | — |

---

## 6. Suggested Implementation Priority

1. **Data models**: Define structures for trainer, Pokémon, potentials, items (including separate 고유포텐셜 / 전용포텐셜 fields)
2. **Battle engine core**: Turn progression, damage calculation, type chart, action order
3. **State management**: Status condition/change system, battle state serialization (save/load/Undo/Redo)
4. **Potential system**: Condition evaluation + automatic triggering + script / editor authoring
5. **Move & ability list editor**: In-app CRUD for 기술 and 특성 master lists (SK-01)
6. **GUI**: Battle screen, party editor, data management, encyclopedia with images
7. **Online features**: Server architecture, real-time communication, spectator mode

---

## 7. Rule Priority (on conflict)

When rules conflict between documents, apply this priority order:
1. 푸키먼 배틀용 스프레드시트
2. 참치백과 오레마스 wiki
3. Original Pokémon wiki

---

## 8. Reference Links

- 오레마스 system: https://wiki.tunaground.net/doku.php?id=오레마스_시스템
- 오레마스 world & terminology: https://wiki.tunaground.net/doku.php?id=오레마스_세계관과_용어
- 오레마스 potential list: https://wiki.tunaground.net/doku.php?id=오레마스_포텐셜일람
- 오레마스 move list: https://wiki.tunaground.net/doku.php?id=오레마스_기술
- 오레마스 ability list: https://wiki.tunaground.net/doku.php?id=오레마스_특성
