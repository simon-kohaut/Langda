import re
import os
import logging
import ast
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from pathlib import Path
from langda import langda_solve
from promis_execute_new import promis_execution, set_path
from problog import get_evaluatable


from datetime import datetime, timedelta

# 全局持久化数据
PERSISTENT_MSG = {"user": "", "police": "use the same coordinate as user", "query": "nothing"}
PERSISTENT_DATA = {"user": None, "police": None, "query": None}

### ====================== the token of chat group ====================== ###
TOKEN = "7802169894:AAFimcnhTr0mI8MK0icoSZ0_hOeIf445Rfs"
# CHAT_ID = 6639340625
### ====================== the token of chat group ====================== ###
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
save_dir = current_dir / "data"

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def process_msg_from_bot(langda_ext: str) -> dict:
    """
    I suppose the message from telegram bot is:
    from telegram: "!Secure: content about secure..."   
        ==> inside langda file: langda(LLM:"/* Secure */")  
        ==> langda(LLM:"content about secure..")
    """
    logger.info(f"=== PARSING MESSAGE ===")
    logger.info(f"Input: '{langda_ext}'")
    
    # 更宽松的正则表达式，冒号后可以有0个或多个空格
    bot_pattern = r'!(\w+):\s*(.+)'
    
    logger.info(f"Using pattern: {bot_pattern}")
    
    matches = re.findall(bot_pattern, langda_ext)
    logger.info(f"Regex matches: {matches}")
    
    result_dict = dict(matches)
    logger.info(f"Result dict: {result_dict}")
    
    return result_dict

async def send_photo_async(update: Update, context: ContextTypes.DEFAULT_TYPE, photo_path, caption=""):
    """异步发送图片到聊天。"""
    chat_id = update.effective_chat.id
    try:
        logger.info(f"Trying to send picture: {photo_path}")
        with open(photo_path, 'rb') as photo:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption or "Pic"
            )
        logger.info(f"Successfully sent picture: {photo_path}")
        return True
    except Exception as e:
        logger.error(f"Error while sending picture: {e}")
        await update.message.reply_text(f"Failed to send picture: {str(e)}")
        return False

def get_coordinate(model_name, msg_dict):
    """获取坐标信息"""
    danger_rules_string = """
% Earth constant: R * π / 180 -> 111194.93 meters/degree

langda(LLM:"According to the user: /* User */, the coordinate of the user is at:
please form as: user_location(Lat,Lon). => 
(Lat and Lon are latitude and longitude)", LOT:"search with 'The geographical coordinates of ... is'").

langda(LLM:"According to the police: /* Police */, the coordinate of the special zone is at:
please form as: special_zone_location(Lat,Lon).
(Lat and Lon are latitude and longitude)").

relative_offset(NorthOffset, EastOffset) :-
langda(LLM:"The location of the danger zone relative to the user, in meters, calculated based on user_location and special_zone_location above
The conversion of longitude should take into account the influence of latitude",FUP:"false").

query(user_location(_,_)).
query(relative_offset(_,_)).
"""
    while(True):
        try:
            special_model = langda_solve("double_dc", danger_rules_string, model_name, 
                        prefix="telegram_bot", langda_ext=msg_dict, 
                        load=False)

            special_model = special_model.strip("'")
            special_result = get_evaluatable().create_from(special_model).evaluate()
            pattern = r"(\w+)\(\s*(-?\d+\.\d+),\s*(-?\d+\.\d+)\s*\)"
            result_list = []
            for key in special_result:
                match = re.match(pattern, str(key))
                if match:
                    predicate, x, y = match.groups()
                    result_list.append((float(x),float(y)))
                    print(f"predicate = {predicate}, x = {x}, y = {y}")
            print(result_list)

            (user_x, user_y), (offset_y, offset_x) = result_list
            with open(save_dir / "get_coordinate.txt", "w") as f:
                f.write(f"({user_x}, {user_y}), ({offset_x}, {offset_y})")
            return user_x, user_y, offset_x, offset_y
        except Exception as e:
            logger.error(f"Error in get_coordinate: {e}")
            print(e)
            continue

