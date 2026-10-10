#!/usr/bin/env python3
"""
build_3d_models.py — готовит 3D-модели домов для просмотра на сайте.

Что делает:
  Для каждой папки houses/<дом>/, где лежит файл .ifc (выгрузка из CabinPlanner),
  создаёт рядом файл model3d.json — облегчённую 3D-модель для viewer3d.js
  (с комнатами для перехода между ними в режиме «Interior»).

Что НЕ делает:
  Не меняет data.json, фото и любые другие файлы. Только создаёт/обновляет model3d.json.

Запуск (из папки проекта):
  python3 build_3d_models.py            — все дома, где есть .ifc
  python3 build_3d_models.py takoma-58-12x8   — один дом
"""
import json, math, os, re, sys
from collections import deque

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
    rooms = []
    try:
        rooms = find_rooms(items)
    except Exception:
        pass
    return {"v": 1, "items": items, "rooms": rooms}


def find_rooms(items, cell=0.05):
    """Комнаты по стенам: разрез стен чуть выше дверей (там стены сплошные),
    заливка областей, ограниченных стенами. Возвращает площадь, центр и границы каждой комнаты."""
    walls=[i for i in items if i['k']=='wall']
    if not walls: return []
    dt=max(p[2] for i in items if i['k'] in('door','window') for f in i['f'] for p in f) if any(i['k'] in('door','window') for i in items) else 2.0
    wt=min(max(p[2] for f in i['f'] for p in f) for i in walls)
    z=(dt+wt)/2 if wt>dt+0.05 else dt+0.05
    segs=[]
    for w in walls:
        for f in w['f']:
            pts=[]
            n=len(f)
            for a in range(n):
                p,q=f[a],f[(a+1)%n]
                if (p[2]-z)*(q[2]-z)<0:
                    t=(z-p[2])/(q[2]-p[2]); pts.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
            if len(pts)>=2:
                # pair along dominant axis
                ax=0 if abs(pts[-1][0]-pts[0][0])>=abs(pts[-1][1]-pts[0][1]) else 1
                pts.sort(key=lambda r:r[ax])
                for k in range(0,len(pts)-1,2): segs.append((pts[k],pts[k+1]))
    xs=[c for s in segs for p in s for c in [p[0]]]; ys=[p[1] for s in segs for p in s]
    x0,y0=min(xs)-0.3,min(ys)-0.3; W=int((max(xs)+0.3-x0)/cell)+1; H=int((max(ys)+0.3-y0)/cell)+1
    g=bytearray(W*H)
    for (a,b) in segs:
        L=math.hypot(b[0]-a[0],b[1]-a[1]); steps=max(1,int(L/(cell*0.5)))
        for s in range(steps+1):
            x=a[0]+(b[0]-a[0])*s/steps; y=a[1]+(b[1]-a[1])*s/steps
            ci=int((x-x0)/cell); cj=int((y-y0)/cell)
            for di in(-1,0,1):
                for dj in(-1,0,1):
                    i,j=ci+di,cj+dj
                    if 0<=i<W and 0<=j<H: g[j*W+i]=1
    lab=[0]*(W*H); rooms=[]; nl=0
    for start in range(W*H):
        if g[start] or lab[start]: continue
        nl+=1; q=deque([start]); lab[start]=nl; cells=[]; border=False
        while q:
            c=q.popleft(); cells.append(c); i,j=c%W,c//W
            if i==0 or j==0 or i==W-1 or j==H-1: border=True
            for d in(1,-1,W,-W):
                n2=c+d
                if 0<=n2<W*H and not g[n2] and not lab[n2] and not (d in(1,-1) and n2//W!=j):
                    lab[n2]=nl; q.append(n2)
        if border: continue
        area=len(cells)*cell*cell
        if area<1.5: continue
        cx=sum(x0+(c%W+0.5)*cell for c in cells)/len(cells); cy=sum(y0+(c//W+0.5)*cell for c in cells)/len(cells)
        # room extents
        ii=[c%W for c in cells]; jj=[c//W for c in cells]
        rooms.append({'a':round(area,1),'c':[round(cx,3),round(cy,3)],'b':[round(x0+min(ii)*cell,3),round(y0+min(jj)*cell,3),round(x0+(max(ii)+1)*cell,3),round(y0+(max(jj)+1)*cell,3)]})
    rooms.sort(key=lambda r:-r['a'])
    return rooms


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
        print(f"  ✓ {slug}: {len(model['items'])} элементов, комнат {len(model['rooms'])}, {kb} КБ")
        done += 1
    print(f"\nГотово: моделей {done}. Домов без .ifc: {skipped}.")


if __name__ == "__main__":
    main()
