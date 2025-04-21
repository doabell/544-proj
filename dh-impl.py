import random
import time
import json

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
from rich.syntax import Syntax

console = Console()


def dh_params() -> tuple[int, int]:
    """
    Generate realistic parameters for Diffie-Hellman key exchange.
    Using pre-computed values for efficiency.

    Returns:
        Tuple of (p, g) where p is a large prime and g is a generator
    """
    # NIST-recommended 2048-bit prime for DH
    # This is the "Second Oakley Group" prime
    p = int(
        "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1"
        + "29024E088A67CC74020BBEA63B139B22514A08798E3404DD"
        + "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245"
        + "E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
        + "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3D"
        + "C2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F"
        + "83655D23DCA3AD961C62F356208552BB9ED529077096966D"
        + "670C354E4ABC9804F1746C08CA18217C32905E462E36CE3B"
        + "E39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9"
        + "DE2BCBF6955817183995497CEA956AE515D2261898FA0510"
        + "15728E5A8AACAA68FFFFFFFFFFFFFFFF",
        16,
    )

    # Generator for the group, usually 2 for DH
    g = 2

    return p, g


def dh_pk(p: int) -> int:
    """Generate a private key for Diffie-Hellman."""
    bit_length = min(256, p.bit_length() - 1)
    max_key_val = p - 2
    private_key = 0
    while private_key == 0:
        private_key = random.getrandbits(bit_length)
        private_key = private_key % max_key_val + 1
    return private_key


