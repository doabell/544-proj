#!/usr/bin/env python3
from __future__ import annotations
import argparse, math, random, sys, time
from fractions import Fraction
from typing import Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table

console = Console()

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
    """Return the multiplicative order r of a mod N (brute‐force)."""
    r, x = 1, a % N
    while x != 1:
        x = (x * a) % N
        r += 1
        if r > N:
            return 0
    return r

def classical_shor(N: int, a: int) -> Dict[str, Any]:
    """Classical analogue of Shor: find order, then gcd trick to factor N."""
    start = time.time()
    r = find_order(a, N)
    t_shor = time.time() - start

    # order must be even and non‐trivial
    if r == 0 or r % 2 == 1:
        return {"ok": False, "reason": "odd or zero order", "time": t_shor}

    ar2 = pow(a, r // 2, N)
    if ar2 in (1, N - 1):
        return {"ok": False, "reason": "a^(r/2) = ±1", "time": t_shor}

    p = math.gcd(ar2 - 1, N)
    q = math.gcd(ar2 + 1, N)
    if p in (1, N) or q in (1, N):
        return {"ok": False, "reason": "gcd gave trivial factor", "time": t_shor}

    return {"ok": True, "factors": (p, q), "order": r, "a_r2": ar2, "time": t_shor}

def run_rsa_crack(n: int, e: int, c: int, a: int) -> None:
    console.print(Panel.fit(f"[bold red]RSA-Crack Demo[/bold red]\n n={n}, e={e}, c={c}\n", border_style="red"))

    attempt = 0
    with Progress(SpinnerColumn(), TextColumn("[magenta]Order finding…[/magenta]"), BarColumn(), TimeElapsedColumn()) as prog:
        while True:
            attempt += 1
            task = prog.add_task("trying", total=None)
            res = classical_shor(n, a)
            prog.update(task, completed=True)
            if res["ok"]:
                p, q = res["factors"]
                break
            a = choose_a(n)

    phi = (p - 1) * (q - 1)
    d = pow(e, -1, phi)
    m = pow(c, d, n)

    tbl = Table(show_header=True, header_style="bold blue")
    tbl.add_column("Step")
    tbl.add_column("Result")
    tbl.add_row("Factor p", str(p))
    tbl.add_row("Factor q", str(q))
    tbl.add_row("Computed φ(n)", str(phi))
    tbl.add_row("Private exponent d", str(d))
    tbl.add_row("Decrypted plaintext m", str(m))
    tbl.add_row("Attempts", str(attempt))
    tbl.add_row("Order-finding time (s)", f"{res['time']:.4f}")
    console.print(tbl)
    console.print("[green]✓ RSA message successfully recovered.[/green]")

def main() -> None:
    ap = argparse.ArgumentParser(description="Shor-style RSA cracker")
    ap.add_argument("--n", required=True, type=int, help="RSA modulus n")
    ap.add_argument("--e", required=True, type=int, help="RSA public exponent e")
    ap.add_argument("--c", required=True, type=int, help="Ciphertext to decrypt")
    ap.add_argument("--a", type=int, help="Optional base a (coprime to n)")
    ap.add_argument("--seed", type=int, help="Optional RNG seed")
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    if args.n < 9 or args.n % 2 == 0:
        console.print("[bold red]Provide an odd composite ≥9 for n.[/bold red]")
        sys.exit(1)

    a = choose_a(args.n, args.a)
    run_rsa_crack(args.n, args.e, args.c, a)

if __name__ == "__main__":
    main()
