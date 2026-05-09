# CLAUDE.md — Project Guide (for AI Agents)

> This document defines project requirements and conventions that AI agents must follow when writing code.
> Client requirements may be added as development progresses.

---

## 0. Agent Start-of-Session Checklist

**Before starting any task, agents MUST:**

1. Read `README.md` in the repository root.
2. Compare the client requirements listed in `README.md` with the requirements recorded in Section 2 of this document.
3. If any requirements in `README.md` are newer or differ from those in this document, update Section 2 of this document to match `README.md` before proceeding with the task.
4. Treat `README.md` as the single source of truth for client requirements — it is updated by the client and must always be reflected here.

> ⚠️ Never begin implementation work without first completing steps 1–3 above.

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
| B-03 | Battle must include presentation effects (animations / event visuals) | Not started |
| B-04 | Battle state must be directly editable during play to handle errors or execution mistakes | Not started |

### 2.3 Party System

| ID | Requirement | Status |
|----|-------------|--------|
| P-01 | A party consists of a trainer + party members | Not started |
| P-02 | Default 1 trainer + 6 party members; party size is variable (1–8) depending on context | Not started |

> **P-02 notes:**
> - Regardless of party size, the battle is fundamentally a 6v6 full battle; this may change depending on the trainer's 고유포텐셜.
> - Party members fill the role of "Pokémon" in a standard Pokémon game; trainers fill the "trainer" role.
> - However, since this simulation is based on the Pokémon battle system, it can also resemble a human-vs-human ability battle.

### 2.4 Potential System

| ID | Requirement | Status |
|----|-------------|--------|
| PT-01 | New potentials can be written as scripts within the program | Not started |
| PT-02 | Existing potentials can be selected from a list | Not started |
| PT-03 | Potentials trigger automatically during the battle processing step when conditions are met | Not started |
| PT-04 | Individual-specific potentials (계제 1–4, 속별, PT1, PT2, 전용포텐셜, 고유포텐셜) must be customizable per entity via script writing or an in-app editor | Not started |
| PT-05 | Potential naming is strict — see note below | Not started |
| PT-06 | Abilities (특성) and potentials are independent: effects that alter abilities do NOT affect potentials, and vice versa | Not started |

> **PT-05 naming rules:**
> - **고유포텐셜** (Unique Potential): A collective term for potentials uniquely held by each *trainer*. Every trainer has different 고유포텐셜.
> - **전용포텐셜** (Exclusive Potential): A particularly powerful potential held by a *Pokémon*, distinct from ordinary potentials. It is not revealed by normal encyclopedia (도감) analysis.
>
> These two categories must be implemented as separate, clearly named fields in the data model.
>
> **Pokémon potential name list (full):**
> 【포텐셜】 『역할』, 『분류』, 『주인』, 『이명』, 『계제 ①』, 『계제 ②』, 『계제 ③』, 『계제 ④』, 『속별』, 『유대』, 『선제』, 『회피』, 『내성』, 『○격』, 『범용』, 『부수』, 『특권』, 『PT ①』, 『PT ②』, 전용포텐셜
>
> **Potential distribution rules:**
> - All Pokémon always have: 계제①~②, 속별, 선제, 회피, 내성, 격, 범용
> - Variable (depends on party allocation and training level): 역할, 분류, 주인, 이명, 계제③~④, 유대, 부수, 특권, PT①~②

### 2.5 Skills (기술)

| ID | Requirement | Status |
|----|-------------|--------|
| SK-01 | 기술 (moves) are selected from a pre-existing list; the list must be updatable within the program via an in-app editor (add, edit, delete entries) | Not started |
| SK-02 | The 「기능확장」 potential allows use of moves not normally learnable; this feature must be supported | Not started |

### 2.6 Abilities (특성)

| ID | Requirement | Status |
|----|-------------|--------|
| SK-03 | 특성 (abilities) are selected from a pre-existing list; the list must be updatable within the program via an in-app editor (add, edit, delete entries) | Not started |
| SK-04 | Abilities (특성) can change mid-battle via moves, potentials, or other abilities | Not started |

