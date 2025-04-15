# ------------------------ HEADERS ------------------------
from chatterbot import ChatBot 
from chatterbot.trainers import ListTrainer, ChatterBotCorpusTrainer
import json
import google.generativeai as genai
import sympy
import re
from difflib import get_close_matches
from typing import List, Optional
from flask import Flask, render_template, request
import os
# who created google - not working

# ------------------------ KAGGLE API INTEGRATION ------------------------
with open("intents.json", "r", encoding="utf-8") as file:
    data = json.load(file)
conversation_data = []
for intent in data["intents"]:
    for user_input in intent["patterns"]:
        for response in intent["responses"]:
            conversation_data.append(user_input)  # Question
            conversation_data.append(response)  # Answer

# ------------------------ GEMINI API INTEGRATION ------------------------
genai.configure(api_key="AIzaSyAe5gAiTQ1DkHuE96HPtptSQa7vL3RXD3M")

# ------------------------ FUNCTION TO GET CHATBOT RESPONSE ------------------------
def get_chatterbot_response(user_response):
    response = bot.get_response(user_response)
    if float(response.confidence) > 0.9:  # Confidence threshold
        return response
    else:
        return None  # Fallback to Google Bard if confidence is low

# ------------------------ FUNCTION TO GET GEMINI RESPONSE ------------------------
def get_bard_response(user_response):
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
    prompt = f"Generate the response to this question using least amount of words: {user_response}"
    response = model.generate_content(prompt)
    return response.text

# ------------------------ FUNCTION TO SOLVE MATH EXPRESSION ------------------------
def is_math_expression(input_string):
    try:
        sympy.sympify(input_string)  # Tries to parse expression
        return True
    except sympy.SympifyError:
        return False

def handle_math_query(user_input):
    try:
        expr = sympy.sympify(user_input, evaluate=True)
        result = str(expr.evalf())  # evalf is required to calculate result in decimals
        return f"{float(result):.3f}"  # Round to 3 decimal places and format

    except Exception as e:
        return f"Error solving math: {e}"

# ------------------------ BOT_LEARN INTEGRATION ------------------------
def load_knowledge_base(file_path: str):
    with open(file_path, 'r') as file:
        data: dict = json.load(file) # Load JSON data into a dictionary
    return data # Return the dictionary

def save_knowledge_base(file_path: str, data: dict):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

def find_best_match(user_question: str, questions: List[str]) -> Optional[str]:
    matches: list = get_close_matches(user_question, questions, n=1, cutoff=0.9)
    return matches[0] if matches else None

def get_answer_for_question(question: str, knowledge_base: dict) -> Optional[str]:
    for q in knowledge_base["questions"]:
        if q["question"] == question:
            return q["answer"]
    return None

knowledge_base: dict = load_knowledge_base('knowledge_base.json')

def read_bot_learn(user_input):

    best_match: str | None = find_best_match(user_input, [q["question"] for q in knowledge_base["questions"]])
    if best_match:
        answer: str = get_answer_for_question(best_match, knowledge_base)
        return answer
    else:
        return None

def write_bot_learn(user_input, new_answer):
    knowledge_base["questions"].append({"question": user_input, "answer": new_answer})
    save_knowledge_base('knowledge_base.json', knowledge_base)


