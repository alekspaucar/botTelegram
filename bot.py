import os
import json
import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ChatMemberHandler,
    ContextTypes,
)

TOKEN = os.getenv("TOKEN")
GROUP_ID = -1003567037436

if not TOKEN:
    raise ValueError("NO se encontro el token en las variables de entorno")
# --------- BASE DE DATOS SIMPLE ---------
def cargar_datos():
    try:
        with open("usuarios.json", "r") as f:
            return json.load(f)
    except:
        return {}


def guardar_datos(datos):
    with open("usuarios.json", "w") as f:
        json.dump(datos, f)


# --------- ACTIVAR USUARIO (SOLO ADMIN) ---------
async def activar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    if not update.message.reply_to_message:
        await update.message.reply_text(
            "Responde al mensaje del usuario con: /activar 30"
        )
        return

    dias = int(context.args[0])
    usuario_id = update.message.reply_to_message.from_user.id

    datos = cargar_datos()
    fecha_vencimiento = (
        datetime.datetime.now() + datetime.timedelta(days=dias)
    ).strftime("%Y-%m-%d")

    datos[str(usuario_id)] = fecha_vencimiento
    guardar_datos(datos)

    await update.message.reply_text(
        f"Usuario activado hasta {fecha_vencimiento}"
    )


# --------- DETECTAR NUEVOS MIEMBROS ---------
async def nuevo_miembro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for miembro in update.chat_member.new_chat_members:
        await context.bot.send_message(
            GROUP_ID,
            f"Bienvenido {miembro.first_name}\nUn administrador debe activarte.",
        )


# --------- REVISIÓN DIARIA ---------
async def revisar_vencimientos(context: ContextTypes.DEFAULT_TYPE):
    datos = cargar_datos()
    hoy = datetime.datetime.now().strftime("%Y-%m-%d")

    for user_id, fecha in list(datos.items()):
        if fecha <= hoy:
            try:
                await context.bot.ban_chat_member(GROUP_ID, int(user_id))
                del datos[user_id]
            except:
                pass

    guardar_datos(datos)


# --------- INICIAR BOT ---------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("activar", activar))
app.add_handler(ChatMemberHandler(nuevo_miembro, ChatMemberHandler.CHAT_MEMBER))

app.job_queue.run_repeating(revisar_vencimientos, interval=86400, first=10)

print("Bot funcionando...")
app.run_polling()
