import logging
import re
import os
import paramiko
import psycopg2

from dotenv import load_dotenv
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from psycopg2 import Error

load_dotenv()

TOKEN = "6453958826:AAFv61_9tjfLpNLlXOIG9mv7tlRMWfToHeY"

logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)

phoneNumberList = []
emailList = []

def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')

def helpCommand(update: Update, context):
    update.message.reply_text('Help!')


def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')
    return 'findPhoneNumbers'

def findPhoneNumbers (update: Update, context):
    user_input = update.message.text

    phoneNumRegex = re.compile(r'(\+7|8)[- ]?\(?(\d{3})\)?[- ]?(\d{3})[- ]?(\d{2})[- ]?(\d{2})\b') 

    global phoneNumberList
    phoneNumberList = []
    phoneNumberList = phoneNumRegex.findall(user_input)

    logging.debug(f'Phone numbers was parsed correctly {phoneNumberList}')

    if not phoneNumberList:
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END
    
    phoneNumbers = ''
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i+1}. {phoneNumberList[i]}\n'
        
    update.message.reply_text(phoneNumbers)

    update.message.reply_text('Добавить найденные номера в базу данных? Введите "1", если да, и "2", если нет')

    return 'insertPhoneNumber'

def findEmailCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска электронных почт: ')
    return 'findEmail'

def findEmail (update: Update, context):
    user_input = update.message.text

    emailRegex = re.compile(r'\b[a-zA-Z0-9.]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}\b') 

    global emailList
    emailList = []
    emailList = emailRegex.findall(user_input)

    logging.debug(f'Emails was parsed correctly {emailList}')

    if not emailList:
        update.message.reply_text('Электронные почты не найдены')
        return ConversationHandler.END 
    
    emails = ''
    for i in range(len(emailList)):
        emails += f'{i+1}. {emailList[i]}\n'
        
    update.message.reply_text(emails)

    update.message.reply_text('Добавить найденные электронные почты в базу данных? Введите "1", если да, и "2", если нет')

    return 'insertEmails'


def verifyPasswordCommand(update: Update, context):
    update.message.reply_text('Введите пароль для проверки его надежности: ')

    return 'verifyPassword'

def verifyPassword (update: Update, context):
    user_input = update.message.text

    verifyPassRegex = re.compile(r'(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()])[A-Za-z\d!@#$%^&*()]{8,}') 

    verState = verifyPassRegex.fullmatch(user_input)
    
    logging.debug(f'Password was parsed correctly {verState}, motherfucker')

    if not verState:
        update.message.reply_text('Пароль простой')
        return ConversationHandler.END
    else:
        update.message.reply_text('Пароль сложный')
        return ConversationHandler.END


def executionCommand(command):
    
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    user = os.getenv('RM_USER')
    password = os.getenv('PASSWORD')

    logging.debug(f"{host} was inserted")
    logging.debug(f"{port} was inserted")
    logging.debug(f"{user} was inserted")
    logging.debug(f"{password} was inserted")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=user, password=password, port=port)

    logging.debug(f'Trying to connect to {client}.')

    stdin, stdout, stderr = client.exec_command(command)
    data = stdout.read() + stderr.read()
    stdin.close()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]

    logging.debug(f"{command} was executed. The result is {data}")
    return data

def getReleaseCommand(update: Update, context):
    update.message.reply_text(f'{executionCommand("cat /etc/*-release")}')

def getUnameCommand(update: Update, context):
    update.message.reply_text(f'{executionCommand("uname -a")}')

def getUptimeCommand(update: Update, context):
    update.message.reply_text(f'{executionCommand("uptime")}')

def getDFCommand(update: Update, context):
    update.message.reply_text(f'{executionCommand("df -h")}')

def getFreeCommand(update: Update, context):
    update.message.reply_text(f'{executionCommand("free -h")}')

def getMpstatCommand(update: Update, context):
    update.message.reply_text(f'{executionCommand("mpstat")}')

