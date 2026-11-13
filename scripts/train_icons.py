"""Train the one-dimensional icon autoencoder served by the hidden slider.

Every pixel-art icon on the site (hand-drawn *and* the official logos) is a
16x16 grid over one shared symbol alphabet.  The model here has a single
circular latent: each icon owns one scalar ``z`` on the unit circle, and a
small implicit decoder maps ``(z, x, y)`` to one of the symbols.  Because the
latent is circular, adding a bias to every icon's ``z`` slides the whole set
along the icon manifold and wraps seamlessly -- that is the footer slider.

The decoder is tiny (~3k parameters) and is quantised to int16, so the site
ships the *network* rather than a table of outputs.  Run with the optional
training group::

    uv run --group train python scripts/train_icons.py

The generated ``src/adapters/outbound/icon_codec.json`` is committed; the
test-suite replays it through the browser decoder to prove that every anchor
still reproduces the authored art exactly.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import math
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from adapters.outbound import pixel_icons

SIZE = pixel_icons.SIZE
LATENT_FREQS = 12
PIXEL_FREQS = 4
DEFAULT_OUT = Path(__file__).resolve().parent.parent / "src/adapters/outbound/icon_codec.json"
QMAX = 32767


def dataset() -> tuple[list[str], list[str], torch.Tensor]:
    """Return ``(names, symbols, index_grids)`` for every icon."""
    names = pixel_icons.all_icon_names()
    grids = {name: "".join(pixel_icons.symbol_grid(name)) for name in names}
    symbols = sorted({ch for grid in grids.values() for ch in grid} - {"."}) + ["."]
    index = {ch: i for i, ch in enumerate(symbols)}
    x = torch.tensor([[index[ch] for ch in grids[name]] for name in names], dtype=torch.long)
    return names, symbols, x


def cycle_order(names: list[str], x: torch.Tensor) -> list[int]:
    """Order icons so consecutive latents are visually similar (greedy + 2-opt)."""
    flat = x.numpy()
    n = len(names)
    distance = (flat[:, None, :] != flat[None, :, :]).sum(-1).astype(np.int64)

    order = [0]
    left = set(range(1, n))
    while left:
        current = order[-1]
        nxt = min(left, key=lambda j: distance[current, j])
        order.append(nxt)
        left.remove(nxt)

    # 2-opt on the closed cycle; cheap at n <= 40.
    for _ in range(8):
        improved = False
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                a, b = order[i - 1], order[i]
                c, d = order[j], order[(j + 1) % n]
                if distance[a, c] + distance[b, d] < distance[a, b] + distance[c, d]:
                    order[i : j + 1] = reversed(order[i : j + 1])
                    improved = True
        if not improved:
            break
    return order


def features() -> tuple[torch.Tensor, torch.Tensor, int, int]:
    """Fourier features for the latent and for each pixel coordinate."""
    yy, xx = torch.meshgrid(torch.arange(SIZE), torch.arange(SIZE), indexing="ij")
    coords = torch.stack([xx.flatten() / (SIZE - 1), yy.flatten() / (SIZE - 1)], -1)
    pixel_freqs = torch.arange(1, PIXEL_FREQS + 1, dtype=torch.float32) * 2 * math.pi
    z_freqs = torch.arange(1, LATENT_FREQS + 1, dtype=torch.float32) * 2 * math.pi

    phase = coords[:, :, None] * pixel_freqs
    pixel = torch.cat([coords, torch.sin(phase).flatten(1), torch.cos(phase).flatten(1)], -1)
    return z_freqs, pixel, z_freqs.numel() * 2, pixel.shape[1]


def latent_features(z: torch.Tensor, freqs: torch.Tensor) -> torch.Tensor:
    return torch.cat([torch.sin(z * freqs), torch.cos(z * freqs)], -1)


def build(hidden: int, n_in: int, n_out: int) -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(n_in, hidden),
        nn.ReLU(),
        nn.Linear(hidden, hidden),
        nn.ReLU(),
        nn.Linear(hidden, n_out),
    )


def train(
    x: torch.Tensor,
    order: list[int],
    hidden: int,
    seed: int,
    steps: int,
) -> tuple[nn.Sequential, torch.Tensor, bool]:
    n = x.shape[0]
    symbols = int(x.max().item()) + 1
    z_freqs, pixel, n_z, n_pixel = features()
    torch.manual_seed(seed)

    latents = torch.tensor([i / n for i in range(n)], dtype=torch.float32).unsqueeze(1)
    model = build(hidden, n_z + n_pixel, symbols)
    opt = torch.optim.Adam(model.parameters(), lr=3e-3)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps)

    zf = latent_features(latents, z_freqs)
    inputs = torch.cat(
        [zf[:, None, :].expand(-1, SIZE * SIZE, -1), pixel[None].expand(n, -1, -1)], -1
    )
    target = x.view(n, SIZE, SIZE)[torch.tensor(order)]

    for _ in range(steps):
        loss = F.cross_entropy(model(inputs).reshape(-1, symbols), target.reshape(-1))
        opt.zero_grad()
        loss.backward()
        opt.step()
        sched.step()

    with torch.no_grad():
        pred = model(inputs).argmax(-1).view(n, SIZE, SIZE)
        exact = (pred == target).all(1).all(1).all().item()
    return model, latents, bool(exact)


def quantise(weights: torch.Tensor) -> tuple[np.ndarray, np.ndarray]:
    w = weights.detach().numpy().astype(np.float64)
    scale = np.abs(w).max(1) / QMAX
    scale[scale == 0] = 1.0
    q = np.clip(np.round(w / scale[:, None]), -QMAX, QMAX).astype(np.int16)
    return q, scale


def dequantised(model: nn.Sequential) -> nn.Sequential:
    """A copy of ``model`` using exactly the int16 weights we will ship."""
    layers = list(model)
    rebuilt = nn.Sequential()
    for layer in layers:
        if isinstance(layer, nn.Linear):
            q, scale = quantise(layer.weight)
            clone = nn.Linear(layer.in_features, layer.out_features)
            with torch.no_grad():
                clone.weight.copy_(
                    torch.tensor(q.astype(np.float64) * scale[:, None], dtype=torch.float32)
                )
                clone.bias.copy_(layer.bias)
            rebuilt.append(clone)
        else:
            rebuilt.append(layer)
    return rebuilt


def exact_at_anchors(
    model: nn.Sequential, latents: torch.Tensor, order: list[int], x: torch.Tensor
) -> bool:
    z_freqs, pixel, _, _ = features()
    n = x.shape[0]
    zf = latent_features(latents, z_freqs)
    inputs = torch.cat(
        [zf[:, None, :].expand(-1, SIZE * SIZE, -1), pixel[None].expand(n, -1, -1)], -1
    )
    target = x.view(n, SIZE, SIZE)[torch.tensor(order)]
    with torch.no_grad():
        pred = model(inputs).argmax(-1).view(n, SIZE, SIZE)
    return bool((pred == target).all(1).all(1).all().item())


def encode(
    model: nn.Sequential,
    order: list[int],
    names: list[str],
    symbols: list[str],
    metrics: dict,
) -> dict:
    layers = []
    for layer in model:
        if not isinstance(layer, nn.Linear):
            continue
        q, scale = quantise(layer.weight)
        layers.append(
            {
                "in": layer.in_features,
                "out": layer.out_features,
                "data": base64.b64encode(q.astype("<i2").tobytes()).decode("ascii"),
                "scale": [round(float(v), 8) for v in scale],
                "bias": [round(float(v), 6) for v in layer.bias.detach().tolist()],
            }
        )
    return {
        "version": 1,
        "size": SIZE,
        "symbols": symbols,
        "paint": pixel_icons.paint(),
        "config": {
            "nf": LATENT_FREQS,
            "np": PIXEL_FREQS,
            "hidden": metrics["hidden"],
            "quant": "i16",
        },
        "layers": layers,
        "latents": {names[order[i]]: round(i / len(names), 8) for i in range(len(names))},
        "order": [names[i] for i in order],
        "metrics": metrics,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--steps", type=int, default=20000)
    ap.add_argument("--hidden", type=int, nargs="+", default=[32, 40, 48])
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    args = ap.parse_args()

    names, symbols, x = dataset()
    order = cycle_order(names, x)
    print(f"icons={len(names)} symbols={len(symbols)} order={[names[i] for i in order]}")

    chosen = None
    for hidden in args.hidden:
        for seed in args.seeds:
            model, latents, exact = train(x, order, hidden, seed, args.steps)
            params = sum(p.numel() for p in model.parameters())
            print(f"hidden={hidden} seed={seed} params={params} exact={bool(exact)}")
            if not exact:
                continue
            shipped = dequantised(model)
            if not exact_at_anchors(shipped, latents, order, x):
                print("  int16 quantisation changed an anchor; trying another seed")
                continue
            chosen = (model, shipped, latents, hidden, params, seed)
            break
        if chosen:
            break

    if chosen is None:
        print("FAIL: no configuration reproduced every icon exactly")
        return 1

    model, shipped, latents, hidden, params, seed = chosen
    metrics = {
        "icons": len(names),
        "params": params,
        "hidden": hidden,
        "seed": seed,
        "exact": 1.0,
    }

    # The payload is written twice: once to measure, then once for real.
    probe = encode(shipped, order, names, symbols, metrics)
    raw = json.dumps(probe, separators=(",", ":")).encode()
    metrics["bytes"] = len(raw)
    metrics["gzip_bytes"] = len(gzip.compress(raw, 9))

    payload = encode(shipped, order, names, symbols, metrics)
    text = json.dumps(payload, separators=(",", ":")) + "\n"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text)
    print(
        f"wrote {args.out} ({metrics['bytes']} B raw, "
        f"{metrics['gzip_bytes']} B gzip, {params} params)"
    )

    # Re-load through the same arithmetic the browser will use.
    reloaded = json.loads(args.out.read_text())
    assert reloaded["latents"] == payload["latents"]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
