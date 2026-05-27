import time
import timeit
from pathlib import Path
from plugins.memory.holographic.store import MemoryStore
from plugins.memory.holographic.retrieval import FactRetriever
import plugins.memory.holographic.store as store_module
import plugins.memory.holographic.retrieval as retrieval_module

def setup_db():
    store = MemoryStore(":memory:")
    # Create 500 facts
    conn = store._conn
    for i in range(500):
        # Insert fact
        conn.execute(
            "INSERT INTO facts (content, category, trust_score, hrr_vector) VALUES (?, ?, ?, ?)",
            (f"Fact content {i}", "general", 1.0, b'mock_hrr_vector_bytes')
        )
        fact_id = i + 1

        # Insert some entities for this fact
        for j in range(3):
            entity_name = f"Entity_{i}_{j}"
            conn.execute("INSERT OR IGNORE INTO entities (name) VALUES (?)", (entity_name,))
            res = conn.execute("SELECT entity_id FROM entities WHERE name = ?", (entity_name,)).fetchone()
            entity_id = res["entity_id"]

            conn.execute(
                "INSERT INTO fact_entities (fact_id, entity_id) VALUES (?, ?)",
                (fact_id, entity_id)
            )
    conn.commit()
    return store

def run_benchmark():
    store = setup_db()
    retrieval = FactRetriever(store)

    def test_func():
        # Mock numpy to bypass numpy check
        retrieval_module.hrr._HAS_NUMPY = True
        # Mock hrr.bytes_to_phases and similarity so it doesn't crash
        class MockVec: pass
        retrieval_module.hrr.bytes_to_phases = lambda x: MockVec()
        retrieval_module.hrr.similarity = lambda x, y: 0.5

        # We only want to test the db lookup part, not the whole thing which is heavily dominated by similarity logic

        conn = store._conn
        where = "WHERE f.hrr_vector IS NOT NULL"
        params = []
        rows = conn.execute(
            f"""
            SELECT f.fact_id, f.content, f.category, f.tags, f.trust_score,
                   f.created_at, f.updated_at, f.hrr_vector
            FROM facts f
            {where}
            """,
            params,
        ).fetchall()

        _MAX_CONTRADICT_FACTS = 500
        if len(rows) > _MAX_CONTRADICT_FACTS:
            rows = sorted(rows, key=lambda r: r["updated_at"] or r["created_at"], reverse=True)
            rows = rows[:_MAX_CONTRADICT_FACTS]

        # THIS IS THE PART WE'RE TESTING
        fact_entities: dict[int, set[str]] = {}
        fact_ids = [row["fact_id"] for row in rows]
        if fact_ids:
            placeholders = ",".join(["?"] * len(fact_ids))
            entity_rows = conn.execute(
                f"""
                SELECT fe.fact_id, e.name
                FROM entities e
                JOIN fact_entities fe ON fe.entity_id = e.entity_id
                WHERE fe.fact_id IN ({placeholders})
                """,
                fact_ids,
            ).fetchall()

            for r in entity_rows:
                fid = r["fact_id"]
                if fid not in fact_entities:
                    fact_entities[fid] = set()
                fact_entities[fid].add(r["name"].lower())

    number = 100
    total_time = timeit.timeit(test_func, number=number)
    print(f"Average time for DB fetches (IN approach): {total_time / number * 1000:.2f} ms")

if __name__ == "__main__":
    run_benchmark()