### 2.7 Base Stats System

| ID | Requirement | Status |
|----|-------------|--------|
| ST-01 | Individual Values (개체치) exist; Effort Values (노력치) exist but default to 0 | Not started |
| ST-02 | Terminology: 「강화」 (reinforcement) = multiplier applied; 「상승」 (increase) = rank stage change — these must be strictly distinguished | Not started |

### 2.8 Field Environment System

| ID | Requirement | Status |
|----|-------------|--------|
| FE-01 | Barrier moves (Reflect, Light Screen, etc.) state management | Not started |
| FE-02 | Terrain moves (Grassy Terrain, etc.) state management | Not started |
| FE-03 | Global field moves (Trick Room, Tailwind, etc.) state management | Not started |
| FE-04 | Electric Field and other persistent field effects state management | Not started |
| FE-05 | Weather (sun, rain, sand, hail, etc.) state management | Not started |
| FE-06 | Special fields (alternate dimensions, arenas, etc.) state management | Not started |

> **Important distinction**: 《필드》 (special arena-type field, FE-06) and 「필드」 (persistent field effect, FE-04) are different concepts and must be treated separately throughout the system.

### 2.9 Interface

| ID | Requirement | Status |
|----|-------------|--------|
| UI-01 | GUI-based interface | Not started |
| UI-02 | Primary color `#34E5FF`, secondary color `#FFE66D` | Not started |
| UI-03 | Refer to provided screenshots (to be supplied) | Not started |
| UI-04 | Battle screen and party/encyclopedia editor are **completely separate application paths** from the launcher. No cross-navigation during battle. | In progress |
| UI-05 | All UI icons and decorative indicators must use **custom-designed image files** (SVG). Emoji / Unicode emoticons are prohibited. | In progress |

### 2.10 Image System

| ID | Requirement | Status |
|----|-------------|--------|
| IMG-01 | Trainers must support an assignable image (illustration) | Not started |
| IMG-02 | Party members (Pokémon) must support an assignable image | Not started |
| IMG-03 | Assigned images must be viewable in the encyclopedia, battle screen, and other relevant views | Not started |

### 2.11 Data Import / Export

| ID | Requirement | Status |
|----|-------------|--------|
| EX-01 | Party data can be imported/exported as external JSON files; multiple files must be selectable at once | In progress |
| EX-02 | Move list, ability list, and potential list must each support import/export as external JSON files | In progress |

> ⚠️ Client requirements may be added during development. Update this section and README.md whenever new requirements are added.

---

## 3. Technical Constraints and Considerations

### 3.1 Distribution
- **Required**: Single executable distribution with no installation steps
- Consider cross-platform support (Windows primary, macOS/Linux secondary)
- Compare server-based vs. browser-based approaches for online battle (see Section 9.7)

### 3.2 Recommended Tech Stack

| Layer | Recommended Technology | Rationale |
|-------|----------------------|-----------|
| Language | Python 3.11+ | Rapid development; large ecosystem; embeddable scripting |
| GUI framework | PySide6 (Qt6) | Mature; supports single-exe packaging; rich widget set |
| Packaging | PyInstaller or Nuitka | Produces `.exe` with no Python install required |
| Scripting engine | Embedded Python (`exec` sandbox) or Lua via `lupa` | For potential scripting (PT-01, PT-04) |
| Persistence | SQLite via SQLAlchemy | Zero-config embedded DB; single-file |
| Online / realtime | asyncio + websockets | Lightweight; no external broker needed |
| Serialization | JSON + dataclasses / Pydantic | Battle state save/load/Undo-Redo |

> See Section 9.7 for detailed comparison of online battle architectures.

### 3.3 Image System Considerations
- Link and persist image files (PNG, JPG etc.) on trainer and Pokémon records
- Display contexts: encyclopedia (data viewer), battle screen, party editor
- Image file path stored in data for serialization / deserialization support
- Display a default placeholder image when no image is set

