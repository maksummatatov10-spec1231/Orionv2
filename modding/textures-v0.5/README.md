# Orion textures v0.5

Texture-only сборка по фидбеку:

1. Деревья — оранжевая дубовая кора, единая для ствола/веток/оснований крон.
2. Все руды — фон из принятой каменной текстуры + оригинальные минеральные вкрапления.
3. Сохранены правки v0.4: трава, стены, броня, мебель, иконки, частицы.

Сборка:

```bash
PYTHONPATH=/tmp/orionpy python3 modding/textures-v0.5/scripts/extract_v05.py
PYTHONPATH=/tmp/orionpy python3 modding/textures-v0.5/scripts/process_v05.py
PYTHONPATH=/tmp/orionpy python3 modding/textures-v0.5/scripts/build_swf_v05.py \
  --input '/tmp/orion-work/Orion Sandbox Enhanced/Orion.swf' \
  --output modding/textures-v0.5/build/Orion.mod.swf
```

Проверка: `verification/swf-build.json`, `verification/fixes-v05.json`, `verification/runtime/`.
