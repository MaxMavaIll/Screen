import logging, json, toml
from aiogram import Bot
from aiogram.dispatcher.filters import Command, Text
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.dispatcher.fsm.storage.redis import RedisStorage

from tgbot.handlers.manage_checkers.router import checker_router
from tgbot.misc.states import DeleteChecker
from tgbot.keyboards.inline import *

@checker_router.callback_query(text="delete")
async def create_checker(callback: CallbackQuery, state: FSMContext):
    """Entry point for create checker conversation"""
    data = await state.get_data()
    type_networks = list(data["validators"].keys())

    if type_networks != []:
        await callback.message.edit_text("Please select a network",
                                         reply_markup=inline_list(type_networks, 'type_networkD'))

    else:
        await callback.message.edit_text(f"<b>There are currently no Networks available</b>",
                                         reply_markup=to_menu())

@checker_router.callback_query(Text(text_startswith="type_networkD&"))
async def change_chain(callback: CallbackQuery, state: FSMContext, bot: Bot):

    data = await state.get_data()
    type_network = callback.data.split("&")[-1].lower()

    if type_network == 'back':
        type_network = data["type_network"]
    else:
        await state.update_data(type_network=type_network)

    networks = list(data["validators"][type_network].keys())

    await bot.edit_message_text("Please select a network",
                                chat_id=callback.from_user.id,
                                message_id=data['message_id'],
                                reply_markup=list_back(
                                    networks, 'networkD', 'delete')
                                # reply_markup=list_validators(list(chains[network].keys()), 'chain'))
                                )


@checker_router.callback_query(Text(text_startswith="networkD&"))
async def create_checker(callback: CallbackQuery, state: FSMContext):
    
    
    """Entry point for create checker conversation"""
    
    data = await state.get_data()
    type_network = data["type_network"]
    network = callback.data.split("&")[-1].lower()

    if network == 'back':
        network = data["network"]
    else:
        await state.update_data(type_network=type_network)

    validators_list = list(data["validators"][type_network][network].keys())

    await callback.message.edit_text(
            'Let\'s see...\n'
            'What\'s your validator\'s name?',
            reply_markup=validator_moniker(list(validators_list), 'delete', 'type_networkD&', 'back')
        )

    await state.update_data(network=network)

@checker_router.callback_query(Text(text_startswith="delete&"))
async def enter_operator_address(callback: CallbackQuery, state: FSMContext):
    
    """Enter validator's name"""

    moniker = callback.data.split("&")[-1]
    user_id = callback.from_user.id
    data = await state.get_data()
    type_network = data["type_network"]
    network = data["network"]
    

    validators = data.get('validators', {})
    logging.debug(f"All mass: {validators}")
    logging.info(f"User: {user_id}. Delete: {moniker}")
    
    del data["validators"][type_network][network][moniker]

    if data["validators"][type_network][network] == {}:
        del data["validators"][type_network][network]

    if data["validators"][type_network] == {}:
        del data["validators"][type_network]

    
 
    await callback.message.edit_text(
        f'Okay, I deleted this checker : {moniker}',
        reply_markup=to_menu(True, "Try again", back_to="networkD&back")
    )

    logging.info(f"I removed moniker {callback.from_user.id}: {moniker} success ✅\n")
    
    await state.update_data(data)
    await state.set_state(None)