### 3.4 Potential Scripting / Editor Considerations
- Individual-specific potentials (계제 1–4, 속별, PT1, PT2, 전용포텐셜, 고유포텐셜) vary per entity — the system must allow authoring new effect logic
- Implementation: sandboxed Python `exec` with a restricted API surface exposed to scripts
- Effects authored in the editor must integrate with the automatic battle-processing trigger system (PT-03)
- Abilities (특성) and potentials operate on completely separate resolution stacks (PT-06)

### 3.5 Move / Ability List Editor Considerations
- 기술 (moves) are chosen from a master list; the list must be editable at runtime (SK-01)
- 특성 (abilities) are chosen from a master list; the list must be editable at runtime (SK-03)
- In-app editor must support add, edit, and delete operations on each master list separately
- Changes to master lists should persist across sessions (SQLite storage)
- 기능확장 potential links a Pokémon entity to additional moves beyond its normal pool (SK-02)

### 3.6 Battle State & Presentation
- All mid-battle state mutations must be recorded as discrete events (event sourcing pattern)
- The event log drives both Undo/Redo (B-02) and animation playback (B-03)
- A separate "battle editor" mode exposes raw state fields for manual correction (B-04)
- Field environment states (FE-01 – FE-06) are part of the battle snapshot

### 3.7 Terminology Enforcement (ST-02)
- 강화 (reinforcement): a multiplier that directly scales a stat value (e.g. ×2) — does NOT use rank stages
- 상승 (rank increase): a rank-stage change (+1, +2, etc.) that modifies stat via the rank multiplier table
- These terms must appear consistently in code, UI labels, and data fields

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
  - Each stat has an Individual Value (개체치); Effort Values (노력치) exist but default to 0 (ST-01)
- **Base stat rank (종족치 랭크)**: E (1–35) to S (200+)
- **Moves (기술)**: 4–8 depending on total base stat; extended pool via 기능확장 potential (SK-02)
- **Ability (특성)**: selected from master list; may change mid-battle (SK-04)
- **Potentials**: 역할, 분류, 주인, 이명, 계제①~④, 속별, 유대, 선제, 회피, 내성, ○격, 범용, 부수, 특권, PT①~②, 전용포텐셜
  - All Pokémon always have: 계제①~②, 속별, 선제, 회피, 내성, 격, 범용
  - Variable by party/training: 역할, 분류, 주인, 이명, 계제③~④, 유대, 부수, 특권, PT①~②
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
- Stat 강화 (multiplier) vs. 상승 (rank stage) are resolved separately in the damage formula (ST-02)

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

1. **Data models**: Define structures for trainer, Pokémon, potentials, items (including separate 고유포텐셜 / 전용포텐셜 fields; IV/EV; 강화/상승 distinction)
2. **Battle engine core**: Turn progression, damage calculation, type chart, action order, field environment states (FE-01–FE-06)
3. **State management**: Status condition/change system, battle state serialization, Undo/Redo (B-01, B-02), battle editor mode (B-04)
4. **Potential system**: Condition evaluation + automatic triggering + script / editor authoring (PT-01 – PT-06); 기능확장 support (SK-02)
5. **Move & ability list editor**: In-app CRUD for 기술 master list (SK-01) and 특성 master list (SK-03); ability mid-battle change (SK-04)
6. **GUI + Presentation**: Battle screen, party editor, data management, encyclopedia with images (UI-01 – UI-03, IMG-01 – IMG-03); animation/event system (B-03)
7. **Online features**: Server architecture, real-time communication, spectator mode (F-02, F-04, F-05)
8. **Packaging**: Single-executable build pipeline (F-03)

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

---

## 9. Architecture Design

> This section describes how the program is structured to satisfy all client requirements. Each layer maps to one or more requirement IDs.