def dh_pubkey(private_key: int, g: int, p: int) -> int:
    """Generate a public key for Diffie-Hellman."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold green]Generating public key...[/bold green]"),
        BarColumn(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("Calculating...", total=None)
        start_time = time.time()
        result = pow(g, private_key, p)
        end_time = time.time()
        progress.update(task, completed=True)

    computation_time = end_time - start_time
    console.print(
        f"[cyan]Public key generation took[/cyan] [bold yellow]{computation_time:.4f}[/bold yellow] [cyan]seconds[/cyan]"
    )
    return result


def dh_ss(other_public_key: int, private_key: int, p: int) -> int:
    """Generate the shared secret for Diffie-Hellman."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Computing shared secret...[/bold blue]"),
        BarColumn(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("Calculating...", total=None)
        start_time = time.time()
        result = pow(other_public_key, private_key, p)
        end_time = time.time()
        progress.update(task, completed=True)

    computation_time = end_time - start_time
    console.print(
        f"[cyan]Shared secret computation took[/cyan] [bold yellow]{computation_time:.4f}[/bold yellow] [cyan]seconds[/cyan]"
    )
    return result


def fmt_hex(number: int, max_len: int = 32) -> str:
    """Format a big number for display: show first few and last few hex digits."""
    hex_str = hex(number)[2:]
    half_len = max_len // 2
    if len(hex_str) <= max_len:
        return f"0x{hex_str}"
    return f"0x{hex_str[:half_len]}...{hex_str[-half_len:]}"


def print_dh_math() -> None:
    """Print the mathematical operations of Diffie-Hellman using Rich syntax highlighting."""
    math_code = """
    # Public Setup
    p = large prime number
    g = generator modulo p (often 2 or 5)

    # Private Key Generation (Secret)
    Alice chooses private key: a (random integer, 1 < a < p-1 or 1 < a < order(g) )
    Bob chooses private key:   b (random integer, 1 < b < p-1 or 1 < b < order(g) )

    # Public Key Calculation (Shared over insecure channel)
    Alice computes public key: A = g^a mod p
    Bob computes public key:   B = g^b mod p

    # Shared Secret Computation (Private)
    Alice computes: S = B^a mod p = (g^b)^a mod p = g^(a*b) mod p
    Bob computes:   S = A^b mod p = (g^a)^b mod p = g^(a*b) mod p

    # Security relies on the difficulty of the Discrete Logarithm Problem (DLP):
    # Given A, g, p, it's computationally hard to find 'a'.
    # Given B, g, p, it's computationally hard to find 'b'.
    """

    syntax = Syntax(math_code, "python", theme="monokai", line_numbers=True)
    console.print(
        Panel(syntax, title="Diffie-Hellman Key Exchange", border_style="green")
    )


def save_dh(data: dict[str], filename: str = "dh-exchange.json") -> None:
    """Save the key exchange data (WITHOUT order r) to a file."""
    with open(filename, "w") as f:
        json_data = {
            "p": str(data["p"]),
            "g": data["g"],
            "alice_public": str(data["alice_public"]),
            "bob_public": str(data["bob_public"]),
            "alice_private": str(data["alice_private"]),
            "bob_private": str(data["bob_private"]),
            "shared_secret": str(data["shared_secret"]),
        }
        json.dump(json_data, f, indent=2)
    console.print(f"[bold green]Key exchange data saved to {filename}[/bold green]")


def main() -> None:
    """Demonstrate Diffie-Hellman key exchange with rich output."""
    console.print(
        Panel.fit(
            "[bold cyan]Cracking Diffie-Hellman with Shor's algorithm[/bold cyan]",
            border_style="cyan",
        )
    )

    # Print mathematical explanation
    print_dh_math()

    # Generate parameters
    console.print(
        "\n[bold green]Step 1:[/bold green] [yellow]Generating DH parameters (p, g)...[/yellow]"
    )
    p, g = dh_params()

    param_table = Table(show_header=True, header_style="bold blue")
    param_table.add_column("Parameter")
    param_table.add_column("Value")
    param_table.add_column("Notes")

    param_table.add_row(
        "Prime (p) size", f"{p.bit_length()} bits", "NIST recommended size"
    )
    param_table.add_row(
        "Prime (p) value",
        fmt_hex(p),
        "",
    )
    param_table.add_row("Generator (g)", f"{g}", "Common generator value")
    console.print(param_table)

    # Generate private keys
    console.print(
        "\n[bold green]Step 2:[/bold green] [yellow]Generating private keys (a, b)...[/yellow]"
    )

    alice_private = dh_pk(p)
    bob_private = dh_pk(p)

    key_table = Table(show_header=True, header_style="bold blue")
    key_table.add_column("Party")
    key_table.add_column("Private Key Size")
    key_table.add_column("Private Key (partial hex)")

    key_table.add_row(
        "Alice (a)",
        f"{alice_private.bit_length()} bits",
        fmt_hex(alice_private),
    )
    key_table.add_row(
        "Bob (b)", f"{bob_private.bit_length()} bits", fmt_hex(bob_private)
    )
    console.print(key_table)

    # Generate public keys
    console.print(
        "\n[bold green]Step 3:[/bold green] [yellow]Computing public keys (A = g^a mod p, B = g^b mod p)...[/yellow]"
    )

    alice_public = dh_pubkey(alice_private, g, p)
    bob_public = dh_pubkey(bob_private, g, p)

    public_key_table = Table(show_header=True, header_style="bold blue")
    public_key_table.add_column("Party")
    public_key_table.add_column("Public Key Size")
    public_key_table.add_column("Public Key (partial hex)")

    public_key_table.add_row(
        "Alice (A)",
        f"{alice_public.bit_length()} bits",
        fmt_hex(alice_public),
    )
    public_key_table.add_row(
        "Bob (B)", f"{bob_public.bit_length()} bits", fmt_hex(bob_public)
    )
    console.print(public_key_table)

    # Exchange simulation
    console.print(
        "\n[bold green]Step 4:[/bold green] [yellow]Simulating Public Key Exchange...[/yellow]"
    )
    console.print(
        f"Alice sends A = {fmt_hex(alice_public)} to Bob [bold]→[/bold]"
    )
    console.print(
        f"Bob sends B = {fmt_hex(bob_public)} to Alice [bold]←[/bold]"
    )
    console.print("[dim](Eve intercepts A, B, p, g)[/dim]")

    # Generate shared secrets
    console.print(
        "\n[bold green]Step 5:[/bold green] [yellow]Computing Shared Secrets (S = B^a mod p, S = A^b mod p)...[/yellow]"
    )

    alice_shared = dh_ss(bob_public, alice_private, p)
    bob_shared = dh_ss(alice_public, bob_private, p)

    # Verify keys match
    shared_key_table = Table(show_header=True, header_style="bold blue")
    shared_key_table.add_column("Party")
    shared_key_table.add_column("Computed Shared Secret (partial hex)")

    shared_key_table.add_row("Alice (S = B^a mod p)", fmt_hex(alice_shared))
    shared_key_table.add_row("Bob (S = A^b mod p)", fmt_hex(bob_shared))
    console.print(shared_key_table)

    if alice_shared == bob_shared:
        console.print(
            "[bold green]✓ Success![/bold green] Alice and Bob have computed the same shared secret."
        )

        # Save keys to file for Eve to intercept
        save_dh(
            {
                "p": p,
                "g": g,
                "alice_public": alice_public,
                "bob_public": bob_public,
                "alice_private": alice_private,
                "bob_private": bob_private,
                "shared_secret": alice_shared,
            }
        )

        console.print(
            "\n[bold yellow]Now run dh-crack.py to simulate Eve's attack (which will include simulating Shor's algorithm)[/bold yellow]"
        )
    else:
        console.print(
            "[bold red]✗ Error![/bold red] Shared secrets don't match. Something went wrong."
        )


if __name__ == "__main__":
    main()
