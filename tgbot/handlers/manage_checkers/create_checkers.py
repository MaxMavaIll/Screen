import asyncio
import logging
import json
import toml
import funtion as fun
from funtion import *

from datetime import datetime

from aiogram import Bot
from aiogram.dispatcher.filters import Command, Text
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from aiogram.dispatcher.fsm.storage.redis import RedisStorage


from tgbot.handlers.manage_checkers.router import checker_router
from tgbot.misc.states import CreateChecker
from tgbot.keyboards.inline import *


@checker_router.callback_query(text="create")
async def create_checker(callback: CallbackQuery, state: FSMContext):
    """Entry point for create checker conversation"""
    config = toml.load("config.toml")
    type_networks = list(config["networks"].keys())

    if type_networks != []:
        await callback.message.edit_text("Please select a network",
                                         reply_markup=inline_list((type_networks), 'type_network'))

    else:
        await callback.message.edit_text(f"<b>There are currently no Networks available</b>",
                                         reply_markup=to_menu())


@checker_router.callback_query(Text(text_startswith="type_network&"))
async def change_chain(callback: CallbackQuery, state: FSMContext, bot: Bot):

    config = toml.load("config.toml")
    type_network = callback.data.split("&")[-1].lower()
    data = await state.get_data()
    if type_network == 'back':
        type_network = data["type_network"]
    else:
        await state.update_data(type_network=type_network)
#    logging.info(f'Chains {chains.keys()} {n}')

    if config["networks"][type_network] != {}:
        await bot.edit_message_text("Please select a network",
                                    chat_id=callback.from_user.id,
                                    message_id=data['message_id'],
                                    reply_markup=list_validators_back(
                                        list(config["networks"][type_network].keys()), 'network', 'create')
                                    # reply_markup=list_validators(list(chains[network].keys()), 'chain'))
                                    )
    else:
        await callback.answer(
            'Sorry, but I didn\'t find any checker. \n'
            'First, create a checker',
            # show_alert=True
        )

        data['type_network'] = ""
        data['network'] = ""
        return


@checker_router.callback_query(Text(text_startswith="network&"))
async def create_checker(callback: CallbackQuery, state: FSMContext):
    """Entry point for create checker conversation"""
    config = toml.load("config.toml")
    data = await state.get_data()
    network = callback.data.split("&")[-1].lower()
    if network == 'back':
        network = data["network"]
    else:
        await state.update_data(network=network)

    await callback.message.edit_text(
        'Let\'s see...\n'
        "What's your validator name?\n"
        "<b>Example</b>: web34ever or web34ever,cyberG,Mavpa...",
        reply_markup=to_menu(
            back=True, text='Try another platform', back_to='type_network&back')
    )

    await state.set_state(CreateChecker.operator_address)


@checker_router.message(state=CreateChecker.operator_address)
async def enter_operator_address(message: Message, state: FSMContext,
                                 #  scheduler: AsyncIOScheduler,
                                 bot: Bot):
    config = toml.load('config.toml')
    data = await state.get_data()
    message_id = data["message_id"]
    type_network = data['type_network']
    network = data['network']
    get_monikers = message.text
    moniker_list = get_monikers.split(",")
    list_validators = ''


    # """Enter validator's name"""
    await asyncio.sleep(1)
    await message.delete()
    a = await bot.send_message(chat_id=message.from_user.id, text="Wait I'm processing the information", request_timeout=6)

    urls = await fun.check_url(config["networks"][type_network][network]["rpc"])


    await asyncio.sleep(1)
    await bot.delete_message(chat_id=message.from_user.id, message_id=a.message_id)

    if urls["active_urls"] == []:

        await bot.edit_message_text(
            f'Sorry, rpc not working 🔴',
            chat_id=message.from_user.id,
            message_id=message_id,
            reply_markup=to_menu(),
        )

        return

    url = urls["active_urls"][0]


    logging.info(f"I create new validator/validators")

    for get_moniker in moniker_list:

        logging.info(f"")

        validators = await fun.get_validators(url, config["networks"][type_network][network]["path_bin"])
        index = await fun.get_index_by_moniker(get_moniker, validators)

        logging.info(f'Got {type(validators)} validators')

        # if index is None:

        #     list_validators += '\n' + get_moniker + " - not found ❌"
        #     logging.info(f"I didn`t find moniker: {get_moniker}")
        # await bot.edit_message_text(
        #     'Sorry, but I don\'t found this validator', chat_id=message.from_user.id,
        #     message_id=message_id,
        #     reply_markup=to_menu()
        # )

        # logging.info(f"I finding moniker: {get_moniker}")
        # validator = validators[index]
        # signing_info = await fun.slashing_signing_info(validator.get("consensus_pubkey").get("key"), url)
        # missed_block = int(signing_info.get("missed_blocks_counter"))

        # data.setdefault('validators', {})

        if index is None:

            list_validators += '\n' + get_moniker + " - not found ❌"
            logging.info(f"I didn`t find moniker: {get_moniker}")

        elif get_moniker in data['validators'].keys():

            list_validators += '\n' + get_moniker + " - added"

        elif get_moniker != moniker_list[len(moniker_list)-1]:
            list_validators += '\n' + get_moniker + " - success 👌"

        else:
            list_validators += '\n' + get_moniker + " - success 👌"

        await bot.edit_message_text(
            f'Nice! Now I\'ll be checking this validator all day : {list_validators}', chat_id=message.from_user.id,
            message_id=message_id,
            reply_markup=to_menu(
                back=True, text='Try again', back_to='network&back')
        )

        if index is not None:
            logging.info(f"I finding moniker: {get_moniker}")
            validator = validators[index]
            signing_info = await fun.slashing_signing_info(validator.get("consensus_pubkey").get("key"), url, config["networks"][type_network][network]["path_bin"])
            missed_block = int(signing_info.get("missed_blocks_counter"))

            data.setdefault('validators', {})

            if type_network not in data['validators']:
                data['validators'][type_network] = {}
            
            if network not in data['validators'][type_network]:
                data['validators'][type_network][network] = {}
            
            if get_moniker not in data['validators'][type_network]:
                data['validators'][type_network][network][get_moniker] = {"const_addr": None, "last_missed_block": 0}

            data["rpc"] = urls
            data["validators"][type_network][network][get_moniker]["last_missed_block"] = missed_block
            data["validators"][type_network][network][get_moniker]["const_addr"] = signing_info["address"]

            logging.info(
                f"I created moniker {message.from_user.id}: {get_moniker} success ✅\n")
            logging.debug(f'Data: {data}')

        # await storage.redis.set('checkers', json.dumps(checkers))

    data['type_network'] = ""
    data['network'] = ""

    await state.update_data(data)
    await state.set_state(None)