### 9.1 Layer Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Packaging Layer (F-03)                                     │
│  PyInstaller / Nuitka → single .exe, no install required    │
├─────────────────────────────────────────────────────────────┤
│  Online Layer (F-02, F-04, F-05)                            │
│  asyncio + websockets — battle sync & spectator broadcast   │
├─────────────────────────────────────────────────────────────┤
│  Interface Layer (UI-01–03, IMG-01–03, B-03, B-04)          │
│  PySide6 GUI — screens: Battle / Party Editor /             │
│  Encyclopedia / Battle Editor / Online Lobby                │
│  Presentation Engine — event-driven animation player        │
├─────────────────────────────────────────────────────────────┤
│  Application Layer                                          │
│  Use-case orchestration: start battle, process turn,        │
│  save/load, undo/redo, connect online, enter edit mode      │
├──────────────────────────┬──────────────────────────────────┤
│  Domain Layer            │  Script / Editor Layer           │
│  Battle Engine           │  (PT-01, PT-04, SK-01, SK-02)   │
│  Effect Engine           │  Potential Script Sandbox        │
│  Rule Modules            │  (sandboxed Python exec + API)   │
│  Integrity Rules         │  Move / Ability List Editor      │
│                          │  기능확장 Move Pool Manager      │
├──────────────────────────┴──────────────────────────────────┤
│  Data Layer                                                 │
│  Master Data (SQLite): 기술 / 특성 / 아이템 / 포텐셜 템플릿  │
│  Runtime State (JSON): battle snapshot, turn history        │
│  Asset Metadata: image paths + default placeholder          │
└─────────────────────────────────────────────────────────────┘
```

### 9.2 Domain Layer — Submodule Breakdown

#### Battle Engine
Responsible for turn lifecycle. Satisfies: F-01, B-01, B-02, B-03, B-04.

```
BattleEngine
├── TurnPipeline          # 6-step turn execution (start → command → order → action → end → effects)
├── ActionOrderResolver   # 가장 먼저 / 상대보다 먼저 / priority+N / speed
├── SwitchResolver        # 임의 / 통상 / 강제 / 추격 / 유턴
├── EventBus              # Emits BattleEvent objects consumed by GUI, Undo stack, and animation player
└── BattleStateSnapshot   # Serializable full state (JSON); used for save/load, Undo/Redo, edit mode
```

#### Effect Engine
Resolves all effects in a unified pipeline. Satisfies: PT-03, PT-06, SK-02, SK-04, FE-01–FE-06.

```
EffectEngine
├── EffectResolver        # Ordered resolution: ability effects → potential effects (separate stacks, PT-06)
├── DamageCalculator      # Applies 강화 (multiplier) then 상승 (rank stage) correctly (ST-02)
├── StatusEngine          # Manages status conditions and status changes
├── FieldStateManager     # Tracks weather, terrain, barriers, global effects (FE-01–FE-06)
└── AbilityChangeHandler  # Handles mid-battle ability changes (SK-04)
```

#### Rule Modules
```
RuleModules
├── TypeChart             # 18-type effectiveness table
├── CriticalHitCalc       # Gen-5 basis; C+N probability tiers
├── StatCalc              # HP / stat formula with IV/EV (ST-01); 강화 vs 상승 (ST-02)
├── MoveValidator         # Checks learnable pool + 기능확장 extended pool (SK-02)
└── ItemValidator         # Banned-item check; duplicate-within-party check
```

#### Integrity Rules
```
IntegrityRules
├── PartyConstraints      # 5–8 members (P-02); item uniqueness
├── PotentialAbilityWall  # Enforces PT-06: blocks cross-influence between ability & potential stacks
└── NamingEnforcer        # Ensures 고유포텐셜 / 전용포텐셜 fields are never confused
```

### 9.3 Data Layer — Schema Summary

#### Master Tables (SQLite, persistent)
| Table | Key Columns | Notes |
|-------|-------------|-------|
| `moves` | id, name, type, category, power, accuracy, pp, effect_script | SK-01 CRUD |
| `abilities` | id, name, effect_description, effect_script | SK-03 CRUD |
| `items` | id, name, effect, banned | includes original items |
| `potential_templates` | id, category, name, trigger_text, effect_text | PT-02 selection list |

#### Entity Tables (SQLite, persistent)
| Table | Key Columns | Notes |
|-------|-------------|-------|
| `trainers` | id, name, alias, origin, career, image_path, qualities_json, innate_potentials_json | 고유포텐셜 as JSON array |
| `pokemon` | id, species, name, gender, is_alien, type1, type2, ability_id, level, iv_json, ev_json, image_path, moves_json, potentials_json, exclusive_potential_json | 전용포텐셜 as separate JSON field |
| `parties` | id, trainer_id, member_ids_json, max_size | P-01, P-02 |

#### Runtime State (JSON files)
| File | Contents | Notes |
|------|----------|-------|
| `battle_save.json` | Full BattleStateSnapshot | B-01 |
| `turn_history.json` | Ordered list of BattleStateSnapshot per turn | B-02 Undo/Redo |
| `event_log.json` | Ordered list of BattleEvent per turn | B-03 animation replay |

### 9.4 Script / Editor Layer

#### Potential Script Sandbox
- Each potential effect is stored as a Python snippet
- At runtime, snippets execute inside a restricted namespace exposing only the `BattleAPI` object
- `BattleAPI` provides read/write access to battle state through typed methods (no arbitrary imports)
- The in-app editor provides syntax highlighting and a "Test Trigger" button

#### Move / Ability List Editor
- Full CRUD UI over the `moves` and `abilities` SQLite tables
- Changes take effect immediately (no restart required)
- 기능확장 move pool: a join table `pokemon_extended_moves(pokemon_id, move_id)` populated when the potential is assigned (SK-02)

### 9.5 Interface Layer — Screen Map

| Screen | Purpose | Key Requirements |
|--------|---------|-----------------|
| Battle Screen | Turn-by-turn battle view with animation | F-01, B-03, UI-01–03 |
| Battle Editor | Direct field editing overlay (HP, status, field state) | B-04 |
| Party Editor | Build / edit trainer + Pokémon party | P-01, P-02, IMG-01, IMG-02 |
| Encyclopedia | Browse trainer / Pokémon data; shows images | IMG-03 |
| Potential Editor | Script / structured editor for potentials | PT-01, PT-04 |
| Move/Ability Editor | CRUD list editor for 기술 and 특성 master data | SK-01, SK-03 |
| Online Lobby | Create / join battle room, spectate | F-02, F-05 |

**Color tokens** (applied globally via Qt stylesheet):
- `--color-primary: #34E5FF`
- `--color-secondary: #FFE66D`

