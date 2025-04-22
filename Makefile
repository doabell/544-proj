.PHONY: default list uv ruff dh clean clean-dh clean-rsa

default: list

list:
	@echo "Available targets:"
	@echo "  uv:        Install uv"
	@echo "  ruff:      Run ruff linter & formatter"
	@echo "  dh:        Echo Diffie-Hellman implementations"
	@echo "  rsa:       Echo RSA implementations"
	@echo "  clean:     Clean up temporary files"
	@echo "  clean-dh:  Clean up Diffie-Hellman temporary files"
	@echo "  clean-rsa: Clean up RSA temporary files"

ruff:
	uvx ruff check --fix .
	uvx ruff format .

uv:
	curl -LsSf https://astral.sh/uv/install.sh | sh

dh:
	@echo "uv run dh-impl.py"
	@echo "uv run dh-crack.py"
	@echo "uv run dh-quantum.py"

clean: clean-dh clean-rsa
	@echo "All clean targets executed"

clean-dh:
	rm -rf db-quantum.png db-quantum-circuit.png db-exchange.json

clean-rsa:
	@echo "RSA: nothing to clean for now"