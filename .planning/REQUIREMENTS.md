# Requirements: Prismlab

**Defined:** 2026-03-24
**Core Value:** At any point in any game, the player knows exactly what to buy next and why -- they never feel lost on itemization.

## v2.0 Requirements

Requirements for v2.0 release. Each maps to roadmap phases.

### GSI Integration

- [x] **GSI-01**: Backend receives Dota 2 GSI HTTP POST data at `/gsi` endpoint and parses game state
- [x] **GSI-02**: Auto-detect player's hero and suggest role when game starts from GSI data
- [x] **GSI-03**: Real-time gold, GPM, and net worth tracked from GSI and displayed in sidebar
- [x] **GSI-04**: Purchased items auto-detected from GSI inventory data and marked in the timeline
- [x] **GSI-05**: Lane result (won/even/lost) auto-determined from GPM vs role benchmarks at 10 minutes

### WebSocket & Real-Time

- [x] **WS-01**: WebSocket endpoint pushes GSI state updates from backend to frontend in real-time
- [x] **WS-02**: Frontend WebSocket hook with auto-reconnect and connection status indicator (green/gray/red)
- [x] **WS-03**: Game clock from GSI displayed in the UI, synced with neutral item tier timing
- [x] **WS-04**: Live gold counter in sidebar replacing manual lane result input when GSI is active

### Auto-Refresh

- [x] **REFRESH-01**: Recommendations auto-refresh on key game events (item purchase, death, tower, Roshan, gold swing >2000g)
- [x] **REFRESH-02**: Rate limiter enforces max 1 auto-refresh per 2 minutes to control API costs
- [x] **REFRESH-03**: Auto-refresh notification toast shows reason for update (e.g., "BKB purchased -- recommendations updated")

### Screenshot Parsing

- [x] **SCREEN-01**: User can paste/upload a scoreboard screenshot and backend parses it via Claude Vision
- [x] **SCREEN-02**: Parsed results show enemy item builds (all 5 enemies) with confirmation UI before applying
- [x] **SCREEN-03**: Enemy hero identification extracted from scoreboard screenshot
- [x] **SCREEN-04**: Kill/death scores extracted from scoreboard screenshot for game state assessment

### Infrastructure

- [x] **INFRA-01**: Nginx config updated with WebSocket upgrade headers and file upload support
- [x] **INFRA-02**: GSI config file generator (gamestate_integration_prismlab.cfg) with correct server IP for user's setup

## Future Requirements

Deferred to future release. Tracked but not in current roadmap.

### Advanced Automation

- **AUTO-01**: Hotkey screen capture (ShareX-style) instead of manual paste
- **AUTO-02**: Clipboard auto-detect for new screenshots
- **AUTO-03**: Ability build suggestions (not just items)

### Mobile & Accessibility

- **MOB-01**: Mobile-responsive layout optimization
- **MOB-02**: Voice coaching / audio callouts

## Out of Scope

| Feature | Reason |
|---------|--------|
| Hotkey/clipboard screen capture | Manual paste sufficient for v2.0 -- lower complexity |
| Voice coaching | Text-only for v2.0 -- audio adds significant complexity |
| Ability build suggestions | Item-focused only -- abilities are a different domain |
| Mobile optimization | Desktop-first -- Dota 2 is a desktop game |
| User accounts / OAuth | Single-user tool, no auth needed |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| GSI-01 | Phase 10 | Complete |
| GSI-02 | Phase 11 | Complete |
| GSI-03 | Phase 11 | Complete |
| GSI-04 | Phase 11 | Complete |
| GSI-05 | Phase 12 | Complete |
| WS-01 | Phase 10 | Complete |
| WS-02 | Phase 11 | Complete |
| WS-03 | Phase 11 | Complete |
| WS-04 | Phase 11 | Complete |
| REFRESH-01 | Phase 12 | Complete |
| REFRESH-02 | Phase 12 | Complete |
| REFRESH-03 | Phase 12 | Complete |
| SCREEN-01 | Phase 13 | Complete |
| SCREEN-02 | Phase 13 | Complete |
| SCREEN-03 | Phase 13 | Complete |
| SCREEN-04 | Phase 13 | Complete |
| INFRA-01 | Phase 10 | Complete |
| INFRA-02 | Phase 10 | Complete |

**Coverage:**
- v2.0 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0

---
*Requirements defined: 2026-03-24*
*Last updated: 2026-03-24 after roadmap creation*
