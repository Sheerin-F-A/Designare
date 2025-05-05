import io
import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
from rembg import remove
from PIL import Image, ImageDraw, ImageFont

from dotenv import load_dotenv
import os

load_dotenv()  # Loads variables from .env file

BOT_TOKEN = os.getenv("BOT_TOKEN")


# Path to the realesrgan-ncnn-vulkan CLI binary
REALESRGAN_CLI = "/Users/sheerinfatimaaijaz/tools/realesrgan-ncnn-vulkan/Real-ESRGAN/realesrgan-ncnn-vulkan"
MODEL_DIR = "/Users/sheerinfatimaaijaz/tools/realesrgan-ncnn-vulkan/Real-ESRGAN/weights"  # Directory containing the model file

# Your Telegram bot token
TOKEN = "BOT_TOKEN"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hi! Send a photo with caption /removebg, /upscale or /previewfont!")

# Handle image for background removal
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = await update.message.photo[-1].get_file()
    image_bytes = await photo.download_as_bytearray()

    input_io = io.BytesIO(image_bytes)
    input_io.seek(0)

    output_bytes = remove(input_io.getvalue(), force_return_bytes=True)
    await update.message.reply_photo(photo=output_bytes, caption="🎉 Here's your image without background!")

# Handle image upscaling using realesrgan
async def handle_upscale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Please send an image to upscale.")
        return

    photo = await update.message.photo[-1].get_file()
    input_path = "input.jpg"
    output_path = "output_upscaled.png"
    await photo.download_to_drive(input_path)

    try:
        # Corrected subprocess command for upscaling
        result = subprocess.run([
            REALESRGAN_CLI,
            "-i", input_path,            # input image path
            "-o", output_path,           # output image path
            "-s", "2",                   # scale factor (upscale by 2x)
            "-n", "RealESRGAN_x4plus",   # model name (RealESRGAN_x4plus)
            "-m", MODEL_DIR              # path to the directory containing the model file
        ], cwd="/Users/sheerinfatimaaijaz/tools/realesrgan-ncnn-vulkan/Real-ESRGAN", check=True)

        with open(output_path, 'rb') as img:
            await update.message.reply_photo(img, caption="🔍 Here's your upscaled image!")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Upscaling failed: {e}")
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

# Font Preview Feature

async def preview_font(update, context):
    if len(context.args) < 2:
        await update.message.reply_text("❗ Usage: /previewfont <FontName> <Your Text>")
        return

    font_name = context.args[0]
    text = " ".join(context.args[1:])

    try:
        # Construct the URL for downloading the font from Google Fonts (no zip)
        font_url = f"https://fonts.googleapis.com/css2?family={font_name.replace(' ', '+')}"

        # Fetch the font CSS file
        response = requests.get(font_url)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch font CSS: {font_url} (Status Code: {response.status_code})")

        # Extract the actual font URL from the CSS file
        import re
        font_url_match = re.search(r"url\((https://fonts.gstatic.com[^)]+)\)", response.text)
        if not font_url_match:
            raise Exception("Font URL not found in the CSS.")

        font_file_url = font_url_match.group(1)

        # Download the font file (ttf/otf)
        font_response = requests.get(font_file_url)
        if font_response.status_code != 200:
            raise Exception(f"Failed to fetch font file: {font_file_url} (Status Code: {font_response.status_code})")

        # Save the font to a temporary file in memory
        font_bytes = io.BytesIO(font_response.content)
        font = ImageFont.truetype(font_bytes, 60)

        # Create an image to draw the text
        image = Image.new("RGB", (len(text) * 40, 100), color="white")
        draw = ImageDraw.Draw(image)
        draw.text((10, 10), text, font=font, fill="black")

        # Save the image in a binary stream and send to user
        bio = io.BytesIO()
        bio.name = f"{font_name}_preview.png"
        image.save(bio, "PNG")
        bio.seek(0)
        await update.message.reply_photo(photo=bio, caption=f"🖋️ Preview using font: *{font_name}*", parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Could not generate preview. Maybe the font `{font_name}` doesn't exist or there's an issue with the font file.\nError: {e}")

# font download feature
async def send_font(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("❗ Usage: /getfont <FontName>")
        return

    font_name = context.args[0]

    try:
        # Construct the URL to fetch the font CSS file from Google Fonts
        font_url = f"https://fonts.googleapis.com/css2?family={font_name.replace(' ', '+')}"

        # Fetch the font CSS file
        response = requests.get(font_url)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch font CSS: {font_url} (Status Code: {response.status_code})")

        # Extract the actual font URL from the CSS file
        import re
        font_url_match = re.search(r"url\((https://fonts.gstatic.com[^)]+)\)", response.text)
        if not font_url_match:
            raise Exception("Font URL not found in the CSS.")

        font_file_url = font_url_match.group(1)

        # Download the font file (ttf/otf)
        font_response = requests.get(font_file_url)
        if font_response.status_code != 200:
            raise Exception(f"Failed to fetch font file: {font_file_url} (Status Code: {font_response.status_code})")

        # Create a byte stream from the font file
        font_bytes = io.BytesIO(font_response.content)
        font_bytes.name = f"{font_name}.ttf"

        # Send the font file to the user
        await update.message.reply_document(document=font_bytes, filename=f"{font_name}.ttf")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Could not fetch the font `{font_name}`. Error: {e}")

# Set up the bot with command handlers
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO & filters.CaptionRegex(r'^/removebg'), handle_image))
app.add_handler(MessageHandler(filters.PHOTO & filters.CaptionRegex(r'^/upscale'), handle_upscale))
app.add_handler(CommandHandler("previewfont", preview_font))
app.add_handler(CommandHandler("getfont", send_font))

# Run the bot
app.run_polling()
