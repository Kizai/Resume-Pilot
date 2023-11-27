from tools.resume_pilot_app import ResumePilotApp
from config import LAYOUT, CHATBOT_HEIGHT, PORT


def main():
    app = ResumePilotApp()
    app.main_interface(LAYOUT, CHATBOT_HEIGHT, PORT)


if __name__ == '__main__':
    main()
