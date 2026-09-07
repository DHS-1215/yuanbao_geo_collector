from datetime import datetime


def build_manifest(
        results,
        batch_id: str,
):
    success = sum(
        1
        for r in results
        if r.status == "success"
    )

    failed = len(results) - success

    return {
        "platform": "yuanbao",
        "batch_id": batch_id,
        "created_at": datetime.now().isoformat(),

        "total": len(results),

        "success": success,

        "failed": failed,
    }