def validate_path(model_name, msg_dict):
    """验证飞行路径"""
    global PERSISTENT_DATA
    
    danger_rules_string = f"""
langda(LLM:"According to the user: /* Query */, 
please extract or generate the points of the path and form as: fly([]).
store all the points inside the list, for example[(0,0),(50,50)],
if there's only a single point mentioned, use similar form as [(50,50)]").

query(fly(_)).
"""
    
    # 使用传入的msg_dict而不是硬编码
    special_model = langda_solve("single_dc", danger_rules_string, model_name, 
                prefix="telegram_bot_fly", langda_ext=msg_dict,
                load=False)
    special_model = special_model.strip("'")
    special_result = get_evaluatable().create_from(special_model).evaluate()
    
    key = next(iter(special_result))  # 提取唯一键

    # 用正则找出中括号部分
    match = re.search(r"fly\((\[.*\])\)", str(key))
    if match:
        list_str = match.group(1)       # 获取 "[(-230, 200), ..., (0, 0)]"
        coord_list = ast.literal_eval(list_str)  # 安全地解析为 Python 列表
        print(f"Parsed coordinates: {coord_list}")
        
        # 修正set_path调用，添加save_dir参数
        valid_result = set_path(0, 0, coord_list, save_dir, switch="path")

        return valid_result
    else:
        logger.error("Could not extract coordinate list from result")
        return None
            

def process_command(message_text):
    """
    处理命令并返回结果和后续操作信息。
    这是一个同步函数，不使用await。
    """
    global PERSISTENT_MSG
    global PERSISTENT_DATA
    
    msg_dict = process_msg_from_bot(message_text)
    if not msg_dict:
        return {"result": "Invalid command format. Please use !Command: message format", "actions": []}

    # 更新持久化消息
    if "User" in msg_dict:
        PERSISTENT_MSG["user"] = msg_dict["User"]
    if "Police" in msg_dict:
        PERSISTENT_MSG["police"] = msg_dict["Police"]
    if "Query" in msg_dict:
        PERSISTENT_MSG["query"] = msg_dict["Query"]

    # 创建返回值
    response = {
        "result": "",
        "actions": []  # 存储需要在异步环境中执行的操作
    }
    
    local_promis_png = save_dir / "mission_landscape.png"
    local_path_png = save_dir / "validation_path.png"
    
    # 添加确认消息动作
    response["actions"].append({
        "type": "send_message",
        "message": "Received your command, processing..."
    })

    model_name = "deepseek-chat"
    promis_prompt = current_dir / "promis_normal_drone.pl"
    
    try:
        with open(promis_prompt, "r") as f:
            rules_string = f.read()
    except FileNotFoundError:
        response["result"] = "Error: promis_normal_drone.pl file not found"
        return response

    # 处理User和Police命令
    if ("Police" in msg_dict or "User" in msg_dict):
        try:
            if "Police" in msg_dict:
                PERSISTENT_MSG["police"] = msg_dict["Police"]
            if "User" in msg_dict:
                PERSISTENT_MSG["user"] = msg_dict["User"]

            # 获取坐标信息
            user_x, user_y, offset_x, offset_y = get_coordinate(model_name, {"User":PERSISTENT_MSG["user"],"Police":PERSISTENT_MSG["police"]})
            PERSISTENT_DATA["police"] = (offset_x, offset_y)
            PERSISTENT_DATA["user"] = (user_x, user_y)

            # 执行 Agent:
            logger.info("Starting call_langda_workflow")
            result = langda_solve("double_dc", rules_string, model_name, 
                                  prefix="telegram_bot_2", langda_ext={"User":PERSISTENT_MSG["user"],"Police":PERSISTENT_MSG["police"]},
                                  load=False)
            logger.info("Finished call_langda_workflow")

            while(True):
                try:
                    logger.info("Starting promis_execution")
                    success = promis_execution(result, (offset_x, offset_y), (user_x, user_y), city_attr="darmstadt",load_uam=False)
                    logger.info("Finished promis_execution")
                    break
                except Exception as e:
                    print(e)
                    continue

            if success:
                # 添加发送完成消息动作
                response["actions"].append({
                    "type": "send_message",
                    "message": "Process finished, creating image..."
                })
                
                # 添加发送图片动作
                if os.path.exists(local_promis_png):
                    response["actions"].append({
                        "type": "send_photo",
                        "path": local_promis_png,
                        "caption": "mission_landscape.png"
                    })
                    
                    response["result"] = "Image created successfully!"
                else:
                    response["result"] = "Process completed, but image file was not found."
            else:
                response["result"] = "Error during promis execution. Please retry!"
                
        except Exception as e:
            logger.error(f"Error processing User/Police command: {e}")
            response["result"] = f"Error processing command: {str(e)}"

    # 处理Query命令
    if "Query" in msg_dict:
        PERSISTENT_MSG["Query"] = msg_dict["Query"]

        try:
            # 使用完整的PERSISTENT_MSG而不是只有Query部分
            valid_result = validate_path(model_name, {"Query":PERSISTENT_MSG["query"]})

            if valid_result is not None:
                # 添加发送完成消息动作
                response["actions"].append({
                    "type": "send_message",
                    "message": "Process finished, creating analysis..."
                })

                # 添加发送图片动作
                if os.path.exists(local_promis_png):
                    response["actions"].append({
                        "type": "send_photo",
                        "path": local_path_png,
                        "caption": "validation_path.png"
                    })  
                response["result"] = f"Path validation result: {valid_result}"
            else:
                response["result"] = "Error validating path. Please check your flight plan format."

        except Exception as e:
            logger.error(f"Error processing Query command: {e}")
            response["result"] = f"Error processing path validation: {str(e)}"

    return response

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "Bot connected. Send messages with the prefix '!{Cmd}: ...'"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        """Use '!{Cmd}:' followed by your command to send to local code.\n
For example:
from telegram: "!Secure: content about secure..."   
    ==> in LangDa source code: langda(LLM:"/* Secure */")
    ==> langda(LLM:"content about secure..")
# You could send multiple commands, just make sure to use line breaks to distinguish them.""")

