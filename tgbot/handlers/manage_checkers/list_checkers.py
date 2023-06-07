import toml, logging

from aiogram import Bot
from aiogram.dispatcher.filters import Command, Text
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from tgbot.handlers.manage_checkers.router import checker_router
from tgbot.keyboards.inline import *

@checker_router.callback_query(text="list")
async def create_checker(callback: CallbackQuery, state: FSMContext):
    """Entry point for create checker conversation"""
    data = await state.get_data()
    type_networks = list(data["validators"].keys())

    if type_networks != []:
        await callback.message.edit_text("Please select a network",
                                         reply_markup=inline_list(type_networks, 'type_networkL'))

    else:
        await callback.message.edit_text(f"<b>There are currently no Networks available</b>",
                                         reply_markup=to_menu())

@checker_router.callback_query(Text(text_startswith="type_networkL&"))
async def change_chain(callback: CallbackQuery, state: FSMContext, bot: Bot):

    type_network = callback.data.split("&")[-1].lower()
    data = await state.get_data()

    if type_network == 'back':
        type_network = data["type_network"]
    else:
        await state.update_data(type_network=type_network)

    networks = list(data["validators"][type_network].keys())
    

    await bot.edit_message_text("Please select a network",
                                chat_id=callback.from_user.id,
                                message_id=data['message_id'],
                                reply_markup=validator_moniker(
                                    list(networks), 'networkL', 'list')
                                # reply_markup=list_validators(list(chains[network].keys()), 'chain'))
                                )




@checker_router.callback_query(Text(text_startswith="networkL&"))
async def list_my_validators(callback: CallbackQuery, state: FSMContext):
    """List all registered validators"""

    logging.info(f"I display the list on the screen {callback.from_user.id}")

    data = await state.get_data()
    validators = data.get('validators')
    type_network = data["type_network"]
    network = callback.data.split("&")[-1].lower()

    logging.info(f"Data: {data}")

    if not validators:
        await callback.answer(
            'Sorry, but I didn\'t find any checker. \n'
            'First, create a checker',
            # show_alert=True
        )

        return

    validators_str = 'I\'m checking the following validators:\n\n'
    validators_str = validators_str + '\n'.join([
        f'{num}. {validator}\n'
        for num, validator in enumerate(list(validators[type_network][network].keys()), 1)
    ]
    )
    await callback.message.edit_text(validators_str,
                                        reply_markup=to_menu(True, "Try another platform", "type_networkL&back"))
    
    logging.info(f"I displayed the list on the screen {callback.from_user.id}: success ✅\n")

    
    
