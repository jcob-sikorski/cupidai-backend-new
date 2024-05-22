from bson.objectid import ObjectId

from typing import Optional

from model.account import Account, Invite, PasswordReset

from pymongo import ReturnDocument
from .init import account_col, invite_col, password_reset_col

def signup(email: str, 
           username: str, 
           password_hash: str) -> None:
    # Check if an account with the provided username exists
    existing_username_account = account_col.find_one({"username": username})
    if existing_username_account:
        raise ValueError("Username already exists")
    
    # Check if an account with the provided email exists
    existing_email_account = account_col.find_one({"email": email})
    if existing_email_account:
        raise ValueError("Email already exists")

    # Create a new account
    account = Account(user_id=str(ObjectId()), email=email, username=username, password_hash=password_hash)
    account_col.insert_one(account.dict())

    # Optionally, return the newly created account
    return account


def create_invite(invite: Invite):
    result = invite_col.insert_one(invite.dict())


def change_email(email: str, user: Account) -> bool:
    result = account_col.find_one_and_update(
        {"user_id": user.user_id},
        {"$set": {"email": email}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )

    if not result:
        raise ValueError("Failed to change email - user does not exist.")


def get_by_username(username: str) -> Optional[Account]:
    print("GETTING USER DETAILS")
    result = account_col.find_one({"username": username})

    if result is not None:
        account = Account(**result)
        return account
    return None

def get_by_id(user_id: str) -> Optional[Account]:
    print("GETTING USER DETAILS BY USER_ID")
    result = account_col.find_one({"user_id": user_id})

    if result is not None:
        account = Account(**result)
        return account
    return None

def get_by_email(email: str) -> Optional[Account]:
    print("GETTING USER DETAILS BY EMAIL")
    result = account_col.find_one({"email": email})

    if result is not None:
        account = Account(**result)
        return account
    return None


def change_profile_picture(profile_uri: str, user: Account) -> None:
    result = account_col.find_one_and_update(
        {"user_id": user.user_id},
        {"$set": {"profile_uri": profile_uri}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )

    if not result:
        raise ValueError("Failed to change profile picture - user does not exist.")

def delete(user: Account) -> None:
    # Find and delete the account with the given user_id
    result = account_col.delete_one({"user_id": user.user_id})

    # Check if an account was actually deleted
    if result.deleted_count == 0:
        raise ValueError("No account found with this user ID")


# def get_invite(invite_id: str) -> None:
#     print("GETTING INVITE DETAILS")
#     result = invite_col.find_one({"_id": invite_id})

#     if result is not None:
#         invite = Invite(**result)
#         return invite
#     return None

def create_password_reset(password_reset: PasswordReset):
    result = password_reset_col.insert_one(password_reset.dict())

def get_password_reset(password_reset_id: str) -> None:
    print("GETTING PASSWORD RESET DETAILS")
    result = password_reset_col.find_one({"reset_id": password_reset_id})

    if result is not None:
        password_reset = PasswordReset(**result)
        return password_reset
    return None

# TODO: check how service interacts with password field and rename user.password
#       to user.password_hash

# TODO: we should not always make upserts because it's unsafe like in this case
#       updates only should suffice
def set_new_password(password_hash: str, user_id: str) -> None:
    print("SETTING NEW PASSWORD")
    result = account_col.find_one_and_update(
        {"user_id": user_id},
        {"$set": {"password_hash": password_hash}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )

    return result is not None

def disable_password_reset(reset_id: str) -> bool:
    print("MARKING THE PASSWORD RESET AS USED")
    result = password_reset_col.find_one_and_update(
        {"reset_id": reset_id},
        {"$set": {"is_used": True}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )

    return result is not None