def getWCommand(update: Update, context):
    update.message.reply_text(f'{executionCommand("w")}')

def getAuthsCommand(update: Update, context):
    update.message.reply_text(f'{executionCommand("last | head")}')

def getCriticalCommand(update: Update, context):
    update.message.reply_text(f'{executionCommand("journalctl -r -p crit -n 5")}')

def getPSCommand(update: Update, context):
    update.message.reply_text(f'{executionCommand("ps")}')

def getSSCommand(update: Update, context):
    update.message.reply_text(f'{executionCommand("ss | tail")}')
  
def getServicesCommand(update: Update, context):
    update.message.reply_text(f'{executionCommand("service --status-all")}')

def echo(update: Update, context):
    update.message.reply_text(update.message.text)


def getAPTListCommand(update: Update, context):
    update.message.reply_text(f"Выберите режим работы команды. \n Введите \"1\", если хотите получить информацию обо всех пакетах, или введите \"2\", если хотите получить информацию о каком-то конкретном пакете")
    return 'enterAptMode'

def getPackageInfo(update: Update, context):
    package = update.message.text
    logging.info(f"Requested info about {package}")
    data = executionCommand(f"apt info {package}")
    update.message.reply_text(f"Информация о пакете {package}:\n{data}")
    return ConversationHandler.END
    
def getAllAPTListCommand(update: Update):
    logging.info(f"Hooker function")
    update.message.reply_text(f'{executionCommand("apt list --installed | head ")}')

def enterAptMode(update: Update, context):
    logging.debug(f"Chosed {update.message.text.strip()} mode")
    if update.message.text.strip() == '1':
        update.message.reply_text(f"Вы выбрали режим вывода всех пакетов")
        getAllAPTListCommand(update)
        return ConversationHandler.END
    elif update.message.text.strip() == '2':
        update.message.reply_text(f"Вы выбрали режим вывода информации о конкретном пакете. \nВведите имя пакета, о котором вы хотите узнать")
        return 'getPackageInfo'
    else:
        update.message.reply_text(f"Пожалуйста, выберите режим, отправив 1 или 2")
        return 


def getLog(update: Update, context):
    var = "cat /var/log/postgresql/* | grep -i 'repl' | tail -n 20"
    update.message.reply_text(f'{executionCommand(var)}')

def fetch(command):
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    database = os.getenv('DB_DATABASE')

    logging.debug(f"{host} was inserted")
    logging.debug(f"{port} was inserted")
    logging.debug(f"{user} was inserted")
    logging.debug(f"{password} was inserted")
    logging.debug(f"{database} was inserted")

    res = list()
    error = False
    try:
        connection = psycopg2.connect(user=user, password = password, host = host, port = port, database = database)
        cursor = connection.cursor()
        cursor.execute(command)
        data = cursor.fetchall()
        res = list(data)
    except(Exception, psycopg2.Error) as error:
        logging.error(f"Error PostgreSQL: {error}, command: {command}")
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
    return res

def commit(command):
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    database = os.getenv('DB_DATABASE')

    logging.debug(f"{host} was inserted")
    logging.debug(f"{port} was inserted")
    logging.debug(f"{user} was inserted")
    logging.debug(f"{password} was inserted")
    logging.debug(f"{database} was inserted")

    problem = False

    try:
        connection = psycopg2.connect(user=user, password = password, host = host, port = port, database = database)
        cursor = connection.cursor()
        cursor.execute(command)
        connection.commit()
    except(Exception, psycopg2.Error) as error:
        problem = True
        logging.error(f"Error PostgreSQL: {error}, command: {command}")
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
        return problem

def getEmails(update: Update, context):
    ans = ''
    var = fetch("SELECT * FROM emails")
    for em in var:
        ans += str(em[0]) + ". " + str(em[1]) + '\n'
    update.message.reply_text(f'{ans}')

