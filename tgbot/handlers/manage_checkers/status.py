import logging
from datetime import datetime
from socket import EAI_SERVICE
import asyncio, toml
import json
from termcolor import colored

from aiogram.dispatcher.filters import Command, Text
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# from api.config import nodes
# from api.functions import get_index_by_moniker
# from api.requests import MintScanner
# from schedulers.jobs import add_user_checker
from tgbot.handlers.manage_checkers.router import checker_router
from tgbot.misc.states import Status
from tgbot.keyboards.inline import validator_moniker
from tgbot.keyboards.inline import *

import os
from funtion import *




    
@checker_router.callback_query(text="status")
async def create_checker(callback: CallbackQuery, state: FSMContext):
    """Entry point for create checker conversation"""
    data = await state.get_data()
    type_networks = list(data["validators"].keys())

    if type_networks != []:
        await callback.message.edit_text("Please select a network",
                                         reply_markup=inline_list(type_networks, 'type_network_status'))

    else:
        await callback.message.edit_text(f"<b>There are currently no Networks available</b>",
                                         reply_markup=to_menu())


@checker_router.callback_query(Text(text_startswith="type_network_status&"))
async def change_chain(callback: CallbackQuery, state: FSMContext, bot: Bot):

    data = await state.get_data()
    type_network = callback.data.split("&")[-1].lower()

    if type_network == 'back':
        type_network = data["type_network"]
    else:
        await state.update_data(type_network=type_network)

    networks = list(data["validators"][type_network].keys())

    await bot.edit_message_text(
                    "Please select a network",
                    chat_id=callback.from_user.id,
                    message_id=data['message_id'],
                    reply_markup=list_back(networks, 'network_status', 'status')
                    )


@checker_router.callback_query(Text(text_startswith="network_status&"))
async def create_checker(callback: CallbackQuery, state: FSMContext):
    

    """Entry point for create checker conversation"""

    data = await state.get_data()
    type_network = data["type_network"]
    network = callback.data.split("&")[-1].lower()
    

    validators_list = list(data["validators"][type_network][network].keys())
    

    
    await callback.message.edit_text(
            'Let\'s see...\n'
            "The status of which validator do you want to know?",
            reply_markup=validator_moniker(validators_list, "status", "type_network_status&", "back")
        )
    
    await state.update_data(network=network)




@checker_router.callback_query(Text(text_startswith="status&"))
async def enter_operator_address(callback: CallbackQuery, state: FSMContext):
    config = toml.load('config.toml')


    """Enter validator's name"""
    data = await state.get_data()
    type_network = data["type_network"]
    network = data["network"]
    moniker = callback.data.split("&")[-1]

    logging.info(f"I display the status on the screen {callback.from_user.id}")

    data = await state.get_data()
    urls = await check_url(config["networks"][type_network][network]["rpc"])
    active_rpc = urls["numer_active"]
    number_rpc = urls["urls"]

    if urls["active_urls"] == []:
        await callback.answer(
        f'Sorry, rpc not working 🔴',
        show_alert=True, 
    )
        return

    url = urls["active_urls"][0]

    


    validators = await get_validators(url, config["networks"][type_network][network]["path_bin"])
    index = await get_index_by_moniker(moniker, validators)

    logging.info(f"Moniker: {moniker}. Index: {index}")
    validator = validators[await get_index_by_moniker(moniker, validators)]
    signing_info = await slashing_signing_info(validator.get("consensus_pubkey").get("key"), url, config["networks"][type_network][network]["path_bin"])
    missed_block = signing_info["missed_blocks_counter"]



    jail = '🔴 true' if validator["jailed"] else '🟢 false'
    status = '🟢 BONDED' if validator["status"] == "BOND_STATUS_BONDED" else '🔴 UNBONDED'


    await callback.answer(
        f'status: '
        f'\n    moniker: {moniker}'
        f'\n    voting power: {validator["tokens"]}'
        f'\n    jailed:  {jail}'
        f'\n    validators status: {status}'
        f'\n    missed blocks: {missed_block}',
        show_alert=True, 
    )

    logging.info(f"I displayed the status on the screen {callback.from_user.id}: success ✅\n")

