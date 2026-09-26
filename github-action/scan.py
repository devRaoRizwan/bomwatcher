#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import tomllib
import uuid
from datetime import UTC, datetime

TOOL_VERSION = "0.1.0"

SKIP_DIRS = {
    ".git", "node_modules", "venv", ".venv", "env", "__pycache__", "dist", "build", ".next", "out",
    "vendor", "site-packages", ".tox", ".mypy_cache", "coverage", "target", ".idea", ".vscode",
}
SOURCE_EXT = {
    ".py", ".ipynb", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".go", ".rb", ".java", ".kt",
    ".cs", ".php", ".rs", ".swift", ".yaml", ".yml", ".toml", ".json", ".env.example",
}
MAX_FILE_BYTES = 1_000_000


PROVIDERS = {
    "Anthropic": {
        "model": re.compile(r"^claude-(\d|instant|opus|sonnet|haiku)[a-z0-9.\-]*$"),
        "sdk": re.compile(r"(\bimport anthropic\b|\bfrom anthropic\b|@anthropic-ai/sdk|anthropic-sdk-go|\bAnthropic\()"),
        "endpoint": "https://api.anthropic.com",
    },
    "OpenAI": {
        "model": re.compile(
            r"^(gpt-(\d|oss-)[\w.\-]*|chatgpt-[\w.\-]+|o[134](-mini|-pro|-preview)?(-\d{4}-\d{2}-\d{2})?"
            r"|text-embedding-(3-small|3-large|ada-002)|dall-e-[23]|gpt-image-[\w.\-]+|whisper-1|tts-1(-hd)?)$"
        ),
        "sdk": re.compile(r"(\bimport openai\b|\bfrom openai\b|['\"]openai['\"]|\bOpenAI\(|langchain_openai)"),
        "endpoint": "https://api.openai.com",
    },
    "Google": {
        "model": re.compile(r"^(gemini-(\d|pro|ultra|flash|nano|embedding)[\w.\-]*|text-embedding-00\d|imagen-[\w.\-]+)$"),
        "sdk": re.compile(r"(google\.generativeai|google\.genai|@google/genai|@google/generative-ai|vertexai)"),
        "endpoint": "https://generativelanguage.googleapis.com",
    },
    "Mistral": {
        "model": re.compile(r"^(mistral|mixtral|codestral|ministral|pixtral|magistral)-[\w.\-]+$"),
        "sdk": re.compile(r"(\bmistralai\b|@mistralai/)"),
        "endpoint": "https://api.mistral.ai",
    },
    "Cohere": {
        "model": re.compile(r"^(command-[\w.\-]+|embed-(english|multilingual)-[\w.\-]+|rerank-[\w.\-]+)$"),
        "sdk": re.compile(r"(\bimport cohere\b|\bfrom cohere\b|cohere-ai)"),
        "endpoint": "https://api.cohere.com",
    },
}

STRING_LITERAL = re.compile(r"""["'`]([A-Za-z0-9][\w.\-/:]{2,120})["'`]""")

HF_LOADERS = re.compile(
    r"""(?:from_pretrained|SentenceTransformer|CrossEncoder|hf_hub_download|snapshot_download|AutoModel\w*\.from_pretrained)"""
    r"""\s*\(\s*(?:repo_id\s*=\s*|model_name_or_path\s*=\s*)?["']([\w.\-]+/[\w.\-]+)["']"""
)
HF_PIPELINE = re.compile(r"""pipeline\s*\(\s*(?:task\s*=\s*)?["']([\w\-]+)["'][^)]*?model\s*=\s*["']([\w.\-]+/[\w.\-]+)["']""", re.S)


def infer_task(provider: str, name: str) -> str:
    n = name.lower()
    if "embed" in n:
        return "feature-extraction"
    if n.startswith("rerank"):
        return "text-ranking"
    if n.startswith("whisper"):
        return "automatic-speech-recognition"
    if n.startswith(("dall-e", "gpt-image", "imagen")):
        return "text-to-image"
    if n.startswith("tts"):
        return "text-to-speech"
    return "text-generation"


