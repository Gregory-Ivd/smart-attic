#!/usr/bin/env python3
"""
Переїзд портфоліо на власний домен — однією командою.

    python set-domain.py smartattic.com.ua

Що робить:
  * переписує всі абсолютні посилання (canonical, hreflang, og:url,
    JSON-LD, перемикач мов) зі старої бази на нову;
  * створює файл CNAME, який GitHub Pages читає при кожній збірці;
  * перезбирає ru/, en/, sitemap.xml і robots.txt під новий домен.

Важлива деталь: зараз сайт лежить у підпапці /smart-attic/, бо це
project page. З власним доменом він переїжджає в корінь — шлях
/smart-attic/ зникає. Тому просто дописати домен недостатньо, треба
переписати саме базу цілком, чим скрипт і займається.

Повернутися назад:
    python set-domain.py --revert
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DEFAULT_BASE = "https://gregory-ivd.github.io/smart-attic"
# Файли, у яких живуть абсолютні посилання
TOUCHED = ["index.html", "build-i18n.py"]


def current_base() -> str:
    """Читає поточну базу з build-i18n.py — там вона одна, рядком BASE."""
    text = (ROOT / "build-i18n.py").read_text(encoding="utf-8")
    m = re.search(r'^BASE = "([^"]+)"', text, re.M)
    if not m:
        sys.exit("Не знайшов рядок BASE у build-i18n.py")
    return m.group(1)


def normalise(arg: str) -> str:
    """smartattic.com.ua → https://smartattic.com.ua (без слеша в кінці)."""
    arg = arg.strip().rstrip("/")
    if not arg.startswith(("http://", "https://")):
        arg = "https://" + arg
    return arg.replace("http://", "https://", 1)


def apply(old: str, new: str) -> int:
    total = 0
    for name in TOUCHED:
        path = ROOT / name
        text = path.read_text(encoding="utf-8")
        hits = text.count(old)
        if hits:
            path.write_text(text.replace(old, new), encoding="utf-8")
            print(f"  {name}: {hits} посилань")
            total += hits
    return total


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)

    old = current_base()
    reverting = sys.argv[1] == "--revert"

    if reverting:
        new = DEFAULT_BASE
        cname = ROOT / "CNAME"
        if cname.exists():
            cname.unlink()
            print("  CNAME видалено")
    else:
        new = normalise(sys.argv[1])
        host = new.split("://", 1)[1]
        (ROOT / "CNAME").write_text(host + "\n", encoding="utf-8")
        print(f"  CNAME → {host}")

    if old == new:
        sys.exit(f"База вже {new} — нічого змінювати.")

    print(f"Переписую {old} → {new}")
    count = apply(old, new)
    if not count:
        sys.exit("Жодного посилання не знайдено — перевір, чи правильна стара база.")

    print("Перезбираю мовні версії:")
    subprocess.run([sys.executable, str(ROOT / "build-i18n.py")], check=True)

    if reverting:
        print(f"\nПовернуто на {new}. Не забудь прибрати Custom domain "
              "у Settings → Pages, якщо він там стоїть.")
        return

    print(f"""
Готово. Далі вручну:

  1. DNS у реєстратора:
     apex ({new.split('://')[1]}) → чотири A-записи:
       185.199.108.153  185.199.109.153  185.199.110.153  185.199.111.153
     www → CNAME на gregory-ivd.github.io

  2. git add -A && git commit && git push

  3. GitHub → репозиторій smart-attic → Settings → Pages:
     Custom domain = {new.split('://')[1]}, дочекатися перевірки,
     потім поставити галочку Enforce HTTPS.

  4. Google Search Console: додати новий ресурс і подати
     {new}/sitemap.xml

Старі адреси gregory-ivd.github.io/smart-attic/ GitHub перенаправить
на новий домен сам — накопичені посилання не пропадуть.
""")


if __name__ == "__main__":
    main()
