import json
import time
import random

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
)

console = Console()


def fmt_hex(number: int, max_len: int = 32) -> str:
    """Format a big number for display: show first few and last few hex digits."""
    hex_str = hex(number)[2:]
    half_len = max_len // 2
    if len(hex_str) <= max_len:
        return f"0x{hex_str}"
    return f"0x{hex_str[:half_len]}...{hex_str[-half_len:]}"


def load_dh(filename: str = "dh-exchange.json") -> dict[str, int]:
    """Load the key exchange data from the file. Returns a dict mapping str to int."""
    try:
        with open(filename, "r") as f:
            data = json.load(f)
            # Convert back to integers
            int_data: dict[str, int] = {
                "p": int(data["p"]),
                "g": int(data["g"]),
                "alice_public": int(data["alice_public"]),
                "bob_public": int(data["bob_public"]),
                # For simulation/verification only
                # Eve will not see these values in a real attack
                "alice_private": int(data["alice_private"]),
                "bob_private": int(data["bob_private"]),
                "shared_secret_original": int(data["shared_secret"]),
            }
            return int_data
    except FileNotFoundError:
        console.print(f"[bold red]Error:[/bold red] File '{filename}' not found.")
        console.print(
            "[yellow]Please run dh-impl.py first to generate the data.[/yellow]"
        )
        exit(1)
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        console.print(f"[bold red]Error:[/bold red] Could not parse '{filename}': {e}")
        exit(1)


