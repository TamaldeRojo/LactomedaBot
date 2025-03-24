

import json
import re


def lactomeda_response(ai_client, msg, conversation_history):
    input_data = {
        "prompt": msg.content,
        "last_20_messages_from_conversation": list(conversation_history),
        "prompt_author": msg.author.name
    } 
    input_data = json.dumps(input_data)
    response = ai_client.send_prompt(input_data)
    res = response.choices[0].message.content
    try:
        res_cleaned = re.sub(r"^```json|\n```$", "", res.strip())                
        dict_data = json.loads(res_cleaned)
        lactomeda_response = dict_data["response"]
        command_name = dict_data["command"] if dict_data["command"] else None
        command_args = dict_data["command_args"] if dict_data["command_args"] else None
    except json.JSONDecodeError as e:
        print(f"error decoding json {e}", repr(res_cleaned))  
        lactomeda_response = "Uuughhh ha habido un error en mi código, nuevo ... Deja que Josué me corrija"
        command_name = None
        command_args = None
    
    return lactomeda_response, command_name, command_args
   