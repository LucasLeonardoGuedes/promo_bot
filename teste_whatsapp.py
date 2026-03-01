from scraper.selenium_busca import iniciar_driver_whatsapp
from poster.whatsapp_channel import enviar_whatsapp_canal

driver = iniciar_driver_whatsapp()

enviar_whatsapp_canal(
    driver,
    "Radar Tech",
    "TESTE DE ENVIO AUTOMÁTICO "
)