import hashlib
import json

from botconfig import *
from classification import ModelTrain

USERS_DB = dict()


def check_session(message) -> bool:
    '''
    Check if current user exists in database and he is sign in already.
    '''
    try:
        return USERS_DB[message.from_user.id][1]
    except KeyError:
        return False


def check_passwd(message) -> None:
    '''
    Password verification
    '''
    user_input = message.text
    chat_id = message.chat.id
    user_id = message.from_user.id
    try:
        if USERS_DB[user_id][0] == hashlib.sha256(user_input.encode() + SALT.encode()).hexdigest():
            USERS_DB[user_id][1] = 1
            BOT.send_message(chat_id, "Access granted")
        else:
            BOT.send_message(chat_id, "Access denied. Check your password")
    except BaseException:
        BOT.send_message(chat_id, "Something went wrong")


@BOT.message_handler(commands=['start', 'help'])
def send_usage(message) -> None:
    '''
    Basic trigger to /start and /help commands
    '''
    BOT.reply_to(message, text=INFO_MESSAGE)


@BOT.message_handler(commands=["register"])
def register_user(message) -> None:
    '''
    Sign up process to another user.
    '''
    BOT.reply_to(message, REGISTER_MESSAGE)
    BOT.register_next_step_handler(message, init_new_user)


@BOT.message_handler(commands=["login"])
def login_user(message) -> None:
    '''
    Login method. Update element in user's database.
    '''
    BOT.reply_to(message, LOGIN_MESSAGE)
    BOT.register_next_step_handler(message, check_passwd)


@BOT.message_handler(commands=['predict'])
def image_processing(message) -> None:
    '''
    Predict object in sended through the message picture
    '''
    if check_session(message):
        BOT.reply_to(message, "Send me your image :>")
        BOT.register_next_step_handler(message, predict_init)
    else:
        BOT.reply_to(message, "Please, login first :<")


@BOT.message_handler(commands=['logout'])
def logout(message) -> None:
    '''
    Logout process.
    '''
    BOT.reply_to(message, "Okey, have a nice day!")
    try:
        USERS_DB[message.from_user.id][1] = 0
        BOT.send_message(message.chat.id, "Logout successful..")
    except KeyError:
        BOT.send_message(message.chat.id, "Wait.. You're not out user :<")


def predict_init(message) -> None:
    '''
    Download object from chat and send it to model
    '''
    BOT.reply_to(message, "Please, wait...")
    fileId = message.photo[-1].file_id
    file_info = BOT.get_file(fileId)
    download_object = BOT.download_file(file_info.file_path)
    with open(f"./tmp/{file_info.file_id}", "wb") as user_image:
        user_image.write(download_object)
    new_model_object = ModelTrain(image_path=f"./tmp/{file_info.file_id}")
    predict_result = new_model_object.predict_image()
    BOT.send_message(message.chat.id, predict_result, parse_mode="Markdown")
    os.remove(f"./tmp/{file_info.file_id}")


def init_new_user(message) -> None:
    '''
    Help function to register process
    '''
    user_passwd = message.text
    chat_id = message.chat.id
    user_id = message.from_user.id
    try:
        if USERS_DB[user_id]:
            BOT.send_message(chat_id, "You are already have an account")
    except KeyError:
        USERS_DB.update(
            {user_id: [hashlib.sha256(user_passwd.encode() + SALT.encode()).hexdigest(), 0]})
        with open(f"{BOT_FOLDER}/user_db", "a") as f:
            f.write(json.dumps(USERS_DB))
        BOT.send_message(chat_id, "Now you can login")


def read_db() -> dict:
    '''
    Try to read all values from file with user's database.
    '''
    database = {}
    if os.path.exists(f"{BOT_FOLDER}/user_db"):
        with open(f"{BOT_FOLDER}/user_db", 'r') as db:
            try:
                database = json.load(db)
            except KeyError:
                pass
    return database


def main() -> None:
    '''
    Main function
    '''
    USERS_DB = read_db()
    print("Telegram Support Bot started...")
    BOT.polling()


if __name__ == "__main__":
    main()