async def send_image_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 /sendimage 命令，发送指定路径的图片。"""
    if not context.args:
        await update.message.reply_text("Please provide an image path, e.g.: /sendimage path/to/image.jpg")
        return
    
    image_path = " ".join(context.args)
    if not os.path.exists(image_path):
        await update.message.reply_text(f"Image not found: {image_path}")
        return
    
    await send_photo_async(
        update, 
        context, 
        image_path, 
        caption=f"Image: {os.path.basename(image_path)}"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages."""
    
    if update.message.date < datetime.now(update.message.date.tzinfo) - timedelta(seconds=60):
        logger.info("Ignoring old message")
        await update.message.reply_text("⏭️ Ignoring old message, send new commands")
        return
    message_text = update.message.text
    print(message_text)
    logger.info(f"=== RECEIVED MESSAGE ===")
    logger.info(f"Raw message: '{message_text}'")
    logger.info(f"Message length: {len(message_text)}")
    logger.info(f"From user: {update.effective_user.username}")
    
    msg_dict = process_msg_from_bot(message_text)
    logger.info(f"Parsed msg_dict: {msg_dict}")

    # Check if the message uses our special format
    if msg_dict:
        logger.info("Message matched special format, processing...")
        
        # 处理特殊格式的 Image 命令
        if "Image" in msg_dict:
            logger.info("Processing Image command")
            image_path = msg_dict["Image"].strip()
            if not os.path.isabs(image_path):
                image_path = os.path.abspath(image_path)
                
            if os.path.exists(image_path):
                await update.message.reply_text(f"Sending image: {os.path.basename(image_path)}")
                await send_photo_async(
                    update, 
                    context, 
                    image_path, 
                    caption=f"Image: {os.path.basename(image_path)}"
                )
            else:
                await update.message.reply_text(f"Image not found: {image_path}")
            return
        
        # 处理其他命令
        logger.info("Processing other commands...")
        try:
            response = process_command(message_text)
            logger.info(f"Command response: {response}")
            
            # 执行返回的所有操作
            for action in response["actions"]:
                logger.info(f"Executing action: {action}")
                if action["type"] == "send_message":
                    await update.message.reply_text(action["message"])
                elif action["type"] == "send_photo":
                    await send_photo_async(update, context, action["path"], action["caption"])
            
            # 发送最终结果
            if response["result"]:
                await update.message.reply_text(response["result"])
                
        except Exception as e:
            logger.error(f"Error in process_command: {e}", exc_info=True)
            await update.message.reply_text(f"Error processing command: {str(e)}")
    else:
        logger.info("Message did not match special format")
        await update.message.reply_text("Message format not recognized. Use !Command: message format")

def main() -> None:
    """Start the bot."""
    try:
        # Create the Application
        application = Application.builder().token(TOKEN).build()

        # Add command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("sendimage", send_image_command))
        
        # Add message handler
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Run the bot until the user presses Ctrl-C
        print("Starting bot...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}", exc_info=True)
        print(f"Error: {e}")

if __name__ == "__main__":
    main()