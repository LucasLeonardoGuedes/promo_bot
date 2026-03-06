import argparse
import os

from src.notifier.whatsapp_cloud import send_whatsapp_text

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return False


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Envia mensagem teste via WhatsApp Cloud API")
    parser.add_argument("--to", required=False, default=os.getenv("WHATSAPP_TO", ""))
    parser.add_argument("--text", required=True)
    args = parser.parse_args()

    ok = send_whatsapp_text(args.to, args.text)
    print("sent:", ok)


if __name__ == "__main__":
    main()

