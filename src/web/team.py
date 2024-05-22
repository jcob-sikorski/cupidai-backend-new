# from fastapi import APIRouter, Depends

# from typing import List

# from model.team import Team

# from service import team as service

# router = APIRouter(prefix="/team")

# 
# @router.post("/accept/{invite_id}", status_code=201)  # Accepts the invite
# async def accept(invite_id: str) -> None:
#     return service.accept(invite_id)

# 
# @router.post("/members/invite", status_code=201)  # Invites a new member
# async def invite(email: str, user_id: str) -> None:
#     return service.invite(email, user_id)

# 
# 
# @router.patch("/members/{member_id}/permissions", status_code=200)  # Updates permissions of a member
# async def update_permissions(permissions: List[str], member_id: str, user_id: str) -> None:
#     return service.update_permissions(permissions, member_id, user_id)

# 
# 
# @router.delete("/members/{member_id}", status_code=204)  # Removes a member, status 204 for No Content
# async def delete(member_id: str, user_id: str) -> None:
#     return service.delete(member_id, user_id)

# 
# 
# @router.patch("/ownership", status_code=200)  # Transfers ownership, status 200 for successful update
# async def transfer_ownership(member_id: str, user_id: str) -> None:
#     return service.transfer_ownership(member_id, user_id)

# 
# 
# @router.get("/members", status_code=200)  # Lists members, status 200 for OK
# async def get_members(user_id: str) -> None:
#     return service.get_members(user_id)

# 
# @router.get("/members/activity", status_code=200)  # Lists members activity, status 200 for OK
# async def get_activity(user_id: str) -> None:
#     return service.get_activity(user_id)

# 
# 
# @router.delete("/disband", status_code=204)  # Disbands the group, status 204 for No Content
# async def disband(user_id: str) -> None:
#     return service.disband(user_id)

# 
# 
# @router.post("/create", status_code=200)  # Creates a group, status 200 for OK
# async def create(team: Team, user_id: str) -> None:
#     return service.create(team, user_id)

# 
# 
# @router.post("/leave", status_code=200)  # Member initiates leave, status 200 for OK
# async def leave(user_id: str) -> None:
#     try:
#         return service.leave(user_id)
#     except Exception as e:
#         return str(e)

# 
# 
# @router.get("/owner", status_code=200)  # Gets the group owner, status 200 for OK
# async def owner(user_id: str) -> None:
#     return service.owner(user_id)