# ------------------------ CHAT LOOP ------------------------
def chat_loop(user_response, p1_user_response, p2_bot_response, p1_bot_response):
    while True:
        # user_response = input("User: ")

        if user_response.lower() in ["exit", "quit", "bye", "good bye"]:
            # print("Chatbot: Goodbye!")
            return str("Chatbot: Goodbye!")
            # break

        user_input = user_response
        if re.search(r'^[\d\s+\-*/().^]+$', user_input):
            if is_math_expression(user_input):
                response = handle_math_query(user_input)
                # print("Chatbot: ", response)
                return str("Chatbot: " + response)
                # continue

        if user_response.lower() in ["not satisfied", "try again", "ask google", "ask bard", "ask gemini", "check with gemini", "check with google"]:
            # choice = input("Chatbot: Would you like me to check with google bard? (yes/no): ")
            return str("Chatbot: Would you like me to check with google bard? (yes/no): ")
            # if choice == "yes":
            #     bard_response = get_bard_response(prev_response).strip()
            #     print("Google Bard: ", bard_response)
            #     continue
            # else:
            #     print("Chatbot: Okay, I am sorry I could not give you a satisfactory response, let me know if you have another question!")
            #     continue
        if p1_user_response in ["not satisfied", "try again", "ask google", "ask bard", "ask gemini", "check with gemini", "check with google"]:
            if user_response == "yes":
                bard_response = get_bard_response(p2_bot_response)
                # print("Google Bard: ", bard_response)
                return  "Google Bard: " + bard_response
                # continue
            else:
                return str("Chatbot: Okay, I am sorry I could not give you a satisfactory response, let me know if you have another question!")
                # continue

        response = str(get_chatterbot_response(user_response))

        if response == "None":
            # response = str("Chatbot: " + read_bot_learn(user_response.lower()))
            response = str(read_bot_learn(user_response))

        if response != "None":
            # print("Chatbot: ", response)
            return str("Chatbot: " + response)
        else:
            return str("Chatbot: I don't have an answer. Do you want me to check Google Bard? (yes/no): ")
            # if choice1 == "yes":
            #     bard_response = get_bard_response(user_response).strip()
            #     print("Google Bard: ", bard_response)
            #     write_bot_learn(user_response, bard_response)
            # else:
            #     choice2 = input("Chatbot: Okay. Would you like to teach me? (yes/no): ").strip().lower()
            #     if choice2 == "yes":
            #         response: str = input("Type the response: ")
            #         write_bot_learn(user_response, response)
            #         print("Chatbot: Thank you! I've learned something new.")
            #     else:
            #         print("Chatbot: Okay, let me know if you have another question!")

        if p1_bot_response == "Chatbot: I don't have an answer. Do you want me to check Google Bard? (yes/no): ":
            if user_response == "yes":
                bard_response = get_bard_response(p1_user_response) #.strip()
                # write_bot_learn(p1_user_response, bard_response)
                return "Google Bard: "+ bard_response
            else:
                return str("Chatbot: Okay. Would you like to teach me? (yes/no): ")
                # if choice2 == "yes":
                #     response: str = input("Type the response: ")
                #     write_bot_learn(user_response, response)
                #     print("Chatbot: Thank you! I've learned something new.")
                # else:
                #     print("Chatbot: Okay, let me know if you have another question!")
        
        if p1_bot_response == "Chatbot: Okay. Would you like to teach me? (yes/no): ":
            if p1_user_response == "yes":
                return str("Chatbot: Type the response: ")

        if p1_bot_response == "Chatbot: Type the response: ":
            # write_bot_learn(p2_bot_response, p1_bot_response)
            return str("Chatbot: Thank you! I've learned something new.")

                # response: str = input("Type the response: ")
                # write_bot_learn(user_response, response)
                # print("Chatbot: Thank you! I've learned something new.")


# ------------------------ CHAT HISTORY FILE ------------------------
CHAT_FILE = "chat_history.json"

def save_chat_to_json(user_input, bot_reply):
    """Saves user and bot responses to a JSON file."""
    chat_data = []

    # Check if file exists and load existing data
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r", encoding="utf-8") as file:
            try:
                chat_data = json.load(file)
            except json.JSONDecodeError:
                pass  # Handle empty or corrupted JSON file

    # Append new conversation entry
    chat_data.append({"user": user_input, "bot": bot_reply})

    # Save back to JSON file
    with open(CHAT_FILE, "w", encoding="utf-8") as file:
        json.dump(chat_data, file, indent=4)

def get_previous_user_response():
    """Retrieves the user response from the chat history."""
    if not os.path.exists(CHAT_FILE):
        # return "Chat history file not found."
        return None, None, None

    try:
        with open(CHAT_FILE, "r", encoding="utf-8") as file:
            chat_data = json.load(file)

        bot_responses = [entry["bot"] for entry in chat_data if "bot" in entry]
        if len(bot_responses) >= 2:
            p1_bot_response = bot_responses[-1]

        # Extract user responses only
        user_responses = [entry["user"] for entry in chat_data if "user" in entry]

        # Return the third last user response if available
        if len(user_responses) >= 2:
            return user_responses[-1], user_responses[-2], p1_bot_response
        else:
            return None, None, None

    except json.JSONDecodeError:
        return None, None, None


# ------------------------ FLASK INTEGRATION ------------------------
app = Flask(__name__)
@app.route("/")
def main():
    return render_template("index.html")

@app.route("/get")
def get_chatbot_response():
    userText = request.args.get('userMessage')
    p1_user_response, p2_user_response, p1_bot_response = get_previous_user_response()
    chat_result = chat_loop(userText, p1_user_response, p2_user_response, p1_bot_response)
    save_chat_to_json(userText, chat_result)
    return str(chat_result)


# ------------------------ CHATBOT OBJECT ------------------------
bot = ChatBot("chatbot", read_only = False, logic_adaptors = ["chatterbot.logic.BestMatch"])

# ------------------------ TRAIN CHATBOT ------------------------
trainer2 = ListTrainer(bot)
trainer2.train(conversation_data)


# ------------------------ MAIN ------------------------
if __name__ == "__main__":
    app.run(debug=True)
    # chat_loop()
