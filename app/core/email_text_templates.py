# flake8: noqa
import datetime


def get_game_generation_alert_email_text(game_date: datetime.date):
    return f"""
        Game could be generated for date: {game_date} because no names were available.

        How to fix this:
        1. Log into App Admin.
        2. Generate new questionnaire(s) (with names) - this step is optional if names are already available 
        but the their difficulty level has not been set.
        3. Set difficulty level for names.
        4. Manually generate new games. 
        
        Good luck :)
        
        This is an automated message.
    """
