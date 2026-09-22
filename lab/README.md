# SC6000M / Engine OS local-library lab

Research notes and a local EAAS experiment for bridging owned audio (Bandcamp downloads, LAN shares mounted on a computer) to a Denon SC6000M via the **Engine Remote Library** path — not by emulating Dropbox or catalog streaming partners.

## How SC6000M sources differ

| Source family | Protocol | What you get |
|---|---|---|
| Beatport / Beatsource / SoundCloud / TIDAL | Embedded partner clients + Engine DJ profile login | Catalog browse/search; DRM/subscription gated |
| Dropbox | OAuth + local Engine `m.db` cache on USB/SD/SATA | Personal Engine library / files from a real Dropbox account |
| Engine Remote Library / EAAS | StageLinQ discovery + gRPC + HTTP | Computer library on the same LAN |
| USB / SD / internal drive | Local Engine Library | Packed media |

Bandcamp is **not** an Engine OS partner. Offer files you already own through EAAS or Engine DJ Desktop (or Dropbox / physical media).

Apple Music / Amazon Music need secure-boot DRM hardware; SC6000 / SC6000M are not on that list.

## Upstream projects (submodules)

```bash
git submodule update --init --recursive
```

- [lab/DenonDJ-Eaas-Server](DenonDJ-Eaas-Server) — self-hosted EAAS server (folder → Engine library)
- [lab/go-stagelinq](go-stagelinq) — StageLinQ / EAAS library, `cmd/storage` demo, `cmd/storage-discover`

Also useful (not vendored here): [honusz/stagelinq-js](https://github.com/honusz/stagelinq-js) (SC6000 captures), [chrisle/StageLinq](https://github.com/chrisle/StageLinq), [Jaxc/PyStageLinQ](https://github.com/Jaxc/PyStageLinQ), [ssabug/piratengine](https://github.com/ssabug/piratengine).

## Ports

| Port | Protocol | Role |
|---|---|---|
| 11224 | UDP | EAAS discovery beacon |
| 50010 | TCP | EAAS gRPC (`EngineLibraryService`, `NetworkTrustService`) |
| 50020 | TCP | HTTP `/ping`, `/download/...`, `/artwork/{id}` |

Docker must use **host networking** or the player never sees UDP 11224.

## Lab verification (done on this machine)

Against `sample-music/` (Genre/Artist[/Album]/Track layout):

1. Built and ran `DenonDJ-Eaas-Server` → `./storage --music-dir …/sample-music --host-ip <lan-ip>`
2. Scanned **2 tracks / 7 playlists** (Electronic + Jazz, plus Recently Added)
3. HTTP: `/ping` → 200; Windows-style download path → valid WAV
4. gRPC: `CreateTrust` granted; library id `cubi-music-library` / title `Cubi Music`; playlist tree and `SearchTracks` / `GetTrack` returned blob URLs like `<C:\…\So What.wav>`
5. Discovery: `storage-discover` saw this host advertising `grpc://…:50010` with software version `1.0.0`

**Not yet done:** confirm the SC6000M lists this host under Source → Engine DJ Desktop / remote library on the same LAN. Cue persistence back into the open-source server is still an open upstream question.

## Resume checklist (with SC6000M)

1. Same Wi-Fi or Ethernet as the player; open firewall for the ports above.
2. `cd lab/DenonDJ-Eaas-Server && go build -o storage ./cmd/storage`
3. Point `--music-dir` at owned files (or a mounted share) in Genre/Artist[/Album] layout.
4. On the player: Source → look for this computer / Cubi Music library; accept trust if prompted.
5. Load a track and confirm download/playback; note Engine OS version for firmware sensitivity.

## Sample music

Synthetic silent WAVs under `sample-music/` for layout and protocol smoke tests only — not for performance use.