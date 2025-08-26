#!/usr/bin/env python3
import os
import sys
import pathlib
import re
import traceback

import trimesh

WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_GLB = WORKSPACE_ROOT / "Godot/WFC_3D/meshes/wfc_modules.glb"
OUTPUT_DIR = WORKSPACE_ROOT / "Godot/WFC_3D/meshes/obj"


def sanitize_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_\-]+", "_", name).strip("_") or "mesh"


def export_glb_nodes_to_obj(glb_path: pathlib.Path, out_dir: pathlib.Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Loading GLB: {glb_path}")
    scene = trimesh.load(glb_path.as_posix(), force='scene')
    if not isinstance(scene, trimesh.Scene):
        scene = trimesh.Scene(scene)
    count = 0
    for entry in scene.graph.nodes_geometry:
        try:
            node_name, geom_name = entry[0], entry[1]
        except Exception:
            node_name, geom_name = entry
        if geom_name not in scene.geometry:
            continue
        geom = scene.geometry[geom_name]
        if geom.is_empty:
            continue
        try:
            transform = scene.graph.get_transform(node_name)
        except Exception:
            transform = None
        mesh = geom.copy()
        if transform is not None:
            mesh.apply_transform(transform)
        safe = sanitize_name(node_name or geom_name)
        m = re.search(r"wfc_module_\d+", (node_name or "") + " " + (geom_name or ""), re.IGNORECASE)
        if m:
            safe = m.group(0)
        out_path = out_dir / f"{safe}.obj"
        print(f"Exporting {safe}.obj")
        mesh.export(out_path.as_posix(), file_type='obj')
        count += 1
    if count == 0 and scene.geometry:
        for geom_name, geom in scene.geometry.items():
            if geom.is_empty:
                continue
            safe = sanitize_name(geom_name)
            out_path = out_dir / f"{safe}.obj"
            print(f"Exporting {safe}.obj (geometry)")
            geom.export(out_path.as_posix(), file_type='obj')
            count += 1
    return count


def main(argv: list[str]) -> int:
    glb_path = pathlib.Path(argv[1]).resolve() if len(argv) > 1 else DEFAULT_GLB
    out_dir = pathlib.Path(argv[2]).resolve() if len(argv) > 2 else OUTPUT_DIR
    if not glb_path.exists():
        print(f"ERROR: GLB not found: {glb_path}", file=sys.stderr)
        return 2
    try:
        count = export_glb_nodes_to_obj(glb_path, out_dir)
    except Exception as e:
        print("ERROR during conversion:", e, file=sys.stderr)
        traceback.print_exc()
        return 1
    print(f"Done. Exported {count} OBJ files to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
