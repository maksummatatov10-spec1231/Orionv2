# Runtime-проверка v0.5 (стенд, не часть мода)

Оригинальный Orion — Adobe AIR + FRESteamWorks. Для визуальной проверки в этой среде используется отдельный тестовый SWF: к `Orion.mod.swf` перед `SymbolClass` добавляются DoABC-стабы AIR/Steam и проверочный `VerifyBootstrap`.

**Важно:** `build/Orion.mod.swf` остаётся texture-only: 44 заменённых image-тега, 274/274 региона, ABC не изменён. Стабы добавляются только в тестовую копию.

Файлы:
- `airstub/` — AIR/Steam-стабы.
- `verify/VerifyBootstrap.as` + `verify.abc` — выдача руд/брони, демонстрационный ряд руд и панель стен в тестовом мире.
- `append_air_stub.py`, `append_verify.py` — сборка тестовой копии.
- `xclick.py`, `xkey.py`, `xmouse.py` — ввод через XTest.

Результаты: `../verification/runtime/` и `../../../pictures/previews/v0.5/`.
