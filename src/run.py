import logging
import os
import time
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

from config.produtos import carregar_produtos, identificar_marketplace
from src.models import ProductSnapshot
from src.notifier import send_whatsapp_text
from src.notifier.telegram import send_telegram
from src.rules import apply_promo_rules
from src.scrapers import (
    coletar_produto_amazon_v2,
    coletar_produto_magalu,
    coletar_produto_ml_v2,
)
from src.storage import save_check_and_maybe_history
from src.storage.migrate import migrate
from src.text_generator.message_builder import build_offer_message
from src.validator import validate_snapshot

try:
    from dotenv import load_dotenv
except ImportError:  # fallback para ambientes sem python-dotenv
    def load_dotenv():
        return False


def _setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "v2_run.log"

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root.addHandler(console_handler)
    root.addHandler(file_handler)


def _coletar_snapshot(item):
    url = item.get("url", "")
    categoria = item.get("categoria")
    marketplace = identificar_marketplace(url)

    if marketplace == "mercadolivre":
        ml_data = coletar_produto_ml_v2(url, driver=None)
        produto = ml_data.get("produto")
        flags = ml_data.get("flags") or {}
        html = ml_data.get("html")
        texto = ml_data.get("texto")

        if produto:
            snapshot = ProductSnapshot(
                nome=produto.get("nome") or categoria or url,
                link=url,
                marketplace=marketplace,
                preco=produto.get("preco"),
                imagem=produto.get("imagem"),
                categoria=categoria,
                disponivel=not flags.get("encontrou_texto_indisponivel"),
                raw_html=html,
                raw_text=texto,
                scraper_flags=flags,
            )
        else:
            snapshot = ProductSnapshot(
                nome=categoria or url,
                link=url,
                marketplace=marketplace,
                preco=flags.get("preco_extraido_html"),
                categoria=categoria,
                disponivel=not flags.get("encontrou_texto_indisponivel"),
                raw_html=html,
                raw_text=texto,
                scraper_flags=flags,
            )

        return snapshot, {
            "collector": marketplace,
            "collected": bool(produto),
            "flags": flags,
        }

    if marketplace == "amazon":
        amz_data = coletar_produto_amazon_v2(url)
        produto = amz_data.get("produto")
        flags = amz_data.get("flags") or {}
        html = amz_data.get("html")
        texto = amz_data.get("texto")

        preco_final = flags.get("preco_principal")
        if preco_final is None and produto:
            preco_final = produto.get("preco")

        if produto:
            snapshot = ProductSnapshot(
                nome=produto.get("nome") or categoria or url,
                link=url,
                marketplace=marketplace,
                preco=preco_final,
                imagem=produto.get("imagem"),
                categoria=categoria,
                disponivel=not flags.get("encontrou_indisponivel_texto"),
                raw_html=html,
                raw_text=texto,
                scraper_flags=flags,
            )
        else:
            snapshot = ProductSnapshot(
                nome=categoria or url,
                link=url,
                marketplace=marketplace,
                preco=preco_final,
                categoria=categoria,
                disponivel=not flags.get("encontrou_indisponivel_texto"),
                raw_html=html,
                raw_text=texto,
                scraper_flags=flags,
            )

        return snapshot, {
            "collector": marketplace,
            "collected": bool(produto),
            "flags": flags,
        }

    elif marketplace == "magalu":
        produto = coletar_produto_magalu(url)
    else:
        produto = None

    if produto:
        return ProductSnapshot(
            nome=produto.get("nome") or categoria or url,
            link=url,
            marketplace=marketplace,
            preco=produto.get("preco"),
            imagem=produto.get("imagem"),
            categoria=categoria,
            disponivel=True,
            scraper_flags={},
        ), {"collector": marketplace, "collected": True}

    return ProductSnapshot(
        nome=categoria or url,
        link=url,
        marketplace=marketplace,
        preco=None,
        categoria=categoria,
        disponivel=False,
        scraper_flags={},
    ), {"collector": marketplace, "collected": False}


