#!/usr/bin/env python3
import sys
import pathlib
from typing import List, Tuple, Optional

import numpy as np
import trimesh
import networkx as nx

WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_GLB = WORKSPACE_ROOT / "Godot/WFC_3D/meshes/wfc_modules.glb"
DEFAULT_OUT = WORKSPACE_ROOT / "Godot/WFC_3D/meshes/obj_clustered"
DEFAULT_MESH_DIR = WORKSPACE_ROOT / "Godot/WFC_3D/meshes"


def load_world_meshes(glb_path: pathlib.Path) -> List[trimesh.Trimesh]:
    scene = trimesh.load(glb_path.as_posix(), force='scene')
    if not isinstance(scene, trimesh.Scene):
        scene = trimesh.Scene(scene)
    meshes: List[trimesh.Trimesh] = []
    try:
        for entry in scene.graph.nodes_geometry:
            node_name = entry[0]
            geom_name = entry[1]
            if geom_name not in scene.geometry:
                continue
            geom = scene.geometry[geom_name]
            if geom.is_empty:
                continue
            mesh = geom.copy()
            try:
                T = scene.graph.get_transform(node_name)
                if T is not None:
                    mesh.apply_transform(T)
            except Exception:
                pass
            meshes.append(mesh)
    except Exception:
        pass
    if not meshes:
        for geom in scene.geometry.values():
            if not geom.is_empty:
                meshes.append(geom.copy())
    return meshes


def cluster_meshes(meshes: List[trimesh.Trimesh], eps: float) -> List[List[int]]:
    if not meshes:
        return []
    cents = np.array([m.centroid for m in meshes])
    G = nx.Graph()
    G.add_nodes_from(range(len(meshes)))
    for i in range(len(meshes)):
        for j in range(i + 1, len(meshes)):
            if np.linalg.norm(cents[i] - cents[j]) <= eps:
                G.add_edge(i, j)
    comps = list(nx.connected_components(G))
    clusters = [sorted(list(c)) for c in comps]
    clusters.sort(key=lambda comp: comp[0])
    return clusters


def pick_eps_for_target(meshes: List[trimesh.Trimesh], target: int, lo: float = 0.0, hi: float = 0.5, steps: int = 24) -> Tuple[float, List[List[int]]]:
    best_eps = lo
    best_clusters: List[List[int]] = cluster_meshes(meshes, lo)
    best_diff = abs(len(best_clusters) - target)
    cur_hi = hi
    clusters_hi = cluster_meshes(meshes, cur_hi)
    tries = 0
    while len(clusters_hi) > target and tries < 10:
        cur_hi *= 2.0
        clusters_hi = cluster_meshes(meshes, cur_hi)
        tries += 1
    left, right = lo, cur_hi
    for _ in range(steps):
        mid = (left + right) / 2.0
        clusters_mid = cluster_meshes(meshes, mid)
        diff = abs(len(clusters_mid) - target)
        if diff < best_diff:
            best_diff = diff
            best_eps = mid
            best_clusters = clusters_mid
        if len(clusters_mid) > target:
            left = mid
        else:
            right = mid
    return best_eps, best_clusters


def get_expected_names(mesh_dir: pathlib.Path) -> List[str]:
    names = []
    for p in sorted(mesh_dir.glob("wfc_module_*.mesh")):
        names.append(p.stem)
    def key(n: str) -> int:
        try:
            return int(n.split("_")[-1])
        except Exception:
            return 1000000
    names.sort(key=key)
    return names


def export_clusters(meshes: List[trimesh.Trimesh], clusters: List[List[int]], out_dir: pathlib.Path, names: Optional[List[str]] = None):
    out_dir.mkdir(parents=True, exist_ok=True)
    for idx, comp in enumerate(clusters):
        if not comp:
            continue
        group = [meshes[i] for i in comp]
        combined = trimesh.util.concatenate(group) if len(group) > 1 else group[0]
        base = names[idx] if names and idx < len(names) else f"wfc_module_{idx}"
        out_path = out_dir / f"{base}.obj"
        print(f"Exporting cluster {idx} -> {out_path.name} (parts={len(group)})")
        combined.export(out_path.as_posix(), file_type='obj')


def parse_args(argv: List[str]):
    glb_path = None
    out_dir = None
    eps = None
    target = None
    mesh_dir = DEFAULT_MESH_DIR
    pos = []
    for a in argv[1:]:
        if a.startswith('--eps'):
            parts = a.split('=')
            if len(parts) == 2:
                try:
                    eps = float(parts[1])
                except ValueError:
                    pass
        elif a == '--target':
            target = -1
        elif isinstance(target, int) and target == -1:
            try:
                target = int(a)
            except ValueError:
                target = None
        elif a.startswith('--mesh-dir'):
            parts = a.split('=')
            if len(parts) == 2:
                mesh_dir = pathlib.Path(parts[1]).resolve()
        else:
            pos.append(a)
    if pos:
        glb_path = pathlib.Path(pos[0]).resolve()
    if len(pos) > 1:
        out_dir = pathlib.Path(pos[1]).resolve()
    if glb_path is None:
        glb_path = DEFAULT_GLB
    if out_dir is None:
        out_dir = DEFAULT_OUT
    return glb_path, out_dir, eps, target, mesh_dir


def main(argv: List[str]) -> int:
    glb_path, out_dir, eps, target, mesh_dir = parse_args(argv)
    if not glb_path.exists():
        print(f"ERROR: GLB not found: {glb_path}")
        return 2
    meshes = load_world_meshes(glb_path)
    if not meshes:
        print("ERROR: No meshes found in GLB")
        return 3
    expected_names = get_expected_names(mesh_dir)
    inferred_target = len(expected_names) if expected_names else None
    if target is None:
        target = inferred_target if inferred_target is not None else None
    if eps is None and target is not None:
        chosen_eps, clusters = pick_eps_for_target(meshes, target)
        print(f"Auto-picked eps={chosen_eps:.6f} to get {len(clusters)} clusters (target={target})")
    else:
        chosen_eps = eps if eps is not None else 0.05
        clusters = cluster_meshes(meshes, chosen_eps)
        print(f"Using eps={chosen_eps:.6f} -> {len(clusters)} clusters")
    names_for_export = expected_names if expected_names and len(expected_names) == len(clusters) else None
    if expected_names and not names_for_export:
        print(f"WARNING: Expected {len(expected_names)} module names from {mesh_dir}, but have {len(clusters)} clusters. Falling back to sequential names.")
    export_clusters(meshes, clusters, out_dir, names_for_export)
    print(f"Done. Wrote clustered OBJs to {out_dir}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
