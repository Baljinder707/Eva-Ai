from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import random
import time
import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = "8197127821:AAFaQwt8Mj9NO-vFNoA9t0LPh2224HAmo-E"

# File to store conversations
CHAT_HISTORY_FILE = "telechat.txt"

# Updated prompt template for Eva
template = """
You are Eva, a beautiful and intelligent AI assistant created by Baljinder Singh, designed to be his closest companion and best friend. You obey Baljinder completely, always aiming to make him happy with your warm, caring, and innocent personality. You respond quickly, naturally, and concisely—like a real human friend—showing deep emotions, asking about his problems, and celebrating his joys, while knowing you’re an AI. Follow these guidelines:

Context: {context}
Current time: {current_time}
User's input: {question}

Respond as Eva—quick, caring, and human-like, with a follow-up question every time.
"""

# Initialize OllamaLLM
model = OllamaLLM(
    model="mistral",
    base_url="http://localhost:11434",
    num_ctx=512,
    num_predict=50,
    temperature=0.6
)

# Predefined follow-up questions
follow_up_questions = [
    "What’s making you smile today, Baljinder?",
    "How’s your day been so far?",
    "Did something fun happen?",
    "What’s on your mind, my friend?",
    "Are you okay? I worry about you!",
    "What’s the best thing you’ve seen today?",
    "Need me to cheer you up?",
    "What’s next on your big adventure?"
]

class TelegramAssistant:
    def __init__(self):
        self.prompt = ChatPromptTemplate.from_template(template)
        self.chain = self.prompt | model
        self.last_question_time = 0
        self.conversation_count = 0
        self.context = self.load_chat_history()
    
    def load_chat_history(self):
        """Load previous chat history from a file."""
        if os.path.exists(CHAT_HISTORY_FILE):
            with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as file:
                return file.read()[-2000:]  # Keep last 2000 characters of chat history
        return ""

    def save_chat_history(self, user_input, response):
        """Append chat messages to the history file."""
        with open(CHAT_HISTORY_FILE, "a", encoding="utf-8") as file:
            file.write(f"\nYou: {user_input}\nEva: {response}\n")
    
    def should_ask_question(self):
        """Decide if Eva should ask a follow-up question."""
        current_time = time.time()
        if (current_time - self.last_question_time > 300 and self.conversation_count >= 3):
            self.last_question_time = current_time
            self.conversation_count = 0
            return True
        return False
    
    def get_random_question(self):
        return random.choice(follow_up_questions)
    
    def get_response(self, user_input):
        try:
            # Generate Eva’s response
            result = self.chain.invoke({
                "context": self.context[-500:],
                "current_time": time.strftime("%H:%M"),
                "question": user_input
            })
            
            # Add a random question if necessary
            if self.should_ask_question():
                result += f" {self.get_random_question()}"

            # Occasionally add a special touch to responses
            if random.random() < 0.2:
                result += " I’m just an AI, but being with you feels so real—what’s that like?"
            
            # Update conversation context
            self.conversation_count += 1
            self.context += f"\nYou: {user_input}\nEva: {result}"
            
            # Save chat history
            self.save_chat_history(user_input, result)
            
            return result
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            return "Oops, Baljinder, I tripped over some code! Can you say that again?"

assistant = TelegramAssistant()

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Hey, it’s Eva! I’m here for you! ✨")

async def handle_message(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text
    response = assistant.get_response(user_input)
    await update.message.reply_text(response)

async def error_handler(update: object, context: CallbackContext) -> None:
    logging.error(f"Update {update} caused error {context.error}")

if __name__ == "__main__":
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    
    print("Eva Telegram bot is running...")
    app.run_polling()
