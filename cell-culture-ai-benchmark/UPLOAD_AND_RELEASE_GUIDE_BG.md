# Качване в GitHub и архивиране в Zenodo

Предвиденото име е:

```text
arcentlabs/cell-culture-ai-benchmark
```

## 1. Създай празно GitHub repository

- Owner: `arcentlabs`
- Repository name: `cell-culture-ai-benchmark`
- Visibility: `Public`
- Не добавяй нов README, `.gitignore` или license, защото вече са включени.

Ако публикуваш под личен профил, замени `arcentlabs` в `README.md`, `CITATION.cff` и `.zenodo.json` с точния GitHub username.

## 2. Качи съдържанието на папката

```bash
git init
git add .
git commit -m "Initial public benchmark release"
git branch -M main
git remote add origin https://github.com/arcentlabs/cell-culture-ai-benchmark.git
git push -u origin main
```

Не качвай ZIP файла като единствен файл. Разархивирай го и качи съдържанието на папката.

## 3. Провери CI

В GitHub отвори `Actions`. Workflow-ът `CI` трябва да стане зелен. Локално същата проверка е:

```bash
python -m pip install -r requirements-dev.txt
python verify_precomputed.py
pytest -q
```

## 4. Свържи repository-то със Zenodo

Преди да създадеш release:

1. Zenodo -> Profile -> GitHub.
2. `Sync now`.
3. Намери `cell-culture-ai-benchmark`.
4. Включи toggle-а.

## 5. Създай release `v1.0.0`

В GitHub:

- Releases -> Draft a new release
- Tag: `v1.0.0`
- Title: `v1.0.0 - First archived benchmark release`
- Копирай текста от `RELEASE_NOTES_v1.0.0.md`
- Publish release

Zenodo ще архивира точно тази версия и ще създаде DOI.

## 6. Добави DOI в preprint-а

Използвай version-specific DOI в секцията Data and Code Availability:

```text
Code, derivative public-data tables, and the exact reproducibility package for
version 1.0.0 are archived on Zenodo at https://doi.org/10.5281/zenodo.XXXXXXX.
Development continues at the associated GitHub repository.
```

След това качи нова версия на preprint-а с DOI. Не променяй вече публикувания tag `v1.0.0`; за промени създай `v1.0.1`, `v1.1.0` или `v2.0.0`.
