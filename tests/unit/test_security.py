from aura.security.permissions import PermissionEngine

def test_auto_permitted_actions():
    assert PermissionEngine.is_permitted("search") is True
    assert PermissionEngine.is_permitted("plan") is True
    assert PermissionEngine.is_permitted("synthesize") is True

def test_restricted_actions_require_approval():
    assert PermissionEngine.is_permitted("send_email") is False
    assert PermissionEngine.is_permitted("delete_file") is False
    assert PermissionEngine.is_permitted("execute_terminal") is False