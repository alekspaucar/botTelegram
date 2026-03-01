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

# 🔥 Cambiado a "TOKEN" como lo pediste
TOKEN = os.getenv("TOKEN")
ADMIN_ID = 8315102092  
GROUP_ID = -1003828473755 

ARCHIVO_DATOS = "/data/usuarios_activos.json"

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
    # Solo responde en chat privado
    if update.effective_chat.type != ChatType.PRIVATE:
        return

    mensaje = (
        "¡Hola, amor! 💕 Qué rico tenerte por aquí...\n\n"
        "Estás a un pasito de entrar a mi VIP exclusivo donde subo todo mi contenido más íntimo y sin censura 😈🔥.\n\n"
        "Ahorita la suscripción está a solo **$5 por 30 días** 💸. ¡Aprovecha mi amor, porque mientras más contenido vaya acumulando, el precio va a subir! 😏\n\n"
        "Para entrar ya mismo, haz la transferencia a la cuenta de mi manager:\n\n"
        "🏦 **Banco Pichincha**\n"
        "👤 **Nombre:** Erick Alexander Vizhñay Paucar\n"
        "🆔 **Cédula:** 0151218468\n"
        "💳 **Nro. Cuenta:** 2212355283\n\n"
        "👉 Cuando hagas el pago, **envíame la foto del comprobante aquí mismo** y te doy tu pase VIP personal al instante.\n\n"
        "¡Te espero adentro, guapo! 💋✨"
    )

    await update.message.reply_text(mensaje, parse_mode="Markdown")

async def recibir_comprobante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Solo procesar en chat privado
    if update.effective_chat.type != ChatType.PRIVATE:
        return

    user = update.effective_user
    
    # Reenvía la foto al Admin
    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=f"📩 **Nuevo Comprobante**\n\nUsuario: @{user.username}\nID: `{user.id}`\n\nPara aprobar usa:\n`/aprobar {user.id}`",
        parse_mode="Markdown"
    )
    # Mensaje coqueto de espera para el cliente
    await update.message.reply_text("✅ Comprobante enviado, mi amor. Dame un ratito que lo reviso y te doy tu acceso. 😘")

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

        # Mensaje de entrada con el link
        await context.bot.send_message(
            chat_id=user_id,
            text=f"¡Pago verificado, guapo! ✅💸\n\nAquí tienes tu pase de entrada exclusivo (es de 1 solo uso, no lo compartas). ¡Disfruta! 😈👇\n{link.invite_link}"
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
                
                # Mensaje de vencimiento coqueto para que renueve
                await context.bot.send_message(
                    user_id, 
                    "Ay, amor... Tus 30 días de suscripción VIP se han terminado. 🥺\n\nPero no te preocupes, ¡puedes renovar ahorita mismo! Mándame el nuevo comprobante de $5 por aquí y te devuelvo el acceso rapidito. 💋🔥"
                )
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
