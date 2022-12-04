from os import getenv

tg_api_hash = getenv("TG_API_HASH", None)
tg_api_id = getenv("TG_API_ID", None)
tg_bot_token = getenv("TG_BOT_TOKEN", None)
fly_web_port = getenv("PORT", "8080")
fly_app_name = getenv("RENDER_APP_NAME", "placeholder")
bot_users = ["el_garro"]
