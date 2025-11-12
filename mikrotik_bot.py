import warnings
warnings.filterwarnings("ignore")

from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext
from routeros_api import RouterOsApiPool

# --- Konfigurasi ---
TELEGRAM_TOKEN = "8151793191:AAGE4ug2wkIZtNCTmGW-iAiS8BMMQt-KMIU"
MIKROTIK_HOST = "192.168.10.1"
MIKROTIK_USERNAME = "admin"
MIKROTIK_PASSWORD = ""
MIKROTIK_PORT = 8728

VALID_USERS = ["aida", "rido", "dinda", "niko", "dias", "zilfa", "isal", "ratna", "adnan"]

def mikrotik_connect():
    try:
        api_pool = RouterOsApiPool(
            host=MIKROTIK_HOST,
            username=MIKROTIK_USERNAME,
            password=MIKROTIK_PASSWORD,
            port=MIKROTIK_PORT,
            plaintext_login=True
        )
        return api_pool.get_api()
    except Exception as e:
        print(f"Koneksi ke Mikrotik gagal: {e}")
        return None

def aktifkan(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        update.message.reply_text("Contoh: /aktifkan adnan")
        return

    user = context.args[0].lower()
    if user not in VALID_USERS:
        update.message.reply_text("User tidak dikenal.")
        return

    api = mikrotik_connect()
    if not api:
        update.message.reply_text("Gagal konek ke Mikrotik.")
        return

    try:
        ppp_secret = api.get_resource('/ppp/secret')
        ppp_secret.set(name=user, disabled='no')

        update.message.reply_text(
            f"✅ User *{user}* berhasil diaktifkan.\nJika modem belum terkoneksi, tunggu beberapa detik atau restart modem.",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        update.message.reply_text(f"Terjadi error: {e}")

def offkan(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        update.message.reply_text("Contoh: /offkan adnan")
        return

    user = context.args[0].lower()
    if user not in VALID_USERS:
        update.message.reply_text("User tidak dikenal.")
        return

    api = mikrotik_connect()
    if not api:
        update.message.reply_text("Gagal konek ke Mikrotik.")
        return

    try:
        ppp_secret = api.get_resource('/ppp/secret')
        ppp_secret.set(name=user, disabled='yes')

        # Putuskan koneksi aktif
        ppp_active = api.get_resource('/ppp/active')
        sessions = ppp_active.get()
        for session in sessions:
            if session.get('name') == user:
                ppp_active.remove(id=session['.id'])
                break

        update.message.reply_text(
            f"⛔️ User *{user}* berhasil dinonaktifkan & koneksi diputus.",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        update.message.reply_text(f"Terjadi error: {e}")

def cek(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        update.message.reply_text("Contoh: /cek adnan")
        return

    user = context.args[0].lower()
    if user not in VALID_USERS:
        update.message.reply_text("User tidak dikenal.")
        return

    api = mikrotik_connect()
    if not api:
        update.message.reply_text("Gagal konek ke Mikrotik.")
        return

    try:
        active = api.get_resource('/ppp/active')
        usage = active.get(name=user)

        queue = api.get_resource('/queue/simple')
        queue_data = queue.get(name=f"pppoe-{user}")

        if queue_data:
            rx = int(queue_data[0]['bytes'][0])
            tx = int(queue_data[0]['bytes'][1])
            total_mb = (rx + tx) / (1024 * 1024)
            kuota_text = f"\n📊 Pemakaian: {total_mb:.2f} MB"
        else:
            kuota_text = "\n📊 Pemakaian: Tidak ditemukan"

        if usage:
            ip_address = usage[0].get('address', 'N/A')
            uptime = usage[0].get('uptime', 'N/A')
            update.message.reply_text(
                f"📶 *{user}* sedang aktif\nIP: {ip_address}\nUptime: {uptime}{kuota_text}",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            update.message.reply_text(
                f"🔌 *{user}* sedang offline.{kuota_text}",
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        update.message.reply_text(f"Terjadi error: {e}")

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Saya siap menerima perintah dari bos!\nGunakan:\n/aktifkan [nama]\n/offkan [nama]\n/cek [nama]")

def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("aktifkan", aktifkan))
    dp.add_handler(CommandHandler("offkan", offkan))
    dp.add_handler(CommandHandler("cek", cek))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
