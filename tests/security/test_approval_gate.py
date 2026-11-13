from aura.security.approval import ApprovalGate
from aura.security.permissions import PermissionEngine

def test_approval_lifecycle():
    ApprovalGate.create_request("req_101", "send_email", {"to": "prof@university.edu"})
    assert ApprovalGate.is_approved("req_101") is False
    assert ApprovalGate.approve("req_101") is True
    assert ApprovalGate.is_approved("req_101") is True

def test_permission_boundaries():
    assert PermissionEngine.is_permitted("search") is True
    assert PermissionEngine.is_permitted("execute_terminal") is False