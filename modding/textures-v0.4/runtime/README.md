# Runtime-проверка v0.4 (стенд, не часть мода)

Оригинальный Orion — Adobe AIR + FRESteamWorks. Standalone Flash Player не содержит AIR-классов, поэтому «голый» projector падает в `Preloader.startup()` с Error #0. Для визуальной проверки в этой среде собран **отдельный тестовый SWF**: к `Orion.mod.swf` (или оригиналу) перед `SymbolClass` добавлены DoABC-теги со стабами `flash.desktop.NativeApplication`, `flash.events.InvokeEvent`, `flash.external.ExtensionContext` и библиотека FRESteamWorks. Steam-вызовы возвращают заглушки (`AIRSteam_Init=false`), игра уходит в offline-режим и запускается.

**Важно:** `build/Orion.mod.swf` остаётся texture-only (29 заменённых image-тегов, ABC не тронут). Стабы добавляются только в тестовую копию скриптом `append_air_stub.py` и в репозиторий как готовый SWF не кладутся.

Файлы:
- `airstub/*.as` + `airstub/airstub.abc` — исходники и скомпилированный стаб (asc.jar из mozilla/shumway + playerglobal 30.0).
- `append_air_stub.py <src.swf> <dst.swf>` — вставка стабов + FRESteamWorks-library.swf перед SymbolClass.
- `xclick.py`, `xkey.py` — ввод через XTest в Xvfb :99.

Результаты (скриншоты 1280×800, контент 800×600 по центру): `../verification/runtime/`. Обрезанные 800×600 версии: `../../../pictures/previews/v0.4/`.

Замеченное: при старте в flashlog один раз пишется `TypeError #1009 at Main/init()` (mx/core-ветка, не related к текстурам); лобби, генерация мира, геймплей, HUD и инвентарь работают. Original и v0.4 снимались в разных случайных мирах, поэтому для попиксельного «до/после» используйте `pictures/previews/v0.4/terrain-before-after-v04.png`, а не runtime-скриншоты.