### 9.6 Presentation Engine (B-03)

- Subscribes to `EventBus` events emitted by `BattleEngine`
- Each `BattleEvent` type maps to one or more animation sequences (move hit, status applied, Pokémon faint, switch, etc.)
- Animations are non-blocking: the battle engine queues events; the GUI plays them sequentially
- Replaying from `event_log.json` supports battle replay after the fact

### 9.7 Online Architecture Comparison (F-04)

| Approach | Description | Pros | Cons |
|----------|-------------|------|------|
| **A. Embedded Server (recommended)** | One player's exe acts as host; both players run the same exe; host runs a local WebSocket server | No external infrastructure; fits F-03 (single exe); works on LAN or via port-forward/VPN | Requires network configuration (port forwarding / IP sharing) for internet play |
| **B. Domain Browser** | Dedicated web server hosts battle logic; players connect via browser | No exe required for clients; easier internet access | Requires always-on server with domain/hosting costs; does not satisfy F-03 for offline use |

**Recommendation**: Approach A (Embedded Server) for the initial release to satisfy F-03. Approach B may be offered as a future add-on.

Implementation detail for Approach A:
- Host exe starts `asyncio` WebSocket server on a configurable port
- Guest exe connects as client
- Spectators connect as read-only clients receiving `BattleEvent` broadcasts (F-05)
- Battle state sync uses the same `BattleStateSnapshot` JSON format

### 9.8 Packaging (F-03)

- Build tool: **PyInstaller** (simpler) or **Nuitka** (smaller / faster exe)
- All assets (images, SQLite DB, default data) bundled into the exe via `--add-data`
- On first run, write-able data (user saves, edited master lists) is copied to `%APPDATA%/TunaedPokemon/` so the exe itself remains read-only
- CI pipeline produces Windows `.exe`; macOS `.app` and Linux binary are stretch goals
