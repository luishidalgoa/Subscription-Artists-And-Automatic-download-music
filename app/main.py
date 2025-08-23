from app.providers.app_provider import AppProvider

def main():
    app = AppProvider()
    app.run()

# Esto permite que siga funcionando con python -m app.main
if __name__ == "__main__":
    main()
