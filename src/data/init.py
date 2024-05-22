from pymongo import MongoClient

from dotenv import load_dotenv

import os

# Determine the environment (default to production)
env = os.getenv('ENV', 'production')

# Map the environment to the corresponding .env file
if env == 'development':
    env_file = '.env.development'
elif env == 'staging':
    env_file = '.env.staging'
else:
    env_file = '.env.production'

# Load the .env file
load_dotenv(env_file)

mongoClient = MongoClient(
    f"mongodb+srv://{os.getenv('MONGODB_CREDENTIALS')}@atlascluster.2zt2wrb.mongodb.net/",
    uuidRepresentation="standard"
)

def get_db():
    """Connect to MongoDB database instance"""

    db = mongoClient[f"{os.getenv('MONGODB_DB')}"]
    account_col = db['Account']
    invite_col = db['Invite']
    password_reset_col = db['PasswordReset']
    payment_account_col = db['PaymentAccount']
    checkout_session_metadata_col = db['CheckoutSessionMetadata']
    tos_col = db['TermsOfService']
    plan_col = db['Plan']
    usage_history_col = db['UsageHistory']
    comfyui_col = db['ComfyUI']
    settings_col = db['Settings']
    midjourney_col = db['Midjourney']
    midjourney_prompt_col = db['MidjourneyPrompt']
    referral_col = db['Referral']
    payout_submission_col = db['PayoutSubmission']
    payout_history_col = db['PayoutHistory']
    earnings_col = db['Earnings']
    statistics_col = db['Statistics']
    bug_col = db['Bug']
    deepfake_col = db['Deepfake']
    social_account_col = db['SocialAccount']
    # member_col = db['Member']

    return (account_col, 
            invite_col, 
            password_reset_col, 
            payment_account_col, 
            checkout_session_metadata_col, 
            tos_col, 
            plan_col, 
            usage_history_col, 
            comfyui_col, 
            settings_col, 
            midjourney_col, 
            midjourney_prompt_col, 
            referral_col, 
            payout_submission_col, 
            payout_history_col, 
            earnings_col, 
            statistics_col, 
            bug_col, 
            deepfake_col, 
            social_account_col)

(account_col, 
 invite_col, 
 password_reset_col, 
 payment_account_col, 
 checkout_session_metadata_col, 
 tos_col, 
 plan_col, 
 usage_history_col, 
 comfyui_col,
 settings_col, 
 midjourney_col, 
 midjourney_prompt_col, 
 referral_col, 
 payout_submission_col, 
 payout_history_col, 
 earnings_col, 
 statistics_col, 
 bug_col, 
 deepfake_col, 
 social_account_col )= get_db()