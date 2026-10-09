import json

from app.yuanbao.exporter import YuanbaoExporter
from app.yuanbao.geo_contract import resolve_product
from app.yuanbao.result import YuanbaoCollectionResult


def test_resolve_tianyishou_product():
    assert resolve_product(
        "tianyishou"
    ) == (
        "tianyishou",
        "天益寿气血固本口服液",
    )


def test_tianyishou_manifest_identity(
        tmp_path,
):
    result = YuanbaoCollectionResult(
        question="气血固本口服液是什么？",
        answer="测试回答",
        model="Hy3",
        mode="快速回答",
        conversation_url=(
            "https://yuanbao.tencent.com/test"
        ),
        task_id="yb_t_test",
        question_id="ybq_test",
        mode_code="quick",
        batch_id="batch_tianyishou_test",
        product="天益寿气血固本口服液",
    )

    exporter = YuanbaoExporter(
        product_id="tianyishou",
        product_name="天益寿气血固本口服液",
    )

    exporter.export(
        [result],
        str(tmp_path),
    )

    manifest = json.loads(
        (
            tmp_path
            / "manifest.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        manifest["product_id"]
        == "tianyishou"
    )

    assert (
        manifest["product_name"]
        == "天益寿气血固本口服液"
    )

    assert (
        manifest["batch_id"]
        == "batch_tianyishou_test"
    )