def getNumbers(update: Update, context):
    ans = ''
    var = fetch("SELECT * FROM phonenumbers")
    for em in var:
        ans += str(em[0]) + ". " + str(em[1]) + '\n'
    update.message.reply_text(f'{ans}')
    
def insertEmails(update: Update, context):
    logging.debug("Entered insertEmails function")
    ans = ''
    if update.message.text.strip() == '1':
        for email in emailList:
            em = ''.join(email)
            ans += f"('{em}'), "
        ans = ans[:-2]
        var = commit(f"INSERT INTO emails (email) VALUES ('{em}');")
        if var: 
            update.message.reply_text("ERROR!")
        else:
            update.message.reply_text(f"Добавлено!")
        return ConversationHandler.END
    elif update.message.text.strip() == '2':
        update.message.reply_text(f"На нет и суда нет")
        return ConversationHandler.END
    else:
        update.message.reply_text(f"Пожалуйста, выберите режим, отправив 1 или 2")        
    
def insertNumbers(update: Update, context):
    logging.debug("Entered insertNumbers function")
    ans = ''
    if update.message.text.strip() == '1':
        for number in phoneNumberList:
            num = ''.join(number)
            ans += f"('{num}'), "
        ans = ans[:-2]
        var = commit(f"INSERT INTO phonenumbers (phonenumber) VALUES {ans};")
        if var :
            update.message.reply_text("ERROR!")
        else:
            update.message.reply_text(f"Добавлено!")
        return ConversationHandler.END
    elif update.message.text.strip() == '2':
        update.message.reply_text(f"На нет и суда нет")
        return ConversationHandler.END
    else:
        update.message.reply_text(f"Пожалуйста, выберите режим, отправив 1 или 2")


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'findPhoneNumbers': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'insertPhoneNumber':[MessageHandler(Filters.text & ~Filters.command, insertNumbers)],
        },
        fallbacks=[]
    )

    convHandlerFindEmails = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailCommand)],
        states={
            'findEmail': [MessageHandler(Filters.text & ~Filters.command, findEmail)],
            'insertEmails': [MessageHandler(Filters.text & ~Filters.command, insertEmails)],
        },
        fallbacks=[]
    )

    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPasswordCommand)],
        states={
             'verifyPassword': [MessageHandler(Filters.text & ~Filters.command, verifyPassword)],
        },
        fallbacks=[]
    )

    convHandlerAptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', getAPTListCommand)],
        states={
            'enterAptMode': [MessageHandler(Filters.text & ~Filters.command, enterAptMode)],
            'getPackageInfo': [MessageHandler(Filters.text & ~Filters.command, getPackageInfo)],
        },
        fallbacks=[]
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerVerifyPassword)    
    dp.add_handler(convHandlerFindEmails)
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(CommandHandler("get_release", getReleaseCommand))
    dp.add_handler(CommandHandler("get_uname", getUnameCommand))
    dp.add_handler(CommandHandler("get_uptime", getUptimeCommand))
    dp.add_handler(CommandHandler("get_df", getDFCommand))
    dp.add_handler(CommandHandler("get_free", getFreeCommand))
    dp.add_handler(CommandHandler("get_mpstat", getMpstatCommand))
    dp.add_handler(CommandHandler("get_w", getWCommand))
    dp.add_handler(CommandHandler("get_auths", getAuthsCommand))
    dp.add_handler(CommandHandler("get_critical", getCriticalCommand))
    dp.add_handler(CommandHandler("get_ps", getPSCommand))
    dp.add_handler(CommandHandler("get_ss", getSSCommand))
    dp.add_handler(CommandHandler("get_services", getServicesCommand))
    dp.add_handler(convHandlerAptList)
    dp.add_handler(CommandHandler("get_repl_logs", getLog))
    dp.add_handler(CommandHandler("get_emails", getEmails))
    dp.add_handler(CommandHandler("get_phone_numbers", getNumbers))
    	
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
		
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()