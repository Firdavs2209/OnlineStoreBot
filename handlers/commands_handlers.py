from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

from config import DB_NAME, admins
from keyboards.admin_inline_keyboards import make_category_list
from states.admin_states import CategoryStates
from utils.database import Database
from utils.my_commands import commands_admin, commands_user

commands_router = Router()
db = Database(DB_NAME)


@commands_router.message(CommandStart())
async def start_handler(message: Message):
    if message.from_user.id in admins:
        await message.bot.set_my_commands(commands=commands_admin)
        await message.answer("Welcome admin, please choose command from commands list")
    else:
        await message.bot.set_my_commands(commands=commands_user)
        await message.answer("Let's start registration")


@commands_router.message(Command('cancel'))
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("All actions canceled, you may continue sending commands")


# With this handler admin can add new category
@commands_router.message(Command('new_category'))
async def new_category_handler(message: Message, state: FSMContext):
    await state.set_state(CategoryStates.newCategory_state)
    await message.answer("Please, send new category name ...")


# Functions for editing category name
@commands_router.message(Command('edit_category'))
async def edit_category_handler(message: Message, state: FSMContext):
    await state.set_state(CategoryStates.updCategory_state_list)
    await message.answer(
        text="Choose category name which you want to change...",
        reply_markup=make_category_list()
    )


@commands_router.callback_query(CategoryStates.updCategory_state_list)
async def callback_category_edit(callback: CallbackQuery, state: FSMContext):
    await state.update_data(cat_name=callback.data)
    await state.set_state(CategoryStates.updCategory_state_new)
    await callback.message.answer(f"Please, send new name for category '{callback.data}'")
    await callback.message.delete()

# /del_catigory
@commands_router.message(CategoryStates.updCategory_state_new)
async def set_new_category_name(message: Message, state: FSMContext):
    new_cat = message.text
    st_data = await state.get_data()
    old_cat = st_data.get('cat_name')
    res = db.upd_category(message.text, old_cat)
    if res['status']:
        await message.answer("Category name successfully changed")
        await state.clear()
    elif res['desc'] == 'exists':
        await message.reply("This category already exists.\n"
                            "Please, send other name or click /cancel")
    else:
        await message.reply(res['desc'])

    @commands_router.message(Command('delete_category'))
    async def delete_category_handler(message: Message, state: FSMContext):
        await state.set_state(CategoryStates.delCategory_state_list)
        await message.answer(
            text="Choose the category name you want to delete...",
            reply_markup=make_category_list()
        )


    @commands_router.callback_query(CategoryStates.delCategory_state_list)
    async def callback_category_delete(callback: CallbackQuery, state: FSMContext):
        cat_name = callback.data
        res = db.delete_category(cat_name)
        if res['status']:
            await callback.message.answer(f"Category '{cat_name}' successfully deleted.")
            await state.clear()
        elif res['desc'] == 'not_found':
            await callback.message.reply("Category not found.\n"
                                         "Please, choose a valid category or click /cancel")
        else:
            await callback.message.reply(res['desc'])




#/add_product
    @commands_router.message(Command('add_product'))
    async def add_product_handler(message: Message, state: FSMContext):
        await state.set_state(CategoryStates.addProduct_state)
        await message.answer("Please, send the name for the new product...")


    @commands_router.message(CategoryStates.addProduct_state)
    async def set_new_product_name(message: Message, state: FSMContext):
        new_product = message.text

        res = db.add_product(new_product)

        if res['status']:
            await message.answer(f"Product '{new_product}' successfully added.")
            await state.clear()
        elif res['desc'] == 'exists':
            await message.reply("This product already exists.\n"
                                "Please, send another name or click /cancel")
        else:
            await message.reply(res['desc'])

#/edit_product
    @commands_router.message(Command('update_product_name'))
    async def update_product_name_handler(message: Message, state: FSMContext):
        await state.set_state(CategoryStates.updateProductName_state_list)
        await message.answer(
            text="Choose the product name you want to update...",
            reply_markup=make_product_list()
        )


    @commands_router.callback_query(CategoryStates.updateProductName_state_list)
    async def callback_product_name_update(callback: CallbackQuery, state: FSMContext):
        product_name = callback.data
        await state.update_data(product_name=product_name)
        await state.set_state(CategoryStates.updateProductName_state_new)
        await callback.message.answer(f"Please, send the new name for the product '{product_name}'")
        await callback.message.delete()


    @commands_router.message(CategoryStates.updateProductName_state_new)
    async def set_new_product_name(message: Message, state: FSMContext):
        new_product_name = message.text
        st_data = await state.get_data()
        old_product_name = st_data.get('product_name')


        res = db.update_product_name(old_product_name, new_product_name)

        if res['status']:
            await message.answer(f"Product name successfully updated to '{new_product_name}'.")
            await state.clear()
        elif res['desc'] == 'exists':
            await message.reply("This product name already exists.\n"
                                "Please, send another name or click /cancel")
        else:
            await message.reply(res['desc'])


    @commands_router.message(Command('delete_product'))
    async def delete_product_handler(message: Message, state: FSMContext):
        await state.set_state(CategoryStates.deleteProduct_state_list)
        await message.answer(
            text="Choose the product name you want to delete...",
            reply_markup=make_product_list()
        )

 #  \del_product
    @commands_router.callback_query(CategoryStates.deleteProduct_state_list)
    async def callback_product_delete(callback: CallbackQuery, state: FSMContext):
        product_name = callback.data
        await state.update_data(product_name=product_name)
        await state.set_state(CategoryStates.deleteProduct_state_confirm)
        await callback.message.answer(f"Are you sure you want to delete the product '{product_name}'?"
                                      f" Confirm by typing 'yes' or click /cancel.")
        await callback.message.delete()


    @commands_router.message(CategoryStates.deleteProduct_state_confirm)
    async def confirm_product_deletion(message: Message, state: FSMContext):
        confirmation = message.text.lower()
        if confirmation == 'yes':
            st_data = await state.get_data()
            product_name = st_data.get('product_name')


            res = db.delete_product(product_name)

            if res['status']:
                await message.answer(f"Product '{product_name}' successfully deleted.")
                await state.clear()
            else:
                await message.reply(res['desc'])
        else:
            await message.answer("Product deletion canceled.")
            await state.clear()



