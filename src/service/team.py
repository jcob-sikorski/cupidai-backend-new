# from typing import List

# import requests

# import data.team as data

# from model.account import Invite
# from model.team import Team

# import service.account as account_service
# import service.email as email_service
# import service.team as team_service

# import uuid

# # TODO: we have to get recipient name from Kinde
# # TODO: set up forgot password and referral buys plan emails
# # TODO: make sure Shaun doesn't remove you from the team

# def accept(invite_id: str) -> None:
#     invite = account_service.get_invite(invite_id)
#     if data.accept(invite_id):
#         host = account_service.get(invite.host_id)
#         guest = account_service.get(invite.guest_id)

#         team_name = team_service.get_team_name(invite.host_id)

#         email_service.send(email=host.email, transactional_id="cltev2j2v02nbofl1p13dz5sk", guest_email=guest.email, team_name=team_name)

# def invite(guest_email: str, host_id: str) -> None:
#     host_as_member = get_member(host_id)

#     if host_as_member and ('invite' in host_as_member.permissions):
#         guest = account_service.get_by_email(guest_email)
#         host = account_service.get(host_id)

#         team_name = data.get_team_name(host_id)

#         invite_id = str(uuid.uuid4())

#         invite_link = f"https://cupidai.tech/team/accept/{invite_id}"

#         invite_model = Invite(
#             invite_id = invite_id,
#             guest_id = getattr(guest, 'user_id', None),
#             host_id = host_id,
#             signup_required = (guest is None)
#         )

#         account_service.create_invite(invite_model)

#         email_service.send(email=host.email, transactional_id="cluwp8qn000xw4hezrgsxau36", host_email=host.email, team_name=team_name, invite_link=invite_link)

#         # TODO: billing permission and team permission are not the same thing
#         #       the billing permissions are the max the team can have
#         #       the team permissions start from zero and can increase 
#         #       into the billing permissions
#     else:
#         return # TODO: return some error here

# 
# def update_permissions(permissions: List[str], member_id: str, user_id: str) -> None:
#     return data.update_permissions(permissions, member_id, user_id)

# 
# def delete(member_id: str, user_id: str) -> None:
#     return data.delete(member_id, user_id)

# 
# def transfer_ownership(member_id: str, user_id: str) -> None:
#     if data.transfer_ownership(member_id, user_id):
#         team_name = team_service.get_team_name(user_id)

#         new_owner = account_service.get(member_id)
#         old_owner = account_service.get(user_id)

#         email_service.send(email=new_owner.email, transactional_id="cluwpfxvd0a0nh991vscb3y0b", old_owner=old_owner.email, team_name=team_name)

#         email_service.send(email=old_owner.email, transactional_id="cluwpvrgx03u3k2unkpll3vnp", new_owner=new_owner.email, team_name=team_name)

# 
# def get_members(user_id: str) -> None:
#     return data.get_members(user_id)

# def get_activity(user_id: str) -> None:
#     return data.get_activity(user_id)
    
# def get_team_name(user_id: str) -> None:
#     return data.get_team_name(user_id)

# 
# def disband(user_id: str) -> None:
#     team_name = team_service.get_team_name(user_id)

#     if data.disband(user_id):
#         account = account_service.get(user_id)

#         email_service.send(account.email, team_name=team_name)

# 
# def create(team: Team, user_id: str) -> None:
#     return data.create(team, user_id)

# 
# def leave(user_id: str) -> None:
#     team = team_service.get_team(user_id)
    
#     if data.leave(user_id):
#         owner_account = account_service.get(team.owner_id)

#         leaver_account = account_service.get(user_id)

#         email_service.send(email=owner_account.email, transactional_id="cluwq6js302cgkqeo2awjl6fh", leaver_email=leaver_account.email, team_name=team.name)

# 
# def owner(user_id: str) -> None:
#     return data.owner(user_id)

# 
# def get_team(user_id: str):
#     return data.get_team(user_id)

# def get_member(user_id: str):
#     return data.get_member(user_id)