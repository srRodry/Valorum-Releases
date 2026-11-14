"""Keep the public download pages and current release in the Pixel Code identity.

Offline validation: python3 scripts/sync_presentation.py --release-json release.json
GitHub Actions: python3 scripts/sync_presentation.py --publish
Only presentation text changes; release assets, tags and update.json stay intact.
"""
import argparse
import json
import os
from pathlib import Path
import re
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REPO = "srRodry/Valorum-Releases"
BASE = f"https://github.com/{REPO}"
RAW = f"https://raw.githubusercontent.com/{REPO}/main"
BEGIN = "<!-- pixel-code:presentation:start -->"
END = "<!-- pixel-code:presentation:end -->"
DOC_BEGIN = "<!-- download:start -->"
DOC_END = "<!-- download:end -->"


def api(path, payload=None):
    token = os.environ["GH_TOKEN"]
    req = Request(
        f"https://api.github.com/repos/{REPO}/{path}",
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json", "X-GitHub-Api-Version": "2022-11-28"},
        method="PATCH" if payload is not None else "GET",
    )
    with urlopen(req, timeout=30) as response:
        return json.load(response)


def validate(feed, release):
    if release["draft"] or release["tag_name"] != feed["tag"]:
        raise ValueError("O catálogo deve apontar para um lançamento publicado.")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-beta\.[0-9]+)?", feed["version_name"]):
        raise ValueError("Versão inválida no catálogo.")
    if feed["tag"] != "v" + feed["version_name"]:
        raise ValueError("Tag e versão não correspondem.")
    asset = next((a for a in release["assets"] if a["browser_download_url"] == feed["apk_url"]), None)
    if not asset or asset["state"] != "uploaded" or not asset["name"].endswith(".apk"):
        raise ValueError("APK publicado não encontrado.")
    if not feed["apk_url"].startswith(BASE + "/releases/download/" + feed["tag"] + "/"):
        raise ValueError("O download deve pertencer ao lançamento oficial.")
    if not re.fullmatch(r"[0-9a-f]{64}", feed["sha256"]):
        raise ValueError("SHA-256 inválido.")
    if asset["digest"] != "sha256:" + feed["sha256"] or asset["size"] != feed["size_bytes"]:
        raise ValueError("O APK publicado não corresponde ao checksum ou tamanho do catálogo.")
    return asset


def download_block(feed, release, asset):
    status = "Beta de testes" if release["prerelease"] else "Versão publicada"
    checksum = next((a["browser_download_url"] for a in release["assets"]
                     if a["name"] == "SHA256SUMS.txt" and a["state"] == "uploaded"), None)
    checksum_link = f" · [Verificação SHA-256]({checksum})" if checksum else ""
    return f'''<p align="center"><a href="{feed['apk_url']}"><img src="{RAW}/assets/download-android.svg" width="300" alt="Baixar Valorum {feed['version_name']} para Android"></a></p>

<p align="center"><strong>{feed['version_name']}</strong> · {status} · Android 8.0 ou superior · {feed['size_bytes'] / 1_000_000:.1f} MB</p>

<p align="center"><a href="{release['html_url']}">Detalhes deste lançamento</a> · <a href="{feed['apk_url']}">Download direto do APK</a></p>

Distribuição pelo GitHub. A publicação na Play Store está em preparação. O repositório e os downloads são públicos; compartilhar com um grupo pequeno não restringe o acesso.

[Notas da versão]({release['html_url']}){checksum_link}

<details>
<summary>Conferir a integridade do APK</summary>

SHA-256 do arquivo `{asset['name']}`:

```text
{feed['sha256']}
```

</details>'''


def replace_download(path, block):
    text = path.read_text()
    if text.count(DOC_BEGIN) != 1 or text.count(DOC_END) != 1:
        raise ValueError(f"Marcadores de download inválidos: {path.name}")
    before, tail = text.split(DOC_BEGIN, 1)
    _, after = tail.split(DOC_END, 1)
    new_text = before + DOC_BEGIN + "\n" + block + "\n" + DOC_END + after
    if new_text != text:
        path.write_text(new_text)


def release_body(release, block):
    body = release.get("body") or ""
    if body.count(BEGIN) != body.count(END) or body.count(BEGIN) > 1:
        raise ValueError("Marcadores de apresentação inválidos no lançamento.")
    if BEGIN in body:
        prefix, tail = body.split(BEGIN, 1)
        _, suffix = tail.split(END, 1)
        notes = (prefix + suffix).strip()
    else:
        notes = body.strip()
    # Keep every existing release note outside the managed presentation block.
    header = f'''{BEGIN}
<p align="center"><img src="{RAW}/assets/pixel-code.png" width="88" alt="Pixel Code"></p>

![Valorum — Pixel Code. Seu dinheiro. Mais conquistas.]({RAW}/assets/valorum-header.svg)

{block}

**Para instalar:** baixe o APK e confirme a instalação no Android. Já usa o Valorum? Faça um backup e atualize sem desinstalar.

[Página principal]({BASE}) · [Guia de instalação]({BASE}/blob/main/docs/DOWNLOADS.md) · [Relatar problema]({BASE}/issues/new/choose) · [Suporte](mailto:pc.valorum@gmail.com)

---
{END}'''
    return header + "\n\n" + notes + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-json", type=Path)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    if args.publish == bool(args.release_json):
        parser.error("Selecione --publish ou --release-json.")
    if args.publish and os.environ.get("GITHUB_REPOSITORY") != REPO:
        raise ValueError("Publicação permitida somente no repositório oficial.")
    feed = json.loads((ROOT / "update.json").read_text())
    release = json.loads(args.release_json.read_text()) if args.release_json else api(
        "releases/tags/" + quote(feed["tag"], safe=""))
    asset = validate(feed, release)
    block = download_block(feed, release, asset)
    for relative in ("README.md", "docs/DOWNLOADS.md"):
        replace_download(ROOT / relative, block)
    body = release_body(release, block)
    if release_body({**release, "body": body}, block) != body:
        raise ValueError("A apresentação deve ser idempotente.")
    if args.publish:
        if release.get("body") != body:
            result = api(f"releases/{release['id']}", {"body": body})
            if result["body"] != body:
                raise ValueError("O GitHub não confirmou a apresentação do lançamento.")
        print("Apresentação pública sincronizada com o catálogo e o APK publicado.")
    else:
        (ROOT.parent / "release-preview.md").write_text(body)
        print("Catálogo, APK, tamanho, checksum, links e idempotência validados.")


if __name__ == "__main__":
    main()
