import os
import json
from datetime import datetime, timedelta
from telegram import Update
from telegram.constants import ChatType
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8315102092  
GROUP_ID = -1003828473755 

ARCHIVO_DATOS = "usuarios_activos.json"

# --- BASE DE DATOS ---

def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, "r") as f:
            try:
                datos = json.load(f)
                return {int(k): datetime.fromisoformat(v) for k, v in datos.items()}
            except:
                return {}
    return {}

def guardar_datos(datos):
    datos_str = {str(k): v.isoformat() for k, v in datos.items()}
    with open(ARCHIVO_DATOS, "w") as f:
        json.dump(datos_str, f, indent=4)

usuarios_activos = cargar_datos()

# --- LÓGICA DEL BOT ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 🔥 ARREGLO 1: Si no es un chat privado (es un grupo), el bot ignora el mensaje
    if update.effective_chat.type != ChatType.PRIVATE:
        return

    await update.message.reply_text(
        "Bienvenido 🔥\n\nPor favor, envíame una foto de tu comprobante de pago."
    )

async def recibir_comprobante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Solo procesar en chat privado
    if update.effective_chat.type != ChatType.PRIVATE:
        return

    user = update.effective_user
    # 🔥 ARREGLO 2: Te reenvía la foto al Admin
    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=f"📩 **Nuevo Comprobante**\n\nUsuario: @{user.username}\nID: `{user.id}`\n\nPara aprobar usa:\n`/aprobar {user.id}`",
        parse_mode="Markdown"
    )
    await update.message.reply_text("✅ Comprobante enviado. El administrador lo revisará pronto.")

async def aprobar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usa: /aprobar ID_USUARIO")
        return

    try:
        user_id = int(context.args[0])
        fecha_vencimiento = datetime.now() + timedelta(days=30)
        
        usuarios_activos[user_id] = fecha_vencimiento
        guardar_datos(usuarios_activos)

        link = await context.bot.create_chat_invite_link(
            chat_id=GROUP_ID,
            member_limit=1
        )

        await context.bot.send_message(
            chat_id=user_id,
            text=f"Pago aprobado ✅\n\nEntra al grupo (El enlace es de 1 solo uso):\n{link.invite_link}"
        )

        await update.message.reply_text(f"Usuario {user_id} aprobado y guardado en la BD 🔥")
    except Exception as e:
        await update.message.reply_text(f"Hubo un error: {e}")

async def revisar_vencimientos(context: ContextTypes.DEFAULT_TYPE):
    ahora = datetime.now()
    hubo_cambios = False

    for user_id, fecha in list(usuarios_activos.items()):
        if ahora >= fecha:
            try:
                # Expulsa al usuario
                await context.bot.ban_chat_member(GROUP_ID, user_id)
                await context.bot.unban_chat_member(GROUP_ID, user_id)
                await context.bot.send_message(user_id, "Tu suscripción de 30 días ha expirado. 😔\nRenueva enviando un nuevo comprobante aquí.")
            except:
                pass
            
            del usuarios_activos[user_id]
            hubo_cambios = True

    if hubo_cambios:
        guardar_datos(usuarios_activos)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("aprobar", aprobar))
    app.add_handler(MessageHandler(filters.PHOTO, recibir_comprobante))

    job_queue = app.job_queue
    job_queue.run_repeating(revisar_vencimientos, interval=60)

    print("Bot final desplegado y funcionando...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
