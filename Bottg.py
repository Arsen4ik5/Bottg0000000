import logging
from telegram import Update, ChatMember
from telegram.ext import Updater, CommandHandler, CallbackContext
from sqlalchemy import create_engine, Column, Integer, String, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from threading import Timer

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Настройка базы данных
Base = declarative_base()
engine = create_engine('sqlite:///admins.db')
Session = sessionmaker(bind=engine)
session = Session()

class Admin(Base):
    __tablename__ = 'admins'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True)

Base.metadata.create_all(engine)

# Подключение к Telegram API
TOKEN = '6883001396:AAEbGBMpzfCjbzYXUBW8jPefiqUhoO1ixv4'

# Список администраторов
admins = set()

def start(update: Update, context: CallbackContext):
    update.message.reply_text('Бот запущен!')

def add_admin(update: Update, context: CallbackContext):
    if update.effective_user.id not in admins:
        update.message.reply_text('У вас нет прав для добавления администраторов.')
        return
        
    if context.args:
        user_id = int(context.args[0])
        new_admin = Admin(user_id=user_id)
        
        session.add(new_admin)
        session.commit()
        admins.add(user_id)
        
        update.message.reply_text(f'Пользователь {user_id} добавлен как администратор.')
    else:
        update.message.reply_text('Используйте: /addadm <user_id>')

def mute(update: Update, context: CallbackContext):
    if update.effective_user.id not in admins or not context.args:
        update.message.reply_text('У вас нет прав для использования этой команды.')
        return

    user_id = int(context.args[0])
    duration = int(context.args[1]) if len(context.args) > 1 else 60  # По умолчанию мут на 60 секунд

    try:
        context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user_id,
            permissions=ChatMember.permissions(),
            until_date=update.message.date.timestamp() + duration
        )
        update.message.reply_text(f'Пользователь {user_id} замучен на {duration} секунд.')
    except Exception as e:
        logging.error(e)
        update.message.reply_text('Не удалось замутить пользователя.')

def kick(update: Update, context: CallbackContext):
    if update.effective_user.id not in admins or not context.args:
        update.message.reply_text('У вас нет прав для использования этой команды.')
        return

    user_id = int(context.args[0])
    duration = int(context.args[1]) if len(context.args) > 1 else 60  # По умолчанию кик на 60 секунд

    try:
        context.bot.kick_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user_id
        )

        # Сообщение для возвращения пользователя
        def unban():
            context.bot.unban_chat_member(chat_id=update.effective_chat.id, user_id=user_id)

        Timer(duration, unban).start()
        update.message.reply_text(f'Пользователь {user_id} кикнут на {duration} секунд.')
    except Exception as e:
        logging.error(e)
        update.message.reply_text('Не удалось кикнуть пользователя.')

def warn(update: Update, context: CallbackContext):
    if update.effective_user.id not in admins or not context.args:
        update.message.reply_text('У вас нет прав для использования этой команды.')
        return

    user_id = int(context.args[0])
    update.message.reply_text(f'Пользователь {user_id} получил варн.')

def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Загрузка администраторов из базы данных
    for admin in session.query(Admin).all():
        admins.add(admin.user_id)

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("addadm", add_admin))
    dispatcher.add_handler(CommandHandler("mute", mute))
    dispatcher.add_handler(CommandHandler("kick", kick))
    dispatcher.add_handler(CommandHandler("warn", warn))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