def shors_find_period(
    g: int, public_key_y: int, p: int, group_order_q: int, actual_private_key_k: int
) -> tuple[int, int]:
    """
    Simulates using Shor's quantum period finding for the DLP.

    This function simulates finding a period (w1, w2) related to the bivariate
    function f(x1, x2) = g^x1 * y^x2 mod p, where y = g^k mod p.
    The period satisfies k*w2 ≡ -w1 (mod q), where q is the group order.

    This simulation constructs a valid period (w1, w2) using the known private key 'k'.

    Args:
        g: The generator.
        public_key_y: The public key y = g^k mod p.
        p: The prime modulus.
        group_order_q: The order of the generator g modulo p (q = (p-1)/2 here).
        actual_private_key_k: The known private key 'k' (used to construct the period).

    Returns:
        A tuple (w1, w2) representing the found period relation (simulated).
    """
    console.print(
        "[yellow]Simulating Shor's Quantum Period Finding for DLP...[/yellow]"
    )
    console.print(
        "[dim]Target: Find period (w1, w2) for function related to f(x1,x2)=g^x1*y^x2[/dim]"
    )
    console.print(f"[dim]Group order q = {fmt_hex(group_order_q)}[/dim]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold magenta]Simulating Quantum Period-Finding...[/bold magenta]"),
        BarColumn(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("Finding period (w1, w2)...", total=None)

        # Simulate finding a non-trivial period (w1, w2) != (0, 0)
        # We know k*w2 ≡ -w1 (mod q).
        # To simulate, we construct a valid period using the known 'k'.
        # Choose a random w2 (1 <= w2 < q)
        w2 = random.randint(1, group_order_q - 1)
        # Calculate corresponding w1 = (-k * w2) mod q
        w1 = (-actual_private_key_k * w2) % group_order_q

        time.sleep(2)
        progress.update(task, completed=True)

    console.print(
        "[bold green]Shor's Simulation Complete:[/bold green] Found a period relation:"
    )
    console.print(f"  w1 = {fmt_hex(w1)}")
    console.print(f"  w2 = {fmt_hex(w2)}")
    console.print("[dim]  Satisfies k*w2 ≡ -w1 (mod q)[/dim]")

    return w1, w2


def dlp_from_period(w1: int, w2: int, group_order_q: int) -> int:
    """
    Calculates the discrete logarithm 'k' from the period (w1, w2).

    This function performs the classical post-processing step after Shor's
    algorithm has found the period relation k*w2 ≡ -w1 (mod q).

    Args:
        w1: The first component of the period.
        w2: The second component of the period.
        group_order_q: The order of the group.

    Returns:
        The calculated discrete logarithm 'k', or 0 if calculation fails.
    """
    console.print(
        "\n[yellow]Classical Post-processing:[/yellow] Calculating 'k' from period (w1, w2)..."
    )
    console.print("[dim]  Using relation: k*w2 ≡ -w1 (mod q)[/dim]")
    console.print("[dim]  Solving for k: k ≡ -w1 * w2^-1 (mod q)[/dim]")

    try:
        # Calculate k = (-w1 * w2^-1) mod q
        # Need modular inverse of w2 mod q
        w2_inv = pow(w2, -1, group_order_q)
        recovered_private_key = (-w1 * w2_inv) % group_order_q
        console.print(
            f"[dim]  Calculated w2^-1 mod q = {fmt_hex(w2_inv)}[/dim]"
        )
        console.print("[dim]  Calculated k = (-w1 * w2^-1) mod q[/dim]")
        console.print(
            "[bold green]Calculation Complete:[/bold green] Recovered private key k."
        )
        return recovered_private_key

    except ValueError:
        # This should not happen if q is prime and w2 != 0 from simulation
        console.print(
            "[bold red]Error:[/bold red] w2 is not invertible modulo q. Cannot calculate k."
        )
        # In a real run, if w2=0 or gcd(w2, q)!=1, the algorithm needs to be run again.
        return 0  # Indicate failure


def dh_ss_eve(
    other_public_key: int, recovered_private_key: int, p: int
) -> int:
    """Generate the shared secret using the recovered private key."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold red]Eve Computing Shared Secret...[/bold red]"),
        BarColumn(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("Calculating S = B^a mod p...", total=None)
        start_time = time.time()
        result = pow(other_public_key, recovered_private_key, p)
        end_time = time.time()
        progress.update(task, completed=True)

    computation_time = end_time - start_time
    console.print(
        f"[cyan]Eve's shared secret computation took[/cyan] [bold yellow]{computation_time:.4f}[/bold yellow] [cyan]seconds[/cyan]"
    )
    return result


def print_attack_explanation() -> None:
    """Print an explanation of the attack."""
    explanation = """
    [bold]Attack Overview:[/bold]
    An attacker (Eve) intercepts the public parameters (p, g) and the public keys (A, B).
    The security of Diffie-Hellman relies on the difficulty of the Discrete Logarithm Problem (DLP).

    A quantum computer running Shor's algorithm can directly solve the DLP:
    Given public key Y = g^k mod p, find the private key k.

    [bold]Attack Steps:[/bold]
    1. Eve intercepts p, g, A, B.
    2. [bold](Quantum Step - Simulated)[/bold] Eve uses Shor's algorithm (quantum period finding on a
       related bivariate function) to find a period (w1, w2) related to Alice's private key 'a'.
       This period satisfies a * w2 ≡ -w1 (mod q), where q is the group order.
    3. [bold](Classical Post-processing)[/bold] Eve classically calculates 'a' from the period
       using the relationship: a = (-w1 * w2^-1) mod q.
    4. Eve computes the shared secret S using Bob's public key B and the recovered private key a:
       S_eve = B^a mod p
    5. Eve now possesses the same shared secret as Alice and Bob.
    """
    console.print(
        Panel(
            explanation,
            title="Cracking Diffie-Hellman: Shor's Period Finding",
            border_style="red",
        )
    )


def main() -> None:
    """Simulate cracking Diffie-Hellman using Shor's algorithm."""
    console.print(
        Panel.fit(
            "[bold red]Eve's Attack on Diffie-Hellman using Shor's Algorithm[/bold red]",
            border_style="red",
        )
    )

    print_attack_explanation()

    # Load data (public)
    console.print(
        "\n[bold yellow]Step 1:[/bold yellow] [cyan]Eve intercepts public communication...[/cyan]"
    )
    exchange_data = load_dh()
    p = exchange_data["p"]
    g = exchange_data["g"]
    alice_public = exchange_data["alice_public"]
    bob_public = exchange_data["bob_public"]
    # For simulation/verification
    alice_private_actual = exchange_data["alice_private"]
    shared_secret_original = exchange_data["shared_secret_original"]

    intercepted_table = Table(show_header=True, header_style="bold blue")
    intercepted_table.add_column("Parameter")
    intercepted_table.add_column("Intercepted Value (partial hex)")
    intercepted_table.add_row("Prime (p)", fmt_hex(p))
    intercepted_table.add_row("Generator (g)", str(g))
    intercepted_table.add_row("Alice's Public Key (A)", fmt_hex(alice_public))
    intercepted_table.add_row("Bob's Public Key (B)", fmt_hex(bob_public))
    console.print(intercepted_table)

    # Shor's Period Finding Simulation
    console.print(
        "\n[bold yellow]Step 2:[/bold yellow] [cyan]Eve uses Shor's Algorithm (Simulated) to find period (w1, w2)...[/cyan]"
    )
    # For the safe prime p=2q+1 used, the order of g=2 is q=(p-1)/2
    group_order_q = (p - 1) // 2
    console.print(
        f"[dim]Group order q = (p-1)/2 = {fmt_hex(group_order_q)}[/dim]"
    )

    w1, w2 = shors_find_period(
        g, alice_public, p, group_order_q, alice_private_actual
    )

    # PK from period
    recovered_alice_private = dlp_from_period(w1, w2, group_order_q)

    recovered_table = Table(show_header=True, header_style="bold magenta")
    recovered_table.add_column("Target")
    recovered_table.add_column("Recovered Private Key (partial hex)")
    recovered_table.add_column("Bit Length")
    if recovered_alice_private != 0:
        recovered_table.add_row(
            "Alice's Private Key (a)",
            fmt_hex(recovered_alice_private),
            f"{recovered_alice_private.bit_length()} bits",
        )
    else:
        recovered_table.add_row(
            "Alice's Private Key (a)", "[red]Calculation Failed[/red]", "-"
        )
    console.print(recovered_table)

    if recovered_alice_private == 0:
        console.print(
            "[bold red]Cannot proceed to compute shared secret as private key recovery failed.[/bold red]"
        )
        exit(1)

    # Compute Shared Secret
    console.print(
        "\n[bold yellow]Step 4:[/bold yellow] [cyan]Eve computes the shared secret using Bob's public key (B) and the recovered private key (a)...[/cyan]"
    )
    # S = B^a mod p
    eve_shared_secret = dh_ss_eve(
        bob_public, recovered_alice_private, p
    )

    result_table = Table(show_header=True, header_style="bold red")
    result_table.add_column("Party")
    result_table.add_column("Shared Secret Calculation")
    result_table.add_column("Computed Secret (partial hex)")

    result_table.add_row(
        "Eve", "S_eve = B^a mod p", fmt_hex(eve_shared_secret)
    )
    result_table.add_row(
        "Original (Alice/Bob)",
        "S = g^(ab) mod p",
        fmt_hex(shared_secret_original),
    )
    console.print(result_table)

    # Verification
    console.print("\n[bold yellow]Step 5:[/bold yellow] [cyan]Verification...[/cyan]")
    if eve_shared_secret == shared_secret_original:
        console.print(
            "[bold green]✓ Attack Successful![/bold green] Eve has successfully computed the same shared secret."
        )
        console.print(
            "[dim]This demonstrates that Shor's algorithm (period finding) + classical calculation breaks DH.[/dim]"
        )
    else:
        console.print(
            "[bold red]✗ Attack Failed?[/bold red] Eve's computed secret does not match the original. "
            "There might be an error in the logic or simulation."
        )
        console.print(f"Eve's Secret:   {fmt_hex(eve_shared_secret)}")
        print(f"Original Secret: {fmt_hex(shared_secret_original)}")


if __name__ == "__main__":
    main()
