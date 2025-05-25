# ------------------------ HEADERS ------------------------
from chatterbot import ChatBot 
from chatterbot.trainers import ListTrainer
import json
import google.generativeai as genai
import sympy
import re
from flask import Flask, render_template, request

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
genai.configure(api_key="AIzaSyBPF1DgslxkhLp2oXJtCY4FH7mTjk6hrN0")

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

knowledge_base: dict = load_knowledge_base('knowledge_base.json')

def write_bot_learn(user_input, new_answer):
    knowledge_base["questions"].append({"question": [user_input], "answer": [new_answer]})
    save_knowledge_base('knowledge_base.json', knowledge_base)

with open("knowledge_base.json", "r", encoding="utf-8") as file:
    data = json.load(file)
conversation_data_2 = []

conversation_data_2 = []
for que in data["questions"]:
    for user_input in que["question"]:
        for response in que["answer"]:
            conversation_data_2.append(user_input)  # Question
            conversation_data_2.append(response)  # Answer

# ------------------------ CHAT LOOP ------------------------
def chat_loop(user_response, x):
    while True:
        if x == "0":   
            if user_response.lower() in ["exit", "quit", "bye", "good bye"]:
                return str("Chatbot: Goodbye!")

            user_input = user_response
            if re.search(r'^[\d\s+\-*/().^]+$', user_input):
                if is_math_expression(user_input):
                    response = handle_math_query(user_input)
                    return str("Chatbot: " + response)

            if user_response.lower() in ["not satisfied", "try again", "ask google", "ask bard", "ask gemini", "check with gemini", "check with google"]:
                stack.append("1")
                respo.append(user_input)
                return str("Chatbot: Would you like me to check with google bard? (yes/no): ")
            response = str(get_chatterbot_response(user_response))

            if response != "None":
                return str("Chatbot: " + response)
            else:
                stack.append("1")
                respo.append(user_input)
                return str("Chatbot: I don't have an answer. Do you want me to check Google Bard? (yes/no): ")

        if x == "1":
            if user_response == "yes":
                p1_user_response = respo.pop()
                bard_response = get_bard_response(p1_user_response).strip()
                write_bot_learn(p1_user_response, bard_response)
                return "Google Bard: "+ bard_response
            elif user_response == "no":
                stack.append("2")
                return str("Chatbot: Okay. Would you like to teach me? (yes/no): ")
            else:
                stack.append("1")
                return str("Chatbot: Please enter either yes or no:")
        
        if x == "2":
            if user_response == "yes":
                stack.append("3")
                return str("Chatbot: Type the response: ")
            else:
                return str("Chatbot: Okay, let me know if you have another question!")

        if x == "3":
            p1_user_response = respo.pop()
            write_bot_learn(p1_user_response, user_response)
            return str("Chatbot: Thank you! I've learned something new.")

# ------------------------ FLASK INTEGRATION ------------------------
app = Flask(__name__)
@app.route("/")
def main():
    return render_template("index.html")

stack = ["0"]
respo = []

@app.route("/get")
def get_chatbot_response():
    userText = request.args.get('userMessage')
    x = stack.pop()
    if x == "0":
        stack.append("0")
    chat_result = chat_loop(userText, x)
    return str(chat_result)


# ------------------------ CHATBOT OBJECT ------------------------
bot = ChatBot("chatbot", read_only = False, logic_adaptors = ["chatterbot.logic.BestMatch"])

# ------------------------ TRAIN CHATBOT ------------------------
trainer2 = ListTrainer(bot)
trainer2.train(conversation_data_2)
trainer1 = ListTrainer(bot)
trainer1.train(conversation_data)



# ------------------------ MAIN ------------------------
if __name__ == "__main__":
    app.run(debug=True, threaded=True)