def iter_source_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".") or d == ".github"]
        for f in filenames:
            path = os.path.join(dirpath, f)
            if os.path.splitext(f)[1] not in SOURCE_EXT or f in ("package-lock.json", "yarn.lock", "pnpm-lock.yaml"):
                continue
            try:
                if os.path.getsize(path) <= MAX_FILE_BYTES:
                    yield path
            except OSError:
                continue


def detect_models(root: str):
    models: dict[str, dict] = {}
    sdk_used: set[str] = set()

    def add(key, name, provider, hosting, task, rel, line, hf=False):
        m = models.setdefault(key, {"name": name, "provider": provider, "hosting": hosting, "task": task, "hf": hf, "occurrences": []})
        if len(m["occurrences"]) < 20:
            m["occurrences"].append({"location": rel, "line": line})

    for path in iter_source_files(root):
        try:
            with open(path, encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
        except OSError:
            continue
        rel = os.path.relpath(path, root)

        for provider, spec in PROVIDERS.items():
            if spec["sdk"].search(text):
                sdk_used.add(provider)

        for lineno, line in enumerate(text.splitlines(), 1):
            for lit in STRING_LITERAL.findall(line):
                for provider, spec in PROVIDERS.items():
                    if spec["model"].match(lit):
                        add(f"{provider}:{lit}", lit, provider, "API", infer_task(provider, lit), rel, lineno)
                        break

        for m in HF_PIPELINE.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            add(f"hf:{m.group(2)}", m.group(2), "Hugging Face", "Self-hosted", m.group(1), rel, line, hf=True)
        for m in HF_LOADERS.finditer(text):
            name = m.group(1)
            line = text.count("\n", 0, m.start()) + 1
            task = "feature-extraction" if "SentenceTransformer" in m.group(0) else None
            key = f"hf:{name}"
            if key in models:
                models[key]["occurrences"].append({"location": rel, "line": line})
            else:
                add(key, name, "Hugging Face", "Self-hosted", task, rel, line, hf=True)

    return list(models.values()), sdk_used


def model_component(m: dict) -> dict:
    first = m["occurrences"][0]
    if m["hf"]:
        ref = f"pkg:huggingface/{m['name']}"
    else:
        ref = f"model:{m['provider'].lower().replace(' ', '-')}/{m['name']}"
    comp = {
        "type": "machine-learning-model",
        "bom-ref": ref,
        "name": m["name"],
        "supplier": {"name": m["provider"]},
        "properties": [
            {"name": "bomwatcher:hosting", "value": m["hosting"]},
            {"name": "bomwatcher:detectedVia", "value": f"{first['location']}:{first['line']}"},
        ],
        "evidence": {"occurrences": m["occurrences"]},
    }
    if m["hf"]:
        comp["purl"] = ref
    if m["task"]:
        comp["modelCard"] = {"modelParameters": {"task": m["task"]}}
    return comp


def norm_py(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


REQ_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._\-]*)")


def direct_dependencies(root: str) -> dict[str, set[str]]:
    direct: dict[str, set[str]] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for f in filenames:
            path = os.path.join(dirpath, f)
            try:
                if re.match(r"requirements.*\.txt$", f):
                    with open(path, encoding="utf-8", errors="ignore") as fh:
                        for line in fh:
                            line = line.split("#")[0].strip()
                            if line and not line.startswith("-"):
                                m = REQ_NAME.match(line)
                                if m:
                                    direct.setdefault("pypi", set()).add(norm_py(m.group(1)))
                elif f == "pyproject.toml":
                    with open(path, "rb") as fh:
                        data = tomllib.load(fh)
                    deps = list(data.get("project", {}).get("dependencies", []))
                    for group in data.get("project", {}).get("optional-dependencies", {}).values():
                        deps.extend(group)
                    deps.extend(k for k in data.get("tool", {}).get("poetry", {}).get("dependencies", {}) if k != "python")
                    for d in deps:
                        m = REQ_NAME.match(d)
                        if m:
                            direct.setdefault("pypi", set()).add(norm_py(m.group(1)))
                elif f == "package.json":
                    with open(path, encoding="utf-8") as fh:
                        data = json.load(fh)
                    for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
                        direct.setdefault("npm", set()).update((data.get(key) or {}).keys())
                elif f == "go.mod":
                    with open(path, encoding="utf-8") as fh:
                        for line in fh:
                            line = line.strip()
                            if "// indirect" in line:
                                continue
                            m = re.match(r"^(?:require\s+)?([\w.\-]+\.[\w]+/[\w.\-/]+)\s+v", line)
                            if m:
                                direct.setdefault("golang", set()).add(m.group(1))
            except (OSError, ValueError, UnicodeDecodeError):
                continue
    return direct


