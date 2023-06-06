import redis, logging, toml, time
from datetime import datetime, timedelta

from aiogram import Bot

from tgbot.config import Config
from tgbot.config import load_config



def get_already_db() -> list[int]:
    r = redis.Redis(host='localhost', port=6379, password='Hallo')

    # Отримання інформації про Redis сервер
    info = r.info()

    # Отримання списку баз даних
    databases = []
    for key in info.keys():
        if key.startswith('db'):
            db_number = key[2:].split(':')[0]
            databases.append(int(db_number))

    return databases
    
def get_db():
    config = load_config(".env")
    config_toml = toml.load("config.toml")
    databases_already = get_already_db()
    for key in config_toml.keys():
        networks = list(config_toml[key].keys())
        number_key = len(networks)
        
        i = j = 1
        while(j < number_key + 1):
            if config_toml[key][networks[j-1]]["db"] != 0:
                i = config_toml[key][networks[j-1]]["db"] + 1
                j+=1
                continue

            if i in databases_already or i == config.redis_config.db:
                i+=1
                continue
            
            config_toml[key][networks[j-1]]["db"] = i
            i+=1
            j += 1
            

        with open('config.toml', 'w') as file:
            toml.dump(config_toml, file)
    
    


def get_keys_redis(config: Config ) -> list:
    
    keys = []
    
    r = redis.Redis(
        host=config.redis_config.host, 
        port=config.redis_config.port, 
        db=config.redis_config.db,
        password=config.redis_config.password
        )

    keys_list = r.keys('*')

    logging.debug(keys_list)

    for key in keys_list:
        if "data" in key.decode("utf-8"):
            keys.append(key.decode("utf-8"))

    logging.info(f"Number of clients: {len(keys)}\n")


    return keys

def check_number_missed_blocks(first_result: int, second_result: int, allow_missed_block: int):
    rizn = second_result - first_result

    logging.info(f"The number of missed blocks for 10 min:  {rizn}\n")

    if rizn >= allow_missed_block:
        logging.info(f"More than allowed {allow_missed_block}\n")
        return True
    
    return False


async def send_message_user(bot: Bot, 
                            chat_id: int, 
                            moniker: str, 
                            missed_blocks: int, 
                            
                            ):
    config = toml.load("config.toml")

    skipped_blocks_allowed = config["signed_blocks_window"] * (1 - config["min_signed_per_window"] / 100)



    time_to_jail_seconds = (skipped_blocks_allowed - missed_blocks) * config["time_create_block"]
    # time_to_jail = datetime.timedelta(seconds=)
    # time_to_jail = datetime.now() + timedelta(seconds=time_to_jail_seconds)
    time_to_jail = time.strftime("%H:%M", time.gmtime(time_to_jail_seconds))


    if missed_blocks > (skipped_blocks_allowed * 0.7):
        await bot.send_message(chat_id, f"<b>Moniker: {moniker}.</b>"
                            f"\n<b>I've just found {missed_blocks} missed blocks out of {skipped_blocks_allowed} total.</b>"
                            f"\n<b>You have ~{time_to_jail} hours before jailing.</b>"
                            f"\n <b>If you don't fix it, your validator will go to jail.</b>")

    else:
        await bot.send_message(chat_id, f"<b>Moniker: {moniker}.</b>"
                            f"\nI've just found {missed_blocks} missed blocks out of {skipped_blocks_allowed} total."
                            f"\nYou have ~{ time_to_jail } hours before jailing.")
        
    logging.info(f"I sent message to {chat_id}")