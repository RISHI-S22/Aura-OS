from typing import Set

class PermissionEngine:
    AUTO_PERMITTED: Set[str] = {"search", "read_file", "plan", "synthesize"}
    REQUIRE_APPROVAL: Set[str] = {"send_email", "delete_file", "execute_terminal"}

    @classmethod
    def is_permitted(cls, action: str) -> bool:
        return action in cls.AUTO_PERMITTED