def purl_parts(purl: str):
    m = re.match(r"^pkg:([^/]+)/(.+?)@", purl or "")
    if not m:
        return None, None
    from urllib.parse import unquote
    return m.group(1), unquote(m.group(2))


def library_components(deps_bom: dict, direct: dict[str, set[str]]) -> list[dict]:
    out, seen = [], set()
    for c in deps_bom.get("components", []):
        if c.get("type") not in ("library", "framework"):
            continue
        purl = c.get("purl")
        key = purl or f"{c.get('name')}@{c.get('version')}"
        if key in seen:
            continue
        seen.add(key)
        comp = {"type": "library", "bom-ref": key, "name": c.get("name"), "version": c.get("version")}
        if c.get("group"):
            comp["group"] = c["group"]
        if purl:
            comp["purl"] = purl
        if c.get("licenses"):
            comp["licenses"] = c["licenses"]
        eco, name = purl_parts(purl)
        if eco in direct:
            n = norm_py(name.split("/")[-1]) if eco == "pypi" else name
            comp["scope"] = "required" if n in direct[eco] else "optional"
        out.append(comp)
    return out


def build(args) -> dict:
    deps_bom = {}
    if args.deps and os.path.exists(args.deps):
        with open(args.deps, encoding="utf-8") as fh:
            deps_bom = json.load(fh)
    else:
        print(f"bomwatcher: no dependency BOM at {args.deps!r}; emitting AI models only", file=sys.stderr)

    libraries = library_components(deps_bom, direct_dependencies(args.path))
    found, sdk_used = detect_models(args.path)
    models = [model_component(m) for m in sorted(found, key=lambda m: (m["provider"], m["name"]))]

    providers = sdk_used | {m["provider"] for m in found if m["hosting"] == "API"}
    services = [
        {
            "bom-ref": f"svc:{p.lower()}",
            "name": f"{p} API",
            "provider": {"name": p},
            "endpoints": [PROVIDERS[p]["endpoint"]],
        }
        for p in sorted(providers) if p in PROVIDERS
    ]

    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tools": {"components": [{"type": "application", "name": "bomwatcher-scan", "version": TOOL_VERSION}]},
            "component": {
                "type": "application",
                "bom-ref": f"repo:{args.name}",
                "name": args.name,
                "properties": [{"name": "git:commit", "value": args.commit}] if args.commit else [],
            },
        },
        "components": libraries + models,
        "services": services,
    }


def main():
    p = argparse.ArgumentParser(description="Generate a CycloneDX AI-BOM")
    p.add_argument("--path", default=".")
    p.add_argument("--deps", help="Syft CycloneDX JSON output")
    p.add_argument("--name", default=os.path.basename(os.path.abspath(".")))
    p.add_argument("--commit", default=os.environ.get("GITHUB_SHA", ""))
    p.add_argument("--out", default="bom.cdx.json")
    args = p.parse_args()

    bom = build(args)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(bom, fh, indent=2)

    n_lib = sum(1 for c in bom["components"] if c["type"] == "library")
    n_mod = sum(1 for c in bom["components"] if c["type"] == "machine-learning-model")
    print(f"bomwatcher: {n_lib} libraries, {n_mod} AI models, {len(bom['services'])} services -> {args.out}")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write(
                "### BOMWatcher AI-BOM\n\n| Libraries | AI models | AI services |\n|---|---|---|\n"
                f"| {n_lib} | {n_mod} | {len(bom['services'])} |\n"
            )


if __name__ == "__main__":
    main()
