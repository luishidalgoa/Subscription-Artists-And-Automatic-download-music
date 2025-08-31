import sys


class ProgressBar:
    """
    Gestor de progreso dinámico en la terminal.
    Cada instancia tiene su propia barra, por lo que no interfieren entre sí.
    """
    def __init__(self, total: int, prefix: str = "", bar_length: int = 40):
        self.total = total
        self.prefix = prefix
        self.bar_length = bar_length
        self.current = 0
        self.printed = False

    def update(self, step: int = 1):
        self.current += step
        percent = (self.current / self.total) * 100
        filled_length = int(self.bar_length * self.current // self.total)
        bar = "█" * filled_length + "-" * (self.bar_length - filled_length)

        if not self.printed:
            # imprimimos la barra y guardamos que ya se imprimió
            print()  
            self.printed = True

        # Mover cursor hacia arriba y reescribir
        sys.stdout.write(f"\033[F{self.prefix} |{bar}| {percent:6.2f}% ({self.current}/{self.total})\n")
        sys.stdout.flush()

        if self.current >= self.total:
            print()  # línea final