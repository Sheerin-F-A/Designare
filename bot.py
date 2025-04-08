from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
from rembg import remove
import io
import os
import subprocess
from PIL import Image

# Update this to your actual CLI binary path
REALESRGAN_CLI = "/Users/sheerinfatimaaijaz/tools/realesrgan-ncnn-vulkan/Real-ESRGAN/realesrgan-ncnn-vulkan"

TOKEN = "BOT_TOKEN_HERE"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hi! Send a photo with caption /removebg or /upscale!")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = await update.message.photo[-1].get_file()
    image_bytes = await photo.download_as_bytearray()

    input_io = io.BytesIO(image_bytes)
    input_io.seek(0)

    output_bytes = remove(input_io.getvalue(), force_return_bytes=True)
    await update.message.reply_photo(photo=output_bytes, caption="🎉 Here's your image without background!")


async def handle_upscale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Please send an image to upscale.")
        return

    photo = await update.message.photo[-1].get_file()
    input_path = "input.jpg"
    output_path = "results/input_out.png"
    await photo.download_to_drive(input_path)

    try:
        # Use the inference script provided by Real-ESRGAN
        result = subprocess.run([
            "python3", "inference_realesrgan.py",
            "-n", "RealESRGAN_x4plus",
            "-i", input_path,
            "--outscale", "2"
        ], cwd="/Users/sheerinfatimaaijaz/tools/realesrgan-ncnn-vulkan/Real-ESRGAN", check=True)

        final_output_path = "/Users/sheerinfatimaaijaz/tools/realesrgan-ncnn-vulkan/Real-ESRGAN/results/input_out.png"
        with open(final_output_path, 'rb') as img:
            await update.message.reply_photo(img, caption="🔍 Here's your upscaled image!")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Upscaling failed: {e}")
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

app = ApplicationBuilder().token(TOKEN).build()


app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO & filters.CaptionRegex(r'^/removebg'), handle_image))
app.add_handler(MessageHandler(filters.PHOTO & filters.CaptionRegex(r'^/upscale'), handle_upscale))

app.run_polling()