def main():
    _setup_logging()
    logger = logging.getLogger("v2.run")

    load_dotenv()

    whatsapp_provider = os.getenv("WHATSAPP_PROVIDER", "disabled").strip().lower()
    if whatsapp_provider not in {"disabled", "selenium", "cloud"}:
        logger.warning(
            "WHATSAPP_PROVIDER inválido '%s'. Usando 'disabled'.",
            whatsapp_provider,
        )
        whatsapp_provider = "disabled"

    logger.info("WHATSAPP_PROVIDER=%s", whatsapp_provider)
    logger.info("WhatsApp provider ativo no V2: %s", whatsapp_provider)
    send_suspect_telegram = os.getenv("V2_TELEGRAM_SUSPECT", "0").strip() in {"1", "true", "True"}
    whatsapp_to = os.getenv("WHATSAPP_TO", "").strip()
    loop_mode = os.getenv("V2_LOOP", "0").strip() in {"1", "true", "True"}
    once_mode = os.getenv("V2_ONCE", "0").strip() in {"1", "true", "True"}
    sleep_seconds = int(os.getenv("V2_SLEEP_SECONDS", "300"))

    migrate()
    max_items = int(os.getenv("V2_MAX_PRODUCTS", "20"))

    def run_cycle(cycle_number):
        cycle_start = time.monotonic()
        produtos = carregar_produtos()
        produtos = produtos[:max_items]

        print("V2 skeleton ok")
        print(f"quantidade de produtos: {len(produtos)}")
        logger.info("inicio ciclo=%s total_produtos=%s", cycle_number, len(produtos))

        validos = 0
        invalidos = 0
        suspect_count = 0
        promo_count = 0
        invalidos_por_motivo = defaultdict(int)

        for item in produtos:
            url = item.get("url", "")
            marketplace = identificar_marketplace(url) or "desconhecido"
            print(f"marketplace: {marketplace} | url: {url}")

            snapshot, raw_meta = _coletar_snapshot(item)
            validation = validate_snapshot(snapshot)
            promo_decision = apply_promo_rules(snapshot, validation)

            if raw_meta is None:
                raw_meta = {}
            raw_meta["promo_rule"] = asdict(promo_decision)

            if promo_decision.status == "SUSPECT":
                validation.status = "SUSPECT"
                validation.reason = f"{validation.reason}; {promo_decision.reason}"

            result = save_check_and_maybe_history(snapshot, validation, raw_meta=raw_meta)
            logger.info(
                "validacao marketplace=%s status=%s motivo=%s promo_status=%s drop_pct=%s url=%s",
                snapshot.marketplace,
                validation.status,
                validation.reason,
                promo_decision.status,
                promo_decision.drop_pct,
                snapshot.link,
            )

            if result["status_validacao"] == "VALID":
                validos += 1
            else:
                invalidos += 1
                if result["status_validacao"] == "SUSPECT":
                    suspect_count += 1
                else:
                    invalidos_por_motivo[validation.reason] += 1

            if promo_decision.status == "PROMO":
                promo_count += 1
                msg = build_offer_message(snapshot, promo_decision)
                wa_sent = send_whatsapp_text(whatsapp_to, msg)
                logger.info("whatsapp promo sent=%s", wa_sent)
                if not wa_sent:
                    tg = send_telegram(msg)
                    logger.info("telegram fallback promo sent=%s reason=%s", tg.get("sent"), tg.get("reason"))
            elif promo_decision.status == "SUSPECT" and send_suspect_telegram:
                msg = build_offer_message(snapshot, promo_decision)
                tg = send_telegram(msg)
                logger.info("telegram suspect sent=%s reason=%s", tg.get("sent"), tg.get("reason"))

        elapsed = time.monotonic() - cycle_start
        logger.info("fim ciclo=%s processados=%s validos=%s invalidos=%s", cycle_number, len(produtos), validos, invalidos)
        logger.info("price_checks gravados: %s", len(produtos))
        logger.info(
            "resumo ciclo=%s total_checks=%s suspect=%s promo_disparadas=%s tempo_total=%.2fs",
            cycle_number,
            len(produtos),
            suspect_count,
            promo_count,
            elapsed,
        )
        if invalidos_por_motivo:
            for motivo, qtd in sorted(invalidos_por_motivo.items(), key=lambda x: x[1], reverse=True):
                logger.info("invalidos motivo='%s' qtd=%s", motivo, qtd)
        else:
            logger.info("invalidos por motivo: nenhum")

        print("\nResumo do ciclo")
        print(f"- total checks: {len(produtos)}")
        print(f"- inválidos por motivo: {dict(invalidos_por_motivo)}")
        print(f"- SUSPECT: {suspect_count}")
        print(f"- PROMO disparadas: {promo_count}")
        print(f"- tempo total: {elapsed:.2f}s")

    if once_mode or not loop_mode:
        run_cycle(1)
        return

    cycle = 1
    logger.info("modo loop ativo sleep_seconds=%s", sleep_seconds)
    try:
        while True:
            run_cycle(cycle)
            cycle += 1
            logger.info("aguardando proximo ciclo por %s segundos", sleep_seconds)
            time.sleep(sleep_seconds)
    except KeyboardInterrupt:
        logger.info("loop interrompido pelo usuario")


if __name__ == "__main__":
    main()
