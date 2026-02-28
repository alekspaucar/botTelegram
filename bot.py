import os
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
import asyncio

# ===== CONFIG =====
TOKEN = os.getenv("TOKEN")
GROUP_ID = -1001234567890  # ⚠️ CAMBIA ESTO por tu ID real

if not TOKEN:
    raise ValueError("NO se encontro el token en las variables de entorno")

# ===== BASE SIMPLE EN MEMORIA =====
usuarios = {}

# ===== COMANDOS =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot activo ✅")

async def agregar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(context.args[0])
        dias = int(context.args[1])

        fecha_vencimiento = datetime.now() + timedelta(days=dias)
        usuarios[user_id] = fecha_vencimiento

        invite_link = await context.bot.create_chat_invite_link(
            chat_id=GROUP_ID,
            member_limit=1
        )

        await update.message.reply_text(
            f"Usuario agregado hasta {fecha_vencimiento.strftime('%Y-%m-%d')} ✅\n"
            f"Link de acceso:\n{invite_link.invite_link}"
        )

    except:
        await update.message.reply_text(
            "Uso correcto:\n/agregar ID_USUARIO DIAS"
        )

async def revisar_vencimientos(context: ContextTypes.DEFAULT_TYPE):
    ahora = datetime.now()

    for user_id, fecha in list(usuarios.items()):
        if ahora > fecha:
            try:
                await context.bot.ban_chat_member(GROUP_ID, user_id)
                await context.bot.unban_chat_member(GROUP_ID, user_id)
                del usuarios[user_id]
                print(f"Usuario {user_id} eliminado por vencimiento")
            except Exception as e:
                print(f"Error eliminando usuario {user_id}: {e}")

# ===== MAIN =====

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("agregar", agregar))

    app.job_queue.run_repeating(revisar_vencimientos, interval=3600, first=10)

    print("Bot funcionando...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
