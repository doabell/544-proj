#!/usr/bin/env python3
from __future__ import annotations

import argparse, math, random, sys, time
from fractions import Fraction
from typing import Dict, List

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table

console = Console()

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def choose_a(N: int, explicit: int | None = None) -> int:
    if explicit:
        if math.gcd(explicit, N) != 1:
            console.print("[bold red]Provided a is not coprime to N.[/bold red]")
            sys.exit(1)
        return explicit
    while True:
        cand = random.randrange(2, N - 1)
        if math.gcd(cand, N) == 1:
            return cand


def find_order(a: int, N: int) -> int:
    """Return the multiplicative order r of a mod N (small N brute loop)."""
    r, x = 1, (a % N)
    while x != 1:
        x = (x * a) % N
        r += 1
        if r > N:  # should not happen if N is composite and gcd(a,N)=1
            return 0
    return r


def classical_shor(N: int, a: int) -> Dict[str, int | List[int]]:
    """Classical analogue of Shor: order‑find, then gcd trick."""
    start = time.time()
    r = find_order(a, N)
    quantum_time = time.time() - start  # pretend this is quantum time

    if r == 0 or r % 2 == 1:
        return {"ok": False, "reason": "odd or zero order"}

    ar2 = pow(a, r // 2, N)
    if ar2 in (1, N - 1):
        return {"ok": False, "reason": "a^(r/2) = ±1"}

    p = math.gcd(ar2 - 1, N)
    q = math.gcd(ar2 + 1, N)

    if p in (1, N) or q in (1, N):
        return {"ok": False, "reason": "gcd gave trivial factor"}

    return {
        "ok": True,
        "factors": [p, q],
        "order": r,
        "a_r2": ar2,
        "elapsed": quantum_time,
    }

# ---------------------------------------------------------------------
# Rich flow
# ---------------------------------------------------------------------

def run_demo(N: int, a: int) -> None:
    console.print(Panel.fit(f"[bold red]Shor‑style RSA demo[/bold red]\nN = {N}, a = {a}", border_style="red"))

    attempt = 0
    with Progress(SpinnerColumn(), TextColumn("[magenta]Order finding…[/magenta]"), BarColumn(), TimeElapsedColumn()) as p:
        while True:
            attempt += 1
            task = p.add_task("try", total=None)
            res = classical_shor(N, a)
            p.update(task, completed=True)
            if res["ok"]:
                break
            a = choose_a(N)  # pick new a and retry

    tbl = Table(show_header=True, header_style="bold blue")
    tbl.add_column("Item"); tbl.add_column("Value")
    tbl.add_row("Composite N", str(N))
    tbl.add_row("Successful a", str(a))
    tbl.add_row("Order r", str(res["order"]))
    tbl.add_row("a^(r/2) mod N", str(res["a_r2"]))
    tbl.add_row("Factors", ", ".join(map(str, res["factors"])))
    tbl.add_row("Attempts", str(attempt))
    tbl.add_row("Elapsed (s)", f"{res['elapsed']:.4f}")
    console.print(tbl)
    console.print("[green]✓ Non‑trivial factors found.[/green]")

# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", required=True, type=int, help="Odd composite ≤4095")
    ap.add_argument("--a", type=int, help="Optional base a (coprime to N)")
    ap.add_argument("--seed", type=int)
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    if args.n < 9 or args.n % 2 == 0:
        console.print("[bold red]Provide an odd composite ≥9.[/bold red]")
        sys.exit(1)

    a = choose_a(args.n, args.a)
    run_demo(args.n, a)

if __name__ == "__main__":
    main()
