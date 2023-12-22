# Simple telegram bot that takes uses stable diffusion
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update,InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    CallbackContext,
)
from backend import BackEnd,post_process
import numpy as np 
import json 
from PIL import Image
import logging
import yaml
import emoji

''' Importing YAML'''
with open("config.yaml", "r") as f:
      config = yaml.safe_load(f)

model = config['model']
api_key = config['API_KEY']

''' States for bot'''
ONE,TWO = range(2)
START,T2IMG,T2IMG2,IMG2IMG,IMG2IMG2= range(5)

''' User logging'''
logging.basicConfig(
     format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s', level = logging.INFO
)

logger = logging.getLogger(__name__)

''' Important pipeline for stable diffusion'''       
engine = BackEnd(model)

''' Function for bot'''
async def startcommand(update,context): 
    keyboard = [
        [ InlineKeyboardButton("Text To Image", callback_data = str(ONE)),
        InlineKeyboardButton("Image Editing",callback_data = str(TWO))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("StableVision Bot v1.0 \U0001F308\
                                    \nby harvestingm00n \U0001F343\
                                    \n\n\nPlease select an option!",reply_markup = reply_markup)
    return START
async def info(update: Update, _:CallbackContext) -> None:
      await update.message.reply_text("StableVision Bot v1.0  \U0001F308\
                                    \n\n Technical Info: \
                                    \n\n Model: Stable Diffusion v2.0 \U0001F3A8 \
                                    \n\n Pipeline: HuggingFace \U0001F917 \
                                    \n\n GPU: min. 6gb VRAM \
                                      ") 
async def text_to_image(update: Update, _: CallbackContext) -> int:
        query = update.callback_query
        query.answer()
        await query.edit_message_text("Please input the text you want to convert to image \u2328\
                                      \nIf you are using this in a group chat please reply to the bot \
                                      \n\nNote: This may take a while...")
        return T2IMG

async def image_to_image(update: Update, _: CallbackContext) -> int:
        query = update.callback_query
        query.answer()
        await query.edit_message_text("Please input the image you want to edit \U0001F5BC\
                                    \n\nIf you are using this in a group chat please reply to the bot")
        return IMG2IMG

async def img2img(update: Update, context: CallbackContext) -> None:
        user_photo = await update.message.photo[-1].get_file()
        array = await user_photo.download_as_bytearray()
        engine.change_picture(array) # temporarily storing the photo there ( will always override no matter what)
        await update.message.reply_text("Please input the text you want to convert to image \u2328\
                                      \nIf you are using this in a group chat please reply to the bot \
                                      \n\nNote: This may take a while...")
        return IMG2IMG2
    
async def t2img(update: Update, context: CallbackContext) -> None:
        user_input = update.message.text
        logging.info("User of text:",user_input)
        pipe = engine.call_engine(1)
        await update.message.reply_text(emoji.emojize("Painting! This may take awhile... :paintbrush:"))
        images = pipe(prompt = user_input).images[0]
        final_images = post_process(images)
        await context.bot.send_photo(chat_id=update.effective_chat.id,photo = final_images ,filename ='photo.jpg', caption = f"Generated Image of {user_input}")
        return ConversationHandler.END

async def t2img2(update: Update, context: CallbackContext) -> None:
      user_input = update.message.text
      logging.info("User of text:",user_input)
      pipe = engine.call_engine(2)
      await update.message.reply_text(emoji.emojize("Painting! This may take awhile... :paintbrush:"))
      images = pipe(prompt = user_input,image = engine.get_picture()).images[0]
      final_images = post_process(images)
      await context.bot.send_photo(chat_id=update.effective_chat.id,photo = final_images ,filename ='photo.jpg', caption = f"Generated Image of {user_input}")  
      return ConversationHandler.END

def error(update,context):
    print(f"Update {update} caused error {context.error}")

API_KEY = api_key
def main():
    application = Application.builder().token(API_KEY).build()
    main_conv = ConversationHandler(
        entry_points= [CommandHandler('start',startcommand)],
        states = {
            START: [CallbackQueryHandler(text_to_image,pattern = '^' + str(ONE) + '$'),
                    CallbackQueryHandler(image_to_image,pattern = '^' + str(TWO) + '$')],
            T2IMG: 
                [MessageHandler(filters.TEXT, t2img)],
            IMG2IMG: [MessageHandler(filters.PHOTO, img2img)],
            IMG2IMG2: [MessageHandler(filters.TEXT, t2img2)]

        },
    fallbacks = [CommandHandler("end",error)]
    )
    application.add_handler(main_conv)
    application.add_handler(CommandHandler("info",info))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
