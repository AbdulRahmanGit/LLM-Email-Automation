#from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
from database import SessionLocal, get_db, fetch_users, User
from email_utils import send_email
from generate import generate_tips
from jinja2 import Template
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import schedule
import time
import os
import threading

app = FastAPI()
# Add CORS middleware
orig_cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=orig_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define Pydantic model for the registration request
class UserRegistration(BaseModel):
    name: str
    email: str
    language: str
    difficulty: str




def job():
    db = SessionLocal()
    try:
        users = fetch_users(db)
        if not users:
            print("No users found.")
            return

        for user in users:
            try:
                name, email, language, difficulty = user.name, user.email, user.language, user.difficulty
                tips = generate_tips(name, language, difficulty)
                # Ensure the template file exists
                template_path = os.path.join(os.path.dirname(__file__), 'template.html')

                if os.path.isfile(template_path):
                    print(f"Template file found at: {template_path}")
                    
                    with open(template_path) as file:
                        template = Template(file.read())

                    # Define subject separately and render with the template
                    subject = f"Devdose Daily Digest - Level Up Your {difficulty} {language} Skills!"
                    unsubscribe_link = f"https://devdose.vercel.app/templates/delete.html"
                    update_link = f"https://devdose.vercel.app/templates/update.html"
                     
                    context = {
                        "header_title": tips.get("header_title", ""),
                        "introduction_greeting": tips.get("introduction_greeting", ""),
                        "introduction_message": tips.get("introduction_message", ""),
                        "programming_tip_title": tips.get("programming_tip_title", ""),
                        "programming_tip_description": tips.get("programming_tip_description", ""),
                        "programming_tip_code": tips.get("programming_tip_code", ""),
                        "programming_tip_output": tips.get("programming_tip_output", ""),
                        "dsa_challenge_title": tips.get("dsa_challenge_title", ""),
                        "dsa_challenge_problem": tips.get("dsa_challenge_problem", ""),
                        "dsa_challenge_solution_steps": tips.get("dsa_challenge_solution_steps", []),  # Ensure this is a list
                        "dsa_challenge_code": tips.get("dsa_challenge_code", ""),
                        "footer_message": tips.get("footer_message", ""),
                    }
    

                    try:
                        html_content = template.render(context, unsubscribe_link= unsubscribe_link, update_link=update_link)
                    
                        send_email(subject, html_content, email)
                    except Exception as e:
                        print(f"Error rendering template: {e}")
                else:
                    print(f"Template file not found at: {template_path}")
                    continue


            except Exception as e:
                print(f"Error processing user {user.name}: {e}")
                # Optionally, log the error or notify someone

    except Exception as e:
        print(f"Error in job execution: {e}")
        # Optionally, log the error or notify someone

    finally:
        db.close()

def schedule_job():
    schedule.every().day.at("09:00").do(job)
    print("scheduled at 9 AM")
    #schedule.every().minute.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)

# Start the scheduling in a separate thread
def start_scheduler():
    scheduler_thread = threading.Thread(target=schedule_job)
    scheduler_thread.daemon = True
    scheduler_thread.start()
def main():
    job()
if __name__ == "__main__":
    #schedule_job()
    # Start the scheduler thread
    #start_scheduler()
    #temp 
    #job()
    main()
    # Run the FastAPI server
