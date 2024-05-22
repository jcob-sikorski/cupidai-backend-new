# from typing import List

# import service.account as account_service

# from model.team import Team, Member, Invite

# from pymongo import ReturnDocument
# from .init import invite_col, team_col, member_col

# def accept(invite_id: str) -> None:
#     invite = account_service.get_invite(invite_id)

#     # TODO: if user is a new one then also require him to signup (redirect him somehow)
#     #       and check in Kinde if he registered successfully

#     # Check if the user is already in another team
#     existing_team = team_col.find_one({"members": {"$in": [invite.guest_id]}})
    
#     if existing_team:
#         print(f"User {invite.guest_id} is already in another team.")
#         return False

#     # Add the user id to the member list
#     host_team = team_col.find_one({"members": {"$in": [invite.host_id]}})
#     if host_team:
#         host_team["members"].append(invite.guest_id)
#         team_col.find_one_and_update(
#             {"_id": host_team["_id"]},
#             {"$set": {"members": host_team["members"]}}
#         )

#     # Create the member model
#     member = Member(user_id=invite.guest_id, permissions=[])
#     member_col.insert_one(member.dict())

#     invite_col.delete_one({"_id": invite_id})

#     return True

# 
# def update_permissions(permissions: List[str], member_id: str, user_id: str) -> bool:
#     # Fetch the team that the user owns
#     team = team_col.find_one({"owner": user_id})

#     # If the user is not an owner of any team, return False
#     if not team:
#         return False

#     # Check if the member is in the same team
#     if member_id not in team["members"]:
#         return False

#     # Update the permissions of the member
#     result = member_col.find_one_and_update(
#         {"user_id": member_id},
#         {"$set": {"permissions": permissions}},
#         upsert=True,
#         return_document=ReturnDocument.AFTER
#     )

#     # Return True if the update was successful, False otherwise
#     return result is not None


# 
# def delete(member_id: str, user_id: str) -> bool:
#     # Fetch the team that the user owns
#     team = team_col.find_one({"owner": user_id})

#     # If the user is not an owner of any team, return False
#     if not team:
#         return False

#     # Check if the member is in the same team
#     if member_id not in team["members"]:
#         return False

#     # Remove the member_id from the team's members list
#     team["members"].remove(member_id)

#     # Update the team document in the database
#     team_col.find_one_and_update(
#         {"_id": team["_id"]},
#         {"$set": {"members": team["members"]}}
#     )

#     # Delete the member model
#     member_col.delete_one({"user_id": member_id})

#     return True


# 
# def transfer_ownership(member_id: str, user_id: str) -> bool:
#     # Fetch the team that the user owns
#     team = team_col.find_one({"owner": user_id})

#     # If the user is not an owner of any team, return False
#     if not team:
#         return False

#     # Check if the member is in the same team
#     if member_id not in team["members"]:
#         return False

#     # Update the owner of the team
#     result = team_col.find_one_and_update(
#         {"_id": team["_id"]},
#         {"$set": {"owner": member_id}}
#     )

#     # Return True if the update was successful, False otherwise
#     return result is not None


# 
# def get_members(user_id: str) -> None:
#     # Fetch the team that the user belongs to
#     team = team_col.find_one({"members": {"$in": [user_id]}})
    
#     if team:
#         # Return the members of the team
#         return team["members"]

# def get_activity(user_id: str) -> None:
#     # TODO: to be implemented
#     pass

# def get_team_name(user_id: str) -> None:
#     result = team_col.find_one({"members": {"$in": [user_id]}})
#     if result is not None:
#         team = Team(**result)
#         return team.name
#     return None

# 
# def disband(user_id: str) -> bool:
#     # Fetch the team that the user owns
#     team = team_col.find_one({"owner": user_id})
    
#     if team:
#         # Remove the team document from the database
#         team_col.delete_one({"_id": team["_id"]})
        
#         # Remove the member models of the team
#         for member_id in team["members"]:
#             member_col.delete_one({"user_id": member_id})

#         return True

#     # If the user does not own a team, return False
#     return False


# 
# def create(team: Team, user_id: str) -> bool:
#     # Fetch the team that the user is a member of
#     existing_team = team_col.find_one({"members": {"$in": [user_id]}})
    
#     # If the user is already in a team, return False
#     if existing_team:
#         return False

#     # If the user is not in a team, add them to the new team
#     if user_id not in team.members:
#         team.members.append(user_id)
#         # Create a new Member object with no permissions and add it to the member_col collection
#         new_member = Member(user_id=user_id, permissions=[])
#         member_col.insert_one(new_member.dict())

#     # For each member in the team, if they are not already in the member_col collection, add them
#     for member_id in team.members:
#         if member_col.find_one({"user_id": member_id}) is None:
#             new_member = Member(user_id=member_id, permissions=[])
#             member_col.insert_one(new_member.dict())
    
#     # Insert the new team into the database
#     result = team_col.insert_one(team.dict())
    
#     # Return True if the insert was successful, False otherwise
#     return result.inserted_id is not None


# 
# def leave(user_id: str) -> bool:
#     # Fetch the team that the user is a member of
#     team = team_col.find_one({"members": {"$in": [user_id]}})
    
#     if team:
#         # If the user is the owner of the team, raise an exception
#         if team["owner"] == user_id:
#             raise Exception("The owner of the team cannot leave the team.")
        
#         # Remove the user_id from the team's members list
#         team["members"].remove(user_id)
        
#         # Update the team document in the database
#         update_result = team_col.find_one_and_update(
#             {"_id": team["_id"]},
#             {"$set": {"members": team["members"]}}
#         )
        
#         # Remove the member model
#         delete_result = member_col.delete_one({"user_id": user_id})

#         # Return True if both operations were successful, False otherwise
#         return update_result is not None and delete_result.deleted_count > 0

#     # If the user is not a member of any team, return False
#     return False


# 
# def owner(user_id: str) -> None:
#     # Fetch the team that the user is a member of
#     team = team_col.find_one({"members": {"$in": [user_id]}})
    
#     if team:
#         # Return the owner of the team
#         return team["owner"]
    
# 
# def get_team(user_id: str) -> None:
#     result = team_col.find_one({"members": {"$in": [user_id]}})
#     if result is not None:
#         team = Team(**result)
#         return team
#     return None

# def get_member(user_id: str) -> None:
#     result = member_col.find_one({"user_id": user_id})
#     if result is not None:
#         member = Member(**result)
#         return member
#     return None