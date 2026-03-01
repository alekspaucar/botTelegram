import os
import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

TOKEN = os.getenv("TOKEN")
ADMIN_ID = 8315102092  
GROUP_ID = -1003828473755 

usuarios_activos = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bienvenido 🔥\n\nEnvíame tu comprobante de pago."
    )

async def aprobar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usa: /aprobar ID_USUARIO")
        return

    user_id = int(context.args[0])
    fecha_vencimiento = datetime.now() + timedelta(days=30)
    usuarios_activos[user_id] = fecha_vencimiento

    link = await context.bot.create_chat_invite_link(
        chat_id=GROUP_ID,
        member_limit=1
    )

    await context.bot.send_message(
        chat_id=user_id,
        text=f"Pago aprobado ✅\n\nEntra al grupo:\n{link.invite_link}"
    )

    await update.message.reply_text("Usuario aprobado 🔥")

async def revisar_vencimientos(context: ContextTypes.DEFAULT_TYPE):
    ahora = datetime.now()

    for user_id, fecha in list(usuarios_activos.items()):
        if ahora >= fecha:
            try:
                await context.bot.ban_chat_member(GROUP_ID, user_id)
                await context.bot.unban_chat_member(GROUP_ID, user_id)
            except:
                pass
            del usuarios_activos[user_id]

# 🔥 CAMBIO CRÍTICO: main() ya no es 'async def'
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("aprobar", aprobar))

    job_queue = app.job_queue
    job_queue.run_repeating(revisar_vencimientos, interval=60)

    print("Bot funcionando en Railway...")
    # drop_pending_updates ignora los mensajes viejos acumulados al reiniciar
    app.run_polling(drop_pending_updates=True) 

if __name__ == "__main__":
    main()
