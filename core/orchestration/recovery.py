def recover_or_report(error: Exception) -> dict:
    return {"error": f"{type(error).__name__}: {error}"}
