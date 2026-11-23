"""実SQLiteと固定ベクトルで、索引作成から検索までを確認する。APIは呼ばない。"""

import json
from unittest.mock import Mock

import pytest

from app import retrieval
from scripts.build_rag_index import build_index


@pytest.fixture
def materials(tmp_path):
    source = tmp_path / "lectures.json"
    source.write_text(json.dumps([
        {"id": f"lec{n:02d}-main", "title": f"講義{n}", "content": [
            {"section": "章", "content": [
                {"id": f"lec{n:02d}-main-p001", "title": f"ページ{n}",
                 "page": 1, "content": f"本文{n}"}]}]}
        for n in (1, 2, 5)
    ], ensure_ascii=False), encoding="utf-8")
    return source, tmp_path / "index.sqlite3"


def test_built_index_can_be_searched(materials, monkeypatch):
    source, database = materials
    texts = []

    def embed(text, task):
        assert task == "RETRIEVAL_DOCUMENT"
        texts.append(text)
        return [1, 0] if "本文1" in text else [0, 1]

    result = build_index(source, database, embedder=embed)
    assert result["pages"] == 2  # 第5回の資料は検索対象に含めない
    assert all("章" in text and "ページ" in text for text in texts)
    monkeypatch.setattr(retrieval, "RAG_DB", database)
    monkeypatch.setattr(retrieval, "embed_text", lambda *_: [1, 0])
    hits = retrieval.search("質問")
    assert [h["page_id"] for h in hits] == ["lec01-main-p001", "lec02-main-p001"]
    assert hits[0]["content"] == "本文1"
    assert hits[0]["distance"] == pytest.approx(0)


def test_search_with_neighbors_stays_in_document_and_deduplicates(monkeypatch):
    pages = [
        {"page_id": f"lec01-main-p{i:03}", "document_id": "lec01-main",
         "page": i, "content": f"本文1-{i}"}
        for i in range(1, 4)
    ] + [
        {"page_id": f"lec02-main-p{i:03}", "document_id": "lec02-main",
         "page": i, "content": f"本文2-{i}"}
        for i in range(1, 3)
    ]
    hits = [
        {**pages[1], "distance": 0.1},
        {**pages[2], "distance": 0.2},
        {**pages[3], "distance": 0.3},
    ]
    monkeypatch.setattr(retrieval, "load_pages", lambda *_: pages)
    monkeypatch.setattr(retrieval, "search", lambda *_: hits)

    results = retrieval.search_with_neighbors("質問")

    assert [page["page_id"] for page in results] == [
        "lec01-main-p002", "lec01-main-p003", "lec02-main-p001",
        "lec01-main-p001", "lec02-main-p002",
    ]
    assert len({page["page_id"] for page in results}) == len(results)
    assert [page["is_neighbor"] for page in results] == [False, False, False, True, True]
    assert results[3]["matched_page_id"] == "lec01-main-p002"
    assert results[3]["content"] == "本文1-1"
    assert results[-1]["matched_page_id"] == "lec02-main-p001"


def test_existing_index_survives_failed_rebuild(materials):
    source, database = materials
    build_index(source, database, embedder=lambda *_: [1, 0])
    before = database.read_bytes()
    embed = Mock(side_effect=RuntimeError("埋め込みに失敗"))
    with pytest.raises(FileExistsError):
        build_index(source, database, embedder=embed)
    embed.assert_not_called()
    with pytest.raises(RuntimeError, match="埋め込みに失敗"):
        build_index(source, database, rebuild=True, embedder=embed)
    assert database.read_bytes() == before
    assert not list(database.parent.glob(".rag-build-*"))
