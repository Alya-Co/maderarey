#!/usr/bin/env python3
"""
build_3d_models.py — готовит 3D-модели домов для просмотра на сайте.

Что делает:
  Для каждой папки houses/<дом>/, где лежит файл .ifc (выгрузка из CabinPlanner),
  создаёт рядом файл model3d.json — облегчённую 3D-модель для viewer3d.js.

Что НЕ делает:
  Не меняет data.json, фото и любые другие файлы. Только создаёт/обновляет model3d.json.

Запуск (из папки проекта):
  python3 build_3d_models.py            — все дома, где есть .ifc
  python3 build_3d_models.py takoma-58-12x8   — один дом
"""
import json, os, re, sys

HOUSES = "houses"
KINDS = ("IFCWALL", "IFCROOF", "IFCBEAM", "IFCWINDOW", "IFCDOOR", "IFCBUILDINGELEMENTPROXY", "IFCSLAB")


def parse_ifc(path):
    src = open(path, encoding="utf-8", errors="replace").read()
    ents = {}
    for m in re.finditer(r"#(\d+)=\s*([A-Z0-9]+)\((.*?)\);\s*$", src, re.M | re.S):
        ents[int(m.group(1))] = (m.group(2), m.group(3))
    refs = lambda s: [int(x) for x in re.findall(r"#(\d+)", s)]
    num = re.compile(r"-?\d+(?:\.\d*)?(?:E[-+]?\d+)?")

    # units: millimetres if the file says so
    scale = 0.001 if re.search(r"IFCSIUNIT\(\*,\.LENGTHUNIT\.,\.MILLI\.", src) else 1.0

    def pt(i):
        return [float(v) * scale for v in num.findall(ents[i][1])[:3]]

    def brep_faces(b):
        out = []
        for shell in refs(ents[b][1])[:1]:
            for f in refs(ents[shell][1]):
                if ents.get(f, ("",))[0] != "IFCFACE":
                    continue
                for bound in refs(ents[f][1])[:1]:
                    loop = refs(ents[bound][1])[0]
                    out.append([pt(p) for p in refs(ents[loop][1])])
        return out

    raw, seen = [], set()
    for i, (t, a) in sorted(ents.items()):
        if t not in KINDS:
            continue
        shapes = [x for x in refs(a) if ents.get(x, ("",))[0] == "IFCPRODUCTDEFINITIONSHAPE"]
        if not shapes:
            continue
        faces = []
        for rep in refs(ents[shapes[0]][1]):
            if ents.get(rep, ("",))[0] != "IFCSHAPEREPRESENTATION":
                continue
            for b in refs(ents[rep][1]):
                if ents.get(b, ("",))[0] == "IFCFACETEDBREP":
                    faces += brep_faces(b)
        if not faces:
            continue
        key = (t, json.dumps(sorted(json.dumps(f) for f in faces)))
        if key in seen:  # CabinPlanner exports some parts twice
            continue
        seen.add(key)
        raw.append((t, faces))

    if not raw:
        raise ValueError("в файле не найдено геометрии")

    zmax_all = max(p[2] for _, fs in raw for f in fs for p in f)
    items = []
    for t, faces in raw:
        zs = [p[2] for f in faces for p in f]
        k = t[3:].lower()
        if k in ("buildingelementproxy", "slab"):
            k = "floor" if max(zs) <= 0.05 else "gable"
        elif k == "beam" and max(zs) <= 0.01:
            k = "joist"
        fs = [[[round(c, 4) for c in p] for p in f] for f in faces]
        items.append({"k": k, "f": fs})
    return {"v": 1, "items": items}


def main():
    if not os.path.isdir(HOUSES):
        sys.exit("Запустите скрипт из папки проекта (рядом должна быть папка houses/).")
    only = sys.argv[1:] or None
    done = skipped = 0
    for slug in sorted(os.listdir(HOUSES)):
        folder = os.path.join(HOUSES, slug)
        if not os.path.isdir(folder) or (only and slug not in only):
            continue
        ifcs = sorted(f for f in os.listdir(folder) if f.lower().endswith(".ifc"))
        if not ifcs:
            skipped += 1
            continue
        if len(ifcs) > 1:
            print(f"  ! {slug}: несколько .ifc, беру {ifcs[0]}")
        try:
            model = parse_ifc(os.path.join(folder, ifcs[0]))
        except Exception as e:
            print(f"  ✗ {slug}: не удалось прочитать {ifcs[0]} ({e})")
            continue
        out = os.path.join(folder, "model3d.json")
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(model, fh, separators=(",", ":"))
        kb = os.path.getsize(out) // 1024
        print(f"  ✓ {slug}: {len(model['items'])} элементов, {kb} КБ")
        done += 1
    print(f"\nГотово: моделей {done}. Домов без .ifc: {skipped}.")


if __name__ == "__main__":
    main()
